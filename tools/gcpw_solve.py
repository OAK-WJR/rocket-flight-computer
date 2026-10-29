#!/usr/bin/env python3
"""2-D quasi-static field solver for the board's grounded coplanar waveguide (REQUIREMENTS F10, R9 gate R-5).

usage: python3 tools/gcpw_solve.py [--w 0.30] [--gap 0.25 | --gaps 0.25,0.31] [--bare] [--json OUT]
       python3 tools/gcpw_solve.py --validate         re-run R7 pass 2's three solves and compare
       python3 tools/gcpw_solve.py --gmax 52.5        the largest symmetric gap that keeps Z0 <= 52.5 ohm

Plain python3 (no numpy, no pcbnew), so the gate runs it under KiCad's Python too. The method is R7 review pass 2's
(sources/r7_review/pass2_rf.md section 7, whose scripts were never committed): 2-D finite volume on a non-uniform
tensor grid, a symmetric half domain (full domain when the two gaps differ), a grounded lid 3 mm above the reference
plane, the side wall Neumann, SOR to a 1e-8 residual. The line's capacitance comes from the field energy,
C = sum(eps * |grad phi|^2) at 1 V, with the dielectrics (C) and in vacuum (C0); Z0 = 1 / (c * sqrt(C * C0)) and
eps_eff = C / C0. The stack is JLC041611-7628 as ordered (pass2_rf section 3.1): F.Cu 0.035 mm over 0.203 mm of
7628 prepreg (er 4.4) on In1, then In1 0.030 mm and the 1.03 mm core (er 4.38) on In2. The solder mask is conformal
(er 3.8): 0.025 mm on the laminate in the gaps and 0.015 mm on the copper's top and sides (pass2_rf section 3.2).
The conductors are rectangles (JLC's engine uses a trapezoid; pass 2 found the two within 0.1 ohm).

Validation (`--validate`, tools/test_r9_check.py): pass 2 gives 50.3 ohm / eps_eff 3.18 coated and 52.2 ohm / 2.95
bare for W 0.30 / gap 0.25 over In1, and 49.0 ohm coated for the SMA launch pad (W 1.2, gap 0.30, In1 cut out, so
referenced to In2). This solver must reproduce each within 1 ohm.

Monotonicity: widening a gap removes ground conductor, which lowers both C and C0 (the capacitance of a conductor
system only falls when a grounded conductor shrinks), so Z0 rises with each gap. A section whose two gaps both lie
in [g_lo, g_hi] therefore has Z0(g_lo, g_lo) <= Z0 <= Z0(g_hi, g_hi): the gate needs only symmetric solves.
"""
import argparse
import json
import math
import sys

C_LIGHT = 299792458.0
EPS0 = 8.8541878128e-12
# JLC041611-7628 (pass2_rf section 3.1), mm and relative permittivity
T_CU = 0.035          # outer copper
H_PREPREG, ER_PREPREG = 0.203, 4.4
T_IN1 = 0.030
H_CORE, ER_CORE = 1.03, 4.38
ER_MASK, MASK_ON_LAMINATE, MASK_ON_COPPER = 3.8, 0.025, 0.015
LID = 3.0             # grounded lid height above the reference plane (pass2_rf section 7)
SIDE = 3.0            # half width of the domain beyond which the field is negligible (Neumann wall)
TOL = 1e-8
# pass2_rf section 3.2: the figures this solver must reproduce (ohm, eps_eff)
PASS2 = {'gcpw_coated': (50.3, 3.18), 'gcpw_bare': (52.2, 2.95), 'launch_coated': (49.0, None)}


def _grade(points, fine, coarse, ratio=1.25):
    """Grid lines: every value in `points` (sorted, deduplicated), refined to `fine` next to each point and growing by
    `ratio` up to `coarse` between them."""
    pts = sorted(set(round(p, 9) for p in points))
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        seg = b - a
        if seg <= 1e-12:
            continue
        # grow from both ends towards the middle
        left, right = [], []
        step, pos = fine, 0.0
        while pos + step < seg / 2:
            pos += step
            left.append(pos)
            step = min(step * ratio, coarse)
        step, pos = fine, 0.0
        while pos + step < seg / 2:
            pos += step
            right.append(seg - pos)
            step = min(step * ratio, coarse)
        inner = sorted(set(round(v, 9) for v in left + right))
        # drop lines that crowd the midpoint (closer than half the local step)
        clean = []
        for v in inner:
            if clean and v - clean[-1] < fine * 0.5:
                continue
            clean.append(v)
        out.extend(a + v for v in clean)
        out.append(b)
    return out


class Section:
    """One cross-section: signal W at x in [xs0, xs1], coplanar ground beyond each gap, a reference plane at y = 0.

    layers: [(top_y, er)] of the dielectric stack from the reference plane up to the copper's underside (y = h)."""

    def __init__(self, w, gap_left, gap_right, layers, coated=True, t=T_CU, side=SIDE, lid=LID, fine=0.004,
                 coarse=0.12, symmetric=None):
        self.w, self.gl, self.gr, self.t = w, gap_left, gap_right, t
        self.layers = layers
        self.h = layers[-1][0]
        self.coated = coated
        self.sym = (abs(gap_left - gap_right) < 1e-9) if symmetric is None else symmetric
        h, t_ = self.h, t
        cm, cl = (MASK_ON_COPPER, MASK_ON_LAMINATE) if coated else (0.0, 0.0)
        self.cm, self.cl = cm, cl
        if self.sym:
            x0 = 0.0
            xedges = [w / 2, w / 2 + gap_left]
            xlines = [x0] + xedges + [w / 2 + gap_left + side]
            if coated:
                xlines += [w / 2 + cm, w / 2 + gap_left - cm]
            self.sig = (-w / 2, w / 2)
            self.gnd_l, self.gnd_r = None, w / 2 + gap_left
        else:
            xl, xr = -w / 2 - gap_left, w / 2 + gap_right
            xlines = [xl - side, xl, -w / 2, w / 2, xr, xr + side]
            if coated:
                xlines += [xl + cm, -w / 2 - cm, w / 2 + cm, xr - cm]
            self.sig = (-w / 2, w / 2)
            self.gnd_l, self.gnd_r = xl, xr
        ylines = [0.0] + [y for y, _ in layers] + [h + t_, lid]
        if coated:
            ylines += [h + cl, h + t_ + cm]
        self.x = _grade(xlines, fine, coarse)
        self.y = _grade(ylines, fine, coarse)

    # material and conductors ----------------------------------------------------------------------------------------
    def _er(self, xc, yc, vacuum):
        """Relative permittivity at a cell centre (xc, yc)."""
        if vacuum:
            return 1.0
        if yc < self.h:
            for top, er in self.layers:
                if yc < top:
                    return er
            return self.layers[-1][1]
        if not self.coated:
            return 1.0
        # conformal mask: on the laminate in the gaps, on the copper's top and sides
        h, t, cm, cl = self.h, self.t, self.cm, self.cl
        inside_copper = self._metal(xc, yc) is not None
        if inside_copper:
            return 1.0
        if yc < h + cl:
            return ER_MASK
        if yc < h + t + cm:
            for a, b in self._copper_x():
                if a - cm <= xc <= b + cm:
                    return ER_MASK
        return 1.0

    def _copper_x(self):
        """x spans of the copper (signal and grounds) in the domain."""
        spans = [self.sig]
        big = 1e3
        if self.sym:
            spans.append((self.gnd_r, big))
        else:
            spans.append((-big, self.gnd_l))
            spans.append((self.gnd_r, big))
        return spans

    def _metal(self, x, y):
        """1.0 inside the signal, 0.0 inside a ground conductor, None in a dielectric (x, y a node)."""
        e = 1e-9
        if y <= e:
            return 0.0                                   # reference plane
        if y >= LID - e:
            return 0.0                                   # lid
        if self.h - e <= y <= self.h + self.t + e:
            if self.sig[0] - e <= x <= self.sig[1] + e:
                return 1.0
            if x >= self.gnd_r - e:
                return 0.0
            if self.gnd_l is not None and x <= self.gnd_l + e:
                return 0.0
        return None

    # solve ------------------------------------------------------------------------------------------------------------
    def capacitance(self, vacuum=False, omega=None, max_iter=200000):
        """Capacitance per unit length (F/m) from the field energy."""
        xs, ys = self.x, self.y
        nx, ny = len(xs), len(ys)
        # cell permittivities eps[i][j] for the cell between x[i]..x[i+1], y[j]..y[j+1]
        eps = [[self._er((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2, vacuum) for j in range(ny - 1)]
               for i in range(nx - 1)]
        dx = [xs[i + 1] - xs[i] for i in range(nx - 1)]
        dy = [ys[j + 1] - ys[j] for j in range(ny - 1)]
        phi = [[0.0] * ny for _ in range(nx)]
        fixed = [[False] * ny for _ in range(nx)]
        for i in range(nx):
            for j in range(ny):
                m = self._metal(xs[i], ys[j])
                if m is not None:
                    phi[i][j] = m
                    fixed[i][j] = True
        # face conductances: ge[i][j] links node (i, j) to (i+1, j); gn[i][j] links (i, j) to (i, j+1)
        ge = [[0.0] * ny for _ in range(nx - 1)]
        gn = [[0.0] * (ny - 1) for _ in range(nx)]
        for i in range(nx - 1):
            for j in range(ny):
                s = 0.0
                if j > 0:
                    s += eps[i][j - 1] * dy[j - 1] / 2
                if j < ny - 1:
                    s += eps[i][j] * dy[j] / 2
                ge[i][j] = s / dx[i]
        for i in range(nx):
            for j in range(ny - 1):
                s = 0.0
                if i > 0:
                    s += eps[i - 1][j] * dx[i - 1] / 2
                if i < nx - 1:
                    s += eps[i][j] * dx[i] / 2
                gn[i][j] = s / dy[j]
        nodes = []
        for i in range(nx):
            for j in range(1, ny - 1):
                if fixed[i][j]:
                    continue
                w = ge[i - 1][j] if i > 0 else 0.0
                e_ = ge[i][j] if i < nx - 1 else 0.0
                s_ = gn[i][j - 1]
                n_ = gn[i][j]
                tot = w + e_ + s_ + n_
                nodes.append((i, j, w / tot, e_ / tot, s_ / tot, n_ / tot))
        # SOR (natural ordering); omega from the grid size unless given
        if omega is None:
            m = max(nx, ny)
            omega = 2.0 / (1.0 + math.sin(math.pi / m))
        it = 0
        while it < max_iter:
            it += 1
            worst = 0.0
            for i, j, w, e_, s_, n_ in nodes:
                col = phi[i]
                v = s_ * col[j - 1] + n_ * col[j + 1]
                if w:
                    v += w * phi[i - 1][j]
                if e_:
                    v += e_ * phi[i + 1][j]
                d = v - col[j]
                col[j] += omega * d
                if d < 0:
                    d = -d
                if d > worst:
                    worst = d
            if worst < TOL:
                break
        self.iterations = it
        # field energy: sum over faces of G * dphi^2 (the discrete Dirichlet energy, = Q * V at 1 V)
        energy = 0.0
        for i in range(nx - 1):
            for j in range(ny):
                d = phi[i + 1][j] - phi[i][j]
                if d:
                    energy += ge[i][j] * d * d
        for i in range(nx):
            for j in range(ny - 1):
                d = phi[i][j + 1] - phi[i][j]
                if d:
                    energy += gn[i][j] * d * d
        c = energy * EPS0                # per metre (grid in mm cancels: G is dimensionless in 2-D)
        return 2 * c if self.sym else c

    def solve(self):
        c = self.capacitance(False)
        c0 = self.capacitance(True)
        z0 = 1.0 / (C_LIGHT * math.sqrt(c * c0))
        return dict(z0_ohm=round(z0, 3), eps_eff=round(c / c0, 4), c_pf_per_m=round(c * 1e12, 3),
                    c0_pf_per_m=round(c0 * 1e12, 3), nodes=len(self.x) * len(self.y))


def stack_in1():
    """Dielectric under an F.Cu line referenced to In1 (the GCPW)."""
    return [(H_PREPREG, ER_PREPREG)]


def stack_in2():
    """Dielectric under an F.Cu pad with In1 cut out, referenced to In2 (the SMA launch, pass2_rf section 3.2): the
    prepreg, In1's thickness filled with prepreg resin, and the core."""
    return [(H_PREPREG, ER_PREPREG), (H_PREPREG + T_IN1, ER_PREPREG), (H_PREPREG + T_IN1 + H_CORE, ER_CORE)]


def z0(w=0.30, gap_left=0.25, gap_right=None, coated=True, ref='In1', **kw):
    gap_right = gap_left if gap_right is None else gap_right
    layers = stack_in1() if ref == 'In1' else stack_in2()
    return Section(w, gap_left, gap_right, layers, coated=coated, **kw).solve()


def gap_for(z_target, w=0.30, lo=0.25, hi=1.0, coated=True, tol=0.002):
    """Largest symmetric gap (mm, to `tol`) whose Z0 stays <= z_target (bisection; Z0 rises with the gap)."""
    zl = z0(w, lo, coated=coated)['z0_ohm']
    if zl > z_target:
        return None, zl
    zh = z0(w, hi, coated=coated)['z0_ohm']
    if zh <= z_target:
        return hi, zh
    while hi - lo > tol:
        mid = (lo + hi) / 2
        zm = z0(w, mid, coated=coated)['z0_ohm']
        if zm <= z_target:
            lo, zl = mid, zm
        else:
            hi = mid
    return round(lo, 4), zl


def validate():
    """Pass 2's three solves against this solver: [(case, pass-2 Z0, this Z0, difference, eps_eff pair)]."""
    rows = []
    for case, kw in (('gcpw_coated', dict(w=0.30, gap_left=0.25, coated=True)),
                     ('gcpw_bare', dict(w=0.30, gap_left=0.25, coated=False)),
                     ('launch_coated', dict(w=1.2, gap_left=0.30, coated=True, ref='In2'))):
        r = z0(**kw)
        want, eff = PASS2[case]
        rows.append(dict(case=case, pass2_ohm=want, solved_ohm=r['z0_ohm'], diff_ohm=round(r['z0_ohm'] - want, 3),
                         pass2_eps_eff=eff, solved_eps_eff=r['eps_eff'], nodes=r['nodes']))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--w', type=float, default=0.30)
    ap.add_argument('--gap', type=float, default=0.25)
    ap.add_argument('--gaps', help='two different gaps "left,right" (full-domain solve)')
    ap.add_argument('--bare', action='store_true', help='no solder mask')
    ap.add_argument('--in2', action='store_true', help='reference In2 (In1 cut out), as the SMA launch')
    ap.add_argument('--validate', action='store_true')
    ap.add_argument('--gmax', type=float, help='largest symmetric gap with Z0 <= this (ohm)')
    ap.add_argument('--json', help='write the result as JSON')
    a = ap.parse_args()
    if a.validate:
        out = validate()
        for r in out:
            print(f"{r['case']:14s} pass 2 {r['pass2_ohm']:5.1f} ohm  solved {r['solved_ohm']:7.3f} ohm  "
                  f"diff {r['diff_ohm']:+6.3f}  eps_eff {r['solved_eps_eff']} (pass 2 {r['pass2_eps_eff']})  "
                  f"{r['nodes']} nodes")
        ok = all(abs(r['diff_ohm']) <= 1.0 for r in out)
        print('validation against pass 2 (within 1 ohm):', 'OK' if ok else 'FAIL')
    elif a.gmax is not None:
        g, z = gap_for(a.gmax, a.w, coated=not a.bare)
        out = dict(z_target=a.gmax, w=a.w, gap_max=g, z0_at_gap=z)
        print(json.dumps(out))
        ok = g is not None
    else:
        gl, gr = (float(v) for v in a.gaps.split(',')) if a.gaps else (a.gap, a.gap)
        out = z0(a.w, gl, gr, coated=not a.bare, ref='In2' if a.in2 else 'In1')
        print(json.dumps(out))
        ok = True
    if a.json:
        with open(a.json, 'w') as fh:
            json.dump(out, fh, indent=1)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

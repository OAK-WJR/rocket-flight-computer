#!/usr/bin/env python3
"""Plate model of the board on its five supports: first modes and the 100 g quasi-static strain (REQUIREMENTS P2).

usage: python3 plate_model.py FIT_REPORT.json [--label R8] [--json OUT]       (needs numpy; not KiCad's Python)

The method and the plate code are R7 review pass 2's (`sources/r7_review/pass2_mechanical.md` section 3.3 and its
Appendix, reproduced verbatim in class Plate below): a Kirchhoff plate 46 x L mm, Rayleigh-Ritz with products of
Legendre polynomials to degree 20, point supports at the hole centres, pinned (w = 0, a lower bound) or point-clamped
(w = dw/dx = dw/dy = 0, an upper bound); D = 5 and 10 N m, nu 0.15, laminate 3.65 kg/m^2 (all Inference). Masses: the
Appendix's lumped heavy parts (U30 / U31 0.5 g from the maker data sheets, the rest Inference) at the centre of their
model box, every other part at 3 g/cm^3 of its model-box volume, the SMA jacks as rigid overhangs at the aft edge
(plugs mated on the jacks: 5.55 g, centre of mass 13.7 mm beyond the edge, 335 g mm^2; jacks only, the plugs carried
by the sled: 1.8 g at 5 mm, pass2_mechanical section 3.4, Inference).

The geometry comes from tools/fit_check.py's report (`--report`): the outline, the five supports and every part's
model box (x0, y0, x1, y1, z0, z1 in board mm); the mated envelopes are not masses. Quasi-static: a 100 g transverse
load on every mass (F = 100 g M 1), solved on the constrained basis; deflection on a 0.5 mm raster; peak principal
surface strain (t/2 times the larger principal curvature, t = 1.566 mm, the JLC041611-7628 laminate) over each named
part's model box on a 0.25 mm raster.
"""
import argparse
import json
import math

import warnings

import numpy as np
from numpy.polynomial import legendre as L

# numpy 2.0 on macOS (Accelerate) raises spurious divide/overflow flags inside matmul with finite results; the R7 rows
# reproduce pass 2's figures exactly with them, so they are silenced here and every result is checked finite below.
warnings.filterwarnings('ignore', category=RuntimeWarning, message='.*encountered in matmul')

LUMPED = {'J1': 6.2, 'J121': 3.1, 'J124': 3.1, 'J122': 4.0, 'C84': 1.8, 'C121': 1.5, 'J3': 0.8, 'J9': 0.8,
          'J123': 0.6, 'U1': 0.65, 'U30': 0.5, 'U31': 0.5, 'L3': 0.3, 'LS120': 0.3, 'L1': 0.15, 'U3': 0.15}   # g
JACKS = ('J30', 'J31')
OVERHANG = {'plugs_on_jacks': (5.55e-3, 13.7e-3, 335e-9), 'jacks_only': (1.8e-3, 5.0e-3, 1.8e-3 * (9.5e-3) ** 2 / 12)}
RHO_H, NU, SMALL_RHO = 3.65, 0.15, 3.0e3        # kg/m^2, -, kg/m^3 (3 g/cm^3)
T = 1.566e-3
STRAIN_PARTS = ('U31', 'U30', 'U4', 'U1', 'J121', 'J124', 'C121', 'C84', 'U5', 'J1', 'J122')


def leg(n, t):
    V = np.zeros((n + 1, t.size)); V1 = np.zeros_like(V); V2 = np.zeros_like(V)
    for i in range(n + 1):
        c = np.zeros(i + 1); c[i] = 1
        V[i] = L.legval(t, c)
        if i >= 1: V1[i] = L.legval(t, L.legder(c, 1))
        if i >= 2: V2[i] = L.legval(t, L.legder(c, 2))
    return V, V1, V2


class Plate:                       # a, b [m]; D [N m]; rho_h [kg/m^2]  (pass2_mechanical Appendix, verbatim)
    def __init__(s, a, b, D, nu, rho_h, N=20):
        s.a, s.b, s.N = a, b, N; t, w = L.leggauss(2 * N + 4); X, X1, X2 = leg(N, t)
        I = lambda A, B, j, k: (A * w) @ B.T * j * k
        sx, sy = 2 / a, 2 / b
        Ex = {k: v for k, v in [((0, 0), I(X, X, a / 2, 1)), ((2, 2), I(X2, X2, a / 2, sx ** 4)),
              ((0, 2), I(X, X2, a / 2, sx ** 2)), ((1, 1), I(X1, X1, a / 2, sx ** 2))]}
        Ey = {k: v for k, v in [((0, 0), I(X, X, b / 2, 1)), ((2, 2), I(X2, X2, b / 2, sy ** 4)),
              ((0, 2), I(X, X2, b / 2, sy ** 2)), ((1, 1), I(X1, X1, b / 2, sy ** 2))]}
        k = np.kron
        s.K = D * (k(Ex[2, 2], Ey[0, 0]) + k(Ex[0, 0], Ey[2, 2]) + nu * (k(Ex[0, 2].T, Ey[0, 2]) + k(Ex[0, 2], Ey[0, 2].T))
                   + 2 * (1 - nu) * k(Ex[1, 1], Ey[1, 1]))
        s.M = rho_h * k(Ex[0, 0], Ey[0, 0]); s.C = []

    def phi(s, x, y, dx=0, dy=0):
        X = leg(s.N, np.array([2 * x / s.a - 1]))[dx][:, 0] * (2 / s.a) ** dx
        Y = leg(s.N, np.array([2 * y / s.b - 1]))[dy][:, 0] * (2 / s.b) ** dy
        return np.kron(X, Y)

    def mass(s, x, y, m): p = s.phi(x, y); s.M += m * np.outer(p, p)

    def overhang(s, x, m, d, I):    # rigid body at (x, 0), CM at y = -d
        p, q = s.phi(x, 0), s.phi(x, 0, dy=1); u = p - d * q
        s.M += m * np.outer(u, u) + I * np.outer(q, q)

    def support(s, x, y, clamp=False):
        s.C.append(s.phi(x, y))
        if clamp: s.C += [s.phi(x, y, dx=1), s.phi(x, y, dy=1)]

    def basis(s):
        _, sv, vt = np.linalg.svd(np.array(s.C)); return vt[int((sv > sv[0] * 1e-10).sum()):].T

    def modes(s, n=4):
        Z = s.basis()
        Kr, Mr = Z.T @ s.K @ Z, Z.T @ s.M @ Z; Li = np.linalg.inv(np.linalg.cholesky(Mr))
        w2 = np.linalg.eigvalsh((Li @ Kr @ Li.T + (Li @ Kr @ Li.T).T) / 2)
        return np.sqrt(w2[:n]) / (2 * math.pi)

    def static(s, g):               # uniform transverse acceleration g [m/s^2] on every mass
        Z = s.basis(); one = np.zeros(s.K.shape[0]); one[0] = 1.0    # P0(x) P0(y) = 1
        F = g * (s.M @ one)
        return Z @ np.linalg.solve(Z.T @ s.K @ Z, Z.T @ F)

    def field(s, c, xs, ys, dx=0, dy=0):
        X = leg(s.N, 2 * xs / s.a - 1)[dx] * (2 / s.a) ** dx         # (N+1, nx)
        Y = leg(s.N, 2 * ys / s.b - 1)[dy] * (2 / s.b) ** dy         # (N+1, ny)
        C = c.reshape(s.N + 1, s.N + 1)
        return X.T @ C @ Y                                           # (nx, ny)


def build(fit, D, clamp, case, profile='r9', mass_spec=None):
    if profile not in ('r9', 'r10'):
        raise ValueError(f'unknown plate profile {profile!r}')
    if profile == 'r10':
        if fit.get('profile') != 'r10' or not mass_spec or mass_spec.get('profile') != 'r10':
            raise ValueError('R10 requires an R10 fit report and explicit R10 mass specification')
        if len(fit['supports']) != 5:
            raise ValueError('R10 plate requires five effective supports')
        if case != 'r10_mated':
            raise ValueError('R10 plate must include the allocated mated plugs')
        names = {row[1] for row in fit['rows']}
        required = {'J1', 'J121', 'J122', 'C84', 'J3', 'J9', 'J123', 'J400', 'J410', 'J420'}
        required |= {name for name in names if name.endswith(' mated')}
        if required - names or required - mass_spec.get('masses_g', {}).keys():
            raise ValueError('R10 missing explicit body/plug masses: ' + str(sorted(
                (required - names) | (required - mass_spec.get('masses_g', {}).keys()))))
        if not mass_spec.get('basis'):
            raise ValueError('R10 mass specification requires a source or labelled inference basis')
        if any(not math.isfinite(v) or v <= 0 for v in mass_spec['masses_g'].values()):
            raise ValueError('R10 masses must be finite and positive')
        # R3-MEC-01: every mass key is placed or refused, never dropped: a key with its own fit row sits on that row's
        # box; 'X mated' with no row of its own (the DB125 terminals' wire and ferrule allowance: no mated envelope in
        # fit_check) sits on its parent X's box; anything else is an error
        parents = {}
        for key in mass_spec['masses_g']:
            if key in names:
                continue
            parent = key[:-len(' mated')] if key.endswith(' mated') else None
            if parent and parent in names:
                parents[key] = parent
            else:
                raise ValueError(f'R10 mass {key!r} has no fit-report row' + (f' and no parent row {parent!r}'
                                                                               if parent else ''))
    x0, y0, x1, y1 = fit['outline']
    a, b = (x1 - x0) / 1e3, (y1 - y0) / 1e3
    p = Plate(a, b, D, NU, RHO_H)
    masses = {}
    rows = list(fit['rows'])
    if profile == 'r10':
        boxes = {row[1]: row for row in fit['rows']}
        rows += [(boxes[parent][0], key, boxes[parent][2], boxes[parent][3]) for key, parent in sorted(parents.items())]
    for _, name, side, box in rows:
        if profile != 'r10' and (' ' in name or name in JACKS):
            continue                                                # mated envelopes; the jacks are overhangs
        bx0, by0, bx1, by1, z0, z1 = box
        cx, cy = ((bx0 + bx1) / 2 - x0) / 1e3, ((by0 + by1) / 2 - y0) / 1e3
        cx, cy = min(max(cx, 0.0), a), min(max(cy, 0.0), b)
        lumped = mass_spec['masses_g'] if profile == 'r10' else LUMPED
        m = lumped[name] / 1e3 if name in lumped else SMALL_RHO * (bx1 - bx0) * (by1 - by0) * (z1 - z0) * 1e-9
        masses[name] = (m, cx, cy, box)
        p.mass(cx, cy, m)
    if case in OVERHANG:
        m, d, I = OVERHANG[case]
        for name, side, box in [(r[1], r[2], r[3]) for r in fit['rows'] if r[1] in JACKS]:
            p.overhang(((box[0] + box[2]) / 2 - x0) / 1e3, m, d, I)
    for sx, sy in fit['supports']:
        p.support((sx - x0) / 1e3, (sy - y0) / 1e3, clamp)
    total = RHO_H * a * b + sum(v[0] for v in masses.values()) + (2 * OVERHANG[case][0] if case in OVERHANG else 0)
    return p, masses, total


def run(fit, label, profile='r9', mass_spec=None):
    out = dict(label=label, profile=profile, mass_spec=mass_spec, board_sha256=fit.get('board_sha256'), supports=fit['supports'], f1={}, static={})
    for case in (('r10_mated',) if profile == 'r10' else ('jacks_only', 'plugs_on_jacks', 'no_jacks')):
        row = {}
        for clamp in (False, True):
            for D in (5.0, 10.0):
                p, masses, total = build(fit, D, clamp, case, profile, mass_spec)
                f1 = float(p.modes(1)[0])
                assert math.isfinite(f1), 'non-finite mode'
                row[f"{'clamped' if clamp else 'pinned'}_D{int(D)}"] = round(f1, 1)
        out['f1'][case] = dict(row, board_mass_g=round(total * 1e3, 1))
    # quasi-static 100 g, D 5 pinned (halve for D 10), flight configuration (jacks only) and plugs on the jacks
    for case in (('r10_mated',) if profile == 'r10' else ('jacks_only', 'plugs_on_jacks', 'no_jacks')):
        p, masses, _ = build(fit, 5.0, False, case, profile, mass_spec)
        c = p.static(100 * 9.80665)
        assert np.all(np.isfinite(c)), 'non-finite static solution'
        x0, y0, x1, y1 = fit['outline']
        xs, ys = np.arange(0, (x1 - x0) + 1e-9, 0.5) / 1e3, np.arange(0, (y1 - y0) + 1e-9, 0.5) / 1e3
        w = p.field(c, xs, ys)
        i, j = np.unravel_index(np.argmax(np.abs(w)), w.shape)
        st = dict(max_deflection_mm=round(float(abs(w[i, j]) * 1e3), 2), at=[round(float(xs[i] * 1e3 + x0), 1),
                                                                               round(float(ys[j] * 1e3 + y0), 1)],
                  strain_ue={})
        for name in STRAIN_PARTS:
            if name not in masses:
                continue
            bx0, by0, bx1, by1 = masses[name][3][:4]
            px = np.clip(np.arange(bx0, bx1 + 1e-9, 0.25) - x0, 0, x1 - x0) / 1e3
            py = np.clip(np.arange(by0, by1 + 1e-9, 0.25) - y0, 0, y1 - y0) / 1e3
            wxx, wyy, wxy = p.field(c, px, py, 2, 0), p.field(c, px, py, 0, 2), p.field(c, px, py, 1, 1)
            mean, rad = (wxx + wyy) / 2, np.sqrt(((wxx - wyy) / 2) ** 2 + wxy ** 2)
            k = np.maximum(np.abs(mean + rad), np.abs(mean - rad))
            st['strain_ue'][name] = round(float(k.max() * T / 2 * 1e6))
        out['static'][case] = st
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('fit')
    ap.add_argument('--label', default='')
    ap.add_argument('--json')
    ap.add_argument('--profile', choices=('r9', 'r10'), default='r9')
    ap.add_argument('--mass-spec', help='R10 JSON: profile, basis and explicit masses_g for changed bodies and plugs')
    a = ap.parse_args()
    out = run(json.load(open(a.fit)), a.label, a.profile, json.load(open(a.mass_spec)) if a.mass_spec else None)
    print(json.dumps(out, indent=1))
    if a.json:
        json.dump(out, open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()

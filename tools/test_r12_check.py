"""Synthetic passing/failing R12 board-rule tests, plus schematic, library and budget regressions.
Real-board tests skip until the board is tracked and has routed tracks; no R12 copper fixture is committed here.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

try:
    import pcbnew
except ImportError:
    pcbnew = None
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'm3_design'))
if pcbnew:
    import check_r12 as r12
    import fit_check as fc
    import route_check as rc
import r12_fire as fire
import r12_sch
import r12_sch_check
import r12_budget

LIB = ROOT / 'm3_design/r12/kilib/rocket.pretty'


def mm(v):
    return pcbnew.FromMM(v)


def kicad_cli():
    """R12F7-TRI-08: KICAD_CLI (tools/check.sh exports the CLI it resolved), else kicad-cli on PATH, else KiCad's macOS
    application folders; None when none exists."""
    for c in (os.environ.get('KICAD_CLI'), shutil.which('kicad-cli'),
              '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli', '/Applications/KiCad.app/Contents/MacOS/kicad-cli'):
        if c and Path(c).exists():
            return c
    return None


class CliResolution(unittest.TestCase):
    """R12F7-TRI-08: the R12 tests find kicad-cli where tools/check.sh does, and fail rather than skip under it."""

    def test_resolution_order_and_check_sh_export(self):
        import importlib
        import test_r12_fab
        with tempfile.TemporaryDirectory() as d:
            fake = Path(d) / 'kicad-cli'
            fake.write_text('#!/bin/sh\n'); fake.chmod(0o755)
            env = dict(os.environ)
            try:
                os.environ.pop('KICAD_CLI', None)
                os.environ['PATH'] = d + os.pathsep + env.get('PATH', '')
                self.assertEqual(kicad_cli(), str(fake))                # PATH, before the application folders
                self.assertEqual(test_r12_fab.kicad_cli(), str(fake))
                os.environ['KICAD_CLI'] = str(fake)
                self.assertEqual(kicad_cli(), str(fake))
                os.environ['KICAD_CLI'] = str(Path(d) / 'missing')     # a stale variable falls through to PATH
                self.assertEqual(kicad_cli(), str(fake))
            finally:
                os.environ.clear(); os.environ.update(env)
        text = (ROOT / 'tools/check.sh').read_text()
        self.assertIn('export KICAD_CLI="$CLI"', text)
        self.assertLess(text.index('export KICAD_CLI="$CLI"'), text.index('selftest() {'))
        importlib.reload(test_r12_fab)

    def test_missing_cli_fails_under_check_sh(self):
        import test_r12_fab
        saved = (test_r12_fab.KICAD_CLI, os.environ.get('R12_BOARD_REQUIRED'), test_r12_fab.BOARD)
        try:
            test_r12_fab.KICAD_CLI = '/nonexistent/kicad-cli'
            test_r12_fab.BOARD = Path(__file__)                         # an existing file stands in for the board
            os.environ.pop('R12_BOARD_REQUIRED', None)
            with self.assertRaises(unittest.SkipTest):
                test_r12_fab.require_kicad()
            os.environ['R12_BOARD_REQUIRED'] = '1'
            with self.assertRaises(AssertionError):
                test_r12_fab.require_kicad()
            probe = FireGaps('test_committed_board_passes_with_recorded_exceptions')
            probe.CLI = '/nonexistent/kicad-cli'
            with self.assertRaises(AssertionError):
                probe.drc_s10()
        finally:
            test_r12_fab.KICAD_CLI, test_r12_fab.BOARD = saved[0], saved[2]
            if saved[1] is None:
                os.environ.pop('R12_BOARD_REQUIRED', None)
            else:
                os.environ['R12_BOARD_REQUIRED'] = saved[1]


@unittest.skipUnless(pcbnew, 'KiCad python required')
class Synthetic(unittest.TestCase):
    """check_r12 rules on a small board: a clean board passes, each seeded fault fails its rule."""

    def board(self, layers=4, length=90.0, width=46.0):
        b = pcbnew.BOARD()
        b.SetCopperLayerCount(layers)
        b.GetDesignSettings().SetBoardThickness(mm(1.6))
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_RECT)
        s.SetStart(pcbnew.VECTOR2I(0, 0))
        s.SetEnd(pcbnew.VECTOR2I(mm(width), mm(length)))
        s.SetLayer(pcbnew.Edge_Cuts)
        b.Add(s)
        fp = pcbnew.FootprintLoad(str(LIB), 'R0402')
        fp.SetReference('R14')
        b.Add(fp)
        fp.SetPosition(pcbnew.VECTOR2I(mm(10), mm(10)))
        b.GetTitleBlock().SetRevision(r12.REVISION)
        return b, fp

    def via(self, b, x, y, drill=0.3, dia=0.45):
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        v.SetDrill(mm(drill))
        v.SetWidth(mm(dia))
        b.Add(v)
        return v

    def run_rules(self, b, only, path=None):
        return r12.check_board(b, path or ROOT / 'm3_design/r12/m3.kicad_pcb', only=set(only), stage='copper')

    def test_clean_board_passes_geometry_rules(self):
        b, _ = self.board()
        self.via(b, 30, 30)
        report = self.run_rules(b, ('L-1', 'M-1', 'F-1', 'V-1', 'V-2'))
        self.assertTrue(report['ok'], report['issues'])

    def test_six_layers_fail(self):
        b, _ = self.board(layers=6)
        self.assertFalse(self.run_rules(b, ('L-1',))['ok'])

    def test_r12f12_tri27_thickness_and_outline_origin(self):
        """R12F12-TRI-27 (gate-6): a 1.2 mm board fails L-1's thickness branch; an outline that starts at x 1 mm fails
        M-1's origin branch (the 46 mm width and the length still pass)."""
        b, _ = self.board()
        b.GetDesignSettings().SetBoardThickness(mm(1.2))
        self.assertEqual(self.run_rules(b, ('L-1',))['issues'], ['L-1: board thickness is not 1.6 mm'])
        b, _ = self.board()
        edge = next(d for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts)
        edge.SetStart(pcbnew.VECTOR2I(mm(1), 0)); edge.SetEnd(pcbnew.VECTOR2I(mm(47), mm(90)))
        self.assertEqual(self.run_rules(b, ('M-1',))['issues'], ['M-1: outline starts at (1, 0), not (0, 0)'])

    def test_r12f12_tri27_through_vias_only(self):
        """R12F12-TRI-27: a blind via of the R12 size fails V-1's via-type branch."""
        b, _ = self.board()
        v = self.via(b, 30, 30)
        v.SetViaType(pcbnew.VIATYPE_BLIND); v.SetLayerPair(pcbnew.F_Cu, pcbnew.In1_Cu)
        self.assertTrue([i for i in self.run_rules(b, ('V-1',))['issues'] if i == 'V-1: via at (30, 30): not a through via'])

    def test_long_or_narrow_outline_fails(self):
        for kw in (dict(length=105.0), dict(width=50.0)):
            with self.subTest(**kw):
                b, _ = self.board(**kw)
                self.assertFalse(self.run_rules(b, ('M-1',))['ok'])

    def test_bottom_side_part_fails(self):
        b, fp = self.board()
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        report = self.run_rules(b, ('F-1',))
        self.assertFalse(report['ok'])
        self.assertTrue(any('bottom side' in i for i in report['issues']), report['issues'])

    def test_small_via_fails(self):
        for drill, dia in ((0.2, 0.45), (0.3, 0.4), (0.25, 0.35)):
            with self.subTest(drill=drill, dia=dia):
                b, _ = self.board()
                self.via(b, 30, 30, drill, dia)
                self.assertFalse(self.run_rules(b, ('V-1',))['ok'])

    def test_via_in_pad_fails(self):
        b, fp = self.board()
        pad = list(fp.Pads())[0]
        self.via(b, pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y))
        self.assertFalse(self.run_rules(b, ('V-2',))['ok'])

    def test_netlist_parity_and_revision(self):
        b, _ = self.board()
        report = r12.check_board(b, ROOT / 'm3_design/r12/m3.kicad_pcb', only={'N-1'}, stage='placement')
        self.assertFalse(report['ok'])                       # one part on the board, every other schematic part off it
        self.assertTrue(any('not on the board' in i for i in report['issues']))
        b.GetTitleBlock().SetRevision('M3-ASSY-R11')
        report = r12.check_board(b, ROOT / 'm3_design/r12/m3.kicad_pcb', only={'N-1'}, stage='placement')
        self.assertTrue(any('revision' in i for i in report['issues']))

    def test_r12f12_tri27_netlist_part_footprint_and_fields(self):
        """R12F12-TRI-27: N-1's three other branches. R14 carries its schematic footprint and fields and passes; a part
        the schematic does not have (R999), R14 on another footprint and R14 with a wrong LCSC code each fail with
        their own message."""
        parts, _ = r12_sch.read_netlist(BOARD12.with_name('schematic.net.xml'))

        def r14(name='R0402', lcsc=None):
            b, _ = self.board()
            b.Remove(next(iter(b.GetFootprints())))
            fp = pcbnew.FootprintLoad(str(LIB), name)
            fp.SetReference('R14'); b.Add(fp)
            for key in ('LCSC', 'Manufacturer', 'Manufacturer Part'):
                fp.SetField(key, parts['R14']['fields'][key])
            if lcsc:
                fp.SetField('LCSC', lcsc)
            return b, fp

        def issues(b):
            rep = r12.check_board(b, BOARD12, only={'N-1'}, stage='placement')
            return [i for i in rep['issues'] if 'not on the board' not in i]
        self.assertEqual(parts['R14']['footprint'], 'rocket:R0402')
        b, _ = r14()
        self.assertEqual(issues(b), [])
        extra = pcbnew.FootprintLoad(str(LIB), 'R0402'); extra.SetReference('R999'); b.Add(extra)
        self.assertEqual(issues(b), ['N-1: R999: on the board, not in the schematic'])
        b, _ = r14('C0402')
        self.assertEqual(issues(b), ['N-1: R14: footprint C0402, schematic rocket:R0402'])
        b, _ = r14(lcsc='C1')
        self.assertEqual(issues(b), [f"N-1: R14: LCSC 'C1', schematic {parts['R14']['fields']['LCSC']!r}"])

    def test_rules_files_must_be_the_generators(self):
        """K-rules: the DRU must be r12_sch.dru()'s; R12F12-TRI-27: the project's floors must be R12's (a min_clearance
        edited fails with its value) and the .kicad_pro must exist."""
        with tempfile.TemporaryDirectory(prefix='r12-krules-') as d:
            path = Path(d) / 'm3.kicad_pcb'
            shutil.copy2(ROOT / 'm3_design/r12/m3.kicad_dru', Path(d) / 'm3.kicad_dru')
            shutil.copy2(ROOT / 'm3_design/r12/m3.kicad_pro', Path(d) / 'm3.kicad_pro')
            b, _ = self.board()
            self.assertTrue(r12.check_board(b, path, only={'K-rules'}, stage='placement')['ok'])
            pro = Path(d) / 'm3.kicad_pro'
            data = json.loads(pro.read_text())
            data['board']['design_settings']['rules']['min_clearance'] = 0.05
            pro.write_text(json.dumps(data))
            self.assertEqual(r12.check_board(b, path, only={'K-rules'}, stage='placement')['issues'],
                             [f"K-rules: project min_clearance 0.05, R12 floor {r12_sch.R12_FLOOR['clearance']}"])
            pro.unlink()
            self.assertEqual(r12.check_board(b, path, only={'K-rules'}, stage='placement')['issues'],
                             ['K-rules: m3.kicad_pro missing'])
            dru = Path(d) / 'm3.kicad_dru'
            dru.write_text(dru.read_text().replace('(min 0.3mm)', '(min 0.2mm)'))
            self.assertFalse(r12.check_board(b, path, only={'K-rules'}, stage='placement')['ok'])

    def test_fit_report_binding(self):
        b, _ = self.board()
        ctx = dict(board=b, fit=dict(profile='r11', board_sha256='x', issues=[]), sha='y')
        self.assertEqual(len(r12.m5(ctx)), 2)
        # R12F12-TRI-27: a bound r12 fit report that has an issue passes it on
        ctx = dict(board=b, fit=dict(profile='r12', board_sha256='y', issues=['J430 lid over the edge']), sha='y')
        self.assertEqual(r12.m5(ctx), ['fit: J430 lid over the edge'])


@unittest.skipUnless(pcbnew, 'KiCad python required')
class Profiles(unittest.TestCase):
    def test_fit_profile_r12(self):
        self.assertEqual((fc.R12_CFG['layers'], fc.R12_CFG['max_length'], fc.R12_CFG['one_side']), (4, 100.0, True))
        self.assertEqual((fc.R11_CFG['layers'], fc.R11_CFG['max_length'], fc.R11_CFG['one_side']), (6, 56.0, False))
        self.assertEqual(fc.GH_CLONE_PART.match('GH1.25-6PWT').group(1), '6')

    def test_fit_r12_flags_bottom_parts_and_layers(self):
        b = pcbnew.BOARD()
        b.SetCopperLayerCount(6)
        b.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(1.6))
        s = pcbnew.PCB_SHAPE(b)
        s.SetShape(pcbnew.SHAPE_T_RECT)
        s.SetStart(pcbnew.VECTOR2I(0, 0))
        s.SetEnd(pcbnew.VECTOR2I(mm(46), mm(110)))
        s.SetLayer(pcbnew.Edge_Cuts)
        b.Add(s)
        fp = pcbnew.FootprintLoad(str(LIB), 'R0402')
        fp.SetReference('R14')
        b.Add(fp)
        fp.SetPosition(pcbnew.VECTOR2I(mm(20), mm(20)))
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        report = fc.check_board(b, ROOT / 'm3_design/r12', profile='r12')
        text = ' '.join(report['issues'])
        self.assertEqual(report['profile'], 'r12')
        for needle in ('four-layer', 'bottom side', '100 mm'):
            self.assertIn(needle, text)

    def test_route_profile_r12(self):
        rc.set_profile('r12')
        try:
            self.assertIn('r12', rc.R10_LIKE)
            # R12F8-TRI-02 / -03: the named second barrels on nets without a pour
            # R12F12-TRI-29: the eight recorded leftovers, each with a reason
            self.assertEqual((rc.LEFTOVERS, rc.PARALLEL_VIAS), (list(rc.LEFTOVERS_R12), list(rc.PARALLEL_VIAS_R12)))
            self.assertEqual(sorted((e[0], e[1]) for e in rc.LEFTOVERS_R12),
                             [('extra_vias', 'CAM_5V_SENSE'), ('extra_vias', 'NRST'), ('extra_vias', 'SERVO2_MCU'),
                              ('extra_vias', 'SERVO3_MCU'), ('extra_vias', 'SERVO4_MCU'), ('extra_vias', 'U9_FLT'),
                              ('extra_vias', 'VLOGIC_SENSE'), ('tiny_jog', 'SERVO2_MCU')])
            self.assertTrue(all(e[4].startswith('R12F12-TRI-29') and len(e[4]) > 80 for e in rc.LEFTOVERS_R12))
            self.assertEqual(sorted(n for n, *_ in rc.PARALLEL_VIAS_R12),             # R12F9-TRI-08: PD10's divider end;
                             ['3V3A', '3V3A', 'ACT_EN_MCU', 'ACT_GATE', 'ACT_GATE', 'BAT_SW_RETURN', 'BAT_SW_RETURN',
                              'PORT_SENSE', 'VCAP1', 'VCAP2', 'VLOGIC_SENSE'])        # R12F12-TRI-02 / -03: six more
            # D-R12-75A: only the recorded forced findings, each with a reason and the measured route figures
            self.assertEqual((rc.ALLOWLIST, rc.ROUTE_FIGURES), (rc.ALLOWLIST_R12, rc.ROUTE_FIGURES_R12))
            for e in rc.ALLOWLIST:
                self.assertTrue(e[4].startswith('D-R12-'), e[:4])
                if e[0] in ('detour', 'extra_vias'):
                    self.assertEqual((e[5]['len_mm'], e[5]['vias']), rc.ROUTE_FIGURES[e[1]], e[:4])
        finally:
            rc.set_profile('r8')


BOARD12 = ROOT / 'm3_design/r12/m3.kicad_pcb'


# ---- R12F12-TRI-25: plants located by identity, checked single-fault, isolated for DRC ------------------------------
BOARD_FLOOR = 0.1           # mm, the DRU's 'R12 board floor: copper clearance'
EDGE_CLEARANCE = 0.5        # mm, m3.kicad_pro min_copper_edge_clearance


def nm(v):
    """mm to whole nm, rounded (pcbnew.FromMM truncates: 33.05 mm is 33049999 nm)."""
    return int(round(v * 1e6))


class Plants:
    """Test plants that survive the next move (round 12 gate lens; R12F12-TRI-25). A plant is placed beside a copper
    item found by identity (a pad by reference; a via by net and the pad it serves; a track by its place in the chain
    that leaves a pad, or by net, layer and width), never at a literal coordinate. Before S-10 or DRC is asked about
    it, assert_isolated() shows that the item is its one intended neighbour; DRC then runs on a copy where
    isolate_for_drc() has taken every other item near the plant away, so KiCad, which names one clearance violation per
    track, can only name the target, and the assertion names the target item and the gap. Mixed into a TestCase whose
    self.board is the committed R12 board."""

    CLI = kicad_cli() or os.environ.get('KICAD_CLI') or 'kicad-cli'     # R12F7-TRI-08

    # ---- building ----------------------------------------------------------------------------------------------
    def pad(self, ref, number):
        return next(p for p in self.board.FindFootprintByReference(ref).Pads() if p.GetNumber() == number)

    def track(self, net, a, b, layer=None, width=0.2):
        """A track of `net` from a to b (mm, rounded to whole nm) on layer (default F.Cu)."""
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pcbnew.VECTOR2I(nm(a[0]), nm(a[1]))); t.SetEnd(pcbnew.VECTOR2I(nm(b[0]), nm(b[1])))
        t.SetWidth(nm(width)); t.SetLayer(pcbnew.F_Cu if layer is None else layer)
        if net:
            t.SetNet(self.board.FindNet(net) or self.add_net(net))
        self.board.Add(t)
        return t

    def add_net(self, name):
        n = pcbnew.NETINFO_ITEM(self.board, name)
        self.board.Add(n)
        return n

    def zone(self, net, pts, layer, name=''):
        """A filled zone of `net` (its outline is its fill: no refill) on layer; a plant is named 'plant'."""
        z = pcbnew.ZONE(self.board); z.SetNet(self.board.FindNet(net)); z.SetLayer(layer)
        if name:
            z.SetZoneName(name)
        o = z.Outline(); o.NewOutline()
        for x, y in pts:
            o.Append(nm(x), nm(y))
        z.SetFilledPolysList(layer, pcbnew.SHAPE_POLY_SET(o)); z.SetIsFilled(True); self.board.Add(z)
        return z

    # ---- identity ----------------------------------------------------------------------------------------------
    def vias(self, net):
        return [t for t in self.board.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == net]

    def via_at(self, net, pad):
        """The via of `net` nearest the centre of `pad` ('REF.N'): the via that serves the pad."""
        c = self.pad(*pad.split('.')).GetPosition()
        return min(self.vias(net), key=lambda v: (v.GetPosition() - c).EuclideanNorm())

    def chain(self, ref, number, layer=None):
        """The tracks that leave pad REF.N on layer (default F.Cu), end to end in order, up to a via, a pad or a
        branch."""
        layer = pcbnew.F_Cu if layer is None else layer
        p = self.pad(ref, number)
        net = p.GetNetname()
        tracks = [t for t in self.board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == net
                  and t.GetLayer() == layer]
        shape = p.GetEffectiveShape(layer)
        nxt = [t for t in tracks if shape.Collide(t.GetStart(), 0) or shape.Collide(t.GetEnd(), 0)]
        self.assertEqual(len(nxt), 1, f'{ref}.{number}: {len(nxt)} tracks leave the pad on {layer}')
        out, at = [], None
        t = nxt[0]
        at = t.GetEnd() if shape.Collide(t.GetStart(), 0) else t.GetStart()
        while True:
            out.append(t)
            if any(v.GetPosition() == at for v in self.vias(net)):
                return out
            if any(q.GetNetname() == net and q.GetEffectiveShape(layer).Collide(at, 0) and q.IsOnLayer(layer)
                   for f in self.board.GetFootprints() for q in f.Pads()):
                return out
            nxt = [q for q in tracks if q is not t and at in (q.GetStart(), q.GetEnd())]
            if len(nxt) != 1:
                return out
            t = nxt[0]
            at = t.GetEnd() if t.GetStart() == at else t.GetStart()

    def link(self, a, b, layer=None):
        """The track of the two pads' net (on layer, default F.Cu) with one end in pad a and the other in pad b."""
        layer = pcbnew.F_Cu if layer is None else layer
        pa, pb = (self.pad(*x.split('.')) for x in (a, b))
        sa, sb = pa.GetEffectiveShape(layer), pb.GetEffectiveShape(layer)
        hit = [t for t in self.board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetLayer() == layer
               and t.GetNetname() == pa.GetNetname() and ((sa.Collide(t.GetStart(), 0) and sb.Collide(t.GetEnd(), 0))
                                                         or (sb.Collide(t.GetStart(), 0) and sa.Collide(t.GetEnd(), 0)))]
        self.assertEqual(len(hit), 1, (a, b))
        return hit[0]

    def label(self, item, layer):
        """The item's label on `layer` as check_r12.copper_items writes it (S-10's rows): 'REF.N', 'via (x, y)' or
        'track (x, y)-(x, y)', ' barrel' added where a pad or via does not flash the layer; 'fill NAME' for a zone."""
        if isinstance(item, pcbnew.ZONE):
            return f'fill {item.GetZoneName() or item.GetNetname()}'
        if isinstance(item, pcbnew.PAD):
            return f'{item.GetParentFootprint().GetReference()}.{item.GetNumber()}' + (
                '' if item.FlashLayer(layer) else ' barrel')
        if item.GetClass() == 'PCB_VIA':
            return f'via ({r12.mm(item.GetPosition().x):g}, {r12.mm(item.GetPosition().y):g})' + (
                '' if item.FlashLayer(layer) else ' barrel')
        return (f'track ({r12.mm(item.GetStart().x):g}, {r12.mm(item.GetStart().y):g})-({r12.mm(item.GetEnd().x):g}, '
                f'{r12.mm(item.GetEnd().y):g})')

    @staticmethod
    def shape(item, layer):
        """The item's copper on `layer` as check_r12.copper_items takes it."""
        if isinstance(item, pcbnew.ZONE):
            return item.GetFilledPolysList(layer)
        if isinstance(item, pcbnew.PAD) or item.GetClass() == 'PCB_VIA':
            return item.GetEffectiveShape(layer) if item.FlashLayer(layer) else item.GetEffectiveHoleShape()
        return item.GetEffectiveShape(item.GetLayer())

    @staticmethod
    def layer_of(plant):
        return plant.GetFirstLayer() if isinstance(plant, pcbnew.ZONE) else plant.GetLayer()

    def plant_beside(self, item, side, gap, net, layer=None, width=0.1, length=0.2, along=0.0):
        """A `length` mm track of `net`, `width` mm wide, on layer (default F.Cu), `gap` mm beyond the item's copper on
        side N / S / E / W, centred on the item (moved `along` mm along that side, + to the east or south). The gap
        is measured back (S-10's shape_gap) and must be `gap` to 0.5 um; returns the track."""
        layer = pcbnew.F_Cu if layer is None else layer
        bb = self.shape(item, layer).BBox()
        x0, y0, x1, y1 = (r12.mm(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
        cx, cy, h = (x0 + x1) / 2 + along, (y0 + y1) / 2 + along, width / 2
        if side in ('E', 'W'):
            x = round(x1 + gap + h if side == 'E' else x0 - gap - h, 4)
            a, b = (x, round(cy - length / 2, 4)), (x, round(cy + length / 2, 4))
        else:
            y = round(y1 + gap + h if side == 'S' else y0 - gap - h, 4)
            a, b = (round(cx - length / 2, 4), y), (round(cx + length / 2, 4), y)
        t = self.track(net, a, b, layer, width)
        got = r12.shape_gap(self.shape(item, layer), t.GetEffectiveShape(layer), gap + 1.0)
        self.assertIsNotNone(got)
        self.assertAlmostEqual(got, gap, delta=5e-4, msg=f'{self.label(item, layer)}: plant gap {got}, want {gap}')
        return t

    def fill_beside(self, item, side, gap, net, layer, depth, length, along=0.0):
        """A rectangular fill of `net` named 'plant', `depth` mm deep and `length` mm long, `gap` mm beyond the item's
        copper on side N / S / E / W of it on layer (centred, moved `along` mm along the side)."""
        bb = self.shape(item, layer).BBox()
        x0, y0, x1, y1 = (r12.mm(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
        cx, cy = (x0 + x1) / 2 + along, (y0 + y1) / 2 + along
        if side in ('E', 'W'):
            u = x1 + gap if side == 'E' else x0 - gap - depth
            box = (u, cy - length / 2, u + depth, cy + length / 2)
        else:
            u = y1 + gap if side == 'S' else y0 - gap - depth
            box = (cx - length / 2, u, cx + length / 2, u + depth)
        a, b, c, d = (round(v, 4) for v in box)
        z = self.zone(net, [(a, b), (c, b), (c, d), (a, d)], layer, name='plant')
        got = r12.shape_gap(self.shape(item, layer), z.GetFilledPolysList(layer), gap + 1.0)
        self.assertAlmostEqual(got, gap, delta=5e-4, msg=f'{self.label(item, layer)}: fill gap {got}, want {gap}')
        return z

    def clear_fills(self, plant, margin=None):
        """Take every other net's fill copper on the plant's layer back to `margin` mm (default S-10's reach) round the
        plant, as a refill under the DRU would (the planes fill the whole layer, so an inner-layer plant sits in one);
        returns the zones touched."""
        lid = self.layer_of(plant)
        g = nm(fire.REACH if margin is None else margin)
        bb = plant.GetBoundingBox()
        cut = pcbnew.SHAPE_POLY_SET(); cut.NewOutline()
        for x, y in ((bb.GetLeft() - g, bb.GetTop() - g), (bb.GetRight() + g, bb.GetTop() - g),
                     (bb.GetRight() + g, bb.GetBottom() + g), (bb.GetLeft() - g, bb.GetBottom() + g)):
            cut.Append(x, y)
        touched = []
        for z in self.board.Zones():
            if z.GetIsRuleArea() or z is plant or z.GetNetname() == plant.GetNetname() or not z.IsOnLayer(lid) \
                    or not z.HasFilledPolysForLayer(lid):
                continue
            f = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(lid))
            if f.OutlineCount() and f.BBox().Intersects(cut.BBox()):
                f.BooleanSubtract(cut)
                f.Fracture()                   # stored fractured, as KiCad saves fills
                z.SetFilledPolysList(lid, f)
                touched.append(z.GetZoneName() or z.GetNetname())
        return touched

    # ---- the single-fault check ---------------------------------------------------------------------------------
    def neighbours(self, plant, reach):
        """Every copper item of another net on the plant's layer within `reach` mm of it, nearest first:
        [dict(gap, net, label, limit, cls)], with S-10's own limit and class for the pair (check_r12.fire_gaps on the
        plant and these items; limit None where S-10 does not hold the pair)."""
        lid = self.layer_of(plant)
        mine = (self.label(plant, lid), plant.GetNetname())
        items = r12.copper_items(self.board)
        me = [it for it in items if it[1] == lid and (it[2], it[0]) == mine]
        self.assertEqual(len(me), 1, mine)
        me = me[0]
        near = []
        for it in items:
            if it[1] == lid and it[0] != me[0]:
                # bisected from S-10's own reach first, so the gap reads to the last digit as S-10's row does
                g = r12.shape_gap(me[3], it[3], fire.REACH)
                g = r12.shape_gap(me[3], it[3], reach) if g is None else g
                if g is not None:
                    near.append((g, it))
        rows = {}
        for r in r12.fire_gaps(self.board, [me] + [it for _, it in near]):
            a, b = (r['a'], r['net_a']), (r['b'], r['net_b'])
            if mine in (a, b):
                rows[b if a == mine else a] = (r['limit'], r['cls'])
        return sorted((dict(gap=round(g, 4), net=it[0], label=it[2], limit=rows.get((it[2], it[0]), (None, None))[0],
                            cls=rows.get((it[2], it[0]), (None, 'unprotected'))[1]) for g, it in near),
                      key=lambda n: (n['gap'], n['net'], n['label']))

    def assert_isolated(self, plant, target, gap=None, also_nets=(), limit=None):
        """The plant is a single fault beside `target`: the target is in reach (at `gap` mm when given); every other
        item of another net that S-10 holds below its limit against the plant, or that is nearer than `limit` mm (a
        DRC rule S-10 does not make: the Tag-Connect or a test pad's clearance), is on the target's net or on one of
        `also_nets` (named by the test, with its reason) and farther than the target; nothing but the target is under
        the board floor; and the plant keeps the board's edge clearance. Fails in under a second when copper moves
        beside a plant. Returns the target's row."""
        lid = self.layer_of(plant)
        tl, tnet = self.label(target, lid), target.GetNetname()
        near = self.neighbours(plant, max(fire.REACH, limit or 0) + 0.05)
        hit = [n for n in near if (n['label'], n['net']) == (tl, tnet)]
        self.assertEqual(len(hit), 1, f'target {tnet} {tl} not beside the plant {self.label(plant, lid)}: {near[:6]}')
        t = hit[0]
        if gap is not None:
            self.assertAlmostEqual(t['gap'], gap, delta=5e-4, msg=(t, gap))
        bad = []
        for n in near:
            if n is t:
                continue
            if n['gap'] < BOARD_FLOOR:
                bad.append(('under the board floor', n))
                continue
            held = n['limit'] is not None and n['gap'] < n['limit'] - 5e-5
            within = limit is not None and n['gap'] < limit - 5e-5
            if (held or within) and not ((n['net'] == tnet or n['net'] in also_nets) and n['gap'] > t['gap']):
                bad.append(('a second neighbour', n))
        self.assertEqual(bad, [], f'plant {self.label(plant, lid)} beside {tnet} {tl}')
        if not isinstance(plant, pcbnew.ZONE) or plant.GetZoneName() == 'plant':
            pb, eb = plant.GetBoundingBox(), self.board.GetBoardEdgesBoundingBox()
            room = min(pb.GetLeft() - eb.GetLeft(), pb.GetTop() - eb.GetTop(), eb.GetRight() - pb.GetRight(),
                       eb.GetBottom() - pb.GetBottom())
            self.assertGreaterEqual(r12.mm(room), EDGE_CLEARANCE, 'plant inside the board edge clearance')
        return t

    # ---- DRC on an isolated copy --------------------------------------------------------------------------------
    ISOLATE = """import pcbnew, sys
path, (x0, y0, x1, y1), keep, target, net = sys.argv[1], map(int, sys.argv[2:6]), set(sys.argv[6].split(',')), \\
    sys.argv[7], sys.argv[8]
b = pcbnew.LoadBoard(path)
box = pcbnew.BOX2I(pcbnew.VECTOR2I(x0, y0), pcbnew.VECTOR2I(x1 - x0, y1 - y0))
uid = lambda i: i.m_Uuid.AsString()
cut = pcbnew.SHAPE_POLY_SET(); cut.NewOutline()
for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
    cut.Append(x, y)
# every edit by typed object first, every removal last: after BOARD.Remove() KiCad 10's wrappers return untyped objects
for z in b.Zones():
    if z.GetIsRuleArea() or uid(z) in keep or uid(z) == target:
        continue
    for lid in z.GetLayerSet().CuStack():
        if z.HasFilledPolysForLayer(lid):
            f = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(lid))
            if f.OutlineCount() and f.BBox().Intersects(box):
                f.BooleanSubtract(cut)
                f.Fracture()          # a fill is stored fractured: unfractured, its holes are lost on save
                z.SetFilledPolysList(lid, f)
gone = [t for t in b.GetTracks() if uid(t) not in keep and uid(t) != target and t.GetBoundingBox().Intersects(box)]
for f in b.Footprints():
    pads = list(f.Pads())
    if any(uid(p) == target for p in pads):
        for p in pads:
            if uid(p) != target and p.GetBoundingBox().Intersects(box):
                p.SetNet(b.FindNet(net))
    elif any(p.GetBoundingBox().Intersects(box) for p in pads):
        gone.append(f)
for item in gone:
    b.Remove(item)
pcbnew.SaveBoard(path, b)
"""

    def kicad_drc(self, edit=None):
        """kicad-cli DRC (errors) of the planted board with the committed DRU and project, after edit(path) on the
        saved copy: ['description | item / item'] of every violation."""
        if not Path(self.CLI).exists():
            if os.environ.get('R12_BOARD_REQUIRED') == '1':              # R12F7-TRI-08: under check.sh, fail
                self.fail(f'kicad-cli unavailable ({self.CLI}) while R12_BOARD_REQUIRED=1')
            self.skipTest('kicad-cli unavailable')
        with tempfile.TemporaryDirectory(prefix='r12-s10-') as d:
            path = Path(d) / 'm3.kicad_pcb'
            for name in ('m3.kicad_dru', 'm3.kicad_pro'):
                shutil.copy2(BOARD12.with_name(name), Path(d) / name)
            pcbnew.SaveBoard(str(path), self.board)
            if edit:
                edit(path)
            subprocess.run([self.CLI, 'pcb', 'drc', '--format', 'json', '--severity-error', '-o', str(Path(d) / 'd.json'),
                            str(path)], capture_output=True, timeout=300, check=True)
            found = json.loads((Path(d) / 'd.json').read_text())['violations']
        return [v['description'] + ' | ' + ' / '.join(i['description'] for i in v['items']) for v in found]

    def isolate_for_drc(self, plants, target, reach=None):
        """DRC of a copy on which, in a box `reach` mm (default S-10's reach plus 0.5 mm) round the plants, every track
        and via but the plants and the target is removed, every footprint but the target's goes, the target
        footprint's other pads join the plant's net and every fill is cut back (a separate KiCad python process; an
        in-process edit of the loaded board would leave pcbnew's wrappers unusable). KiCad names one clearance
        violation per track and picks among the candidates run to run (round 6 V-5), so the target must be the plant's
        only candidate. Returns every violation (kicad_drc)."""
        plants = list(plants) if isinstance(plants, (list, tuple)) else [plants]
        g = nm((fire.REACH if reach is None else reach) + 0.5)
        boxes = [p.GetBoundingBox() for p in plants]
        box = (min(b.GetLeft() for b in boxes) - g, min(b.GetTop() for b in boxes) - g,
               max(b.GetRight() for b in boxes) + g, max(b.GetBottom() for b in boxes) + g)
        keep = ','.join(p.m_Uuid.AsString() for p in plants)
        net = plants[-1].GetNetname()

        def edit(path):
            subprocess.run([sys.executable, '-I', '-c', self.ISOLATE, str(path), *map(str, box), keep,
                            target.m_Uuid.AsString(), net], check=True, capture_output=True, timeout=300)
        return self.kicad_drc(edit)

    @staticmethod
    def drc_item(item):
        """How KiCad's DRC report names the item: 'PTH pad 1 [PYRO1_OUT] of J121' / 'Pad A1 [...] of U1' (the part
        after 'pad' / 'Pad'), 'Via [NET]', 'Track [NET] on LAYER', "Zone 'NAME' [NET]" or 'Zone [NET]'."""
        if isinstance(item, pcbnew.ZONE):
            return f"Zone '{item.GetZoneName()}' [{item.GetNetname()}]" if item.GetZoneName() else \
                f'Zone [{item.GetNetname()}]'
        if isinstance(item, pcbnew.PAD):
            return f'ad {item.GetNumber()} [{item.GetNetname()}] of {item.GetParentFootprint().GetReference()}'
        if item.GetClass() == 'PCB_VIA':
            return f'Via [{item.GetNetname()}]'
        return f'Track [{item.GetNetname()}] on {item.GetBoard().GetLayerName(item.GetLayer())}'

    def assert_drc(self, found, rule, plant, target, gap):
        """A DRC violation of `rule` between the plant and the target, at `gap` mm (KiCad's 'actual', to 0.5 um)."""
        import re
        want = (rule, self.drc_item(plant), self.drc_item(target))
        hits = [v for v in found if all(w in v for w in want)
                and abs(float(re.search(r'actual ([0-9.]+) mm', v).group(1)) - gap) < 5e-4]
        self.assertTrue(hits, (want, gap, found))
        return hits


@unittest.skipUnless(pcbnew and BOARD12.is_file(), 'KiCad python and the R12 board required')
class KPower(Plants, unittest.TestCase):
    """R12F8-TRI-02 / -03: R10 / R11's single-via-open rule on R12 (check_r12 K-power), seeded on the committed board."""

    def setUp(self):
        self.board = pcbnew.LoadBoard(str(BOARD12))

    def kpower(self, exceptions=None):
        return r12.r10.single_via_opens(self.board, taps=r12.SINGLE_OPEN_TAPS_R12,
                                        exceptions=r12.SINGLE_OPEN_EXCEPTIONS_R12 if exceptions is None else exceptions)

    def pairs(self, tap):
        """The tap's doubled vias, from check_r10's K-power graph (no coordinates): [(via, partner, partner's key)] for
        every via on the tap's first path to its source whose removal together with one partner via (within 5 mm)
        cuts the tap off. Removing the partner leaves the tap on that via."""
        import re
        net, _, sources, _ = next(t for t in r12.SINGLE_OPEN_TAPS_R12 if t[1] == tap)
        label, adj = r12.r10._copper_adjacency(r12.r10.copper_nodes(self.board), net)
        start = {k for k, v in label.items() if v == tap}
        goal = {k for k, v in label.items() if v in sources}

        def path(skip):
            parent = {k: None for k in start if k not in skip}
            todo = list(parent)
            while todo:
                k = todo.pop(0)
                if k in goal:
                    out = []
                    while k is not None:
                        out.append(k)
                        k = parent[k]
                    return out
                for m in adj[k]:
                    if m not in skip and m not in parent:
                        parent[m] = k
                        todo.append(m)
            return None
        xy = {k: tuple(map(float, re.search(r'\(([-0-9.]+), ([-0-9.]+)\)$', v).groups()))
              for k, v in label.items() if v.startswith('via ')}
        first = path(set())
        self.assertIsNotNone(first, tap)
        return [(label[k], label[m], m) for k in first if k in xy for m in xy
                if m != k and max(abs(xy[m][0] - xy[k][0]), abs(xy[m][1] - xy[k][1])) < 5
                and path({k}) is not None and path({k, m}) is None]

    def assert_doubled(self, taps):
        """Each tap has a doubled via, and each partner removed leaves the tap on its via: K-power names the tap and
        that via (R10 R21-PWR-01's seed, found from the graph rather than at a coordinate)."""
        for tap in taps:
            pairs = self.pairs(tap)
            self.assertTrue(pairs, f'{tap}: no doubled via on its path')
            for via, partner, key in pairs:
                with self.subTest(tap=tap, drop=partner):
                    item = next(t for t in self.board.GetTracks() if t.m_Uuid.AsString() == key)
                    self.board.Remove(item)
                    try:
                        issues, _ = self.kpower()
                    finally:
                        self.board.Add(item)
                    self.assertTrue([i for i in issues if i.startswith(f'{tap} (') and f'hangs on one via: opening {via} '
                                     in i], (tap, partner, issues))

    def test_registered_and_committed_board_passes(self):
        self.assertIn('K-power', r12.STAGES['copper'])
        rep = r12.check_board(self.board, BOARD12, only={'K-power'}, stage='copper')
        self.assertTrue(rep['ok'], rep['issues'])
        taps = {t[1] for t in r12.SINGLE_OPEN_TAPS_R12}
        for tap in ('R14.1', 'R15.2', 'U2.2', 'R81.2', 'C87.2', 'R93.2', 'R84.2', 'R94.2', 'U9.8', 'R401.2', 'U400.1',
                    'R435.2', 'U403.1', 'R5.2', 'U1.D5', 'C19.2', 'C20.2', 'U1.F8', 'U1.E7', 'U4.6', 'U4.7', 'R61.2',
                    'D5.2', 'D9.1', 'C97.1', 'U403.3', 'U1.H1', 'U5.1',
                    'R164.1', 'U6.7', 'U6.14', 'U6.17', 'U1.H9', 'R111.1', 'R112.2',      # R12F9-TRI-07 / -08
                    'U5.3', 'U5.4', 'R12.2', 'R13.2', 'U1.G1', 'C30.1',                    # R12F10-TRI-07
                    # R12F12-TRI-17: the fire / arming chain, the safety gate networks, required supplies and returns
                    'R122.1', 'C120.2', 'R165.1', 'Q122.2', 'R123.2', 'R118.2', 'C123.2', 'R128.2', 'C126.2', 'R127.2',
                    'U1.F1', 'U1.H4', 'U1.J3', 'R130.2', 'R178.2', 'C127.2', 'R133.2', 'R180.2', 'C129.2', 'C128.2',
                    'R136.1', 'R89.1', 'D95.3', 'D436.3', 'D402.2', 'D121.2', 'R154.2', 'R155.2', 'R156.2', 'R157.2',
                    'R431.2', 'C88.2', 'C81.2', 'C97.2', 'R92.2', 'R167.2', 'U6.1', 'U6.13', 'U6.15', 'U6.16', 'C33.2',
                    'U3.8', 'U3.4', 'J430.4', 'J430.6', 'J410.2', 'J420.2', 'J440.2', 'J410.1', 'J420.1', 'J440.1',
                    'J9.3', 'J9.4', 'J122.5', 'D123.1', 'R163.2', 'Q123.2', 'C22.2'):
            self.assertIn(tap, taps)
        # the single points left on purpose: the U1 dog-bones (PD10's since R12F9-TRI-08), BOOT0's far via and the two
        # 3V3A feeds (owner rows)
        self.assertEqual(sorted({x[1] for x in r12.SINGLE_OPEN_EXCEPTIONS_R12}),
                         ['via 3V3 (20.25, 35.35)', 'via 3V3A (19.65, 40.65)', 'via 3V3A (25.70, 46.60)',
                          'via 3V3A (25.80, 33.65)',
                          'via ACT_EN_MCU (18.60, 57.85)', 'via ARM1_SENSE (16.60, 41.00)',      # R12F12-TRI-17: nine
                          'via ARM1_SENSE (18.40, 60.25)', 'via BOOT0 (17.80, 52.05)',
                          'via BOOT0 (23.00, 56.25)', 'via GND (16.50, 22.05)', 'via GND (31.75, 15.70)',
                          'via PORT_SENSE (26.20, 60.25)', 'via PYRO1_CONT (13.50, 54.55)',
                          'via PYRO1_CONT (17.10, 58.15)', 'via VCAP1 (25.40, 57.85)',
                          'via VCAP2 (24.60, 57.85)', 'via VLOGIC_SENSE (15.50, 61.05)',
                          'via VLOGIC_SENSE (19.80, 61.05)'])
        self.assertTrue(all(len(x[2]) > 60 for x in r12.SINGLE_OPEN_EXCEPTIONS_R12 if x[0] != 'C22.1'))

    def test_second_via_removed_fails(self):
        """Seeded: R14.1's second 3V3 via (R10 R21-PWR-01's case), U9.8's second GND via and each of D9.1's doubled RAW
        barrels removed: K-power names the tap left on one via."""
        self.assert_doubled(('R14.1', 'U9.8', 'D9.1'))

    def test_r12f9_tri07_tri08_second_vias_removed_fail(self):
        """Seeded (R12F9-TRI-07 / -08): each second barrel of R164.1's 3V3 end, U6's ground, PD10's divider end of the
        PORT_SENSE lane, R111.1's PORT_4V8 feed and R112.2's GND end removed: K-power names the tap left on one via."""
        self.assert_doubled(('R164.1', 'U6.7', 'U6.14', 'U6.17', 'U1.H9', 'R111.1', 'R112.2'))

    def test_r12f10_tri07_second_vias_removed_fail(self):
        """Seeded (R12F10-TRI-07): each new second barrel removed (U5's ground, R13.2's 3V3, U1's VSSA): K-power names the
        taps left on one via; and R12.2's / C30.1's measured exceptions removed, K-power names their single vias."""
        self.assert_doubled(('U5.3', 'U5.4', 'R13.2', 'U1.G1'))
        short = [x for x in r12.SINGLE_OPEN_EXCEPTIONS_R12 if x[0] not in ('R12.2', 'C30.1')]
        issues = self.kpower(short)[0]
        for tap, via in (('R12.2', 'via 3V3 (20.25, 35.35)'), ('C30.1', 'via 3V3A (25.70, 46.60)')):
            self.assertTrue([i for i in issues if i.startswith(f'{tap} (') and via in i], issues)



    def test_r12f12_tri17_second_vias_removed_fail(self):
        """Seeded (R12F12-TRI-17): each round 12 partner via removed on GND (Q122.2's, R118.2's both ways, J9's, the
        servo pull-downs'), 3V3 (R136.1's, U6.1's), PORT_4V8 (J410.2's) and each doubled signal pair (ACT_EN_MCU, ACT_GATE
        at both ends of C120.2's jumper, BAT_SW_RETURN at both ends of its link, VLOGIC_SENSE): K-power names every tap
        left on one via. The pad-to-pad F links of the PC0 and PC5 banks removed: each bank pad is on one via again."""
        self.assert_doubled(('Q122.2', 'R118.2', 'J9.3', 'J9.4', 'D121.2', 'R154.2', 'R155.2', 'R156.2', 'R157.2',
                             'R136.1', 'U6.1', 'J410.2', 'R122.1', 'C120.2', 'R165.1', 'U1.J3'))
        r118 = self.pairs('R118.2')
        self.assertEqual(len({(v, p) for v, p, _ in r118} | {(p, v) for v, p, _ in r118}), 2, r118)
        for (a, b), taps in ((('R130.2', 'R178.2'), ('R130.2',)), (('R178.2', 'C127.2'), ('C127.2',)),
                             (('R133.2', 'R180.2'), ('R133.2', 'R180.2'))):
            with self.subTest(link=(a, b)):
                link = self.link(a, b)
                self.board.Remove(link)
                try:
                    issues, _ = self.kpower()
                finally:
                    self.board.Add(link)
                for tap in taps:
                    self.assertTrue([i for i in issues if i.startswith(f'{tap} (') and 'hangs on one via' in i], issues)

    def test_r12f12_tri17_new_exceptions_are_exact(self):
        """Each round 12 exception is needed (without it K-power names its tap and via) and none is stale; an entry
        for a via that now has a partner (R136.1's first 3V3 via, found from the graph) is stale."""
        new = [x for x in r12.SINGLE_OPEN_EXCEPTIONS_R12 if 'R12F12' in x[2] or 'triage' in x[2]
               or x[0] in ('R122.1', 'U1.F1', 'U1.H4', 'U1.J3', 'R431.2', 'C81.2')]
        self.assertEqual(len(new), 9)
        self.assertEqual([i for i in self.kpower()[0] if i.startswith('stale')], [])
        for tap, via, _ in new:
            with self.subTest(tap=tap, via=via):
                short = [x for x in r12.SINGLE_OPEN_EXCEPTIONS_R12 if (x[0], x[1]) != (tap, via)]
                self.assertTrue([i for i in self.kpower(short)[0] if i.startswith(f'{tap} (') and via in i])
        doubled = self.pairs('R136.1')[0][1]
        stale = list(r12.SINGLE_OPEN_EXCEPTIONS_R12) + [('R136.1', doubled, 'has a partner now')]
        self.assertTrue([i for i in self.kpower(stale)[0] if i.startswith('stale SINGLE_OPEN_EXCEPTIONS entry R136.1')
                         and doubled in i])

    def test_exceptions_are_exact(self):
        """A missing exception fails the tap it covered; an entry whose via is no longer a single point is stale. The
        stale seed is one of R14.1's two 3V3 vias, found from the graph, so it exists on the board (R12F12-TRI-25)."""
        short = [x for x in r12.SINGLE_OPEN_EXCEPTIONS_R12 if x[1] != 'via BOOT0 (23.00, 56.25)']
        self.assertTrue([i for i in self.kpower(short)[0] if 'opening via BOOT0 (23.00, 56.25)' in i])
        via, partner, _ = self.pairs('R14.1')[0]
        on_board = {f'via 3V3 ({pcbnew.ToMM(v.GetPosition().x):.2f}, {pcbnew.ToMM(v.GetPosition().y):.2f})'
                    for v in self.vias('3V3')}
        self.assertTrue({via, partner} <= on_board, (via, partner))
        stale = list(r12.SINGLE_OPEN_EXCEPTIONS_R12) + [('R14.1', via, 'not a single point')]
        self.assertTrue([i for i in self.kpower(stale)[0] if i.startswith('stale SINGLE_OPEN_EXCEPTIONS entry R14.1')
                         and via in i])


@unittest.skipUnless(pcbnew and BOARD12.is_file(), 'KiCad python and the R12 board required')
class Round12Board(unittest.TestCase):
    """R12F12 (round 12, the final pass): the committed board against the rules that pass added, each with a seeded
    fault that fails without the fix (TRI-03 / -18 S-8 inner tracks, TRI-04 R118, TRI-05 / -19 GND spokes, TRI-07 J1's
    polarity legends, TRI-29 the recorded route leftovers and the second barrels' PARALLEL_VIAS_R12 entries)."""

    def setUp(self):
        self.board = pcbnew.LoadBoard(str(BOARD12))

    def rule(self, rid, stage='copper'):
        return r12.check_board(self.board, BOARD12, only={rid}, stage=stage)

    EDIT = """import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1])
op, args = sys.argv[2], sys.argv[3:]
zones = {z.GetZoneName(): z for z in b.Zones()}
texts = {d.GetText(): d for d in b.GetDrawings() if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() == pcbnew.F_SilkS}
if op == 'remove_zone':
    b.Remove(zones[args[0]])
elif op == 'min_width':
    zones[args[0]].SetMinThickness(pcbnew.FromMM(float(args[1])))
elif op == 'swap_text':
    texts[args[0]].SetText(args[1]); texts[args[1]].SetText(args[0])
elif op == 'remove_text':
    b.Remove(texts[args[0]])
if op in ('remove_zone', 'min_width'):
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[1], b)
"""

    def edited(self, rid, stage, *edit):
        """check_r12's report of rule `rid` on a temporary copy of the committed board after one edit: ('remove_zone',
        name) or ('min_width', name, mm), each followed by KiCad's zone fill under the committed DRU, ('swap_text', a, b)
        or ('remove_text', a) on F.Silkscreen; no edit: the board as committed. The edit and the rule run in separate
        KiCad python processes: an in-process refill, and K-legends on the loaded board, leave pcbnew's wrappers
        unusable for the tests that follow."""
        with tempfile.TemporaryDirectory(prefix='r12-edit-') as d:
            path = Path(d) / 'm3.kicad_pcb'
            for name in ('m3.kicad_dru', 'm3.kicad_pro'):
                shutil.copy2(BOARD12.with_name(name), Path(d) / name)
            shutil.copy2(BOARD12, path)
            if edit:
                subprocess.run([sys.executable, '-I', '-c', self.EDIT, str(path), *map(str, edit)], check=True,
                               capture_output=True, timeout=600)
            subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'tools/check_r12.py'), str(path), '--stage', stage,
                            '--only', rid, '--report', str(Path(d) / 'r.json')], capture_output=True, timeout=600)
            return json.loads((Path(d) / 'r.json').read_text())

    def test_tri03_inner_act_gate_links_keep_s8(self):
        """ACT_GATE's In2 jumper at C120.2 (four tracks: the jumper's two and the two links to the second barrels) keeps
        1 mm from the In2 3V3 fill. Seeded: without the fill void at the jumper's bend (7.7, 34.85) the refilled 3V3
        pour comes back to under 1 mm and S-8 names the track."""
        rep = self.rule('S-8')
        self.assertTrue(rep['ok'], rep['issues'])
        ev = rep['evidence']['s8']['inner_tracks']
        self.assertEqual((ev['tracks'], ev['near']), (4, {}))
        voids = sorted(z.GetZoneName() for z in self.board.Zones() if z.GetIsRuleArea()
                       and z.GetZoneName().startswith('S8_track_'))
        self.assertEqual(voids, ['S8_track_ACT_GATE_In2_6.8_33.95', 'S8_track_ACT_GATE_In2_7.2_33.55',
                                 'S8_track_ACT_GATE_In2_7.7_34.85', 'S8_track_ACT_GATE_In2_8.6_34.85',
                                 'S8_track_ACT_GATE_In2_9.15_34.85'])
        rep = self.edited('S-8', 'copper', 'remove_zone', 'S8_track_ACT_GATE_In2_7.7_34.85')
        self.assertFalse(rep['ok'])
        self.assertTrue([i for i in rep['issues'] if '3V3 copper is 0.' in i and 'ACT_GATE track' in i
                         and 'inner-layer track of a barrel net' in i], rep['issues'])

    def test_tri04_r118_second_gate_pull_down(self):
        """R118 (10k, ACT_EN to GND) is on the board beside R123; S-3 and K-neighbours hold it. Seeded: its GND end
        moved to 3V3 fails both."""
        rep = self.rule('S-3')
        self.assertTrue(rep['ok'], rep['issues'])
        self.assertEqual(rep['evidence']['s3']['load_enable_hold2'], dict(ref='R118', nets=['ACT_EN', 'GND'], ohm=10000.0))
        self.assertEqual(r12.GUARD_LOAD['ACT_EN_MCU'][4], ('R118',))
        self.assertTrue(self.rule('K-neighbours')['ok'])
        pad = next(p for p in self.board.FindFootprintByReference('R118').Pads() if p.GetNumber() == '2')
        pad.SetNet(self.board.FindNet('3V3'))
        self.assertTrue([i for i in self.rule('S-3')['issues'] if 'R118' in i and 'must join ACT_EN to GND' in i])
        self.assertTrue([i for i in self.rule('K-neighbours')['issues']
                         if 'further pull-down R118 must join ACT_EN to GND' in i])

    def test_tri19_plated_gnd_pads_keep_their_spokes(self):
        """Every plated GND pad inside a GND pour has at least two thermal spokes on each GND pour layer and J1.2, the
        battery return, four on B and four on In1. Seeded (R12F12-TRI-05): with GND_pour_B's minimum width back at
        0.5 mm the refill drops J1.2's B spokes and K-copper fails; a pad asked for more than it has and a stale name
        fail too."""
        rep = self.rule('K-copper')
        self.assertTrue(rep['ok'], rep['issues'])
        spokes = rep['evidence']['k_copper']['gnd_spokes']
        self.assertEqual(spokes['J1.2'], {'B.Cu': 4, 'In1.Cu': 4})
        self.assertEqual(sorted(spokes), ['J1.2', 'J3.1', 'J3.2', 'J3.3', 'J3.4'])
        for pad, layers in spokes.items():
            self.assertEqual(sorted(layers), ['B.Cu', 'In1.Cu'], pad)
            self.assertTrue(all(n == 'solid' or n >= r12.GND_SPOKES_MIN for n in layers.values()), (pad, layers))
        self.assertEqual(r12.GND_SPOKES_PADS, {'J1.2': (4, ('In1.Cu', 'B.Cu'))})
        self.assertTrue([i for i in r12.gnd_spokes(self.board, named={'J3.2': (5, ('B.Cu',))})[0]
                         if 'J3.2' in i and 'needs 5' in i])
        self.assertTrue([i for i in r12.gnd_spokes(self.board, named={'J1.1': (4, ('B.Cu',))})[0]
                         if 'J1.1' in i and 'stale' in i])                 # BAT_IN: no GND pad
        self.assertTrue([i for i in r12.gnd_spokes(self.board, named={'J1.2': (4, ('F.Cu', 'B.Cu'))})[0]
                         if 'J1.2 (GND, plated) joins no GND pour on F.Cu' in i])
        self.assertEqual(r12.gnd_spokes(self.board, named={'J99.1': (4, ('B.Cu',))})[0], [])    # no such part: N-1's
        pour = next(z for z in self.board.Zones() if z.GetZoneName() == 'GND_pour_B')
        self.assertAlmostEqual(pcbnew.ToMM(pour.GetMinThickness()), 0.25)
        rep = self.edited('K-copper', 'copper', 'min_width', 'GND_pour_B', 0.5)
        self.assertFalse(rep['ok'])
        self.assertTrue([i for i in rep['issues'] if 'J1.2 (GND, plated) joins GND_pour_B on B.Cu by 0 thermal spokes, '
                         'needs 4' in i], rep['issues'])

    def test_tri07_j1_polarity_legends(self):
        """BAT+ and GND are on the top silkscreen beside J1.1 / J1.2, within the legend reach. Seeded: swapped, or one
        missing, K-legends fails."""
        rep = self.edited('K-legends', 'full')
        self.assertTrue(rep['ok'], rep['issues'])
        ev = rep['evidence']['k_legends']['polarity_legends']
        self.assertEqual(sorted(ev), ['BAT+', 'GND'])
        for word in ev:
            self.assertLess(ev[word]['own_mm'], ev[word]['other_mm'] - r12.POLARITY_MARGIN, word)
        rep = self.edited('K-legends', 'full', 'swap_text', 'BAT+', 'GND')
        self.assertEqual(len([i for i in rep['issues'] if 'is not nearer contact' in i]), 2, rep['issues'])
        rep = self.edited('K-legends', 'full', 'remove_text', 'GND')
        self.assertTrue([i for i in rep['issues'] if "polarity legend 'GND' must appear exactly once" in i], rep['issues'])

    def test_tri29_route_leftovers_recorded_and_second_barrels_named(self):
        """route_check r12 on the committed board: nothing failing, the eight non-critical leftovers each recorded, none
        unrecorded and none stale. Seeded: an entry dropped is reported missing, an extra one stale; without ACT_GATE's
        PARALLEL_VIAS_R12 entries its second barrels fail as extra vias and loops."""
        rc.set_profile('r12')
        try:
            inst = rc.scan(self.board)
            failures, allowed, stale = rc.evaluate(inst)
            self.assertEqual((failures, stale), ([], []))
            recorded, missing, stale_left = rc.leftover_check(inst)
            self.assertEqual((len(recorded), missing, stale_left), (8, [], []))
            _, missing, _ = rc.leftover_check(inst, rc.LEFTOVERS[1:])
            self.assertEqual([(d['cat'], d['net']) for d in missing], [rc.LEFTOVERS[0][:2]])
            gone = ('extra_vias', 'GONE', 'net', (1.0, 1.0), 'no such net')
            self.assertEqual(rc.leftover_check(inst, rc.LEFTOVERS + [gone])[2], [gone])
            rc.PARALLEL_VIAS = [e for e in rc.PARALLEL_VIAS if e[0] != 'ACT_GATE']
            failures, _, _ = rc.evaluate(rc.scan(self.board))
            self.assertTrue([d for d in failures if d['net'] == 'ACT_GATE' and d['cat'] in ('extra_vias', 'track_loop')],
                            failures)
        finally:
            rc.set_profile('r8')


@unittest.skipUnless(pcbnew and BOARD12.is_file(), 'KiCad python and the R12 board required')
class Round1Fixes(unittest.TestCase):
    """R12 review round 1 gate fixes (D-R12-86 ... -90), seeded on the committed board."""

    @classmethod
    def setUpClass(cls):
        cls.board = pcbnew.LoadBoard(str(BOARD12))

    def kn(self, board=None):
        return r12.check_board(board or self.board, BOARD12, only={'K-neighbours'}, stage='full')

    def test_k_neighbours_registered_in_every_stage(self):
        for stage in ('placement', 'copper', 'full'):
            self.assertIn('K-neighbours', r12.STAGES[stage], stage)
        self.assertNotIn(('ACT_EN_MCU', 'LOGIC_SOURCE_ST'), r12.NEIGHBOUR_INERT)   # U11 deleted (D-R12-04)

    def test_k_neighbours_pass_on_board_and_fail_on_port_sense_at_g3(self):
        rep = self.kn()
        self.assertTrue(rep['ok'], rep['issues'])
        gates = rep['evidence']['k_neighbours']['bridged_gate_V']
        # D-R12-93: PORT_SENSE left G3 for PD10 (H9); its D-R12-86 inert entry is gone, so PORT_SENSE back on G3 fails
        self.assertEqual(set(gates), {f'ACT_EN_MCU/{n}' for n in ('PYRO1_CONT', 'CAM_5V_SENSE', 'NRST')})
        self.assertNotIn(('ACT_EN_MCU', 'PORT_SENSE'), r12.NEIGHBOUR_INERT)
        u1 = self.board.FindFootprintByReference('U1')
        g3 = next(p for p in u1.Pads() if p.GetNumber() == 'G3')
        kept = g3.GetNet()
        try:
            g3.SetNet(self.board.FindNet('PORT_SENSE'))
            rep = self.kn()
            self.assertFalse(rep['ok'])
            self.assertTrue(any('G3' in i and 'PORT_SENSE' in i for i in rep['issues']), rep['issues'])
        finally:
            g3.SetNet(kept)

    def test_k_neighbours_driver_or_uninert_net_fails(self):
        u1 = self.board.FindFootprintByReference('U1')
        g3 = next(p for p in u1.Pads() if p.GetNumber() == 'G3')
        g2 = next(p for p in u1.Pads() if p.GetNumber() == 'G2')
        net_g3, net_g2 = g3.GetNet(), g2.GetNet()
        led = self.board.FindNet('HG_CS')
        try:
            g2.SetNet(led)                                                    # a push-pull GPIO beside PC1
            rep = self.kn()
            self.assertFalse(rep['ok'])
            self.assertTrue(any('neighbour G2 carries HG_CS' in i for i in rep['issues']), rep['issues'])
        finally:
            g2.SetNet(net_g2)
        r33 = self.board.FindFootprintByReference('R33')
        pad = next(iter(r33.Pads()))
        kept = pad.GetNet()
        try:
            pad.SetNet(next(p for p in u1.Pads() if p.GetNumber() == 'E2').GetNet())   # an unrecorded part on CAM_5V_SENSE
            rep = self.kn()
            self.assertFalse(rep['ok'])
            self.assertTrue(any('R33' in i and 'sense net' in i for i in rep['issues']), rep['issues'])
        finally:
            pad.SetNet(kept)
        self.assertTrue(self.kn()['ok'])

    def test_dru_unconditional_after_scoped_refused(self):
        text = (BOARD12.with_suffix('.kicad_dru')).read_text()
        self.assertEqual(r12.dru_order(text), [])
        floor = text[text.index('# JLC multilayer 0.09 mm, plus 0.01 mm'):]
        floor = floor[:floor.index('\n\n')]
        self.assertIn('R12 board floor: copper clearance', floor)
        late = text.replace(floor + '\n\n', '') + '\n' + floor + '\n'       # the round-1 order: floor after J2's rule
        found = r12.dru_order(late)
        # the first scoped clearance rule is the JLC SMD pad rule since R12F5-TRI-06 (Tag-Connect's before it)
        self.assertTrue(any('R12 board floor: copper clearance' in i and 'R12 JLC SMD pad to pad' in i for i in found),
                        found)
        with tempfile.TemporaryDirectory(prefix='r12-druorder-') as d:
            path = Path(d) / 'm3.kicad_pcb'
            (Path(d) / 'm3.kicad_dru').write_text(late)
            shutil.copy2(ROOT / 'm3_design/r12/m3.kicad_pro', Path(d) / 'm3.kicad_pro')
            rep = r12.check_board(self.board, path, only={'K-rules'}, stage='placement')
            self.assertFalse(rep['ok'])
            self.assertTrue(any('follows the scoped rule' in i for i in rep['issues']), rep['issues'])
        gen = r12_sch.dru((r12_sch.INPUT / 'm3.kicad_dru').read_text())
        self.assertEqual(r12.dru_order(gen), [])
        self.assertLess(gen.index('R12 board floor: copper clearance'), gen.index('Tag-Connect contact'))

    def test_route_check_hg_cs_is_spi(self):
        rc.set_profile('r12')
        try:
            for net in ('HG_CS', 'IMU_CS', 'SD_CS', 'QSPI_NCS'):
                self.assertEqual(rc.net_class(net), 'spi', net)
                self.assertIn(rc.net_class(net), rc.SIGNAL_CRITICAL, net)
        finally:
            rc.set_profile('r8')

    def test_fit_r12_db125_terminal_tails(self):
        report = fc.check_board(self.board, ROOT / 'm3_design/r12', profile='r12')
        tails = report['terminal_tails']
        self.assertEqual((tails['count'], tails['refs'], tails['max_below_seating_mm']),
                         (4, ['J1', 'J121'], {'J1': 3.9, 'J121': 3.8}))
        rows = {ref: box for _, ref, _, box in report['rows']}
        self.assertAlmostEqual(rows['J121.1 terminal tail'][4], -3.8, places=6)
        self.assertAlmostEqual(rows['J1.1 terminal tail'][4], -3.9, places=6)
        self.assertGreater(tails['minimum_bore_margin_mm'], 0)


@unittest.skipUnless(pcbnew and BOARD12.is_file(), 'KiCad python and the R12 board required')
class FireGaps(Plants, unittest.TestCase):
    """R12F5-TRI-01 (tightened by the round 5 verifier, lane P2): S-10 carries R10's fire-net copper gaps (D-R26-02 / -04)
    and D-R11-23 to R12 on every layer, fills and barrels included, default-deny, with item-pair exceptions at their
    floors (m3_design/r12_fire.py). The committed board passes; each planted bridge-risk item fails S-10, and DRC with
    the committed DRU fails it too (the DRU is generated from the same definition)."""

    def setUp(self):
        self.board = pcbnew.LoadBoard(str(BOARD12))

    def s10(self):
        return r12.check_board(self.board, BOARD12, only={'S-10'}, stage='copper')


    def drc_s10(self):
        """kicad-cli DRC of the planted board as it stands, with the committed DRU: the S-10 rule violations (off-board
        plants need no isolation)."""
        return [v for v in self.kicad_drc() if "rule 'S-10" in v]

    def planted(self, want, drc=None):
        """S-10 fails with an issue containing every string of want; with drc = (rule, plant, target, gap), DRC of
        the isolated copy reports that rule between the plant and the target at that gap (assert_drc)."""
        rep = self.s10()
        self.assertFalse(rep['ok'])
        hits = [i for i in rep['issues'] if all(w in i for w in want)]
        self.assertTrue(hits, rep['issues'])
        if drc is not None:
            rule, plant, target, gap = drc
            self.assert_drc(self.isolate_for_drc(plant, target), rule, plant, target, gap)
        return hits

    def fails_s10(self, made, cls, drc=None):
        """S-10 fails on exactly the plant-target pair of `made` (plant, target, measured gap), at that gap and
        'below LIMIT mm (CLASS)' (cls = (limit, class)); with drc, the isolated copy's DRC reports that rule between the
        plant and the target at that gap. Returns the S-10 issues that hit."""
        plant, target, gap = made
        lid = self.layer_of(plant)
        p, t = f'{plant.GetNetname()} {self.label(plant, lid)}', f'{target.GetNetname()} {self.label(target, lid)}'
        tail = f' on {self.board.GetLayerName(lid)}: {gap:.4f} mm, below {cls[0]:g} mm ({cls[1]})'
        rep = self.s10()
        self.assertFalse(rep['ok'])
        hits = [i for i in rep['issues'] if f'{t} to {p}{tail}' in i or f'{p} to {t}{tail}' in i]
        self.assertTrue(hits, (p, t, tail, rep['issues']))
        if drc is not None:
            self.assert_drc(self.isolate_for_drc(plant, target), drc, plant, target, gap)
        return hits

    def test_committed_board_passes_with_recorded_exceptions(self):
        rep = self.s10()
        self.assertTrue(rep['ok'], rep['issues'])
        ev = rep['evidence']['s10']
        kept = {e['pair'] for e in ev['exceptions']}
        for pair in ('PYRO1_GATE_N track (20.6, 55.45)-(18.9, 55.45) to 3V3 U1.B2 on F.Cu: 0.150',
                     'PYRO1_GATE Q124.1 to PYRO1_OUT Q124.3 on F.Cu: 1.04'):
            self.assertTrue([k for k in kept if k.startswith(pair)], pair)
        # no stale, none extra (a pad label names every pad of its number: U9's L-shaped pins are two pads each)
        self.assertEqual(len({(e['exception'], e['pair'].rsplit(': ', 1)[0]) for e in ev['exceptions']}),
                         sum(len(v) for v in fire.EXCEPTIONS.values()))
        self.assertEqual(set(fire.EXCEPTIONS), set(fire.WHY))
        self.assertTrue(ev['u1_nc_balls'])
        self.assertTrue(all(' U1.' in p and 'unconnected-(U1-' in p for p in ev['u1_nc_balls']))
        self.assertIn('ACT_DRV', ev['netlist_classes']['sink'])
        self.assertIn('BUZZ_OUT', ev['netlist_classes']['sink'])
        self.assertIn('VLOGIC', ev['netlist_classes']['supply'])
        self.assertIn('PYRO1_CONT', ev['netlist_classes']['mcu'])

    def test_verifier_A_B_J_low_side_sinks_and_vlogic_near_out_fail(self):
        """Round 5 verifier cases A, B, J: a 0.2 mm track of a low-side sink (ACT_DRV, BUZZ_OUT) or VLOGIC 0.2 mm east of
        J121.1 (PYRO1_OUT) fails S-10 and DRC, which names J121.1."""
        for net in ('ACT_DRV', 'BUZZ_OUT', 'VLOGIC'):
            with self.subTest(net=net):
                self.setUp()
                self.fails_s10(self.plant_out(net), (1.04, 'out'), drc="'S-10 PYRO1_OUT to every net'")

    def test_verifier_C_D_G_bridges_to_the_gate_track_fail(self):
        """Cases C, D (formerly the blanket-inert nets) and G: a 0.1 mm track 0.10 / 0.20 mm north of PYRO1_GATE's run
        into R126.2 (gate_run) fails S-10 and DRC, which names the run."""
        for net, gap in (('QSPI_IO2', 0.10), ('HSE_OUT', 0.10), ('ACT_EN_MCU', 0.20)):
            with self.subTest(net=net):
                self.setUp()
                self.fails_s10(self.plant_gate(net, gap), (fire.GATE_MIN, 'gate'),
                               drc="'S-10 Q124 gate nets to every raising net'")

    def test_verifier_E_new_3v3_near_the_pe4_lane_inside_u1_fails(self):
        """The D-R11-23 exception names its item pairs: a new 3V3 track 0.15 mm south of PE4's lane (as near as U1.B2,
        the excepted pair's floor) is not excepted. The plant sits between balls C1 (HSE_IN) and C2 (GND), 0.13 mm from
        each, which S-10 does not hold against 3V3, so the lane is its one neighbour under the gate limit; S-10 and the
        DRC of the isolated copy name the lane."""
        made = self.plant_e()
        rows = [r for r in r12.fire_gaps(self.board) if r['b'] == self.label(made[0], pcbnew.F_Cu)]
        self.assertTrue(all(r['gap'] >= 0.13 for r in rows if r['net_a'] != 'PYRO1_GATE_N'), rows)
        self.fails_s10(made, (fire.GATE_MIN, 'gate'), drc="'S-10 Q124 gate nets to every raising net'")

    def test_verifier_F_protected_net_fill_is_measured(self):
        # a PYRO1_OUT fill on In2 over a 3V3 track, off the board aft of its forward edge (y 93-96, nothing there to
        # isolate from): S-10 measures protected-net fills too (was one-directional), and DRC names the fill
        z = self.zone('PYRO1_OUT', [(30, 93.85), (31, 93.85), (31, 94.85), (30, 94.85)], pcbnew.In2_Cu)
        t = self.track('3V3', (30.5, 93.35), (30.5, 95.35), pcbnew.In2_Cu)
        self.planted(('PYRO1_OUT fill PYRO1_OUT to 3V3 track (30.5, 93.35)-(30.5, 95.35)', ': 0.0000 mm'))
        self.assert_drc(self.kicad_drc(), "'S-10 PYRO1_OUT to every net'", t, z, 0.0)

    def test_verifier_G_H_I_still_fail(self):
        # H: VCAP1 0.3 mm east of J121.1; I: PORT_4V8 on In2 0.5 mm east of J121.1's barrel
        self.fails_s10(self.plant_out('VCAP1', 0.3), (1.04, 'out'), drc="'S-10 PYRO1_OUT to every net'")
        self.setUp()
        self.fails_s10(self.plant_out_in2(), (1.04, 'out'), drc="'S-10 PYRO1_OUT to every net'")

    def test_out_to_gnd_copper_and_fill(self):
        """GND copper 0.1 mm west of J121.1 fails at 0.25 mm, a GND fill 0.3 mm east of it on B at 0.5 mm."""
        self.fails_s10(self.plant_out_gnd(), (fire.GND_MIN, 'out-gnd'), drc="'S-10 PYRO1_OUT to GND'")
        self.setUp()
        self.fails_s10(self.plant_out_gnd_fill(), (fire.FILL_MIN, 'out-gnd'), drc="'S-10 PYRO1_OUT to GND fills'")

    def test_ign_to_gnd_copper_and_fill_fail(self):
        # J121.2 (PYRO1_IGN) is RAW_ACT through R134 2 ohm: a GND bridge overloads R134 (verifier). GND copper 0.2 mm
        # south of it and a GND fill 0.3 mm south fail S-10 and DRC.
        self.fails_s10(self.plant_ign_gnd(), (fire.IGN_MIN, 'ign'), drc="'S-10 PYRO1_IGN to every net'")
        self.setUp()
        self.fails_s10(self.plant_ign_gnd_fill(), (fire.FILL_MIN, 'ign'), drc="'S-10 PYRO1_IGN to fills'")

    def test_ign_pours_pulled_back(self):
        # J121.2 sat 0.100 mm from GND_pour_B (B) and 0.25 mm from GND_In1: every fill now keeps 0.5 mm
        near = [r for r in r12.fire_gaps(self.board) if r['a'] == 'J121.2' and r['b'].startswith('fill ')]
        self.assertTrue(all(r['gap'] >= fire.FILL_MIN - 5e-4 for r in near), near)

    def test_nc_exemption_is_u1_balls_only(self):
        # another part's NC pad net, copper with no net and a U1 NC net on a track all count as foreign copper
        for net in ('unconnected-(D120-A2-Pad2)', '', 'unconnected-(U1-PC15-PadB1)'):
            with self.subTest(net=net):
                self.setUp()
                self.fails_s10(self.plant_gate(net, 0.2), (fire.GATE_MIN, 'gate'),
                               drc="'S-10 Q124 gate nets to every raising net'" if net else None)

    def test_exception_floor_and_stale_entries(self):
        key = 'D-R11-23'
        kept = fire.EXCEPTIONS[key]
        try:
            fire.EXCEPTIONS[key] = tuple((a, b, layer, 0.2 if b == 'U1.B2' and floor < 0.2 else floor)
                                         for a, b, layer, floor in kept)
            self.planted(('PYRO1_GATE_N track (20.6, 55.45)-(18.9, 55.45) to 3V3 U1.B2', 'below the 0.200 mm floor'))
            fire.EXCEPTIONS[key] = kept + (('U1.C3', 'via (1, 1)', 'F.Cu', 0.5),)
            self.planted(('exception U1.C3 to via (1, 1) on F.Cu', 'stale entry'))
        finally:
            fire.EXCEPTIONS[key] = kept
        self.assertTrue(self.s10()['ok'])

    def test_moved_excepted_item_is_not_excepted(self):
        # U1.B2's 3V3 dog-bone via moved 0.1 mm toward PE4's lane: a new item (fails its limit), the old pair stale
        via = self.via_at('3V3', 'U1.B2')
        old = self.label(via, pcbnew.F_Cu)
        self.assertTrue([e for e in fire.EXCEPTIONS['D-R11-23'] if e[1] == old], old)
        via.SetPosition(via.GetPosition() + pcbnew.VECTOR2I(0, nm(0.1)))
        new = self.label(via, pcbnew.F_Cu)
        lane = self.label(self.pe4_lane(), pcbnew.F_Cu)
        self.assertTrue(self.planted((f'PYRO1_GATE_N {lane} to 3V3 {new}', 'below 1.0585')))
        self.assertTrue(any(old in i and 'stale' in i for i in self.s10()['issues']))

    def test_netlist_guard_refuses_classing_a_sink_out(self):
        kept = dict(fire.NOT_A_PATH)
        try:
            fire.NOT_A_PATH[(fire.OUT, 'ACT_DRV')] = 'planted'
            self.planted(('PYRO1_OUT / ACT_DRV is classed "not a path"', 'sink'))
        finally:
            fire.NOT_A_PATH.clear(); fire.NOT_A_PATH.update(kept)

    # ---- R12F6-TRI-02: the U1 NC-ball exemption is the gate nets' only -------------------------------------------
    def test_r12f6_tri02_nc_ball_counts_against_out_and_ign(self):
        """A U1 NC ball is foreign copper to PYRO1_OUT (1.04 mm) and PYRO1_IGN (0.25 mm), exempt only for the gate nets;
        a PYRO1_OUT track 0.38 mm (the gate lens's plant) and a PYRO1_IGN track 0.20 mm north of U1.A1 (PC14, NC) fail
        S-10 and DRC. (0.38 mm is above IGN's own 0.25 mm limit, so IGN is planted below that limit.)"""
        nc = 'unconnected-(U1-PE3-PadB3)'
        self.assertEqual(fire.pair_limit(fire.OUT, None, nc, 'U1', False)[:2], (fire.OUT_MIN, 'out'))
        self.assertEqual(fire.pair_limit(fire.IGN, None, nc, 'U1', False)[:2], (fire.IGN_MIN, 'ign'))
        self.assertEqual(fire.pair_limit(fire.IGN, None, nc, 'U1', True)[:2], (fire.FILL_MIN, 'ign'))
        for gate in fire.GATES:
            self.assertEqual(fire.pair_limit(gate, None, nc, 'U1', False)[:2], (None, 'U1 NC ball'))
        rules = {r[0]: r[2] for r in fire.dru_rules()}
        for name in ('S-10 PYRO1_OUT to every net', 'S-10 PYRO1_IGN to every net', 'S-10 PYRO1_IGN to fills'):
            self.assertNotIn("unconnected-*", rules[name], name)
        self.assertIn(fire.NOT_U1_NC, rules['S-10 Q124 gate nets to every raising net'])
        # KiCad names one clearance violation per track and picks among candidates (round 6 V-5): the isolated copy
        # keeps U1.A1 alone (the field's other balls join the plant's net, PE4's lane and the A2 / B2 copper go)
        for net, gap, cls, rule in ((fire.OUT, 0.38, (1.04, 'out'), "'S-10 PYRO1_OUT to every net'"),
                                    (fire.IGN, 0.20, (0.25, 'ign'), "'S-10 PYRO1_IGN to every net'")):
            with self.subTest(net=net):
                self.setUp()
                self.fails_s10(self.plant_a1(net, gap), cls, drc=rule)

    # ---- R12F6-TRI-01: the cold pull-up through R136, and the commanded-fire state -------------------------------
    def netlist(self, mutate):
        """A temporary copy of the committed netlist with mutate(root) applied (the board stays the committed one)."""
        import xml.etree.ElementTree as ET
        tree = ET.parse(BOARD12.with_name('schematic.net.xml'))
        mutate(tree.getroot())
        d = tempfile.mkdtemp(prefix='r12-net-')
        self.addCleanup(shutil.rmtree, d, True)
        path = Path(d) / 'schematic.net.xml'
        tree.write(path)
        return path

    @staticmethod
    def move_node(root, ref, pin, net):
        node = parent = None
        for n in root.findall('./nets/net'):
            for x in n.findall('node'):
                if (x.get('ref'), x.get('pin')) == (ref, pin):
                    node, parent = x, n
        parent.remove(node)
        next(n for n in root.findall('./nets/net') if n.get('name') == net).append(node)

    @staticmethod
    def set_value(root, ref, value):
        next(c for c in root.findall('./components/comp') if c.get('ref') == ref).find('value').text = value

    def s10_netlist(self, path):
        return r12.check_board(self.board, BOARD12, only={'S-10'}, stage='copper', netlist=path)

    def test_r12f6_tri01_cold_pullup_holds_in_the_fire_state(self):
        """The committed netlist: 3V3 -> R136 5.1k -> D120.1 (PYRO1_COLD_PU) -> PYRO1_COLD -> R131 5.1k -> PYRO1_OUT, so
        a bridge across R131 while Q124 conducts meets R136; CONT_MID meets R129; each class reason covers Q124 on."""
        parts, pins = r12_sch_check.read_netlist(BOARD12.with_name('schematic.net.xml'))
        self.assertEqual((pins['R136', '1'], pins['R136', '2'], pins['D120', '1'], pins['D120', '3'], pins['R131', '2'],
                          pins['R131', '1']), ('3V3', 'PYRO1_COLD_PU', 'PYRO1_COLD_PU', 'PYRO1_COLD', 'PYRO1_COLD',
                                               'PYRO1_OUT'))
        self.assertEqual((parts['R131']['value'], parts['R136']['value']), ('5.1k', '5.1k'))
        ev = self.s10()['evidence']['s10']['fire_state']
        self.assertEqual(ev['series_ohm']['PYRO1_COLD'], {'3V3': 5100.0})
        self.assertEqual(ev['series_ohm']['PYRO1_CONT_MID'], {'PYRO1_CONT': 5100.0})
        self.assertEqual(ev['series_ohm']['D120.1'], 'PYRO1_COLD_PU')
        for (p, f), why in fire.NOT_A_PATH.items():
            if p == fire.OUT and f not in ('GND',) + fire.PROTECTED:
                self.assertIn('Q124 on', why, f)
        self.assertNotIn((fire.OUT, 'PYRO1_COLD_PU'), fire.NOT_A_PATH)     # held at OUT_MIN like every net

    def test_r12f6_tri01_anode_on_3v3_fails(self):
        """D120's anode planted back on 3V3 (round 6's circuit): S-10's netlist guard fails twice (the anode itself, and
        the PYRO1_COLD class at 0 ohm in the fire state), and S-2 refuses D120 as an unnamed armed-side supply tie."""
        path = self.netlist(lambda root: self.move_node(root, 'D120', '1', '3V3'))
        rep = self.s10_netlist(path)
        self.assertFalse(rep['ok'])
        self.assertTrue([i for i in rep['issues'] if "D120.1 (the cold pull-up diode's anode) is on 3V3 itself" in i],
                        rep['issues'])
        self.assertTrue([i for i in rep['issues'] if 'PYRO1_OUT / PYRO1_COLD is classed "not a path"' in i
                         and 'joins 3V3 to GND through only 0 ohm' in i], rep['issues'])
        for pad in self.board.FindFootprintByReference('D120').Pads():
            if pad.GetNumber() == '1':
                pad.SetNet(self.board.FindNet('3V3'))
        s2 = r12.check_board(self.board, BOARD12, only={'S-2'}, stage='copper')
        self.assertTrue([i for i in s2['issues'] if 'D120 has pads on the armed / RAW_ACT side net PYRO1_COLD and on the '
                         'supply 3V3' in i], s2['issues'])

    def test_r12f6_tri01_series_resistor_bypassed_or_too_small_fails(self):
        for value, ohm in (('0', '0'), ('1k', '1000')):
            with self.subTest(value=value):
                path = self.netlist(lambda root: self.set_value(root, 'R136', value))
                rep = self.s10_netlist(path)
                self.assertTrue([i for i in rep['issues'] if 'PYRO1_COLD' in i and f'through only {ohm} ohm' in i],
                                rep['issues'])

    def test_r12f6_tri01_new_class_must_hold_with_q124_on(self):
        """A planted not-a-path class the older guard passes (LED_RED_A is no rail, sink or MCU pin) fails the fire-state
        guard: PE4's neighbour LED_RED reaches it through R32 220 ohm."""
        kept = dict(fire.NOT_A_PATH)
        try:
            fire.NOT_A_PATH[(fire.OUT, 'LED_RED_A')] = 'planted'
            self.assertEqual(fire.guard(fire.netlist_classes(BOARD12.with_name('schematic.net.xml'))), [])
            self.planted(('PYRO1_OUT / LED_RED_A is classed "not a path"', 'joins LED_RED to GND through only 220 ohm'))
        finally:
            fire.NOT_A_PATH.clear(); fire.NOT_A_PATH.update(kept)
        self.assertTrue(self.s10()['ok'])

    def test_r12f6_tri01_cold_pullup_node_held_from_out(self):
        """PYRO1_COLD_PU is not classed out: its copper 0.2 mm from J121.1 fails S-10 and DRC like any net."""
        self.fails_s10(self.plant_out('PYRO1_COLD_PU'), (1.04, 'out'), drc="'S-10 PYRO1_OUT to every net'")

    # ---- round 6 verifier V-1 / V-2: the pack-energy nets ---------------------------------------------------------
    def test_round6_v1_pack_nets_derived_and_held(self):
        """pack_nets() derives BAT_IN / ACT_FET_S / RAW_ACT from the netlist (J1.1 through Q120 / Q121, stopping at U9,
        capacitors, R134 and every larger resistor); each is held at PACK_MIN from every net, fills included, but the
        classed nets; the DRU carries one rule per pack net, after PYRO1_IGN's so 1.04 mm wins over IGN's 0.25 mm."""
        net = BOARD12.with_name('schematic.net.xml')
        self.assertEqual(fire.pack_nets(net), (sorted(fire.PACK), []))
        self.assertEqual(fire.pack_guard(net)[0], [])
        self.assertEqual(fire.PACK_MIN, fire.OUT_MIN)
        for p in fire.PACK:
            for f, fill in (('GND', False), ('GND', True), ('BAT_DAMP', False), ('3V3', True), ('ARM1_SENSE', False),
                            ('BAT_FAULT_N', False), ('PYRO1_CONT', False)):
                self.assertEqual(fire.pair_limit(p, None, f, None, fill)[:2], (fire.PACK_MIN, 'pack'), (p, f))
            self.assertEqual(fire.pair_limit(p, None, 'ACT_GATE', None, False)[:2], (None, 'not a path'))
        self.assertEqual(fire.pair_limit('RAW_ACT', None, 'ARM1_SENSE_MID', None, False)[0], None)
        self.assertEqual(fire.pair_limit('BAT_IN', None, 'ARM1_SENSE_MID', None, False)[0], fire.PACK_MIN)
        self.assertEqual(fire.pair_limit(fire.IGN, None, 'BAT_IN', None, False)[:3], (fire.PACK_MIN, 'pack', 'BAT_IN'))
        self.assertEqual(fire.pair_limit(fire.GATES[0], None, 'BAT_IN', None, False)[0], fire.GATE_MIN)
        names = [r[0] for r in fire.dru_rules()]
        for p in fire.PACK:
            rule = next(r for r in fire.dru_rules() if r[0] == f'S-10 {p} (pack energy) to every net')
            self.assertGreater(names.index(rule[0]), names.index('S-10 PYRO1_IGN to fills'))
            self.assertIn("B.NetName != 'PYRO1_GATE'", rule[2])
            self.assertNotIn("B.NetName != 'GND'", rule[2])
            self.assertEqual(rule[1], 'clearance (min 1.04mm)')
        ev = self.s10()['evidence']['s10']['pack']
        self.assertEqual(ev['pack_nets'], sorted(fire.PACK))
        self.assertEqual(ev['RAW_ACT / ARM1_SENSE_MID'], {'ARM1_SENSE': 5100.0})
        self.assertEqual(ev['BAT_IN / ACT_GATE'], {'ACT_DRV': 10000.0})

    def test_round6_v1_v2_verifier_pairs_cleared(self):
        """The verifier's pairs (RAW_ACT to GND 0.792 mm and to ARM1_SENSE 0.546 mm at R132.1, ACT_FET_S to BAT_DAMP
        0.772 mm at R120.1 / R166.1) are gone: RAW_ACT and ACT_FET_S keep PACK_MIN from every unclassed net, with no
        exception; the only pack exceptions are BAT_IN's, in the pack-entry cell (keys PACK_*)."""
        gaps = r12.fire_gaps(self.board)
        for p, f in (('RAW_ACT', 'GND'), ('RAW_ACT', 'ARM1_SENSE'), ('ACT_FET_S', 'BAT_DAMP'), ('ACT_FET_S', 'GND'),
                     ('RAW_ACT', '3V3'), ('BAT_IN', '3V3')):
            near = [r for r in gaps if {r['net_a'], r['net_b']} == {p, f}]
            self.assertTrue(all(r['gap'] >= fire.PACK_MIN - 5e-5 for r in near), (p, f, near))
        pack_items = {a for k, v in fire.EXCEPTIONS.items() if k.startswith('PACK_') for a, *_ in v}
        self.assertEqual({fire.EXCEPTION_NETS[a] for a in pack_items}, {'BAT_IN'})
        self.assertFalse([1 for k, v in fire.EXCEPTIONS.items() if not k.startswith('PACK_')
                          for a, b, *_ in v if fire.EXCEPTION_NETS[a] in fire.PACK or fire.EXCEPTION_NETS[b] in fire.PACK])
        self.assertEqual({k for k in fire.EXCEPTIONS if k.startswith('PACK_')},
                         {'PACK_GND', 'PACK_EN', 'PACK_SW', 'PACK_FLT', 'PACK_OUT', 'PACK_U9'})

    def test_round6_v1_raw_act_plants_fail(self):
        """New copper near the moved R132.1 (RAW_ACT): a GND or ARM1_SENSE track 0.5 mm south of it fails S-10 (pack
        class) and DRC, which names R132.1; a BAT_DAMP track 0.5 mm north of Q121.2 (ACT_FET_S) fails S-10."""
        for net in ('GND', 'ARM1_SENSE'):
            with self.subTest(net=net):
                self.setUp()
                self.fails_s10(self.plant_raw_act(net), (fire.PACK_MIN, 'pack'),
                               drc="'S-10 RAW_ACT (pack energy) to every net'")
        self.setUp()
        self.fails_s10(self.plant_bat_damp(), (fire.PACK_MIN, 'pack'))

    def test_round6_v1_pack_netlist_guard(self):
        """pack_nets() is default-deny: a 0-ohm part off a pack net makes a new pack net, an unclassified IC or a
        lower R134 makes S-10 fail; a pack not-a-path class onto an MCU pin or a low-resistance net fails the guard."""
        import xml.etree.ElementTree as ET

        def add(root, ref, value, nodes):
            comp = ET.SubElement(root.find('components'), 'comp', ref=ref)
            ET.SubElement(comp, 'value').text = value
            for pin, net, fn in nodes:
                n = next((x for x in root.findall('./nets/net') if x.get('name') == net), None)
                if n is None:
                    n = ET.SubElement(root.find('nets'), 'net', name=net, code='9999')
                ET.SubElement(n, 'node', ref=ref, pin=pin, pinfunction=fn, pintype='passive')
        cases = (
            ('0R off RAW_ACT', lambda r: add(r, 'R998', '0R', (('1', 'RAW_ACT', ''), ('2', 'NEW_NET', '')))),
            ('fuse off BAT_IN', lambda r: add(r, 'F1', '2A', (('1', 'BAT_IN', ''), ('2', 'NEW_NET', '')))),
            ('IC on BAT_IN', lambda r: add(r, 'U99', 'LDO', (('1', 'BAT_IN', 'VIN'), ('2', 'NEW_NET', 'VOUT'),
                                                             ('3', 'GND', 'GND')))),
            ('R134 1 ohm', lambda r: self.set_value(r, 'R134', '1R')),
        )
        for name, mutate in cases:
            with self.subTest(case=name):
                rep = self.s10_netlist(self.netlist(mutate))
                self.assertFalse(rep['ok'])
                want = 'is not a classified part' if name.startswith('IC') else 'carries the pack\'s current'
                self.assertTrue([i for i in rep['issues'] if want in i], rep['issues'])
        net = BOARD12.with_name('schematic.net.xml')
        for f, want in (('ARM1_SENSE', 'through only 0 ohm'), ('LED_RED_A', 'through only 220 ohm'),
                        ('ACT_DRV', 'through only 0 ohm')):
            with self.subTest(cls=f):
                self.assertTrue([i for i in fire.pack_guard(net, not_a_path={('RAW_ACT', f): 'planted'})[0]
                                 if f'RAW_ACT / {f} is classed' in i and want in i])

    # ---- round 6 verifier V-1 follow-up: PACK_FLT (R95 and D95 between U9's FLT and PC13) -------------------------
    def test_round6_pack_flt_series_resistor_and_clamp(self):
        """The committed netlist: U9.4 (FLT, beside U9.5 BAT_IN) is U9_FLT with R89 10k to 3V3; PC13 (U1.A2, BAT_FAULT_N)
        reads it through R95 10k and D95 (A1 BAT_FAULT_N, K 3V3) clamps PC13; flt_guard() passes and S-10 records it.
        The PACK_FLT pairs stay measured exceptions on U9_FLT's items (U9's own pin is over-driven)."""
        net = BOARD12.with_name('schematic.net.xml')
        parts, pins = r12_sch_check.read_netlist(net)
        self.assertEqual((pins['U9', '4'], pins['R89', '2'], pins['R89', '1'], pins['R95', '1'], pins['R95', '2'],
                          pins['D95', '1'], pins['D95', '3'], pins['U1', 'A2']),
                         ('U9_FLT', 'U9_FLT', '3V3', 'U9_FLT', 'BAT_FAULT_N', 'BAT_FAULT_N', '3V3', 'BAT_FAULT_N'))
        self.assertEqual((parts['R95']['value'], parts['D95']['value']), ('10k', 'BAT54C'))
        issues, ev = fire.flt_guard(net)
        self.assertEqual(issues, [])
        self.assertEqual(ev['series_ohm'], {'3V3': 10000.0, 'BAT_FAULT_N': 10000.0})
        self.assertEqual(ev['clamp BAT_FAULT_N'], ['D95'])
        rep = self.s10()
        self.assertTrue(rep['ok'], rep['issues'])
        self.assertEqual(rep['evidence']['s10']['pack_flt']['net'], 'U9_FLT')
        flt_items = {b for a, b, *_ in fire.EXCEPTIONS['PACK_FLT']}
        self.assertEqual({fire.EXCEPTION_NETS[b] for b in flt_items}, {'U9_FLT'})
        self.assertNotIn('BAT_FAULT_N', {fire.EXCEPTION_NETS[b] for k, v in fire.EXCEPTIONS.items()
                                         if k.startswith('PACK_') for _, b, *_ in v})
        for w in ('R95', 'D95', 'no positive injection', 'Owner acceptance', '6.5 V'):
            self.assertIn(w, fire.WHY['PACK_FLT'])
        self.assertIn('0.158 V', fire.WHY['BAT_FAULT_N'])

    def test_round6_pack_flt_planted_netlists_fail(self):
        """Planted: R95 removed (PC13 on U9_FLT), R95 0 ohm, R95 1k, D95 removed, D95 reversed, D95's cathode on a
        non-rail net: each fails flt_guard() and S-10."""
        def drop(root, ref):
            root.find('components').remove(next(c for c in root.findall('./components/comp') if c.get('ref') == ref))
            for n in root.findall('./nets/net'):
                for x in list(n.findall('node')):
                    if x.get('ref') == ref:
                        n.remove(x)

        def swap_d95(root):
            self.move_node(root, 'D95', '1', '3V3')
            self.move_node(root, 'D95', '3', 'BAT_FAULT_N')
        cases = (
            ('R95 removed', lambda r: (drop(r, 'R95'), self.move_node(r, 'U1', 'A2', 'U9_FLT')),
             'is on U9_FLT, an MCU-pin net'),
            ('R95 0 ohm', lambda r: self.set_value(r, 'R95', '0R'), 'reaches BAT_FAULT_N through only 0 ohm'),
            ('R95 1k', lambda r: self.set_value(r, 'R95', '1k'), 'reaches BAT_FAULT_N through only 1000 ohm'),
            ('R89 1k', lambda r: self.set_value(r, 'R89', '1k'), 'reaches 3V3 through only 1000 ohm'),
            ('D95 removed', lambda r: drop(r, 'D95'), 'has no diode clamp to 3V3'),
            ('D95 reversed', swap_d95, 'has no diode clamp to 3V3'),
            ('D95 cathode off the rail', lambda r: self.move_node(r, 'D95', '3', 'GND'), 'has no diode clamp to 3V3'),
        )
        for name, mutate, want in cases:
            with self.subTest(case=name):
                path = self.netlist(mutate)
                self.assertTrue([i for i in fire.flt_guard(path)[0] if want in i], fire.flt_guard(path)[0])
                rep = self.s10_netlist(path)
                self.assertFalse(rep['ok'])
                self.assertTrue([i for i in rep['issues'] if 'PACK_FLT' in i or want in i], rep['issues'])

    def test_round6_v3_ign_raw_act_reason(self):
        why = fire.NOT_A_PATH[('RAW_ACT', fire.IGN)]          # R12F12-TRI-21: the one remaining direction carries it
        self.assertNotIn('ILIM', why)
        self.assertIn('U9 is not in this path', why)
        self.assertIn('Inference', why)

    # ---- round 6 verifier V-4: the fire-state guard is default-deny on part type ---------------------------------
    def test_round6_v4_part_classes_default_deny(self):
        """The verifier's planted netlists, each recreating R12F6-TRI-01's unlimited path with a part prefix the old
        walk ignored, now fail the fire-state guard: a fuse, LED or solder jumper in place of / across R136, a 0-ohm
        resistor array across R136, an LED from 3V3 to PYRO1_COLD, an oscillator output on PYRO1_COLD_PU and an IC
        output on PYRO1_CONT_MID."""
        import xml.etree.ElementTree as ET
        self.assertEqual(fire.part_kind('C9', '1uF', {'1': 'A', '2': 'B'}), 'cap')
        self.assertEqual(fire.part_kind('TP9', '', {'1': 'A'}), 'inert')
        self.assertEqual(fire.part_kind('R9', '5.1k', {'1': 'A', '2': 'B'}), 'res')
        for ref, value in (('R9', 'bad'), ('F9', '1A'), ('JP9', ''), ('LED9', 'RED'), ('X9', '?'), ('FB9', '')):
            self.assertEqual(fire.part_kind(ref, value, {'1': 'A', '2': 'B'}), 'pass', ref)
        self.assertEqual(fire.part_kind('D9', 'BAT54C', {'1': 'A', '2': 'B', '3': 'C'}), 'pass')
        for ref in ('RN9', 'X9', 'IC9', 'U9', 'Q9'):
            self.assertEqual(fire.part_kind(ref, '0R', {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}), 'source', ref)
        self.assertEqual(fire.part_kind('X9', 'OSC', {'1': 'A'}), 'source')

        def comp(root, ref, value, nodes, drop=()):
            for c in list(root.find('components')):
                if c.get('ref') in drop:
                    root.find('components').remove(c)
            for n in root.findall('./nets/net'):
                for x in list(n):
                    if x.get('ref') in drop:
                        n.remove(x)
            c = ET.SubElement(root.find('components'), 'comp', ref=ref)
            ET.SubElement(c, 'value').text = value
            for pin, net, kind in nodes:
                n = next(x for x in root.findall('./nets/net') if x.get('name') == net)
                ET.SubElement(n, 'node', ref=ref, pin=pin, pintype=kind)
        P, C, CM = 'PYRO1_COLD_PU', 'PYRO1_COLD', 'PYRO1_CONT_MID'
        cases = (
            ('F1 for R136', lambda r: comp(r, 'F1', '0.5A', (('1', '3V3', 'passive'), ('2', P, 'passive')), ('R136',)), C),
            ('LED9 for R136', lambda r: comp(r, 'LED9', 'RED', (('2', '3V3', 'passive'), ('1', P, 'passive')), ('R136',)), C),
            ('JP1 across R136', lambda r: comp(r, 'JP1', 'SolderJumper', (('1', '3V3', 'passive'), ('2', P, 'passive'))), C),
            ('RN1 0R array', lambda r: comp(r, 'RN1', '0R', (('1', '3V3', 'passive'), ('8', P, 'passive'),
                                                             ('2', 'GND', 'passive'), ('7', 'GND', 'passive'))), C),
            ('LED9 3V3 to COLD', lambda r: comp(r, 'LED9', 'RED', (('2', '3V3', 'passive'), ('1', C, 'passive'))), C),
            ('X1 on COLD_PU', lambda r: comp(r, 'X1', 'OSC', (('3', P, 'output'),)), C),
            ('IC1 on CONT_MID', lambda r: comp(r, 'IC1', 'buffer', (('4', CM, 'output'),)), CM),
        )
        for name, mutate, cls in cases:
            with self.subTest(case=name):
                issues, _ = fire.fire_state_guard(self.netlist(mutate))
                self.assertTrue([i for i in issues if f'PYRO1_OUT / {cls} is classed "not a path"' in i], issues)

    # ---- R12F7-TRI-01: the FMEA I-5 rails above 3V3 against 3V3 / 3V3A --------------------------------------------
    def test_r12f7_tri01_i5_rails_derived_and_held(self):
        """i5_rails() derives the pack-voltage rails (U9's OUT, VLOGIC behind D5, the converters' SW / bootstrap nodes)
        and the port-voltage rails (CAM_5V, PORT_4V8 above 3V3's window, USB VBUS) from the netlist; each is held from
        3V3 / 3V3A only (PACK_MIN / I5_PORT_MIN), and the DRU carries one rule per rail; the committed board clears
        every one with no exception."""
        net = BOARD12.with_name('schematic.net.xml')
        derived, issues = fire.i5_rails(net)
        self.assertEqual(issues, [])
        self.assertEqual((derived['pack'], derived['port']), (sorted(fire.I5_PACK), sorted(fire.I5_PORT)))
        self.assertEqual(fire.i5_guard(net)[0], [])
        self.assertEqual((fire.PACK_MIN, fire.I5_PORT_MIN), (1.040, 0.300))
        for rail in fire.I5_PACK:
            for v in fire.LOGIC:
                self.assertEqual(fire.pair_limit(rail, None, v, None, True)[:3], (fire.PACK_MIN, 'i5-pack', rail))
                self.assertEqual(fire.pair_limit(v, None, rail, None, False)[:3], (fire.PACK_MIN, 'i5-pack', rail))
            self.assertEqual(fire.pair_limit(rail, None, 'GND', None, False)[0], None)
        for rail in fire.I5_PORT:
            self.assertEqual(fire.pair_limit(rail, None, '3V3', None, False)[:2], (fire.I5_PORT_MIN, 'i5-port'))
            # R12F8-TRI-01: every victim but the FT-only nets; a non-victim stays unprotected
            self.assertEqual(fire.pair_limit(rail, None, 'SERVO1_MCU', None, False)[:2], (fire.I5_PORT_MIN, 'i5-port'))
            self.assertEqual(fire.pair_limit(rail, None, 'VBUS_SENSE', None, False)[0], None)
            # R12F10-TRI-06: CAM_MCU_RX's loader reason covers CAM_5V only
            self.assertEqual(fire.pair_limit(rail, None, 'CAM_MCU_RX', None, False)[0],
                             None if rail == 'CAM_5V' else fire.I5_PORT_MIN)
            # R12F9-TRI-01: CAM_EN is an IC-pin victim, rated (I5_RATED) only above CAM_BST / CAM_SW / RAW_PROTECTED
            self.assertEqual(fire.pair_limit(rail, None, 'CAM_EN', None, False)[:2], (fire.I5_PORT_MIN, 'i5-port'))
        # the stricter classes still win: PYRO1_OUT against VLOGIC, BAT_IN against RAW_PROTECTED
        self.assertEqual(fire.pair_limit('VLOGIC', None, fire.OUT, None, False)[1:], ('out', fire.OUT))
        self.assertEqual(fire.pair_limit('RAW_PROTECTED', None, 'BAT_IN', None, False)[1:], ('pack', 'BAT_IN'))
        for rail in fire.I5_PACK + fire.I5_PORT:
            rule = next(r for r in fire.dru_rules() if r[0] == f'S-10 {rail} (I-5 rail) to every victim')
            lim = fire.PACK_MIN if rail in fire.I5_PACK else fire.I5_PORT_MIN
            self.assertEqual(rule[1], f'clearance (min {lim:.2f}mm)')
            victims = fire.i5_rule_victims(rail)
            self.assertEqual(victims[:2], ('3V3', '3V3A'))
            self.assertTrue(rule[2].startswith(f"A.NetName == '{rail}' && (B.NetName == '3V3' || B.NetName == '3V3A' || "))
            # R12F8-TRI-05 / R12F9-TRI-03: NOT_PROBE on the port rules only
            self.assertEqual(rule[2].endswith(fire.NOT_PROBE), rail in fire.I5_PORT, rail)
            for v in ('SERVO1_MCU', 'SERVO1_OUT', 'CAM_5V_SENSE', 'QSPI_NCS', 'CAM_PWR_EN', 'U9_FLT', 'BAT_ENABLE',
                      'PORT_FB', 'CAM_FB', 'FB_3V3'):
                self.assertIn(f"B.NetName == '{v}'", rule[2])
            self.assertEqual("B.NetName == 'CAM_EN'" in rule[2], rail not in fire.I5_RATED['CAM_EN'][3], rail)
            for g in fire.GATES:                                                    # their own, stricter, rule
                self.assertNotIn(f"B.NetName == '{g}'", rule[2])
            for ft in fire.I5_PORT_FT:                              # R12F10-TRI-06: exempt only from its loader rails
                self.assertEqual(f"B.NetName == '{ft}'" in rule[2], rail not in fire.ft_rails(ft), (rail, ft))
        self.assertFalse([1 for k, v in fire.EXCEPTIONS.items() for a, b, *_ in v
                          if fire.EXCEPTION_NETS[a] in fire.I5_PACK + fire.I5_PORT and fire.EXCEPTION_NETS[b] in fire.LOGIC])
        ev = self.s10()['evidence']['s10']['i5']
        self.assertEqual(ev['pack'], sorted(fire.I5_PACK))
        least = {k: float(v.split(' mm')[0]) for k, v in ev['least'].items()}
        self.assertIn('RAW_PROTECTED / 3V3', least)
        excepted = {f'{fire.EXCEPTION_NETS[a]} / {fire.EXCEPTION_NETS[b]}' for v in fire.EXCEPTIONS.values()
                    for a, b, *_ in v}
        for k, g in least.items():
            lim = fire.PACK_MIN if k.split(' / ')[0] in fire.I5_PACK else fire.I5_PORT_MIN
            if k in excepted:                         # R12F8-TRI-01: PA6's divider; R12F9-TRI-01: U9's / U400's own pins
                self.assertIn(k, ('VLOGIC / VLOGIC_SENSE', 'RAW_PROTECTED / BAT_ENABLE', 'RAW_PROTECTED / BAT_OVLO',
                                  'RAW_PROTECTED / U9_FLT', 'RAW_PROTECTED / BAT_DVDT', 'RAW_PROTECTED / BAT_ILIM',
                                  'RAW_PROTECTED / PORT_FB', 'RAW_PROTECTED / unconnected-(U9-ITIMER-Pad10)',
                                  'RAW_PROTECTED / unconnected-(U9-AUXOFF-Pad3)',          # R12F10-TRI-05
                                  'CAM_SW / CAM_EN',                                       # R12F12-TRI-20
                                  'PORT_BST / PORT_FB_TOP', 'RAW_PROTECTED / PORT_FB_TOP'))   # R12F12-TRI-21
                continue
            self.assertGreaterEqual(g, lim - 5e-5, k)

    def test_r12f7_tri01_i5_plants_fail(self):
        """R12F12-TRI-25 gate-2: a 3V3 track 0.50 mm from RAW_PROTECTED's forward feed (found by net, layer and width at
        the trunk's forward via) fails S-10 (i5-pack) and DRC on that feed; one 0.20 mm from R104.1 (CAM_5V) fails S-10
        (i5-port) and DRC on R104.1; a 3V3 In2 track 0.20 mm from a PORT_4V8 fill (off the board) fails S-10."""
        self.fails_s10(self.plant_i5_feed(), (fire.PACK_MIN, 'i5-pack'),
                       drc="'S-10 RAW_PROTECTED (I-5 rail) to every victim'")
        self.setUp()
        self.fails_s10(self.plant_i5_cam5v(), (fire.I5_PORT_MIN, 'i5-port'),
                       drc="'S-10 CAM_5V (I-5 rail) to every victim'")
        self.setUp()
        self.zone('PORT_4V8', [(30, 98.85), (31, 98.85), (31, 99.85), (30, 99.85)], pcbnew.In2_Cu)
        self.track('3V3', (31.25, 98.85), (31.25, 99.85), pcbnew.In2_Cu, width=0.1)
        self.planted(('PORT_4V8 fill PORT_4V8 to 3V3 track (31.25, 98.85)-(31.25, 99.85) on In2.Cu: 0.20', '(i5-port)'))

    def test_r12f7_tri01_i5_netlist_guard_default_deny(self):
        """A rail a diode or a converter carries above 3V3, or a new supply net in no class, fails the I-5 guard."""
        import xml.etree.ElementTree as ET

        def add(root, ref, value, nodes):
            comp = ET.SubElement(root.find('components'), 'comp', ref=ref)
            ET.SubElement(comp, 'value').text = value
            for pin, net, fn, kind in nodes:
                n = next((x for x in root.findall('./nets/net') if x.get('name') == net), None)
                if n is None:
                    n = ET.SubElement(root.find('nets'), 'net', name=net, code='9999')
                ET.SubElement(n, 'node', ref=ref, pin=pin, pinfunction=fn, pintype=kind)
        cases = (
            ('diode off RAW_PROTECTED', lambda r: add(r, 'D98', 'SS34', (('1', 'NEW_RAIL', 'K', 'passive'),
                                                                         ('2', 'RAW_PROTECTED', 'A', 'passive'))),
             'NEW_RAIL can sit above 3V3 (pack voltage'),
            ('converter on VLOGIC', lambda r: add(r, 'U98', 'BUCK', (('1', 'VLOGIC', 'VIN', 'power_in'),
                                                                    ('2', 'NEW_SW', 'SW', 'output'),
                                                                    ('3', 'GND', 'GND', 'power_in'))),
             'NEW_SW can sit above 3V3 (pack voltage'),
            ('unclassed supply', lambda r: add(r, 'U97', 'LDO', (('1', 'NEW_LDO_OUT', 'VOUT', 'power_out'),
                                                                ('2', 'GND', 'GND', 'power_in'))),
             'supply net NEW_LDO_OUT is in no I-5 class'),
        )
        for name, mutate, want in cases:
            with self.subTest(case=name):
                issues = fire.i5_guard(self.netlist(mutate))[0]
                self.assertTrue([i for i in issues if want in i], issues)
        # a rail in the windows above 3V3 is port voltage; dropping CAM_5V's window drops it from the derivation
        w = json.loads(fire.WINDOWS.read_text())
        w['rails'] = {k: v for k, v in w['rails'].items() if not k.startswith('CAM_5V')}
        self.assertTrue([i for i in fire.i5_guard(BOARD12.with_name('schematic.net.xml'), w)[0]
                         if 'CAM_5V is held as an I-5 port-voltage rail' in i])

    # ---- R12F8-TRI-01 / -05: the I-5 victims, the FT-only exemptions, the camera EN, NOT_PROBE ---------------------
    def test_r12f8_tri01_victims_derived_and_held(self):
        """i5_victims() derives the victims from the netlist (D121's IO pins put SERVO1-4_MCU on 3V3 at 0 ohm, the
        1 kohm series resistors their _OUT nets, CAM_5V_SENSE is PC2_C) and i5_guard() holds them equal to I5_VICTIMS;
        R12F9-TRI-01: 80 with the nine nets on a non-MCU IC pin (CAM_EN on U403.5 is one, though it reaches PC12 only
        through R436 5.1 kohm); the FT-only exemptions hold."""
        net = BOARD12.with_name('schematic.net.xml')
        victims, _ = fire.i5_victims(net)
        self.assertEqual(sorted(victims), sorted(fire.I5_VICTIMS))
        self.assertEqual(len(victims), 80)
        self.assertEqual(victims['SERVO1_OUT'], (1000.0, 'SERVO1_MCU'))
        self.assertEqual(victims['BUZZ_OUT'], (0.0, '3V3'))
        self.assertEqual(victims['CAM_EN'], (0.0, 'CAM_EN'))
        self.assertEqual(fire.i5_ft_guard(net), [])
        self.assertEqual(fire.i5_guard(net)[0], [])
        for rail in fire.I5_PACK:
            self.assertEqual(fire.pair_limit(rail, None, 'SERVO2_MCU', None, True)[:2], (fire.PACK_MIN, 'i5-pack'))
            self.assertEqual(fire.pair_limit(rail, None, 'CAM_EN', None, False)[:2],
                             (None, 'i5-rated') if rail in fire.I5_RATED['CAM_EN'][3] else (fire.PACK_MIN, 'i5-pack'))

    def test_r12f8_tri01_victim_and_ft_guards_default_deny(self):
        """A new net reaching an MCU pin through 1 kohm, a stale victim, and an FT exemption whose net reaches a TT pin
        or 3V3 each fail the I-5 guard."""
        import xml.etree.ElementTree as ET

        def add(root, ref, value, nodes):
            comp = ET.SubElement(root.find('components'), 'comp', ref=ref)
            ET.SubElement(comp, 'value').text = value
            for pin, net in nodes:
                n = next((x for x in root.findall('./nets/net') if x.get('name') == net), None)
                if n is None:
                    n = ET.SubElement(root.find('nets'), 'net', name=net, code='9999')
                ET.SubElement(n, 'node', ref=ref, pin=pin, pinfunction='', pintype='passive')
        cases = (
            ('new 1k tap off PC12', lambda r: add(r, 'R998', '1k', (('1', 'CAM_PWR_EN'), ('2', 'NEW_TAP'))),
             'NEW_TAP reaches CAM_PWR_EN through 1000 ohm'),
            ('R436 shorted', lambda r: self.set_value(r, 'R436', '0R'), 'CAM_EN reaches CAM_PWR_EN through 0 ohm'),
            ('servo series 1k gone', lambda r: self.set_value(r, 'R150', '10k'),
             'SERVO1_OUT is held as an I-5 victim but the netlist no longer derives it'),
            ('FT net onto a TT pin', lambda r: self.move_node(r, 'U1', 'E2', 'CAM_MCU_RX'),
             'CAM_MCU_RX (FT-only, I5_PORT_FT) reaches U1.E2'),
            ('FT net clamped to 3V3', lambda r: add(r, 'D998', 'BAT54', (('1', 'VBUS_SENSE'), ('2', '3V3'))),
             'VBUS_SENSE (FT-only, I5_PORT_FT) reaches 3V3'),
        )
        for name, mutate, want in cases:
            with self.subTest(case=name):
                issues = fire.i5_guard(self.netlist(mutate))[0]
                self.assertTrue([i for i in issues if want in i], issues)

    def test_r12f8_tri01_victim_plants_fail(self):
        """A RAW_PROTECTED In2 plant 0.155 mm from the SERVO1_MCU via that serves R150 (the round 8 servo-cell pair; the
        3V3 plane cut back round it) and a PORT_4V8 track 0.13 mm from U3.1 (QSPI_NCS, W25Q128 /CS) each fail S-10 and
        DRC on that item. R12F12-TRI-25 gate-4: a CAM_5V In2 plant 0.175 mm from the CAM_MCU_RX via at U1.B8 is under
        I5_PORT_MIN, but CAM_MCU_RX is FT-only, so S-10 does not hold the pair ('unprotected') and does not fail it; the
        plant has no other neighbour under a limit, so the absence is the exemption's."""
        self.fails_s10(self.plant_servo(), (fire.PACK_MIN, 'i5-pack'),
                       drc="'S-10 RAW_PROTECTED (I-5 rail) to every victim'")
        self.setUp()
        self.fails_s10(self.plant_u3(), (fire.I5_PORT_MIN, 'i5-port'), drc="'S-10 PORT_4V8 (I-5 rail) to every victim'")
        self.setUp()
        plant, via, gap = self.plant_cam_rx()
        self.assertLess(gap, fire.I5_PORT_MIN)
        self.assertEqual(fire.pair_limit('CAM_5V', None, 'CAM_MCU_RX', None, False)[1], 'unprotected')
        rep = self.s10()
        self.assertFalse([i for i in rep['issues'] if 'CAM_MCU_RX' in i and 'CAM_5V' in i], rep['issues'])
        self.assertTrue(rep['ok'], rep['issues'])

    def test_r12f8_tri05_i5_rules_leave_the_tag_connect_rule(self):
        """R12F8-TRI-05: the I-5 port DRU rules carry NOT_PROBE, so the Tag-Connect rule (0.508 mm) keeps J2: a VBUS track
        0.45 mm forward of J2.1 (3V3) fails DRC on 'Tag-Connect contact to foreign copper' (it passed at 0.30 mm before).
        R12F9-TRI-03: the pack rules do not carry it (test_r12f9_tri03_pack_rules_hold_probes)."""
        for r in fire.dru_rules():
            if '(I-5 rail)' in r[0]:
                self.assertEqual(fire.NOT_PROBE in r[2], r[0].split()[1] in fire.I5_PORT, r[0])
        plant, j2, gap = self.plant_tag()
        self.assert_drc(self.isolate_for_drc(plant, j2), 'Tag-Connect contact to foreign copper', plant, j2, gap)

    # ---- R12F12-TRI-25: every plant of this class, found by identity and asserted a single fault -----------------
    # Each plant_* builds its plant on self.board beside an item found by identity, asserts it a single fault
    # (assert_isolated) and returns (plant, target, gap); test_r12f12_tri25_every_plant_is_a_single_fault runs them all.
    def gate_run(self):
        """PYRO1_GATE's run from TP122.1 to Q124's gate node: its last segment, the one that ends on R126.2."""
        run = self.chain('TP122', '1')
        self.assertTrue(self.pad('R126', '2').GetEffectiveShape(pcbnew.F_Cu).Collide(run[-1].GetEnd(), 0)
                        or self.pad('R126', '2').GetEffectiveShape(pcbnew.F_Cu).Collide(run[-1].GetStart(), 0))
        return run[-1]

    def pe4_lane(self):
        """PE4's lane: the second segment of PYRO1_GATE_N's chain out of U1.C3 (west of C3's dog-bone, along row C)."""
        return self.chain('U1', 'C3')[1]

    def raw_feed(self):
        """RAW_PROTECTED's feed off the trunk: the F.Cu 0.6 mm track that ends on the trunk's forward via (the
        RAW_PROTECTED via column nearest the east edge, largest y)."""
        vias = self.vias('RAW_PROTECTED')
        east = max(v.GetPosition().x for v in vias)
        via = max((v for v in vias if v.GetPosition().x == east), key=lambda v: v.GetPosition().y)
        feed = [t for t in self.board.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'RAW_PROTECTED'
                and t.GetLayer() == pcbnew.F_Cu and t.GetWidth() == nm(0.6) and via.GetPosition() in (t.GetStart(), t.GetEnd())]
        self.assertEqual(len(feed), 1, [self.label(t, pcbnew.F_Cu) for t in feed])
        return feed[0]

    def nc_ball(self):
        """R12F12-TRI-25 gate-1: the last unconnected U1 ball by (y, x) (K7 now), not a ball past a literal y."""
        return max((p for p in self.board.FindFootprintByReference('U1').Pads() if p.GetNetname().startswith('unconnected-')),
                   key=lambda p: (p.GetPosition().y, p.GetPosition().x))

    def made(self, plant, target, gap, also_nets=(), limit=None):
        """(plant, target, the measured gap) after assert_isolated."""
        return plant, target, self.assert_isolated(plant, target, gap, also_nets, limit)['gap']

    def plant_out(self, net, gap=0.2):
        """0.2 mm wide, 0.5 mm long, `gap` east of J121.1 (PYRO1_OUT; its own track leaves south-west, 0.55 mm farther)."""
        j = self.pad('J121', '1')
        return self.made(self.plant_beside(j, 'E', gap, net, width=0.2, length=0.5), j, gap)

    def plant_out_in2(self):
        """PORT_4V8 on In2 0.5 mm east of J121.1's barrel (the 3V3 plane's edge is 0.32 mm away: i5-port, 0.3 mm)."""
        j = self.pad('J121', '1')
        return self.made(self.plant_beside(j, 'E', 0.5, 'PORT_4V8', pcbnew.In2_Cu, width=0.2, length=0.5), j, 0.5)

    def plant_out_gnd(self):
        j = self.pad('J121', '1')
        return self.made(self.plant_beside(j, 'W', 0.1, 'GND', width=0.2, length=0.35), j, 0.1)

    def plant_out_gnd_fill(self):
        j = self.pad('J121', '1')
        return self.made(self.fill_beside(j, 'E', 0.3, 'GND', pcbnew.B_Cu, 0.85, 0.5), j, 0.3)

    def plant_ign_gnd(self):
        j = self.pad('J121', '2')
        return self.made(self.plant_beside(j, 'S', 0.2, 'GND', width=0.2, length=0.4), j, 0.2)

    def plant_ign_gnd_fill(self):
        j = self.pad('J121', '2')
        return self.made(self.fill_beside(j, 'S', 0.3, 'GND', pcbnew.F_Cu, 0.4, 0.8), j, 0.3)

    def plant_ign_raw_act(self):
        j = self.pad('J121', '2')
        return self.made(self.plant_beside(j, 'S', 0.15, 'RAW_ACT'), j, 0.15)

    def plant_gate(self, net, gap):
        """0.1 mm wide, 0.8 mm long, `gap` north of the gate run, centred on it. PYRO1_GATE_N's run (the other gate
        net, held by the same rule) is parallel 0.5 mm south of it: it is 0.65 mm or more from the plant."""
        run = self.gate_run()
        return self.made(self.plant_beside(run, 'N', gap, net, length=0.8), run, gap, also_nets=('PYRO1_GATE_N',))

    def plant_e(self):
        """3V3 0.15 mm south of PE4's lane, midway between U1.C1 (HSE_IN) and U1.C2 (GND), 0.13 mm from each."""
        lane = self.pe4_lane()
        c1, c2 = self.pad('U1', 'C1').GetPosition(), self.pad('U1', 'C2').GetPosition()
        along = (c1.x + c2.x) / 2e6 - (lane.GetStart().x + lane.GetEnd().x) / 2e6
        return self.made(self.plant_beside(lane, 'S', 0.15, '3V3', length=0.1, along=along), lane, 0.15)

    def plant_a1(self, net, gap):
        """0.1 mm wide, `gap` north of U1.A1 (PC14, NC), the BGA's corner: PE4's lane west of the field (x 18.7),
        BAT_FAULT_N's A2 and its run, and 3V3's B2 dog-bone are within PYRO1_OUT's 1.04 mm of any spot that near A1, all
        farther than A1; PYRO1_IGN's 0.25 mm reaches only A1 and PE4's lane holds its own 1.0585 mm."""
        a1 = self.pad('U1', 'A1')
        also = ('PYRO1_GATE_N', 'BAT_FAULT_N', '3V3') if net == fire.OUT else ('PYRO1_GATE_N',)
        return self.made(self.plant_beside(a1, 'N', gap, net), a1, gap, also_nets=also)

    def plant_raw_act(self, net):
        """0.3 mm long, 0.5 mm south of R132.1 (RAW_ACT; its own run west and R134.2 are farther)."""
        r = self.pad('R132', '1')
        return self.made(self.plant_beside(r, 'S', 0.5, net, length=0.3), r, 0.5)

    def plant_bat_damp(self):
        """BAT_DAMP 0.5 mm north of Q121.2 (ACT_FET_S): Q121.3 (RAW_ACT) is 0.54 mm from a plant east of it."""
        q = self.pad('Q121', '2')
        return self.made(self.plant_beside(q, 'N', 0.5, 'BAT_DAMP', length=0.5), q, 0.5)

    def plant_i5_feed(self):
        """R12F12-TRI-25 gate-2: 3V3 0.5 mm north of RAW_PROTECTED's forward feed, toward its trunk via, inside the
        edge clearance (the aft feed has a GND pad north of it and the D-R12-174 via south)."""
        feed = self.raw_feed()
        return self.made(self.plant_beside(feed, 'N', 0.5, '3V3', length=0.4, along=0.3), feed, 0.5)

    def plant_i5_cam5v(self):
        r = self.pad('R104', '1')
        return self.made(self.plant_beside(r, 'S', 0.2, '3V3', length=0.3), r, 0.2)

    def plant_servo(self):
        """RAW_PROTECTED on In2 0.155 mm south of the SERVO1_MCU via that serves R150 (the round 8 servo-cell pair); the
        3V3 plane is cut back round it as a refill under the DRU would."""
        via = self.via_at('SERVO1_MCU', 'R150.1')
        t = self.plant_beside(via, 'S', 0.155, 'RAW_PROTECTED', pcbnew.In2_Cu, length=0.6)
        self.assertEqual(self.clear_fills(t), ['3V3_In2'])
        return self.made(t, via, 0.155)

    def plant_u3(self):
        u3 = self.pad('U3', '1')
        return self.made(self.plant_beside(u3, 'S', 0.13, 'PORT_4V8', width=0.15, length=0.4), u3, 0.13)

    def plant_cam_rx(self):
        """R12F12-TRI-25 gate-4: CAM_5V on In2 0.175 mm south of the CAM_MCU_RX via at U1.B8 (the 3V3 plane cut back)."""
        via = self.via_at('CAM_MCU_RX', 'U1.B8')
        t = self.plant_beside(via, 'S', 0.175, 'CAM_5V', pcbnew.In2_Cu, length=0.6)
        self.assertEqual(self.clear_fills(t), ['3V3_In2'])
        return self.made(t, via, 0.175)

    def plant_loader(self):
        """VBUS on B 0.2 mm east of the CAM_MCU_RX via at U1.B8 (GND_pour_B cut back)."""
        via = self.via_at('CAM_MCU_RX', 'U1.B8')
        t = self.plant_beside(via, 'E', 0.2, 'VBUS', pcbnew.B_Cu, length=0.4)
        self.assertEqual(self.clear_fills(t), ['GND_pour_B'])
        return self.made(t, via, 0.2)

    def plant_tag(self):
        """VBUS 0.45 mm south (forward) of J2.1 (3V3): inside the Tag-Connect rule's 0.508 mm, outside i5-port's 0.3."""
        j2 = self.pad('J2', '1')
        return self.made(self.plant_beside(j2, 'S', 0.45, 'VBUS', length=0.5), j2, 0.45, limit=0.508)

    def plant_probe_j2(self):
        """RAW_PROTECTED 0.70 mm south of J2.1 (east of it a 3V3 via sits 0.10 mm from such a plant)."""
        j2 = self.pad('J2', '1')
        return self.made(self.plant_beside(j2, 'S', 0.7, 'RAW_PROTECTED', length=0.4), j2, 0.7)

    def plant_tp(self, ref, net, side, gap, also_nets=()):
        """`net` `gap` mm beyond a test pad, inside the pad's own clearance override (fire.probe_clearance)."""
        tp = self.pad(ref, '1')
        lim = fire.probe_clearance(tp.GetNetname())
        return self.made(self.plant_beside(tp, side, gap, net, length=0.4), tp, gap, also_nets, limit=lim)

    def plant_ic_flt(self):
        via = self.via_at('U9_FLT', 'U9.4')
        return self.made(self.plant_beside(via, 'S', 0.13, 'RAW_PROTECTED', pcbnew.In2_Cu, length=0.6), via, 0.13)

    def plant_ic_cam_fb(self):
        r = self.pad('R434', '2')
        return self.made(self.plant_beside(r, 'E', 0.13, 'CAM_5V', length=0.4), r, 0.13)

    def plant_cam_en(self, net):
        """0.2 mm north of R431.1 (CAM_EN). CAM_BST is a pack-voltage rail, so the feedback top R433.2 and the servo
        lanes beside R431 (held from it at 1.04 mm) are within its reach, all farther than R431.1."""
        r = self.pad('R431', '1')
        also = ('CAM_FB_TOP', 'SERVO3_MCU', 'SERVO2_MCU') if net == 'CAM_BST' else ()
        return self.made(self.plant_beside(r, 'N', 0.2, net), r, 0.2, also_nets=also)

    def plant_cam_tx(self):
        """CAM_5V on B 0.2 mm north of the CAM_MCU_TX via at R101.1 (GND_pour_B cut back)."""
        via = self.via_at('CAM_MCU_TX', 'R101.1')
        t = self.plant_beside(via, 'N', 0.2, 'CAM_5V', pcbnew.B_Cu, length=0.4)
        self.assertEqual(self.clear_fills(t), ['GND_pour_B'])
        return self.made(t, via, 0.2)

    def plant_nc_ball(self):
        """RAW_PROTECTED 0.15 mm south of the last NC ball, outside the field: the other balls (0.8 mm pitch) and their
        escapes are within 1.04 mm of any plant beside a ball, all farther than the NC ball."""
        nc = self.nc_ball()
        u1 = tuple(sorted({p.GetNetname() for p in nc.GetParentFootprint().Pads()} - {nc.GetNetname()}))
        return self.made(self.plant_beside(nc, 'S', 0.15, 'RAW_PROTECTED'), nc, 0.15, also_nets=u1)

    def plant_nc_pass(self):
        """R12F12-TRI-21 (a): RAW_PROTECTED 0.5 mm south of D436.2, a BAT54C clamp's unused anode (D95.2's spots all
        have D95.1 or a 3V3 via nearer)."""
        d = self.pad('D436', '2')
        return self.made(self.plant_beside(d, 'S', 0.5, 'RAW_PROTECTED'), d, 0.5)

    def plant_fb_top(self):
        """R12F12-TRI-21 (b): RAW_PROTECTED 0.2 mm south of R433.2 (CAM_FB_TOP). U403's divider sits among the camera
        UART and servo lanes, all held from a pack rail: the nearest of them is farther than R433.2."""
        r = self.pad('R433', '2')
        return self.made(self.plant_beside(r, 'S', 0.2, 'RAW_PROTECTED'), r, 0.2,
                         also_nets=('CAM_FB', 'CAM_MCU_TX', 'CAM_MCU_RX', 'SERVO3_MCU'))

    GUARDED = (('out', dict(net='ACT_DRV')), ('out', dict(net='VCAP1', gap=0.3)), ('out', dict(net='PYRO1_COLD_PU')),
               ('out_in2', {}), ('out_gnd', {}), ('out_gnd_fill', {}), ('ign_gnd', {}), ('ign_gnd_fill', {}),
               ('ign_raw_act', {}), ('gate', dict(net='QSPI_IO2', gap=0.1)), ('gate', dict(net='ACT_EN_MCU', gap=0.2)),
               ('gate', dict(net='', gap=0.2)), ('e', {}), ('a1', dict(net=fire.OUT, gap=0.38)),
               ('a1', dict(net=fire.IGN, gap=0.2)), ('raw_act', dict(net='GND')), ('raw_act', dict(net='ARM1_SENSE')),
               ('bat_damp', {}), ('i5_feed', {}), ('i5_cam5v', {}), ('servo', {}), ('u3', {}), ('cam_rx', {}),
               ('loader', {}), ('tag', {}), ('probe_j2', {}), ('tp', dict(ref='TP83', net='3V3', side='E', gap=1.02)),
               ('tp', dict(ref='TP88', net='RAW_ACT', side='W', gap=1.02)),
               ('tp', dict(ref='TP83', net='PYRO1_GATE_N', side='E', gap=1.045, also_nets=('VBUS',))),
               ('ic_flt', {}), ('ic_cam_fb', {}), ('cam_en', dict(net='PORT_4V8')), ('cam_en', dict(net='CAM_BST')),
               ('cam_tx', {}), ('nc_ball', {}), ('nc_pass', {}), ('fb_top', {}))

    def test_r12f12_tri25_every_plant_is_a_single_fault(self):
        """The round 12 gate lens's probe as a standing guard (R12F12-TRI-25): every plant of this class, rebuilt on the
        committed board, has its target as its one neighbour under the rule's limit (assert_isolated), so copper moved
        beside a plant fails here in seconds rather than as a quietly different case. Every plant_* is listed."""
        names = {n[len('plant_'):] for n in dir(self) if n.startswith('plant_') and n != 'plant_beside'}
        self.assertEqual(names, {n for n, _ in self.GUARDED})
        for name, kw in self.GUARDED:
            with self.subTest(plant=name, **kw):
                self.setUp()
                plant, target, gap = getattr(self, 'plant_' + name)(**kw)
                self.assertIsNotNone(target)

    def test_r12f8_tri01_camera_en_series_resistor_and_clamp(self):
        """The committed netlist: U403.5 (EN, beside U403.6 CAM_BST) is CAM_EN with R431 47k to GND; PC12 (U1.C8,
        CAM_PWR_EN) reaches it through R436 5.1k and D436 (A1 CAM_PWR_EN, K 3V3) clamps PC12; en_guard() passes. Planted:
        R436 removed (PC12 on CAM_EN), R436 1k, D436 removed / reversed / cathode off the rail: each fails en_guard() and
        S-10."""
        net = BOARD12.with_name('schematic.net.xml')
        parts, pins = r12_sch_check.read_netlist(net)
        self.assertEqual((pins['U403', '5'], pins['R431', '1'], pins['R436', '2'], pins['R436', '1'], pins['D436', '1'],
                          pins['D436', '3'], pins['U1', 'C8']),
                         ('CAM_EN', 'CAM_EN', 'CAM_EN', 'CAM_PWR_EN', 'CAM_PWR_EN', '3V3', 'CAM_PWR_EN'))
        self.assertEqual((parts['R436']['value'], parts['D436']['value'], parts['R431']['value']),
                         ('5.1k', 'BAT54C', '47k 1%'))
        issues, ev = fire.en_guard(net)
        self.assertEqual(issues, [])
        self.assertEqual(ev['clamp CAM_PWR_EN'], ['D436'])

        def drop(root, ref):
            root.find('components').remove(next(c for c in root.findall('./components/comp') if c.get('ref') == ref))
            for n in root.findall('./nets/net'):
                for x in list(n.findall('node')):
                    if x.get('ref') == ref:
                        n.remove(x)

        def swap(root):
            self.move_node(root, 'D436', '1', '3V3')
            self.move_node(root, 'D436', '3', 'CAM_PWR_EN')
        cases = (
            ('R436 removed', lambda r: (drop(r, 'R436'), self.move_node(r, 'U1', 'C8', 'CAM_EN')),
             'is on CAM_EN, an MCU-pin net'),
            ('R436 1k', lambda r: self.set_value(r, 'R436', '1k'), 'reaches CAM_PWR_EN through only 1000 ohm'),
            ('D436 removed', lambda r: drop(r, 'D436'), 'has no diode clamp to 3V3'),
            ('D436 reversed', swap, 'has no diode clamp to 3V3'),
            ('D436 cathode off the rail', lambda r: self.move_node(r, 'D436', '3', 'GND'), 'has no diode clamp to 3V3'),
        )
        for name, mutate, want in cases:
            with self.subTest(case=name):
                path = self.netlist(mutate)
                self.assertTrue([i for i in fire.en_guard(path)[0] if want in i], fire.en_guard(path)[0])
                rep = self.s10_netlist(path)
                self.assertFalse(rep['ok'])

    # ---- R12F9-TRI-01 / -02 / -03: IC-pin victims, the rated guard, the FT direction, the pack rules at J2 / TPs ----
    def test_r12f9_tri01_ic_pin_victims_derived_and_default_deny(self):
        """Every net on a non-MCU IC pin is a victim (U9's EN / OVLO / FLT / dVdT / ILM, U403's FB / EN, U400's FB, U2's
        FB): i5_victims() derives them, I5_VICTIMS holds them, the DRU names them; a table that lacks one, a new net on an
        IC pin and a 1 kohm tap off it each fail the I-5 guard."""
        from unittest import mock
        import xml.etree.ElementTree as ET
        net = BOARD12.with_name('schematic.net.xml')
        victims, _ = fire.i5_victims(net)
        for n in ('BAT_DVDT', 'BAT_ENABLE', 'BAT_ILIM', 'BAT_OVLO', 'U9_FLT', 'CAM_EN', 'CAM_FB', 'PORT_FB', 'FB_3V3'):
            self.assertEqual(victims[n], (0.0, n))
            self.assertIn(n, fire.I5_VICTIMS)
            self.assertEqual(fire.pair_limit('VLOGIC', None, n, None, False)[:2], (fire.PACK_MIN, 'i5-pack'))
        with mock.patch.object(fire, 'I5_VICTIMS', tuple(v for v in fire.I5_VICTIMS if v != 'U9_FLT')):
            self.assertTrue([i for i in fire.i5_guard(net)[0] if 'U9_FLT reaches U9_FLT through 0 ohm' in i])

        def add(root):
            for ref, value, nodes in (('U98', 'IC', (('1', 'NEW_PIN'), ('2', 'GND'))),
                                      ('R997', '1k', (('1', 'NEW_PIN'), ('2', 'NEW_TAP')))):
                comp = ET.SubElement(root.find('components'), 'comp', ref=ref)
                ET.SubElement(comp, 'value').text = value
                for pin, name in nodes:
                    n = next((x for x in root.findall('./nets/net') if x.get('name') == name), None)
                    if n is None:
                        n = ET.SubElement(root.find('nets'), 'net', name=name, code='9998')
                    ET.SubElement(n, 'node', ref=ref, pin=pin, pinfunction='IO', pintype='input')
        issues = fire.i5_guard(self.netlist(add))[0]
        self.assertTrue([i for i in issues if 'NEW_PIN reaches NEW_PIN through 0 ohm' in i], issues)
        self.assertTrue([i for i in issues if 'NEW_TAP reaches NEW_PIN through 1000 ohm' in i], issues)

    def test_r12f9_tri01_ic_pin_plants_fail(self):
        """A RAW_PROTECTED In2 plant 0.13 mm from the U9_FLT via at U9.4 (the round 9 fill pair) and a CAM_5V plant
        0.13 mm from R434.2 (CAM_FB, held at the port class) each fail S-10 and DRC; a PORT_4V8 plant 0.20 mm north of
        R431.1 (CAM_EN) fails S-10, a CAM_BST one there does not (I5_RATED: EN is rated 19 V above CAM_BST): S-10
        measures that pair, as i5-rated with no limit."""
        self.fails_s10(self.plant_ic_flt(), (fire.PACK_MIN, 'i5-pack'),
                       drc="'S-10 RAW_PROTECTED (I-5 rail) to every victim'")
        self.setUp()
        self.fails_s10(self.plant_ic_cam_fb(), (fire.I5_PORT_MIN, 'i5-port'),
                       drc="'S-10 CAM_5V (I-5 rail) to every victim'")
        self.setUp()
        self.fails_s10(self.plant_cam_en('PORT_4V8'), (fire.I5_PORT_MIN, 'i5-port'))
        self.setUp()
        plant, r431, gap = self.plant_cam_en('CAM_BST')
        rows = [r for r in r12.fire_gaps(self.board) if {r['a'], r['b']} == {self.label(plant, pcbnew.F_Cu), 'R431.1'}]
        self.assertEqual([(r['gap'], r['limit'], r['cls']) for r in rows], [(gap, None, 'i5-rated')])
        self.assertFalse([i for i in self.s10()['issues'] if 'CAM_BST' in i and 'CAM_EN' in i])

    def test_r12f9_tri01_rated_guard(self):
        """I5_RATED holds on the committed netlist and windows (U403.5 is EN, rated 19 V; CAM_BST's maximum is U9's OVLO
        rising drift maximum + 6 V). A pack whose CAM_BST would pass 19 V, a rail with no maximum, a wrong pin, a rated net
        that reaches the MCU under 5 kohm and a stale entry each fail; with the table empty, U403.6 to U403.5 fails S-10."""
        import copy
        from unittest import mock
        net = BOARD12.with_name('schematic.net.xml')
        self.assertEqual(fire.i5_rated_guard(net), [])
        self.assertEqual(sorted(fire.I5_RATED), ['CAM_EN'])
        w = json.loads(fire.WINDOWS.read_text())
        top = w['u9']['drift']['ovlo_rising_V'][1]
        self.assertAlmostEqual(fire.rail_max('CAM_BST', w)[0], top + 6.0)
        self.assertAlmostEqual(fire.rail_max('RAW_PROTECTED', w)[0], top)
        self.assertEqual(fire.rail_max('CAM_5V', w)[0], w['rails'][next(k for k in w['rails'] if k.startswith('CAM_5V'))]
                         ['drift']['max_V'])
        hot = copy.deepcopy(w)
        hot['u9']['drift']['ovlo_rising_V'][1] = 13.5
        self.assertTrue([i for i in fire.i5_rated_guard(net, hot) if 'CAM_BST reaches 19.500 V' in i])
        pin, vmax, src, rails, why = fire.I5_RATED['CAM_EN']
        cases = (
            ({'CAM_EN': (pin, vmax, src, rails + ('VLOGIC',), why)}, net, 'no maximum for VLOGIC'),
            ({'CAM_EN': (('U403', '4', 'EN'), vmax, src, rails, why)}, net, 'U403.4 is not its EN pin'),
            ({'CAM_EN': (pin, vmax, src, rails, why)}, self.netlist(lambda r: self.set_value(r, 'R436', '0R')),
             'I5_RATED CAM_EN reaches CAM_PWR_EN through 0 ohm'),
            ({'NOT_A_VICTIM': (pin, vmax, src, rails, why)}, net, 'I5_RATED names NOT_A_VICTIM, which is no I-5 victim'),
        )
        for rated, path, want in cases:
            with self.subTest(want=want):
                issues = fire.i5_rated_guard(path, w, rated)
                self.assertTrue([i for i in issues if want in i], issues)
        with mock.patch.dict(fire.I5_RATED, clear=True):
            rep = self.s10()
        self.assertTrue([i for i in rep['issues'] if 'CAM_BST U403.6 to CAM_EN U403.5' in i and '(i5-pack)' in i],
                        rep['issues'])

    def test_r12f9_tri02_ft_exemption_reads_the_pin_direction(self):
        """CAM_MCU_TX (PC10, UART4_TX) is no FT exemption: put back, the direction check fails it, S-10 fails, and a
        CAM_5V plant 0.20 mm from its via at R101.1 fails S-10 and DRC as committed. The pin map (pin_table.tsv
        r12_mode / an2606_t119_loader_role) is the direction source: PD10 made an output, a ball with no input mode,
        a loader-driven ball without an I5_FT_LOADER reason and R101 below 1 kohm each fail."""
        from unittest import mock
        net = BOARD12.with_name('schematic.net.xml')
        self.assertNotIn('CAM_MCU_TX', fire.I5_PORT_FT)
        self.assertEqual(fire.pair_limit('CAM_5V', None, 'CAM_MCU_TX', None, False)[:2], (fire.I5_PORT_MIN, 'i5-port'))
        modes = fire.read_pin_modes()
        self.assertEqual((modes['B9'][0], modes['B8'][0], modes['H9'][0][:7], modes['E9'][0]),
                         ('AF8 UART4_TX', 'AF8 UART4_RX', 'GPIO in', 'GPIO in'))
        self.assertIn('[LOADER-DRIVEN]', modes['B8'][1])
        self.assertEqual(fire.i5_ft_guard(net), [])
        tx = dict(fire.I5_PORT_FT, CAM_MCU_TX='test')
        self.assertTrue([i for i in fire.i5_ft_guard(net, exempt=tx)
                         if 'CAM_MCU_TX (FT-only, I5_PORT_FT) reaches U1.B9 (PC10) through 0 ohm' in i
                         and 'output' in i])
        for ball, mode, who in (('H9', 'GPIO out', 'PORT_SENSE'), ('H9', 'as R11', 'PORT_SENSE')):
            m = dict(modes)
            m[ball] = (mode, m[ball][1])
            with self.subTest(mode=mode):
                self.assertTrue([i for i in fire.i5_ft_guard(net, modes=m) if i.startswith(f'{who} (FT-only')
                                 and f'U1.{ball}' in i and 'output' in i])
        loader = {k: v for k, v in fire.I5_FT_LOADER.items() if k != 'CAM_MCU_RX'}
        with mock.patch.object(fire, 'I5_FT_LOADER', loader):
            self.assertTrue([i for i in fire.i5_ft_guard(net) if i.startswith('CAM_MCU_RX (FT-only')
                             and 'LOADER-DRIVEN' in i])
        issues = fire.i5_ft_guard(self.netlist(lambda r: self.set_value(r, 'R101', '470')))
        self.assertTrue([i for i in issues if 'CAM_TX_WIRE (FT-only, I5_PORT_FT) reaches U1.B9 (PC10) through 470 ohm'
                         in i], issues)
        with mock.patch.object(fire, 'I5_PORT_FT', tx):
            rep = self.s10()
        self.assertTrue([i for i in rep['issues'] if 'CAM_MCU_TX' in i and 'output' in i], rep['issues'])
        self.fails_s10(self.plant_cam_tx(), (fire.I5_PORT_MIN, 'i5-port'), drc="'S-10 CAM_5V (I-5 rail) to every victim'")

    def test_r12f9_tri03_pack_rules_hold_probes(self):
        """R12F9-TRI-03: the pack-class I-5 rules carry no NOT_PROBE, so their 1.040 mm wins at J2 and the test pads: a
        RAW_PROTECTED track 0.70 mm forward of J2.1 (3V3; the Tag-Connect rule's 0.508 mm passes it) fails S-10 and DRC
        on the S-10 rule. KiCad applies a pad's own clearance in place of the DRU's rules, so a test pad on an S-10 net
        carries that net's floor as its override (r12_fire.probe_clearance): a 3V3 track 1.02 mm east of TP83 (VLOGIC;
        the old 1.0 mm override passed it) fails S-10 and DRC at its 1.06 mm, and TP83's override set back to 1.0 mm
        fails S-10."""
        for r in fire.dru_rules():
            if '(I-5 rail)' in r[0] and r[0].split()[1] in fire.I5_PACK:
                self.assertNotIn(fire.NOT_PROBE, r[2], r[0])
        self.fails_s10(self.plant_probe_j2(), (fire.PACK_MIN, 'i5-pack'),
                       drc="'S-10 RAW_PROTECTED (I-5 rail) to every victim'")
        self.setUp()
        made = self.plant_tp('TP83', '3V3', 'E', 1.02)
        self.fails_s10(made, (fire.PACK_MIN, 'i5-pack'), drc='pad clearance 1.0600 mm')
        self.setUp()
        tp = self.pad('TP83', '1')
        self.assertAlmostEqual(pcbnew.ToMM(tp.GetLocalClearance()), fire.DRU_GATE_MM)
        tp.SetLocalClearance(mm(1.0))
        self.planted(('test pad TP83.1 (VLOGIC) local clearance 1.0 mm, below its S-10 floor 1.06 mm',))

    def test_r12f10_tri02_probe_clearance_is_the_largest_pair_limit(self):
        """R12F10-TRI-02: a test pad's override replaces the DRU against every net, so it is the largest S-10 limit any
        pair of its net can take: every net but GND sits beside the gate nets (DRU_GATE_MM), GND beside a pack-energy net
        (PACK_MIN). Plants: a RAW_ACT track 1.020 mm west of TP88 (GND; the round 10 safety lens's TP74 case, passed by
        the old 1.0 mm override; TP74 sits among GND vias, so no spot keeps it a plant's one neighbour) and a
        PYRO1_GATE_N track 1.045 mm east of TP83 (VLOGIC; passed by the old 1.04 mm override; D6.2 on VBUS, the gate
        rule's too, is 0.01 mm farther) each fail S-10 and DRC at the pad's override; and every TP on the board carries
        probe_clearance() of its net."""
        for net in fire.PROTECTED + fire.LOGIC + fire.I5_VICTIMS + ('CAM_5V', 'SOME_OTHER_NET'):
            with self.subTest(net=net):
                self.assertEqual(fire.probe_clearance(net), fire.DRU_GATE_MM)
        self.assertEqual(fire.probe_clearance('GND'), fire.PACK_MIN)
        for f in self.board.GetFootprints():
            if f.GetReference().startswith('TP'):
                for p in f.Pads():
                    self.assertAlmostEqual(pcbnew.ToMM(p.GetLocalClearance()), fire.probe_clearance(p.GetNetname()))
        for ref, net, side, gap, also, cls, rule in (
                ('TP88', 'RAW_ACT', 'W', 1.02, (), (fire.PACK_MIN, 'pack'), 'pad clearance 1.0400 mm'),
                ('TP83', 'PYRO1_GATE_N', 'E', 1.045, ('VBUS',), (fire.GATE_MIN, 'gate'), 'pad clearance 1.0600 mm')):
            with self.subTest(ref=ref):
                self.setUp()
                self.fails_s10(self.plant_tp(ref, net, side, gap, also), cls, drc=rule)

    def test_r12f10_tri03_floors_are_the_measured_gaps(self):
        """R12F10-TRI-03: every exception floor is its pair's measured gap rounded down to 1 um; U9.5-C82.1 is 0.700 (it
        kept round 6's 0.650 after C82 moved), and a floor put back 0.05 mm below its gap fails S-10."""
        from unittest import mock
        self.assertIn(('U9.5', 'C82.1', 'F.Cu', 0.700), fire.EXCEPTIONS['PACK_OUT'])
        rep = self.s10()
        self.assertTrue(rep['ok'], rep['issues'])
        loose = tuple((a, b, l, 0.650 if (a, b) == ('U9.5', 'C82.1') else f) for a, b, l, f in fire.EXCEPTIONS['PACK_OUT'])
        with mock.patch.dict(fire.EXCEPTIONS, PACK_OUT=loose):
            rep = self.s10()
        self.assertTrue([i for i in rep['issues'] if 'exception U9.5 to C82.1 on F.Cu (PACK_OUT): floor 0.650 mm' in i
                         and 'more than 1 um below its measured gap 0.7000 mm' in i], rep['issues'])

    def test_r12f10_tri05_unconnected_ic_pins_are_i5_victims(self):
        """R12F10-TRI-05: an unconnected IC pin is an I-5 victim (U9's AUXOFF / ITIMER beside its OUT are measured
        exceptions under I5_U9_NC; a connector's NC contact is not an IC pin); without the exceptions S-10 fails them,
        the DRU's I-5 rules name the wildcard, and a RAW_PROTECTED plant 0.15 mm outside the last unconnected U1 ball by
        (y, x) (R12F12-TRI-25 gate-1) fails S-10 and DRC on that ball."""
        from unittest import mock
        self.assertEqual(fire.pair_limit('RAW_PROTECTED', 'U9', 'unconnected-(U9-ITIMER-Pad10)', 'U9', False)[:2],
                         (fire.PACK_MIN, 'i5-pack'))
        self.assertEqual(fire.pair_limit('VBUS', None, 'unconnected-(U1-PA0-PadA1)', 'U1', False)[:2],
                         (fire.I5_PORT_MIN, 'i5-port'))
        self.assertEqual(fire.pair_limit('RAW_PROTECTED', None, 'unconnected-(J410-NC-Pad5)', 'J410', False)[1],
                         'unprotected')
        for r in fire.dru_rules():
            if '(I-5 rail)' in r[0]:
                self.assertIn(f"B.NetName == '{fire.I5_NC_DRU}'", r[2], r[0])
        with mock.patch.dict(fire.EXCEPTIONS, I5_U9_NC=()):
            rep = self.s10()
        for pin in ('unconnected-(U9-ITIMER-Pad10) U9.10', 'unconnected-(U9-AUXOFF-Pad3) U9.3'):
            self.assertTrue([i for i in rep['issues'] if pin in i and '(i5-pack)' in i], rep['issues'])
        self.setUp()
        self.fails_s10(self.plant_nc_ball(), (fire.PACK_MIN, 'i5-pack'),
                       drc="'S-10 RAW_PROTECTED (I-5 rail) to every victim'")

    def test_r12f10_tri06_loader_exemption_is_rail_specific(self):
        """R12F10-TRI-06: CAM_MCU_RX's loader reason covers CAM_5V only, so it is held 0.300 mm from VBUS and PORT_4V8
        (S-10 and the DRU); i5_ft_guard() fails a loader entry whose reason does not name a rail it exempts, or a rail that
        is no port rail; a VBUS plant 0.20 mm from CAM_MCU_RX's via at U1.B8 fails S-10 and DRC."""
        from unittest import mock
        net = BOARD12.with_name('schematic.net.xml')
        self.assertEqual(fire.pair_limit('CAM_5V', None, 'CAM_MCU_RX', None, False)[1], 'unprotected')
        for rail in ('VBUS', 'PORT_4V8'):
            self.assertEqual(fire.pair_limit(rail, None, 'CAM_MCU_RX', None, False)[:2], (fire.I5_PORT_MIN, 'i5-port'))
            rule = next(r for r in fire.dru_rules() if r[0] == f'S-10 {rail} (I-5 rail) to every victim')
            self.assertIn("B.NetName == 'CAM_MCU_RX'", rule[2])
        rule = next(r for r in fire.dru_rules() if r[0] == 'S-10 CAM_5V (I-5 rail) to every victim')
        self.assertNotIn("B.NetName == 'CAM_MCU_RX'", rule[2])
        self.assertEqual(fire.ft_rails('VBUS_SENSE'), ('CAM_5V', 'PORT_4V8', 'VBUS'))
        self.assertEqual(fire.i5_ft_guard(net), [])
        rails, why = fire.I5_FT_LOADER['CAM_MCU_RX']
        for bad, want in ((('CAM_5V', 'VBUS'), 'the reason does not name VBUS'), (('RAW_PROTECTED',), 'non-empty set of port rails'),
                          ((), 'non-empty set of port rails')):
            with self.subTest(rails=bad), mock.patch.dict(fire.I5_FT_LOADER, CAM_MCU_RX=(bad, why.replace('VBUS', 'USB'))):
                self.assertTrue([i for i in fire.i5_ft_guard(net) if i.startswith('I5_FT_LOADER CAM_MCU_RX') and want in i])
        self.fails_s10(self.plant_loader(), (fire.I5_PORT_MIN, 'i5-port'), drc="'S-10 VBUS (I-5 rail) to every victim'")

    # ---- round 12 (R12F12-TRI-20 / -21) ---------------------------------------------------------------------------
    def test_r12f12_tri20_rated_exemption_checks_the_minimum(self):
        """R12F12-TRI-20: a rating has two ends. CAM_SW (rated to -2 V) is below U403 EN's -0.3 V, so the guard refuses it
        as an I5_RATED rail; a switch node with no recorded minimum and a rated pin with none both fail; S-10 holds
        CAM_SW from CAM_EN at the pack class, the two pairs beside U403.5 being measured exceptions."""
        from unittest import mock
        net = BOARD12.with_name('schematic.net.xml')
        pin, vmax, src, rails, why = fire.I5_RATED['CAM_EN']
        self.assertEqual(rails, ('CAM_BST', 'RAW_PROTECTED'))
        self.assertEqual(fire.rail_min('CAM_SW', net)[0], -2.0)
        self.assertEqual(fire.rail_min('CAM_BST', net)[0], 0.0)
        self.assertIsNone(fire.rail_min('SW_NODE', net)[0])                 # default-deny: U2's SW has no entry
        self.assertEqual(fire.i5_rated_guard(net), [])
        w = json.loads(fire.WINDOWS.read_text())
        cases = (({'CAM_EN': (pin, vmax, src, rails + ('CAM_SW',), why)}, None, 'CAM_SW goes down to -2 V'),
                 ({'CAM_EN': (pin, vmax, src, rails + ('SW_NODE',), why)}, None, 'no minimum for SW_NODE'),
                 (None, {}, 'no absolute minimum recorded for U403.5'),
                 (None, dict(fire.I5_RATED_MIN, GONE=(0.0, 'x')), 'I5_RATED_MIN names GONE'))
        for rated, floors, want in cases:
            with self.subTest(want=want):
                issues = fire.i5_rated_guard(net, w, rated, floors)
                self.assertTrue([i for i in issues if want in i], issues)
        self.assertEqual(fire.pair_limit('CAM_SW', None, 'CAM_EN', 'U403', False)[:2], (fire.PACK_MIN, 'i5-pack'))
        self.assertEqual(fire.pair_limit('CAM_BST', None, 'CAM_EN', 'U403', False)[:2], (None, 'i5-rated'))
        self.assertIn("B.NetName == 'CAM_EN'", next(r[2] for r in fire.dru_rules() if r[0].startswith('S-10 CAM_SW ')))
        self.assertEqual([round(f, 3) for *_, f in fire.EXCEPTIONS['I5_U403_EN_SW']], [0.524, 0.525])
        with mock.patch.dict(fire.EXCEPTIONS, I5_U403_EN_SW=()):
            rep = self.s10()
        hits = [i for i in rep['issues'] if 'CAM_SW track' in i and 'to CAM_EN U403.5' in i and '(i5-pack)' in i]
        self.assertEqual(len(hits), 2, rep['issues'])

    def test_r12f12_tri21_unconnected_diode_anodes_are_victims(self):
        """R12F12-TRI-21 (a): the BAT54C clamps' unused second anodes (D95.2, D436.2) are one junction from 3V3, so they
        are I-5 victims, derived from the netlist; D120.2 is not (its nets reach 3V3 only through R136). A stale or a
        missing I5_NC_PASS entry fails the guard, the DRU's I-5 rules name both nets, and a RAW_PROTECTED track 0.50 mm
        from D436.2 fails S-10 (plant_nc_pass: D95.2's spots all have D95.1 or a 3V3 via nearer)."""
        from unittest import mock
        net = BOARD12.with_name('schematic.net.xml')
        d95, d436, d120 = ('unconnected-(D95-A2-Pad2)', 'unconnected-(D436-A2-Pad2)', 'unconnected-(D120-A2-Pad2)')
        self.assertEqual(sorted(fire.i5_nc_pass(net)), sorted(fire.I5_NC_PASS))
        self.assertEqual(sorted(fire.I5_NC_PASS), sorted((d95, d436)))
        self.assertEqual(fire.i5_nc_pass(net)[d95], ('D95', '2', '3V3'))
        self.assertEqual(fire.pair_limit('RAW_PROTECTED', None, d95, 'D95', False)[:2], (fire.PACK_MIN, 'i5-pack'))
        self.assertEqual(fire.pair_limit('CAM_5V', None, d436, 'D436', True)[:2], (fire.I5_PORT_MIN, 'i5-port'))
        self.assertEqual(fire.pair_limit('RAW_PROTECTED', None, d120, 'D120', False)[1], 'unprotected')
        for r in fire.dru_rules():
            if '(I-5 rail)' in r[0]:
                for n in (d95, d436):
                    self.assertIn(f"B.NetName == '{n}'", r[2], r[0])
        with mock.patch.object(fire, 'I5_NC_PASS', (d436,)):
            self.assertTrue([i for i in fire.i5_guard(net)[0] if d95 in i and 'I5_NC_PASS' in i])
        with mock.patch.object(fire, 'I5_NC_PASS', (d95, d436, d120)):
            self.assertTrue([i for i in fire.i5_guard(net)[0] if d120 in i and 'stale I5_NC_PASS' in i])
        # a clamp whose cathode is moved off 3V3 onto a net that is no victim no longer makes its spare anode one
        moved = self.netlist(lambda r: [n.remove(x) for n in r.findall('./nets/net') for x in list(n.findall('node'))
                                        if x.get('ref') == 'D95' and x.get('pin') in ('1', '3')])
        self.assertNotIn(d95, fire.i5_nc_pass(moved))
        self.assertEqual(self.pad('D436', '2').GetNetname(), d436)
        self.fails_s10(self.plant_nc_pass(), (fire.PACK_MIN, 'i5-pack'))

    def test_r12f12_tri21_feedback_divider_middles_held_from_pack_rails(self):
        """R12F12-TRI-21 (b): PORT_FB_TOP and CAM_FB_TOP reach a 6 V VFB pin through one divider resistor, so the
        pack-voltage rails are held from them (derived from the netlist); the port rails are not. The eleven PORT_FB_TOP
        pairs under 1.040 mm are measured exceptions: without them S-10 fails each, and a RAW_PROTECTED track 0.20 mm
        from R433.2 (CAM_FB_TOP) fails S-10 (plant_fb_top: every spot 0.5 mm from it touches other copper)."""
        from unittest import mock
        net = BOARD12.with_name('schematic.net.xml')
        mids = fire.i5_fb_mids(net)
        self.assertEqual(sorted(mids), sorted(fire.I5_FB_MID))
        self.assertEqual(mids['PORT_FB_TOP'], ('U400.4', 5100.0))
        self.assertEqual(mids['CAM_FB_TOP'], ('U403.4', 10000.0))
        for rail in fire.I5_PACK:
            self.assertEqual(fire.pair_limit(rail, None, 'PORT_FB_TOP', None, False)[:2], (fire.PACK_MIN, 'i5-pack'))
        for rail in fire.I5_PORT:
            self.assertEqual(fire.pair_limit(rail, None, 'CAM_FB_TOP', None, False)[1], 'unprotected')
        for r in fire.dru_rules():
            if '(I-5 rail)' in r[0]:
                rail = r[0].split()[1]
                self.assertEqual("B.NetName == 'PORT_FB_TOP'" in r[2], rail in fire.I5_PACK, r[0])
        with mock.patch.object(fire, 'I5_FB_MID', ('CAM_FB_TOP',)):
            self.assertTrue([i for i in fire.i5_guard(net)[0] if 'PORT_FB_TOP reaches the feedback pin U400.4' in i])
        with mock.patch.object(fire, 'I5_FB_MID', ('CAM_FB_TOP', 'PORT_FB_TOP', 'PORT_SENSE')):
            self.assertTrue([i for i in fire.i5_guard(net)[0] if 'PORT_SENSE' in i and 'stale I5_FB_MID' in i])
        self.assertEqual(len(fire.EXCEPTIONS['I5_U400_FB_TOP']), 11)
        with mock.patch.dict(fire.EXCEPTIONS, I5_U400_FB_TOP=()):
            rep = self.s10()
        hits = [i for i in rep['issues'] if 'to PORT_FB_TOP ' in i and '(i5-pack)' in i]
        self.assertEqual(len(hits), 11, rep['issues'])
        self.assertEqual(self.pad('R433', '2').GetNetname(), 'CAM_FB_TOP')
        self.fails_s10(self.plant_fb_top(), (fire.PACK_MIN, 'i5-pack'))

    def test_r12f12_tri21_raw_act_to_ign_is_held_one_way(self):
        """R12F12-TRI-21 (c): RAW_ACT against PYRO1_IGN is classed out of the pack class only; PYRO1_IGN's class holds
        the pair (0.25 mm copper, 0.5 mm fills). Before, both directions were exempt and nothing held it: a RAW_ACT
        track 0.15 mm from J121.2 fails S-10 and DRC."""
        self.assertNotIn((fire.IGN, 'RAW_ACT'), fire.NOT_A_PATH)
        self.assertIn(('RAW_ACT', fire.IGN), fire.NOT_A_PATH)
        self.assertEqual(fire.pair_limit('RAW_ACT', None, fire.IGN, None, False), (fire.IGN_MIN, 'ign', fire.IGN))
        self.assertEqual(fire.pair_limit(fire.IGN, None, 'RAW_ACT', None, True), (fire.FILL_MIN, 'ign', fire.IGN))
        rules = {r[0]: r[2] for r in fire.dru_rules()}
        self.assertNotIn("B.NetName != 'RAW_ACT'", rules['S-10 PYRO1_IGN to every net'])
        self.assertIn(f"B.NetName != '{fire.IGN}'", rules['S-10 RAW_ACT (pack energy) to every net'])
        # the isolated copy keeps J121.2 the plant's one neighbour, so DRC names PYRO1_IGN's rule on it
        self.fails_s10(self.plant_ign_raw_act(), (fire.IGN_MIN, 'ign'), drc="'S-10 PYRO1_IGN to every net'")

    def test_dru_is_generated_from_s10(self):
        """The DRU's S-10 rules are r12_fire.dru_rules(), in order after R11's scoped rules, with general limits at least
        S-10's; each exception names its two items and its floor (kicad-cli matches them: the build's DRC is 0)."""
        text = BOARD12.with_suffix('.kicad_dru').read_text()
        rules = fire.dru_rules()
        at = [text.index(f'(rule "{r[0]}"') for r in rules]
        self.assertEqual(at, sorted(at))
        self.assertGreater(at[0], text.index('R9 bare test pads to foreign copper'))
        for r in rules:
            self.assertIn(fire.dru_text(r), text)
        self.assertGreaterEqual(fire.DRU_GATE_MM, fire.GATE_MIN)
        self.assertEqual(len(rules), 6 + len(fire.PACK) + len(fire.I5_PACK) + len(fire.I5_PORT) +
                         sum(len(v) for v in fire.EXCEPTIONS.values()))
        for key, pairs in fire.EXCEPTIONS.items():
            for a, b, layer, floor in pairs:
                self.assertIn(f'(rule "S-10 exception ({key}): {a} to {b} on {layer}"\n  (layer "{layer}")', text)
                self.assertLess(floor, fire.GATE_MIN)
        self.assertLess(text.index('R12 JLC SMD pad to pad'), text.index('Tag-Connect contact'))
        self.assertIs(r12.fire, fire)
        self.assertEqual(r12_sch.FIRE_RULES, tuple(rules))

    def test_u6_corner_lands_clear_jlc_limits(self):
        """R12F5-TRI-06: U6's corner lands (NXP's chamfered land) keep >= 0.15 mm pad to pad and >= 0.10 mm mask web."""
        f = self.board.FindFootprintByReference('U6')
        pads = {p.GetNumber(): p for p in f.Pads()}

        def gap(a, b):
            lo, hi = 0, mm(0.5)
            while hi - lo > 100:
                mid = (lo + hi) // 2
                lo, hi = (lo, mid) if a.Collide(b, mid) else (mid, hi)
            return hi / 1e6

        def mask(p):
            s = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(s, pcbnew.F_Mask, p.GetSolderMaskExpansion(pcbnew.F_Mask), mm(0.001),
                                      pcbnew.ERROR_OUTSIDE)
            return s
        for a, b in (('4', '5'), ('8', '9'), ('12', '13'), ('16', '1')):
            with self.subTest(pair=(a, b)):
                pa, pb = pads[a], pads[b]
                self.assertGreaterEqual(gap(pa.GetEffectiveShape(pcbnew.F_Cu), pb.GetEffectiveShape(pcbnew.F_Cu)), 0.15)
                self.assertGreaterEqual(gap(mask(pa), mask(pb)), 0.10)
        self.assertIn('R12 JLC SMD pad to pad (different nets)', BOARD12.with_suffix('.kicad_dru').read_text())


@unittest.skipUnless(pcbnew and BOARD12.is_file() and (BOARD12.parent / 'fab/m3_bom_jlc.csv').is_file(),
                     'KiCad python, the R12 board and its fab package required')
class FabContent(unittest.TestCase):
    """R12F3-TRI-03: the R12 package's content checks run S-4 on the exported BOM / CPL (quantity, Manufacturer Part and
    Footprint against the board's native parts), as R10's and R11's packages do; seeded on a copy of the package."""

    def s4(self, out):
        import fab_manifest_r12 as fm12
        checks = fm12.content_checks(BOARD12, out, sys.executable)
        label, argv = checks[0]
        self.assertEqual(label, 'S-4 BOM / CPL identities')
        self.assertTrue(argv[2].endswith('check_r12.py'))
        self.assertEqual(argv[4:6], ['--only', 'S-4'])
        self.assertIn('--bom', argv)
        self.assertIn('--cpl', argv)
        return subprocess.run(argv, capture_output=True, text=True, timeout=600)

    def test_s4_bound_and_run_on_the_package(self):
        import fab_manifest_r12 as fm12
        self.assertIn('tools/check_r12.py', fm12.R12_INPUTS)
        fab = BOARD12.parent / 'fab'
        ok = self.s4(fab)
        self.assertEqual(ok.returncode, 0, ok.stdout[-2000:] + ok.stderr[-2000:])
        import csv
        with tempfile.TemporaryDirectory(prefix='r12-fabmut-') as d:
            out = Path(d)
            shutil.copy2(fab / 'm3_cpl_jlc.csv', out / 'm3_cpl_jlc.csv')
            with (fab / 'm3_bom_jlc.csv').open(newline='') as src:
                reader = csv.DictReader(src)
                fields, rows = reader.fieldnames, list(reader)
            row = next(r for r in rows if r['Designator'] == 'Q122,Q123,Q124')
            row.update({'Footprint': 'R0402', 'Manufacturer Part': 'AO3401A', 'Qty': '0'})
            with (out / 'm3_bom_jlc.csv').open('w', newline='') as dst:
                w = csv.DictWriter(dst, fieldnames=fields)
                w.writeheader()
                w.writerows(rows)
            bad = self.s4(out)
        self.assertNotEqual(bad.returncode, 0)
        text = bad.stdout
        for want in ("Qty '0' must be a positive integer", "Q124 Manufacturer Part 'AO3401A' differs",
                     "Q122 Footprint 'R0402' differs"):
            self.assertIn(want, text)


class Schematic(unittest.TestCase):
    """The committed R12 netlist meets the contract and every seeded fault is caught (ERC runs in the R12 gate)."""

    @classmethod
    def setUpClass(cls):
        cls.parts, cls.pins = r12_sch_check.read_netlist(ROOT / 'm3_design/r12/schematic.net.xml')

    def test_contract_holds(self):
        self.assertEqual(r12_sch_check.contract(self.parts, self.pins, ROOT / 'm3_design/r12'), [])

    def test_seeds_are_caught(self):
        seeded = r12_sch_check.seeds(self.parts, self.pins)
        self.assertTrue(all(seeded.values()), [k for k, v in seeded.items() if not v])
        self.assertTrue(r12_sch_check.side_seed(ROOT / 'm3_design/r12'))

    def test_r12f6_tri09_port_pin_names(self):
        """R12F6-TRI-09 (R10 test_r27_port_terminal_pin_names, ported): the SH ports' pin names are D-R12-31's order
        (1 GND, 2 4V8, 3 TXO, 4 RXI; J410 5-6 NC) on their own symbols, each name on the net it names; R11's
        PortTerminal names, the servo symbol on J410 and the other seeded name faults are caught."""
        names = r12_sch_check.read_pin_names(ROOT / 'm3_design/r12/schematic.net.xml')
        self.assertEqual(r12_sch_check.terminal_pin_issues(names), [])
        seeded = r12_sch_check.name_seeds(names)
        self.assertEqual(len(seeded), 5)
        self.assertTrue(all(seeded.values()), seeded)
        data = r12_sch.circuit()
        self.assertEqual({ref: data['parts'][ref]['lib'] for ref in ('J410', 'J420', 'J440')},
                         {'J410': 'M3:PortSH6', 'J420': 'M3:PortSH4', 'J440': 'M3:PortSH4'})
        self.assertEqual({names['J410', p][0] for p in '56'}, {'NC'})
        lib = (ROOT / 'm3_design/r12/kilib/m3.kicad_sym').read_text()
        sheets = ''.join((ROOT / 'm3_design/r12' / s).read_text() for s in r12_sch.SHEET_FILES)
        for name in ('PortSH4', 'PortSH6', 'ServoGH6', 'SwitchGH4', 'CameraGH6'):
            s = lib.index(f'\t(symbol "{name}"\n')
            descr = lib[s:lib.index('(property "ki_keywords"', s)]
            self.assertIn('ZX-SH1.0', descr, name)
        self.assertNotIn('GH-1.25', sheets)
        self.assertNotIn('SM06B-GHS', sheets)
        self.assertNotIn('SM04B-GHS', sheets)

    def test_pin_table_current(self):
        self.assertEqual((r12_sch.DESIGN / 'pin_table.tsv').read_text(), r12_sch.pin_table_text())

    def test_inputs_pinned(self):
        r12_sch.source_check()

    def test_one_side_and_economic(self):
        data = r12_sch.circuit()
        self.assertEqual(data['assembly']['sides'], 1)
        self.assertEqual(data['owner_fit'], {})          # D-R12-85: every part JLC-assembled (owner 2026-11-05)


@unittest.skipUnless(pcbnew, 'KiCad python required')
class Library(unittest.TestCase):
    def test_library_current_and_lands(self):
        import r12_parts
        files, copied = r12_parts.generated()
        self.assertEqual(r12_parts.stale(files, copied), [])
        r12_parts.geometry_checks()


class Windows(unittest.TestCase):
    """Stage A windows: the committed JSON is the generator's and the key results hold."""

    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(r12_budget.OUT.read_text())

    def test_current(self):
        self.assertEqual(json.dumps(r12_budget.compute(), indent=1, sort_keys=True) + '\n', r12_budget.OUT.read_text())

    def test_fire_floor(self):
        self.assertGreaterEqual(self.data['fire']['four_stall_A'], 1.125)
        self.assertTrue(self.data['fire']['four_stall_ok'])

    def test_rails_inside_limits_at_initial_tolerance(self):
        for name, row in self.data['rails'].items():
            with self.subTest(rail=name):
                self.assertTrue(row['initial']['inside_limits'], row['initial'])

    def test_ovlo_and_sense(self):
        self.assertTrue(self.data['u9']['ovlo_check_ok'])
        self.assertTrue(self.data['sense']['PORT_SENSE_ok'])
        self.assertTrue(self.data['crystal']['ok'])
        self.assertTrue(self.data['vlogic']['usb_only_ok'])

    def test_crystal_range_includes_capacitor_tolerance(self):
        """R12F3-TRI-05: the gm_crit range spans C25 / C26's tolerance and 2-5 pF stray; 18 pF +5 % at 5 pF stray gave
        1.5027 mA/V, above DS12110's 1.5 mA/V Gm_critmax, so C25 / C26 are 15 pF."""
        x = self.data['crystal']
        self.assertEqual(x['C25_C26_pF'], [15.0, 15.0])
        self.assertEqual(x['C25_C26_tolerance'], [0.05, 0.05])
        self.assertEqual(x['circuit_CL_pF'], [9.125, 11.0, 12.875])
        self.assertLess(x['gm_crit_range_mA_per_V'][1], 1.5)
        self.assertGreater(x['gm_crit_18pF_5pct_corner_mA_per_V'], 1.5)
        self.assertLess(x['total_offset_ppm_bound'], x['usb_fs_limit_ppm'] / 10)

    def test_round1_labels_and_cam_input(self):
        """D-R12-86 / -87 (R12F1-TRI-03, -17): PA4 sense labelled with its drift Inference; CAM_5V input condition."""
        self.assertEqual(self.data['sense']['label'],
                         'Calculation (1 % resistors, R60 / R61 0.1 % (PA6_TOL, R12F9-TRI-04), rail windows above; '
                         'DS12110 leakage); drift Inference; the PORT_SENSE '
                         'thresholds: Calculation / Inference (3V3 window, D-R12-139)')   # R12F7-TRI-02 (D-R12-149)
        self.assertEqual((self.data['sense']['PORT_SENSE_divider']['R111_ohm'],
                          self.data['sense']['PORT_SENSE_divider']['R112_ohm']), (47e3, 100e3))
        cam = self.data['cam_input']
        self.assertIn('VO / 0.75', cam['window_holds_for'])
        self.assertTrue(cam['label'].startswith('Calculation / Inference'))
        lo, hi = cam['min_recommended_VIN_V']['initial']
        rail = self.data['rails']['CAM_5V (U403 TPS563208, R433 51k + R434 10k / R435 10k)']['initial']
        self.assertAlmostEqual(lo, rail['min_V'] / 0.75, places=3)
        self.assertAlmostEqual(hi, rail['max_V'] / 0.75, places=3)
        self.assertLess(cam['four_stall_U403_VIN_V'], lo)                 # the four-stall point is below the condition

    def test_divider_math(self):
        lo, hi = r12_budget.divider((1.0, 1.0), 1e3, 1e3, 0.0)
        self.assertEqual((lo, hi), (2.0, 2.0))
        lo, hi = r12_budget.divider((0.749, 0.787), 52e3, 10e3, 0.01)
        self.assertLess(lo, 0.749 * 6.2)
        self.assertGreater(hi, 0.787 * 6.2)


@unittest.skipUnless(pcbnew, 'KiCad python required')
class RealBoard(unittest.TestCase):
    def test_r12_board_placement_rules(self):
        path = os.environ.get('R12_BOARD')
        if not path:
            if os.environ.get('R12_BOARD_REQUIRED') == '1':
                self.fail('R12_BOARD_REQUIRED=1 but R12_BOARD is not set')
            self.skipTest('no tracked, routed R12 board supplied')
        path = Path(path).resolve()
        if not path.is_file() or not path.is_relative_to(ROOT):
            self.skipTest('R12 board is not a repository build')
        tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', str(path.relative_to(ROOT))],
                                 cwd=ROOT, capture_output=True).returncode == 0
        if not tracked:
            self.skipTest('R12 board is untracked (build output)')
        board = pcbnew.LoadBoard(str(path))
        if not any(t.GetClass() in ('PCB_TRACK', 'PCB_ARC') for t in board.GetTracks()):
            self.skipTest('R12 board is unrouted')
        report = r12.check_board(board, Path(path), stage='placement')
        self.assertTrue(report['ok'], report['issues'])


# Reuse only synthetic construction helpers; every assertion invokes the R12 rule dispatcher.
if pcbnew:
    import test_r11_check as fixtures11
    import test_r10_check as fixtures10
    import check_r10 as r10


class Four(fixtures11.Six if pcbnew else object):
    def __init__(self):
        super().__init__(length=100)
        self.board.SetCopperLayerCount(4)
        self.board.GetTitleBlock().SetRevision(r12.REVISION)
        for net in r12.reference_names():
            self.net(net)

    def run(self, only, **kw):
        return r12.check_board(self.board, kw.pop('path', r12.R12_DIR / 'm3.kicad_pcb'), only=set(only), **kw)

    def rect_fill(self, net, box, layer):
        x0, y0, x1, y1 = box
        self.net(net)
        z = self.zone(net, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer)
        z.SetFilledPolysList(layer, pcbnew.SHAPE_POLY_SET(z.Outline()))
        z.SetIsFilled(True)
        return z

    def yard(self, f, x0, y0, x1, y1):
        g = pcbnew.PCB_SHAPE(f); g.SetShape(pcbnew.SHAPE_T_RECT); g.SetLayer(pcbnew.F_CrtYd)
        g.SetStart(self.P(x0, y0)); g.SetEnd(self.P(x1, y1)); g.SetWidth(mm(.05)); f.Add(g)
        f.BuildCourtyardCaches()

    def text(self, text, x, y, layer=None):
        t = pcbnew.PCB_TEXT(self.board); t.SetText(text)
        t.SetLayer(pcbnew.F_SilkS if layer is None else layer)
        t.SetPosition(self.P(x, y)); t.SetTextSize(self.P(1, 1)); t.SetTextThickness(mm(.15))
        self.board.Add(t)
        return t

    def sh(self, ref, x, y):
        want = r12.SH_PORTS[ref]
        return self.part(ref, x, y, [(n, net, (int(n) * 2, 0), 'smd') for n, net in want.items()],
                         part=f'ZX-SH1.0-{len(want)}PWT')


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class SafetyPorts(fixtures10.SyntheticBase if pcbnew else unittest.TestCase):
    def run_rule(self, rid):
        return r12.check_board(self.board, r12.R12_DIR / 'm3.kicad_pcb', only={rid})['issues']

    def load_switch(self):
        for ref, drain, y in (('Q120', 'BAT_IN', 40), ('Q121', 'RAW_ACT', 50)):
            self.part(ref, [('1', 3, 0, 'ACT_GATE'), ('2', 2, 0, 'ACT_FET_S'), ('3', 1, 3, drain)], at=(20, y))

    def test_s1_pass_and_bypass(self):
        self.assertEqual(self.run_rule('S-1'), [])
        self.part('R999', [('1', 0, 0, 'RAW_ACT'), ('2', 2, 0, 'PYRO1_IGN')], at=(10, 10))
        self.assertTrue(self.run_rule('S-1'))

    def test_s2_pass_and_swapped_source(self):
        self.load_switch()
        self.assertEqual(self.run_rule('S-2'), [])
        self.board.FindFootprintByReference('Q121').FindPadByNumber('2').SetNet(self.board.FindNet('BAT_IN'))
        self.assertTrue(self.run_rule('S-2'))

    def test_s3_pass_and_missing_bias_or_cap(self):
        fixtures10.Synthetic.gates(self)
        u1 = self.board.FindFootprintByReference('U1')
        u1.FindPadByNumber('16').SetNumber('F2')
        q = self.board.FindFootprintByReference('Q124')
        # Change the synthetic DFN to the three-pad AO3400A package, preserving the gate-network fixture.
        for p in list(q.Pads()):
            if p.GetNumber() in ('2', '3'):
                q.Remove(p)
        for p in q.Pads():
            p.SetNumber({'1': '2', '4': '1', '5': '3'}[p.GetNumber()])
        # R12F12-TRI-04: without Q122's second gate pull-down R118 (10k, ACT_EN to GND) S-3 fails; so does a wrong
        # value, its GND end elsewhere, or a further part on ACT_EN
        self.assertTrue(any('R118' in i and 'second gate pull-down' in i for i in self.run_rule('S-3')))
        r118 = self.part('R118', [('1', 0, 0, 'ACT_EN'), ('2', 1.5, 0, 'GND')], at=(35, 76))
        r118.SetValue('10k')
        self.assertEqual(self.run_rule('S-3'), [])
        r118.SetValue('100k')
        self.assertTrue(any('R118 must be 10000 ohm' in i for i in self.run_rule('S-3')))
        r118.SetValue('10k')
        r118.FindPadByNumber('2').SetNet(self.board.FindNet('3V3'))
        self.assertTrue(any('R118' in i and 'must join ACT_EN to GND' in i for i in self.run_rule('S-3')))
        r118.FindPadByNumber('2').SetNet(self.board.FindNet('GND'))
        extra = self.part('R999', [('1', 0, 0, 'ACT_EN'), ('2', 1.5, 0, 'GND')], at=(35, 80))
        self.assertTrue(any("ACT_EN must touch only ['C123', 'Q122', 'R118', 'R122', 'R123']" in i
                            for i in self.run_rule('S-3')))
        self.board.Remove(extra)
        self.assertEqual(self.run_rule('S-3'), [])
        self.board.Remove(self.local[0])
        self.assertTrue(any('copper alone' in i for i in self.run_rule('S-3')))
        self.board.Add(self.local[0])
        self.board.FindFootprintByReference('C123').SetValue('1nF')
        self.assertTrue(self.run_rule('S-3'))

    def test_s5_pass_and_switch_nc_or_bypass(self):
        fixtures10.Synthetic.power_switch(self)
        f = self.board.FindFootprintByReference('J400')
        for n in ('3', '4'):
            p = pcbnew.PAD(f); p.SetNumber(n); p.SetPosition(self.P(5, 15 + int(n))); f.Add(p)
        self.assertEqual(self.run_rule('S-5'), [])
        f.FindPadByNumber('3').SetNet(self.board.FindNet('BAT_IN'))
        self.assertTrue(self.run_rule('S-5'))
        self.board.FindFootprintByReference('R80').SetValue('0R')
        self.assertTrue(any('470k' in i for i in self.run_rule('S-5')))

    def test_s6_pass_and_port_bridge(self):
        self.part('J410', [('1', 0, 0, 'GPS_TX_MCU')], at=(15, 10))
        self.assertEqual(self.run_rule('S-6'), [])
        self.part('R999', [('1', 0, 0, 'GPS_TX_MCU'), ('2', 2, 0, 'RAW_ACT')], at=(15, 15))
        self.assertTrue(self.run_rule('S-6'))


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class PortedRules(unittest.TestCase):
    def assert_rule(self, s, rid, good=True, want=None, **kw):
        """The rule passes (good) or fails; with want, an issue contains that text (R12F12-TRI-27: a failing seed
        names its branch, not only ok False)."""
        rep = s.run({rid}, **kw)
        self.assertFalse(any('check could not run' in i for i in rep['issues']), rep['issues'])
        self.assertEqual(rep['ok'], good, rep['issues'])
        self.assertIn(rid, rep['rules'])
        if want is not None:
            self.assertTrue([i for i in rep['issues'] if want in i], (want, rep['issues']))
        return rep

    @staticmethod
    def populated():
        s = Four()
        parts, _ = r12_sch.model(r12_sch.circuit())
        for i, (ref, part) in enumerate(parts.items()):
            f = pcbnew.FootprintLoad(str(LIB), part['footprint'].split(':')[1])
            f.SetReference(ref); f.SetValue(part['value']); s.board.Add(f)
            f.SetPosition(s.P(10 + 15 * (i % 10), 10 + 15 * (i // 10)))
            for k, v in part['fields'].items():
                f.SetField(k, v)
            if 'exclude_from_bom' in part['flags']:
                f.SetAttributes(f.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        return s, parts

    def test_s4_owner_fit_refused(self):
        """D-R12-85: a part named in circuit.json owner_fit (hand-fitted, off the JLC BOM) fails S-4."""
        s, _ = self.populated()
        real = r12_sch.circuit
        try:
            r12_sch.circuit = lambda: dict(real(), owner_fit={'LS120': 'hand-fitted after reflow'})
            rep = self.assert_rule(s, 'S-4', False)
        finally:
            r12_sch.circuit = real
        self.assertTrue(any('LS120 is owner-fitted' in i for i in rep['issues']), rep['issues'])

    def test_s4_population_and_assembly(self):
        s, parts = self.populated()
        self.assert_rule(s, 'S-4')
        f = s.board.FindFootprintByReference('R128')
        old = f.GetAttributes(); f.SetAttributes(old | pcbnew.FP_DNP)
        self.assert_rule(s, 'S-4', False)
        f.SetAttributes(old)
        # Both files exercise the assembly branch, including the separate owner BOM identities.
        import csv
        with tempfile.TemporaryDirectory() as tmp:
            bom = Path(tmp) / 'r12_bom_jlc.csv'; cpl = Path(tmp) / 'r12_cpl.csv'
            fields = ['Designator', 'Qty', 'LCSC Part #', 'Manufacturer Part', 'Footprint']
            rows = [dict(zip(fields, [ref, 1, p['fields'].get('LCSC', ''), p['fields'].get('Manufacturer Part', ''),
                                     p['footprint'].split(':')[1]])) for ref, p in parts.items() if 'exclude_from_bom' not in p['flags']]
            manual = set(r12_sch.circuit()['owner_fit'])
            for path, chosen in ((bom, [r for r in rows if r['Designator'] not in manual]),
                                 (bom.with_name('r12_bom_owner.csv'), [r for r in rows if r['Designator'] in manual])):
                with path.open('w') as out:
                    w = csv.DictWriter(out, fieldnames=fields); w.writeheader(); w.writerows(chosen)
            cpl.write_text('Designator\n' + '\n'.join(r['Designator'] for r in rows if r['Designator'] not in manual) + '\n')
            self.assert_rule(s, 'S-4', bom=bom, cpl=cpl)
            cpl.write_text(cpl.read_text().replace('R128\n', ''))
            self.assert_rule(s, 'S-4', False, bom=bom, cpl=cpl)

    def test_s7_and_w2_sh_ports(self):
        s = Four()
        for i, ref in enumerate(r12.SH_PORTS):
            s.sh(ref, 10, 10 + i * 10)
        for rid in ('S-7', 'W-2'):
            self.assert_rule(s, rid)
        # R12F12-TRI-27: another part number on a port fails W-2's part branch
        j410 = s.board.FindFootprintByReference('J410')
        j410.SetField('Manufacturer Part', 'GH1.25-4PWT')
        self.assert_rule(s, 'W-2', False, want=f'W-2: J410 must be ZX-SH1.0-{len(r12.SH_PORTS["J410"])}PWT (D-R12-31)')
        j410.SetField('Manufacturer Part', f'ZX-SH1.0-{len(r12.SH_PORTS["J410"])}PWT')
        s.board.FindFootprintByReference('J122').FindPadByNumber('6').SetNet(s.net('3V3'))
        for rid in ('S-7', 'W-2'):
            self.assert_rule(s, rid, False)
        s.board.FindFootprintByReference('J410').FindPadByNumber('1').SetNet(s.net('PORT_4V8'))
        self.assert_rule(s, 'W-2', False)

    def test_s8_foreign_inner_copper_and_rings(self):
        for layer in (pcbnew.In1_Cu, pcbnew.In2_Cu):
            for net in ('SIGNAL', 'GND'):
                with self.subTest(layer=layer, net=net):
                    s = Four(); s.via(10, 10, 'PYRO1_OUT', d=.45)
                    t = s.track((12, 8), (12, 12), net, layer, .1)
                    self.assert_rule(s, 'S-8')
                    t.Move(s.P(-1, 0)); self.assert_rule(s, 'S-8', False)
        s = Four()
        s.part('J121', 10, 10, [('1', 'PYRO1_OUT', (0, 0), 'pth')])
        # 1.1 mm from the hole wall, but only 0.7 mm from the retained ring.
        s.track((11.65, 8), (11.65, 12), 'SIGNAL', pcbnew.In2_Cu, .1)
        rep = self.assert_rule(s, 'S-8', False)
        self.assertTrue(any('inner ring' in i for i in rep['issues']))
        s = Four(); s.via(10, 10, 'RAW_ACT', d=.45)
        s.track((10.8, 8), (10.8, 12), 'GND', pcbnew.In2_Cu, .1)
        self.assert_rule(s, 'S-8')  # Original safe GND exception, not a signal exemption.

    def test_s8_inner_tracks_of_barrel_nets(self):
        """R12F12-TRI-03 / -18: an inner-layer track of a barrel net keeps 1 mm from foreign copper on its layer, fills
        included; GND counts for the GND-hazard nets (ACT_GATE) and not for the others (BAT_SW_RETURN)."""
        for net, other, good in (('ACT_GATE', 'SIGNAL', False), ('ACT_GATE', 'GND', False),
                                 ('BAT_SW_RETURN', 'SIGNAL', False), ('BAT_SW_RETURN', 'GND', True)):
            with self.subTest(net=net, other=other):
                s = Four()
                s.track((10, 10), (10.5, 10.5), net, pcbnew.In2_Cu, .2)
                t = s.track((12.2, 8), (12.2, 12), other, pcbnew.In2_Cu, .1)      # 1.55 mm from the track's end
                rep = self.assert_rule(s, 'S-8')
                self.assertEqual(rep['evidence']['s8']['inner_tracks']['tracks'], 1)
                t.Move(s.P(-1, 0))                                                 # 0.55 mm
                rep = self.assert_rule(s, 'S-8', good)
                if not good:
                    self.assertTrue(any('inner-layer track of a barrel net' in i and f'{other} copper is 0.5' in i
                                        for i in rep['issues']), rep['issues'])
        s = Four()
        s.track((10, 10), (10.5, 10.5), 'ACT_GATE', pcbnew.In2_Cu, .2)
        s.rect_fill('3V3', (11.1, 5, 20, 15), pcbnew.In2_Cu)                       # a fill 0.5 mm from the track's end
        rep = self.assert_rule(s, 'S-8', False)
        self.assertTrue(any('3V3 copper is 0.5' in i for i in rep['issues']), rep['issues'])
        s = Four()
        s.track((10, 10), (10.5, 10.5), 'ACT_GATE', pcbnew.In2_Cu, .2)
        s.track((11.2, 8), (11.2, 12), 'SIGNAL', pcbnew.In1_Cu, .1)                # another layer: not this rule's
        self.assert_rule(s, 'S-8')

    def test_s9_current_paths(self):
        s = Four()
        paths = [('PYRO1_IGN', 'R134', 'J121'), ('PYRO1_OUT', 'J121', 'Q124'),
                 ('RAW_ACT', 'Q121', 'R134'), ('ACT_FET_S', 'Q120', 'Q121'), ('BAT_IN', 'J1', 'Q120')]
        fps, tracks = {}, []
        for i, (net, a, b) in enumerate(paths):
            for ref, x in ((a, 10), (b, 20)):
                if ref not in fps:
                    fps[ref] = s.part(ref, 0, 0, [])
                f = fps[ref]; p = pcbnew.PAD(f); p.SetNumber(str(i + 1)); p.SetNet(s.net(net))
                p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
                layers = pcbnew.LSET(); layers.AddLayer(pcbnew.F_Cu); p.SetLayerSet(layers)
                p.SetSize(s.P(.8, .8)); p.SetPosition(s.P(x, 10 + i * 10)); f.Add(p)
            tracks.append(s.track((10, 10 + i * 10), (20, 10 + i * 10), net, width=1 if net == 'BAT_IN' else .5))
        self.assert_rule(s, 'S-9')
        for t in tracks:
            old = t.GetWidth(); t.SetWidth(mm(.3))
            self.assert_rule(s, 'S-9', False, want=f'S-9: {t.GetNetname()} fire-path track 0.300 mm wide')
            t.SetWidth(old)
        s.board.Remove(tracks[0])
        self.assert_rule(s, 'S-9', False, want="S-9: PYRO1_IGN: no copper path between its power terminals")

    def test_w1_kf301_battery_and_db125_pyro(self):
        """D-R12-174: J1 is the plated KF301-5.0-2P screw terminal (BAT_IN / GND), J121 the DB125 (PYRO1_OUT / _IGN);
        a swapped net or another part number on either fails W-1."""
        def two():
            s = Four()
            for ref, nets in (('J1', ('BAT_IN', 'GND')), ('J121', ('PYRO1_OUT', 'PYRO1_IGN'))):
                s.part(ref, 10, 10 if ref == 'J1' else 20,
                       [(str(i + 1), net, (i * 5, 0), 'pth') for i, net in enumerate(nets)],
                       part='DB125-3.5-2P-BK-S' if ref == 'J121' else 'KF301-5.0-2P')
            return s
        s = two(); self.assert_rule(s, 'W-1')
        s.board.FindFootprintByReference('J121').FindPadByNumber('1').SetNet(s.net('PYRO1_IGN'))
        self.assert_rule(s, 'W-1', False)
        s = two(); s.board.FindFootprintByReference('J1').FindPadByNumber('2').SetNet(s.net('BAT_IN'))
        self.assert_rule(s, 'W-1', False)
        s = two(); s.board.FindFootprintByReference('J1').SetField('Manufacturer Part', 'KF128-5.0-2P')
        self.assert_rule(s, 'W-1', False)

    def test_r12f12_tri27_w1_battery_pads_plated(self):
        """R12F12-TRI-27: J1 with its BAT_IN contact made an SMD pad fails W-1's plated-through-hole branch."""
        s = Four()
        s.part('J1', 10, 10, [('1', 'BAT_IN', (0, 0), 'smd'), ('2', 'GND', (5, 0), 'pth')], part='KF301-5.0-2P')
        s.part('J121', 10, 20, [('1', 'PYRO1_OUT', (0, 0), 'pth'), ('2', 'PYRO1_IGN', (5, 0), 'pth')],
               part='DB125-3.5-2P-BK-S')
        self.assert_rule(s, 'W-1', False, want='W-1: J1.1 must be plated through-hole')

    def test_lc1_local_floors(self):
        for ref, floor in (('R1', .15), ('J2', .508), ('TP1', 1.0)):
            s = Four(); f = s.part(ref, 10, 10, [('1', 'GND', (0, 0), 'smd')])
            f.SetLocalClearance(mm(floor)); self.assert_rule(s, 'LC-1')
            f.FindPadByNumber('1').SetLocalClearance(mm(floor - .01)); self.assert_rule(s, 'LC-1', False)

    def test_m3_recorded_supports(self):
        s = Four(); supports = [(3, 5.9), (43, 5.9), (3.5, 94.1), (42.5, 94.1)]
        for xy in supports: s.hole(*xy)
        self.assert_rule(s, 'M-3', data={'supports': supports})
        s.hole(23, 50); self.assert_rule(s, 'M-3', False, data={'supports': supports})
        # R12F12-TRI-27: a support drilled 3.0 mm fails the diameter branch
        s = Four()
        for xy in supports: s.hole(*xy)
        h = next(d for d in s.board.GetDrawings() if d.GetShape() == pcbnew.SHAPE_T_CIRCLE)
        h.SetEnd(h.GetCenter() + s.P(1.5, 0))
        self.assert_rule(s, 'M-3', False, data={'supports': supports}, want='M-3: support diameter must be 3.2 mm')

    def test_m6_one_side(self):
        s = Four(); f = s.part('R1', 10, 10, [('1', 'GND', (0, 0), 'smd')])
        self.assert_rule(s, 'M-6')
        f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM); self.assert_rule(s, 'M-6', False)

    def test_m7_sensor_geometry_without_pin_numbers(self):
        """M-7 on U4 (the IMU), U5 (the barometer) and U99 (a high-g part found by its HG_ net): each fault fails with
        its own message (R12F12-TRI-27: the U4 record, rotation, lever arm, face and F.Cu fill branches seeded too)."""
        def board():
            s = Four()
            for ref, x in (('U4', 23), ('U5', 10), ('U99', 35)):
                f = s.part(ref, x, 40, [('A', 'IMU_CS' if ref == 'U4' else 'HG_CS' if ref == 'U99' else 'I2C1_SDA',
                                        (-2, 0), 'smd'), ('Z', 'GND', (2, 0), 'smd')])
                s.yard(f, x - 2, 38, x + 2, 42)
            return s
        data = {'imu': {'rotation': 0, 'lever_mm': 0}}
        s = board(); self.assert_rule(s, 'M-7', data=data)
        s.via(35, 40, 'GND'); self.assert_rule(s, 'M-7', False, data=data, want='M-7: via under U99')
        # D-R12-52: U5 (MS5607) has R10's pad-interior track ban again.
        s = board(); s.track((9.5, 39.5), (10.5, 39.5), 'I2C1_SCL', pcbnew.F_Cu)
        self.assert_rule(s, 'M-7', False, data=data, want='M-7: track inside U5 pad-ring interior')
        s = board()
        self.assert_rule(s, 'M-7', False, data={'imu': {'rotation': 0}},
                         want='M-7: U4 or its recorded rotation / lever arm missing')
        u4 = s.board.FindFootprintByReference('U4')
        u4.SetOrientationDegrees(90)
        self.assert_rule(s, 'M-7', False, data=data, want='M-7: U4 differs from its recorded top-side rotation')
        s = board(); s.board.FindFootprintByReference('U4').Move(s.P(0.2, 0))
        self.assert_rule(s, 'M-7', False, data=data, want='M-7: U4 differs from its recorded roll-axis lever arm')
        s = board(); u5 = s.board.FindFootprintByReference('U5'); u5.Flip(u5.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        self.assert_rule(s, 'M-7', False, data=data, want='M-7: U5 must be on F (D-R12-25)')
        s = board(); s.rect_fill('GND', (8, 38, 12, 42), pcbnew.F_Cu)
        self.assert_rule(s, 'M-7', False, data=data, want='M-7: fill under U5')

    def test_m8_short_edges(self):
        s = Four(); f = s.part('R1', 10, 10, [])
        s.yard(f, 9, 9, 11, 11); self.assert_rule(s, 'M-8', data={})
        f.Move(s.P(0, -8)); f.BuildCourtyardCaches(); self.assert_rule(s, 'M-8', False, data={})

    def test_k_copper_no_vippo(self):
        s = Four(); f = s.part('U401', 10, 10, [('11', 'SIGNAL', (0, 0), 'smd')])
        p = f.FindPadByNumber('11'); layers = p.GetLayerSet(); layers.AddLayer(pcbnew.F_Paste); p.SetLayerSet(layers)
        self.assert_rule(s, 'K-copper')
        s.via(10, 10, 'SIGNAL', d=.45); self.assert_rule(s, 'K-copper', False)

    def test_r12f12_tri27_k_copper_pour_debris(self):
        """R12F12-TRI-27: a GND fill piece with no via and one GND pad is R12 pour debris (r10.pour_debris in
        K-copper); with a via of its net in it, it passes."""
        s = Four(); s.part('R1', 10, 10, [('1', 'GND', (0, 0), 'smd')])
        s.rect_fill('GND', (9, 8, 11, 12), pcbnew.In1_Cu)
        self.assert_rule(s, 'K-copper', False, want='K-copper: pour debris: GND fill  on In1.Cu has a 8.000 mm^2 piece')
        s.via(10, 11.5, 'GND', d=.45)
        self.assert_rule(s, 'K-copper')

    def test_k_inner_mixed_layer(self):
        s = Four(); s.track((5, 5), (10, 5), 'GND', pcbnew.In1_Cu)
        t = s.track((5, 6), (10, 6), 'GPS_TX_WIRE', pcbnew.In2_Cu)
        self.assert_rule(s, 'K-inner')
        t.SetNet(s.net('SPI1_SCK')); self.assert_rule(s, 'K-inner', False, want='K-inner: SPI1_SCK track on In2.Cu')
        t.SetNet(s.net('GPS_TX_WIRE')); t.SetLayer(pcbnew.In1_Cu)
        self.assert_rule(s, 'K-inner', False, want='K-inner: GPS_TX_WIRE track on In1.Cu')
        # R12F12-TRI-27: a fire-only net on In2, and copper that is no track (a fill) on a net that is not real
        s = Four(); s.track((5, 6), (10, 6), 'PYRO1_OUT', pcbnew.In2_Cu)
        self.assert_rule(s, 'K-inner', False, want='K-inner: PYRO1_OUT track on In2.Cu')
        s = Four(); s.rect_fill('', (5, 5, 10, 10), pcbnew.In2_Cu)
        self.assert_rule(s, 'K-inner', False, want='K-inner: (no net) fill on In2.Cu on In2.Cu')

    def test_k_reference_all_signal_layers(self):
        for layer, plane, net in ((pcbnew.F_Cu, pcbnew.In1_Cu, 'GND'),
                                  (pcbnew.In2_Cu, pcbnew.In1_Cu, 'GND'),
                                  (pcbnew.B_Cu, pcbnew.In2_Cu, '3V3')):
            s = Four(); t = s.track((10, 10), (20, 10), 'GPS_TX_WIRE', layer, .1)
            s.rect_fill(net, (5, 5, 25, 15), plane)
            if layer == pcbnew.In2_Cu:
                self.assert_rule(s, 'K-reference', False)  # In1 alone cannot replace the nearer B reference.
                s.rect_fill('GND', (5, 5, 25, 15), pcbnew.B_Cu)
            self.assert_rule(s, 'K-reference')
            t.Move(s.P(0, 20)); self.assert_rule(s, 'K-reference', False)

    def test_k_region_one_plane(self):
        s = Four(); s.track((10, 10), (20, 10), 'USB_DP', pcbnew.B_Cu)
        s.rect_fill('3V3', (5, 5, 25, 15), pcbnew.In2_Cu)
        self.assert_rule(s, 'K-region')
        s.rect_fill('PORT_4V8', (15, 5, 25, 15), pcbnew.In2_Cu)
        self.assert_rule(s, 'K-region', False, want="K-region: USB_DP B.Cu run (10.00, 10.00) - (20.00, 10.00) lies over "
                         "In2 planes ['3V3', 'PORT_4V8']")
        s.rect_fill('USB_DP', (30, 5, 35, 15), pcbnew.In2_Cu)
        self.assert_rule(s, 'K-region', False, want='K-region: non-plane In2 fill USB_DP is not a reference region')

    def test_k_plane_split(self):
        s = Four(); s.rect_fill('3V3', (5, 5, 15, 15), pcbnew.In2_Cu)
        self.assert_rule(s, 'K-plane')
        s.rect_fill('3V3', (20, 5, 30, 15), pcbnew.In2_Cu)
        self.assert_rule(s, 'K-plane', False, want='K-plane: 3V3 on In2.Cu fills as 2 pieces; the 100.0 mm^2 piece at '
                         '(25.00, 10.00) has 0 link(s)')

    def test_advisory_tier(self):
        # D-R12-67A: stage C pass 1 reports K-reference / K-region / K-plane without failing; safety never relaxes.
        s = Four(); s.rect_fill('3V3', (5, 5, 15, 15), pcbnew.In2_Cu); s.rect_fill('3V3', (20, 5, 30, 15), pcbnew.In2_Cu)
        s.via(10, 30, 'PYRO1_OUT', d=.45); s.track((11, 28), (11, 32), 'SIGNAL', pcbnew.In2_Cu, .1)
        strict = s.run({'K-plane', 'S-8'})
        self.assertEqual(set(strict['failing']), {'K-plane', 'S-8'})
        rep = s.run({'K-plane', 'S-8'}, advisory=('K-plane',))
        self.assertFalse(rep['ok'])  # S-8 still fails the run
        self.assertEqual(rep['failing'], ['S-8'])
        self.assertEqual(rep['reported'], ['K-plane'])
        self.assertTrue(rep['advisory'] and all(i.startswith('K-plane: ') for i in rep['advisory']))
        self.assertFalse(any(i.startswith('K-plane') for i in rep['issues']))
        self.assertFalse(rep['rules']['K-plane']['ok'])
        only = s.run({'K-plane'}, advisory=('K-plane',))
        self.assertTrue(only['ok'], only['issues'])  # advisory findings alone pass
        for bad in (('S-8',), ('M-7',), ('W-1',), ('LC-1',), ('K-inner',), ('K-copper',), ('S-*',)):
            with self.subTest(advisory=bad), self.assertRaises(ValueError):
                s.run({'K-plane'}, advisory=bad)
        cli = subprocess.run([sys.executable, '-I', '-B', str(ROOT / 'tools/check_r12.py'), '--advisory', 'S-8'],
                             capture_output=True, text=True)
        self.assertNotEqual(cli.returncode, 0)
        self.assertIn('always fatal', cli.stderr)

    def test_k_plane_neck_floor(self):
        # D-R12-34 / -36: a 3V3 neck must be >= 1.0 mm; 1.4 mm passes, 0.6 mm fails.
        for width, ok in ((1.4, True), (.6, False)):
            s = Four()
            s.rect_fill('3V3', (5, 5, 15, 15), pcbnew.In2_Cu)
            s.rect_fill('3V3', (14.9, 10 - width / 2, 20.1, 10 + width / 2), pcbnew.In2_Cu)
            s.rect_fill('3V3', (20, 5, 30, 15), pcbnew.In2_Cu)
            s.via(10, 10, '3V3'); s.via(25, 10, '3V3')    # plane_necks judges pieces that hold a 3V3 landing
            s.fill()
            self.assert_rule(s, 'K-plane', ok, want=None if ok else 'only through a neck under 1.0 mm')

    def test_k_fill_saved_geometry(self):
        s = Four(); z = s.rect_fill('3V3', (5, 5, 20, 20), pcbnew.In2_Cu)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER); s.fill()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'm3.kicad_pcb'; pcbnew.SaveBoard(str(p), s.board)
            self.assert_rule(s, 'K-fill', path=p)
            poly = pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(pcbnew.In2_Cu)); poly.Move(s.P(1, 0))
            z.SetFilledPolysList(pcbnew.In2_Cu, poly); pcbnew.SaveBoard(str(p), s.board)
            self.assert_rule(s, 'K-fill', False, path=p)

    def test_k_legends_complete_and_wrong_sh_pin(self):
        s = Four()
        pins = dict(r12.TERMINAL_PINS)
        pins['J2'] = tuple(enumerate(r10.PORT_LEGENDS_R10['J2'], 1))
        labels = []
        for i, (ref, contacts) in enumerate(pins.items()):
            x, y = 40 + (i % 3) * 60, 30 + (i // 3) * 40
            f = s.part(ref, x, y, [(str(n), 'SIGNAL', (5 * j, 0), 'smd') for j, (n, _) in enumerate(contacts)])
            s.yard(f, x - 6, y - 5, x + 5 * (len(contacts) - 1) + 6, y + 5)
            f.Reference().SetPosition(s.P(x, y + 4)); f.Reference().SetTextSize(s.P(1, 1))
            f.Value().SetVisible(False)
            fab = pcbnew.PCB_TEXT(f); fab.SetText('${REFERENCE}'); fab.SetLayer(pcbnew.F_Fab)
            fab.SetTextSize(s.P(1, 1)); fab.SetTextThickness(mm(.15)); fab.SetPosition(s.P(x, y)); f.Add(fab)
            for j, (n, word) in enumerate(contacts):
                labels.append(s.text(f'{n}:{word}' if ref != 'J2' else f'J2 {n}:{word}', x + 5 * j, y + 2))
            for word, subject in r10.WORD_LEGENDS_R10.items():
                if subject == ref:
                    s.text(word, x + 5 * (len(contacts) - 1) / 2, y - 3)
        note = s.text(r10.SERVO_HARNESS_NOTE, 30, 150)
        s.text(r12.REVISION, 30, 160, pcbnew.B_SilkS)
        # R12F12-TRI-07: J1's polarity words on the top face, each beside its own contact (J1.1 at (jx, jy), J1.2 5 mm east)
        (jx, jy) = next((40 + (i % 3) * 60, 30 + (i // 3) * 40) for i, ref in enumerate(pins) if ref == 'J1')
        rep = self.assert_rule(s, 'K-legends', False)
        self.assertEqual(len([i for i in rep['issues'] if 'polarity legend' in i and 'exactly once' in i]), 2)
        plus, minus = s.text('BAT+', jx - 4.5, jy - 3.5), s.text('GND', jx + 9.5, jy - 3.5)
        self.assert_rule(s, 'K-legends')
        plus.SetText('GND'); minus.SetText('BAT+')                                  # swapped: each at the wrong contact
        rep = self.assert_rule(s, 'K-legends', False)
        self.assertEqual(len([i for i in rep['issues'] if 'is not nearer contact' in i]), 2, rep['issues'])
        plus.SetText('BAT+'); minus.SetText('GND')
        plus.SetLayer(pcbnew.B_SilkS)                                               # the top face is where the screws are
        self.assertTrue(any("'BAT+' must appear exactly once, on F.Silkscreen" in i
                            for i in self.assert_rule(s, 'K-legends', False)['issues']))
        plus.SetLayer(pcbnew.F_SilkS)
        extra = s.text('BAT-', jx + 9.5, jy - 5.5)                                  # no other free word is allowed
        self.assertTrue(any("'BAT-'" in i and 'allowed legend' in i for i in self.assert_rule(s, 'K-legends', False)['issues']))
        s.board.Remove(extra)
        self.assert_rule(s, 'K-legends')
        labels[0].SetText('1:WRONG'); self.assert_rule(s, 'K-legends', False)
        labels[0].SetText(f'{pins["J1"][0][0]}:{pins["J1"][0][1]}'); self.assert_rule(s, 'K-legends')
        # D-R12-81: an absent harness note is waived; a conflicting or duplicated one still fails; a contact legend
        # is never waived
        note.SetText('SERVO FROM HARNESS'); self.assert_rule(s, 'K-legends', False)
        s.board.Remove(note); self.assert_rule(s, 'K-legends')
        twice = [s.text(r10.SERVO_HARNESS_NOTE, 30, 150), s.text(r10.SERVO_HARNESS_NOTE, 90, 150)]
        self.assert_rule(s, 'K-legends', False)
        for t in twice:
            s.board.Remove(t)
        self.assert_rule(s, 'K-legends')
        s.board.Remove(labels[1]); self.assert_rule(s, 'K-legends', False)

    def test_every_pending_rule_is_registered(self):
        self.assertNotIn('K-legends', r12.STAGES['copper'])  # r12_build runs routing before stage-D post.
        self.assertEqual(r12.PENDING, ())
        self.assertEqual(set(r12.IMPLEMENTED), set(r12.PORTED))
        self.assertTrue(set(r12.IMPLEMENTED) <= set(r12.STAGES['full']))


if __name__ == '__main__':
    unittest.main()

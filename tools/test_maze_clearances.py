"""Native grid-routing regressions for the R6 exposed-pad and rule-area guards."""
from pathlib import Path
import sys
import unittest

try:
    import pcbnew
except ImportError:
    pcbnew = None
if pcbnew:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'm3_design'))
    import r5_maze as maze
    import r6_joints as joints
    import check_r6 as gate


@unittest.skipUnless(pcbnew, 'KiCad Python required')
class MazeClearances(unittest.TestCase):
    def setUp(self):
        self.margin = maze.MARGIN
        maze.MARGIN = .02
        self.board = pcbnew.BOARD()
        self.board.SetCopperLayerCount(4)
        for net in ('SIGNAL', 'OTHER', 'RAW_ACT'):
            self.board.Add(pcbnew.NETINFO_ITEM(self.board, net))
        for a, b in (((0, 0), (20, 0)), ((20, 0), (20, 20)),
                     ((20, 20), (0, 20)), ((0, 20), (0, 0))):
            edge = pcbnew.PCB_SHAPE(self.board)
            edge.SetLayer(pcbnew.Edge_Cuts); edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
            edge.SetStart(self.point(*a)); edge.SetEnd(self.point(*b)); self.board.Add(edge)

    def tearDown(self):
        maze.MARGIN = self.margin

    def point(self, x, y):
        return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))

    def pad(self, ref, net='OTHER', attr=None, position=(10, 10)):
        fp = pcbnew.FOOTPRINT(self.board); fp.SetReference(ref); self.board.Add(fp)
        pad = pcbnew.PAD(fp); pad.SetNumber('1'); pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        attr = pcbnew.PAD_ATTRIB_SMD if attr is None else attr
        pad.SetAttribute(attr); pad.SetSize(self.point(1.5, 1.5))
        layers = pcbnew.LSET.AllCuMask() if attr == pcbnew.PAD_ATTRIB_PTH else pcbnew.LSET()
        layers.AddLayer(pcbnew.F_Cu); layers.AddLayer(pcbnew.F_Mask); pad.SetLayerSet(layers)
        if attr == pcbnew.PAD_ATTRIB_PTH:
            pad.SetDrillSize(self.point(.8, .8))
        pad.SetNet(self.board.FindNet(net)); fp.Add(pad); pad.SetPosition(self.point(*position))
        return pad

    def grid(self, position, layer=pcbnew.F_Cu if pcbnew else 0, width=.2):
        grid = maze.Grid(self.board, 'SIGNAL', layer, (4, 4, 16, 16), width, position)
        i, j = grid.cell(*position)
        return bool(grid.blk[j * grid.nx + i])

    def route(self, start, end, width=.2):
        points = maze.maze(self.board, 'SIGNAL', pcbnew.F_Cu, start, end, width,
                           box=(4, 4, 16, 16))
        tracks = []
        for a, b in zip(points, points[1:]):
            track = pcbnew.PCB_TRACK(self.board); track.SetLayer(pcbnew.F_Cu)
            track.SetNet(self.board.FindNet('SIGNAL')); track.SetWidth(pcbnew.FromMM(width))
            track.SetStart(self.point(*a)); track.SetEnd(self.point(*b))
            self.board.Add(track); tracks.append(track)
        return tracks

    def assert_pad_guarded(self):
        issues, _ = gate.foreign_clearances(self.board, gate.copper_shapes(self.board))
        self.assertFalse(issues, issues)

    def test_testpad_guard_without_local_override(self):
        self.pad('TP1')
        self.assertTrue(self.grid((10, 11.7)))
        self.assertFalse(self.grid((10, 11.7), pcbnew.In2_Cu))
        self.route((5, 11.7), (15, 11.7))
        self.assert_pad_guarded()

    def test_raw_through_pad_guard_on_every_copper_layer(self):
        self.pad('J124', 'RAW_ACT', pcbnew.PAD_ATTRIB_PTH)
        for layer in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            self.assertTrue(self.grid((10, 11.1), layer))
        self.route((5, 11.1), (15, 11.1))
        self.assert_pad_guarded()

    def test_tag_connect_foreign_track_guard(self):
        pad = self.pad('J2', attr=pcbnew.PAD_ATTRIB_CONN)
        pad.SetSize(self.point(.7874, .7874))
        self.assertTrue(self.grid((10, 10.99)))
        self.assertFalse(self.grid((10, 11.1)))
        self.route((5, 10.99), (15, 10.99))
        self.assert_pad_guarded()

    def test_joint_bridge_keeps_tag_connect_foreign_clearance(self):
        pad = self.pad('J2', attr=pcbnew.PAD_ATTRIB_CONN)
        pad.SetSize(self.point(.7874, .7874))
        index = joints.index_copper(self.board)[pcbnew.F_Cu]
        for y, expected in ((10.99, False), (11.1, True)):
            points = [(pcbnew.FromMM(x), pcbnew.FromMM(y)) for x in (5, 15)]
            tracks = joints.candidate(self.board, 'SIGNAL', pcbnew.F_Cu, pcbnew.FromMM(.2), points)
            self.assertEqual(joints.clear(self.board, tracks, index, {}, []), expected)

    def test_foreign_vias_keep_testpad_clearance(self):
        self.pad('TP1')
        grid, blocked = maze._via_blocked(self.board, 'SIGNAL', (4, 4, 16, 16), (10, 11.8))
        i, j = grid.cell(10, 11.8)
        self.assertTrue(blocked[j * grid.nx + i])

    def test_edge_clearance_uses_milled_outline_not_drawing_stroke(self):
        for stroke in (.05, .1, .2):
            for edge in self.board.GetDrawings():
                edge.SetWidth(pcbnew.FromMM(stroke))
            # Copper 0.48 mm from the actual right edge must be blocked,
            # even though the drawing bounding box extends beyond that edge.
            for width in (.15, .5):
                for clearance, blocked in ((.48, True), (.52, False)):
                    point = (20 - width / 2 - clearance, 10)
                    grid = maze.Grid(self.board, 'SIGNAL', pcbnew.F_Cu,
                                     (18, 9, 20, 11), width, point)
                    i, j = grid.cell(*point)
                    self.assertEqual(bool(grid.blk[j * grid.nx + i]), blocked,
                                     (stroke, width, clearance))

    def test_same_net_conn_contact_rejects_via_in_both_placement_paths(self):
        pad = self.pad('J2', 'SIGNAL', pcbnew.PAD_ATTRIB_CONN)
        pad.SetSize(self.point(.7874, .7874))
        grid, blocked = maze._via_blocked(self.board, 'SIGNAL', (8, 8, 12, 12), (10, 10))
        i, j = grid.cell(10, 10)
        self.assertTrue(blocked[j * grid.nx + i])
        position = maze.via_spot(self.board, 'SIGNAL', (10, 10), (10, 10), r=1.3)
        via = pcbnew.PCB_VIA(self.board); via.SetPosition(self.point(*position))
        via.SetWidth(pcbnew.FromMM(.6)); via.SetDrill(pcbnew.FromMM(.3))
        self.assertFalse(pad.GetEffectiveShape(pcbnew.F_Cu).Collide(
            via.GetEffectiveShape(pcbnew.F_Cu), pcbnew.FromMM(.15) - 1))

    def keepout(self, footprint=False):
        owner = self.board
        if footprint:
            owner = pcbnew.FOOTPRINT(self.board); owner.SetReference('J2'); self.board.Add(owner)
        zone = pcbnew.ZONE(owner); zone.SetLayer(pcbnew.F_Cu)
        zone.SetIsRuleArea(True); zone.SetDoNotAllowTracks(True); zone.Outline().NewOutline()
        for point in ((8, 8), (12, 8), (12, 12), (8, 12)):
            zone.Outline().Append(self.point(*point))
        owner.Add(zone)
        return zone

    def test_track_radius_cannot_cross_footprint_rule_area(self):
        zone = self.keepout(footprint=True)
        self.assertTrue(self.grid((12.05, 10)))
        tracks = self.route((6, 7.95), (14, 7.95))
        self.assertTrue(all(not t.GetEffectiveShape().Collide(zone.Outline(), 0) for t in tracks))

    def test_diagonal_segment_cannot_cut_rule_area_corner(self):
        zone = self.keepout()
        tracks = self.route((13.1, 9), (11, 6.9), width=.15)
        self.assertTrue(all(not t.GetEffectiveShape().Collide(zone.Outline(), 0) for t in tracks))

    def test_validated_j2_outward_pad_escape_stays_available(self):
        zone = self.keepout(footprint=True)
        self.pad('J2_CONTACT', 'SIGNAL', pcbnew.PAD_ATTRIB_CONN, (12, 10))
        self.assertFalse(self.grid((12.215, 10)))
        tracks = self.route((12.215, 10), (14.215, 10))
        self.assertTrue(all(not t.GetEffectiveShape().Collide(zone.Outline(), 0) for t in tracks))


if __name__ == '__main__':
    unittest.main()

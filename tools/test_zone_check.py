"""Pure-Python regressions for R12 route-finding coordinates."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'm3_design/r12_aid/zones'))
import zone_check
import zone_guard
import json


class RouteZones(unittest.TestCase):
    def test_route_check_xy_takes_precedence_over_at(self):
        self.assertEqual(zone_check.route_zones(dict(x=10, y=10, at='free')), ['W1'])
        self.assertEqual(zone_check.route_zones(dict(x=10, y=10, at=[-10, -10])), ['W1'])

    def test_legacy_coordinates_and_noncoordinate_at(self):
        for finding in (dict(at=[10, 10]), dict(at='free', xy=[10, 10]),
                        dict(at=['free', 10], pos=[10, 10]), dict(pos=dict(x=10, y=10)),
                        dict(x=None, y=10, at='free', xy=[10, 10])):
            with self.subTest(finding=finding):
                self.assertEqual(zone_check.route_zones(finding), ['W1'])

    def test_missing_and_invalid_coordinates_are_unknown(self):
        for finding in ({}, dict(at='free'), dict(xy=[10]), dict(at=['free', 'label']),
                        dict(x=float('nan'), y=10), dict(x=True, y=10)):
            with self.subTest(finding=finding):
                self.assertEqual(zone_check.route_zones(finding), ['?'])
        self.assertEqual(zone_check.route_zones(dict(x=-10, y=-10)), ['outside'])


class ZoneGuardOutline(unittest.TestCase):
    """R12F4-TRI-08: zone polygons and fragment points stay inside the board's Edge.Cuts outline."""

    def setUp(self):
        self.Z = json.loads((Path(zone_guard.__file__).with_name('zones.json')).read_text())
        self.box = zone_guard.outline()

    def test_outline_is_the_83_mm_board(self):
        self.assertEqual(self.box, (0.0, 0.0, 46.0, 83.0))      # R12F10-TRI-16: 46 x 83 mm (was 85, R12F9 lane L)

    def test_w5_fragment_is_inside_its_zone(self):
        """R12F8-TRI-17: every W5 row lies inside W5 (zone_guard reported 31 rows outside after the 88 mm shrink)."""
        frag = Path(zone_guard.__file__).with_name('r12_routes_W5.tsv').read_text().splitlines(True)
        self.assertEqual(zone_guard.check(self.Z, 'W5', frag, self.box), [])

    def test_rows_outside_their_zone_are_the_recorded_ones(self):
        """R12F10-TRI-15: each fragment's rows outside its own zone are exactly the recorded hand-offs (W1 6, W3 9: the
        BAT_FAULT_N / GND / ARM1_SENSE / ACT_EN_MCU / BUZZ_DRV lanes crossing into W1 / W4 / W5; W2, W4, W5 none), so a
        fragment edit that leaves its zone fails here (lane C's C460 / C461 rows sat in W5 outside it, round 10)."""
        want = {'W1': 6, 'W2': 0, 'W3': 9, 'W4': 0, 'W5': 0}
        for zone, n in want.items():
            with self.subTest(zone=zone):
                frag = Path(zone_guard.__file__).with_name(f'r12_routes_{zone}.tsv').read_text().splitlines(True)
                self.assertEqual(len(zone_guard.check(self.Z, zone, frag, self.box)), n)

    def test_every_zone_polygon_is_on_the_board(self):
        for zone in self.Z['zones']:
            with self.subTest(zone=zone):
                self.assertEqual(zone_guard.polygon_issues(self.Z, zone, self.box), [])

    def test_off_board_fragment_is_refused(self):
        rows = ['track\tGND\tF\t0.2\t23\t95\t24\t95\n', 'via\tGND\t-\t0.45\t5\t95\n',
                'track\tGND\tF\t0.2\t5\t80\t6\t80\n']
        self.assertEqual(sorted({n for n, _ in zone_guard.check(self.Z, 'W5', rows, self.box)}), [1, 2])

    def test_a_row_is_counted_once(self):
        """R12F6-TRI-17: a track with both ends outside the zone is one row, not two."""
        rows = ['track\tGND\tF\t0.2\t23\t95\t24\t95\n', 'track\tGND\tF\t0.2\t5\t80\t6\t80\n']
        self.assertEqual(zone_guard.check(self.Z, 'W5', rows, self.box), [(1, rows[0].strip())])

    def test_polygon_beyond_the_outline_is_reported(self):
        Z = json.loads(json.dumps(self.Z))
        Z['zones']['W5']['polygon'][-2:] = [[46, 100], [0, 100]]
        self.assertEqual(zone_guard.polygon_issues(Z, 'W5', self.box), [(46, 100), (0, 100)])


if __name__ == '__main__':
    unittest.main()

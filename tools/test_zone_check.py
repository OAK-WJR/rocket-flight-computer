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

    def test_outline_is_the_90_mm_board(self):
        self.assertEqual(self.box, (0.0, 0.0, 46.0, 90.0))

    def test_every_zone_polygon_is_on_the_board(self):
        for zone in self.Z['zones']:
            with self.subTest(zone=zone):
                self.assertEqual(zone_guard.polygon_issues(self.Z, zone, self.box), [])

    def test_off_board_fragment_is_refused(self):
        rows = ['track\tGND\tF\t0.2\t23\t95\t24\t95\n', 'via\tGND\t-\t0.45\t5\t95\n',
                'track\tGND\tF\t0.2\t5\t80\t6\t80\n']
        self.assertEqual(sorted({n for n, _ in zone_guard.check(self.Z, 'W5', rows, self.box)}), [1, 2])

    def test_polygon_beyond_the_outline_is_reported(self):
        Z = json.loads(json.dumps(self.Z))
        Z['zones']['W5']['polygon'][-2:] = [[46, 100], [0, 100]]
        self.assertEqual(zone_guard.polygon_issues(Z, 'W5', self.box), [(46, 100), (0, 100)])


if __name__ == '__main__':
    unittest.main()

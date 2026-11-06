"""Pure-Python regressions for R12 route-finding coordinates."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'm3_design/r12_aid/zones'))
import zone_check


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


if __name__ == '__main__':
    unittest.main()

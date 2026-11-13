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

    def test_outline_is_the_86_85_mm_board(self):
        # D-R12-174: 46 x 86.85 mm, 3.85 mm added at the aft end for J1's KF301 terminal (was 83, R12F10-TRI-16)
        self.assertEqual(self.box, (0.0, 0.0, 46.0, 86.85))

    def test_w5_fragment_is_inside_its_zone(self):
        """R12F8-TRI-17: every W5 row lies inside W5 (zone_guard reported 31 rows outside after the 88 mm shrink)."""
        frag = Path(zone_guard.__file__).with_name('r12_routes_W5.tsv').read_text().splitlines(True)
        self.assertEqual(zone_guard.check(self.Z, 'W5', frag, self.box), [])

    # R12F10-TRI-15 / R12F12-TRI-28: the recorded hand-offs, row by row (kind, net, layer, width, end points)
    HANDOFFS = {
        'W1': ('track GND F 0.3 13.1 52.75 13.7 52.75', 'via GND - 0.45 13.6 53.95', 'via GND - 0.45 13.6 51.35',
               'via GND - 0.45 13.7 52.75', 'track PYRO1_CONT F 0.1 12.2 53.95 12.8 54.55',
               'track PYRO1_GATE_N F 0.1 18.7 50.65 16.6 48.55'),
        'W2': ('track GND F 0.3 40.1 56.05 39.7 55.65',),
        'W3': ('track BAT_FAULT_N F 0.1 20.2 49.85 19.3 48.95', 'via BAT_FAULT_N - 0.45 19.3 48.95',
               'track BAT_FAULT_N B 0.2 19.3 48.95 18.15 47.8', 'track GND F 0.2 26.6 48.61 25.99 48.61',
               'track GND F 0.2 25.99 48.61 25.75 48.85', 'track ARM1_SENSE B 0.2 13 59.85 13 44.6',
               'track ACT_EN_MCU B 0.1 16.4 56.875 16.4 49.75', 'track ACT_EN_MCU B 0.1 16.4 49.75 17.1 49.05',
               'track BUZZ_DRV B 0.2 12.3 65.15 11.2 64.05'),
        'W4': (),
        'W5': (),
    }

    def test_rows_outside_their_zone_are_the_recorded_ones(self):
        """R12F10-TRI-15 / R12F12-TRI-28: each fragment's rows outside its own zone are exactly the recorded hand-offs,
        compared row by row (a count alone passes a row swapped for another): in W1 the PC0 bank's GND link and vias, a
        PYRO1_CONT and a PYRO1_GATE_N track; in W3 the BAT_FAULT_N / GND / ARM1_SENSE / ACT_EN_MCU / BUZZ_DRV lanes
        crossing into W1 / W4 / W5; in W2 since R12F12-TRI-02 the F stub from U3.4's first GND via (in W3) to its second
        (in W2); W4, W5 none. A fragment edit that leaves its zone fails here (lane C's C460 / C461 rows sat in W5
        outside it, round 10), and so does a recorded hand-off moved or replaced."""
        self.assertEqual(sorted(self.HANDOFFS), sorted(self.Z['zones']))
        for zone, want in self.HANDOFFS.items():
            with self.subTest(zone=zone):
                frag = Path(zone_guard.__file__).with_name(f'r12_routes_{zone}.tsv').read_text().splitlines(True)
                rows = [' '.join(row.split('\t')).strip() for _, row in zone_guard.check(self.Z, zone, frag, self.box)]
                self.assertEqual(sorted(rows), sorted(want))

    def test_handoff_comparison_sees_a_swapped_row(self):
        """The row comparison fails a hand-off replaced by another outside row of the same count (a count would not)."""
        frag = Path(zone_guard.__file__).with_name('r12_routes_W2.tsv').read_text().splitlines(True)
        moved = [r.replace('\t39.7\t55.65', '\t39.6\t55.55') for r in frag]
        rows = [' '.join(row.split('\t')).strip() for _, row in zone_guard.check(self.Z, 'W2', moved, self.box)]
        self.assertEqual(len(rows), len(self.HANDOFFS['W2']))
        self.assertNotEqual(sorted(rows), sorted(self.HANDOFFS['W2']))

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

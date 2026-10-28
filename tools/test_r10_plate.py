"""R10 masses must explicitly replace changed R9 bodies and include mated plugs."""
import json
from pathlib import Path
import unittest

try:
    import plate_model as plate
except ImportError:
    plate = None


@unittest.skipUnless(plate, 'NumPy required')
class PlateProfile(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((Path(__file__).resolve().parents[1] /
            'm3_design/assembly_review/sources/r10_design/masses.json').read_text())
        refs = ['J1', 'J121', 'J122', 'C84', 'LS120', 'J3', 'J9', 'J123', 'J400', 'J410', 'J420',
                'J9 mated', 'J123 mated', 'J400 mated', 'J410 mated', 'J420 mated', 'J122 mated']
        self.fit = dict(profile='r10', outline=[0, 0, 46, 84], supports=[[4,4], [42,4], [4,80], [42,80], [42,42]],
                        rows=[(1, ref, 'F', [20, 40, 22, 42, 0, 2]) for ref in refs])

    def test_changed_body_and_plug_masses_used(self):
        p, masses, total = plate.build(self.fit, 5, False, 'r10_mated', 'r10', self.spec)
        self.assertEqual(masses['J1'][0], self.spec['masses_g']['J1'] / 1000)
        self.assertIn('J410 mated', masses)
        self.assertNotIn('U30', masses)
        self.assertNotIn('J30', masses)
        self.assertGreater(total, sum(v[0] for v in masses.values()))

    def test_r10_refuses_missing_mass_basis_or_support(self):
        for field in ('basis', 'masses_g'):
            mutant = dict(self.spec); mutant.pop(field)
            with self.assertRaises(ValueError):
                plate.build(self.fit, 5, False, 'r10_mated', 'r10', mutant)
        mutant = dict(self.fit, supports=self.fit['supports'][:-1])
        with self.assertRaises(ValueError):
            plate.build(mutant, 5, False, 'r10_mated', 'r10', self.spec)
        mutant = dict(self.spec, masses_g=dict(self.spec['masses_g']))
        mutant['masses_g'].pop('J410 mated')
        with self.assertRaises(ValueError):
            plate.build(self.fit, 5, False, 'r10_mated', 'r10', mutant)

    def test_r9_default_keeps_legacy_mass_policy(self):
        fit = dict(self.fit, profile='r9')
        _, masses, _ = plate.build(fit, 5, False, 'jacks_only')
        self.assertEqual(masses['J1'][0], plate.LUMPED['J1'] / 1000)
        self.assertNotIn('J410 mated', masses)


if __name__ == '__main__':
    unittest.main()

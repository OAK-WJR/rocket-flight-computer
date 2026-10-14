"""Purchase quantities and unavailable supplier evidence must not produce a false release pass."""
import csv
import datetime
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import fab_manifest
import jlc_cost
import jlc_stock
import check_procurement


class ProcurementValidation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.bom([('C100', 'R1,R2'), ('C100', 'R3')])
        (self.folder / 'm3_cpl_jlc.csv').write_text('Designator,Layer\nR1,Top\nR2,Bottom\n')
        self.item = dict(stockCount=100, minPurchaseNum=1, componentLibraryType='expand',
            componentPrices=[dict(startNumber=1, endNumber=9, productPrice=3),
                             dict(startNumber=10, endNumber=-1, productPrice=2)])

    def bom(self, rows, owner=False):
        path = self.folder / ('m3_bom_owner.csv' if owner else 'm3_bom_jlc.csv')
        with path.open('w', newline='') as output:
            writer = csv.writer(output)
            writer.writerow(['LCSC Part #', 'Designator', 'Qty', 'Assembly'])
            for code, refs in rows:
                writer.writerow([code, refs, len(refs.split(',')), 'owner' if owner else 'SMT'])

    def parts(self):
        return jlc_stock.read_bom(self.folder)

    def test_shared_code_stock_uses_total_demand(self):
        fetch = Mock(return_value=dict(self.item, stockCount=10))
        report = jlc_stock.stock_report(self.parts(), 5, fetch)
        self.assertFalse(report['ok'])
        self.assertEqual(report['lines'][0]['order_qty'], 15)
        fetch.assert_called_once_with('C100')

    def test_shared_code_price_break_and_moq_are_applied_once(self):
        fetch = Mock(return_value=dict(self.item, minPurchaseNum=20))
        report = jlc_cost.cost_report(self.parts(), 5, 'standard', 2, fetch=fetch)
        self.assertTrue(report['ok'])
        self.assertEqual(report['parts_usd_per_board'], 6)
        self.assertEqual(report['order_usd_per_board_with_min_purchase'], 8)
        self.assertEqual(report['charged_codes'], 1)
        self.assertEqual(report['total_usd_per_board'], 6.31)
        fetch.assert_called_once_with('C100')

    def test_owner_and_assembled_same_code_share_purchase_and_single_fee(self):
        self.bom([('C100', 'R4'), ('C200', 'R5')], owner=True)
        report = jlc_cost.cost_report(self.parts(), 5, 'standard', 1, fetch=lambda _: self.item)
        self.assertEqual(report['charged_codes'], 1)
        self.assertEqual(report['extended_codes'], ['C100'])
        part = next(line for line in report['lines'] if line['lcsc'] == 'C100')
        self.assertEqual(part['order_qty'], 20)
        self.assertEqual(part['jlc_qty_per_board'], 3)
        self.assertEqual(part['owner_qty_per_board'], 1)

    def test_unknown_stock_invalid_counts_and_missing_prices_fail(self):
        for stock in (None, 'unknown', -1, 4.5, True):
            with self.subTest(stock=stock):
                self.assertFalse(jlc_stock.stock_report(self.parts(), 5,
                    lambda _: dict(self.item, stockCount=stock))['ok'])
        for changes in ({'componentPrices': []}, {'componentLibraryType': None},
                        {'minPurchaseNum': 'unknown'}):
            with self.subTest(changes=changes):
                self.assertFalse(jlc_cost.cost_report(self.parts(), 5, 'standard', 1,
                    fetch=lambda _: dict(self.item, **changes))['ok'])

    def test_price_without_matching_quantity_break_is_not_guessed(self):
        self.assertIsNone(jlc_cost.unit_price(dict(componentPrices=[
            dict(startNumber=100, endNumber=-1, productPrice=0.01)]), 15))

    def test_economic_two_sides_fails_before_supplier_query(self):
        fetch = Mock()
        with self.assertRaisesRegex(ValueError, 'one side only'):
            jlc_cost.cost_report(self.parts(), 5, 'economic', 2, fetch=fetch)
        fetch.assert_not_called()

    def test_duplicate_designator_is_not_double_purchased(self):
        self.bom([('C100', 'R1'), ('C200', 'R1')])
        with self.assertRaisesRegex(ValueError, 'duplicate BOM'):
            self.parts()

    def test_cli_shortage_returns_failure_and_binds_bom(self):
        with patch.object(jlc_stock, 'lookup', return_value={}), patch.object(jlc_stock.time, 'sleep'), \
                patch('sys.argv', ['jlc_stock.py', '--fab', str(self.folder)]):
            self.assertEqual(jlc_stock.main(), 1)
        report = json.loads((self.folder / 'stock_check.json').read_text())
        self.assertFalse(report['ok'])
        digest = hashlib.sha256((self.folder / 'm3_bom_jlc.csv').read_bytes()).hexdigest()
        self.assertEqual(report['inputs_sha256']['m3_bom_jlc.csv'], digest)

    def test_bom_change_during_lookup_cannot_leave_valid_report(self):
        output = self.folder / 'stock_check.json'
        output.write_text('{"ok": true}')
        def change(_):
            self.bom([('C100', 'R1,R2,R3,R4')])
            return self.item
        with patch.object(jlc_stock, 'lookup', side_effect=change), patch.object(jlc_stock.time, 'sleep'), \
                patch('sys.argv', ['jlc_stock.py', '--fab', str(self.folder)]):
            with self.assertRaises(SystemExit) as error:
                jlc_stock.main()
        self.assertEqual(error.exception.code, 1)
        self.assertFalse(output.exists())

    def test_cost_cli_binds_cpl_and_both_boms(self):
        self.bom([('C200', 'C1')], owner=True)
        with patch.object(jlc_cost, 'lookup', return_value=self.item), patch.object(jlc_cost.time, 'sleep'), \
                patch('sys.argv', ['jlc_cost.py', '--fab', str(self.folder)]):
            self.assertEqual(jlc_cost.main(), 0)
        report = json.loads((self.folder / 'cost_check.json').read_text())
        self.assertEqual(set(report['inputs_sha256']),
                         {'m3_bom_jlc.csv', 'm3_bom_owner.csv', 'm3_cpl_jlc.csv'})
        self.assertEqual(report['targets'], {'max_total': 84.41, 'max_extended': 48})

    def test_supplier_snapshot_preserves_identity_and_expiry(self):
        now = datetime.datetime(2026, 10, 13, 12, tzinfo=datetime.timezone.utc)
        path = self.folder / 'supplier.json'
        data = dict(source=jlc_stock.API, checked_utc=now.isoformat(),
                    parts={'C100': dict(self.item, componentCode='C100')})
        path.write_text(json.dumps(data))
        self.assertEqual(jlc_stock.supplier_snapshot(path, now)['parts']['C100']['stockCount'], 100)
        for timestamp in ('2026-10-11T12:00:00+00:00', '2026-10-14T12:00:00+00:00',
                          '2026-10-13T12:00:00'):
            path.write_text(json.dumps(dict(data, checked_utc=timestamp)))
            with self.subTest(timestamp=timestamp), self.assertRaises(ValueError):
                jlc_stock.supplier_snapshot(path, now)
        data['parts']['C100']['componentCode'] = 'C999'
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'exact supplier identity'):
            jlc_stock.supplier_snapshot(path, now)

    def test_report_verifier_rejects_stale_bom_and_relaxed_targets(self):
        with patch.object(jlc_cost, 'lookup', return_value=self.item), patch.object(jlc_cost.time, 'sleep'), \
                patch('sys.argv', ['jlc_cost.py', '--fab', str(self.folder)]):
            self.assertEqual(jlc_cost.main(), 0)
        check_procurement.verify(self.folder, cost_only=True)
        path = self.folder / 'cost_check.json'
        original = json.loads(path.read_text())
        for change in ({'supplier_checked_utc': '2020-01-01T00:00:00Z'},
                       {'targets': {'max_total': 100, 'max_extended': 60}}, {'ok': False}):
            path.write_text(json.dumps(dict(original, **change)))
            with self.subTest(change=change), self.assertRaises(ValueError):
                check_procurement.verify(self.folder, cost_only=True)
        path.write_text(json.dumps(original))
        self.bom([('C100', 'R1,R2,R3,R4')])
        with self.assertRaisesRegex(ValueError, 'BOM/CPL changed'):
            check_procurement.verify(self.folder, cost_only=True)

    def test_final_verifier_rejects_current_pricing_for_old_cad_export(self):
        board = self.folder / 'm3.kicad_pcb'
        board.write_text('CAD revision A')
        for name in ('m3.kicad_pro', 'm3.kicad_dru', 'fp-lib-table', 'sym-lib-table',
                     'm3_gerber.zip', 'm3_assembly_top.pdf', 'm3_assembly_bottom.pdf'):
            (self.folder / name).write_text('fixture ' + name)
        fab_manifest.write_manifest(board, self.folder, fab_manifest.input_hashes(board))
        with patch.object(jlc_cost, 'lookup', return_value=self.item), patch.object(jlc_cost.time, 'sleep'), \
                patch('sys.argv', ['jlc_cost.py', '--fab', str(self.folder)]):
            self.assertEqual(jlc_cost.main(), 0)
        with patch.object(jlc_stock, 'lookup', return_value=self.item), patch.object(jlc_stock.time, 'sleep'), \
                patch('sys.argv', ['jlc_stock.py', '--fab', str(self.folder)]):
            self.assertEqual(jlc_stock.main(), 0)
        check_procurement.verify(self.folder, board=board)
        cost_path = self.folder / 'cost_check.json'
        original = json.loads(cost_path.read_text())
        with patch.object(jlc_cost, 'lookup', return_value=self.item), patch.object(jlc_cost.time, 'sleep'), \
                patch('sys.argv', ['jlc_cost.py', '--fab', str(self.folder), '--fee', '0']):
            self.assertEqual(jlc_cost.main(), 0)
        check_procurement.verify(self.folder, cost_only=True)
        with self.assertRaisesRegex(ValueError, 'nonstandard feeder fee'):
            check_procurement.verify(self.folder, board=board)
        cost_path.write_text(json.dumps(original))
        board.write_text('CAD revision B with changed components and placement')
        # The old exported BOM still has valid fresh prices, but is not current CAD evidence.
        check_procurement.verify(self.folder, cost_only=True)
        with self.assertRaisesRegex(ValueError, 'current CAD/export inputs'):
            check_procurement.verify(self.folder, board=board)

    def test_final_verifier_rejects_stock_for_smaller_order(self):
        with patch.object(jlc_cost, 'lookup', return_value=self.item), patch.object(jlc_cost.time, 'sleep'), \
                patch('sys.argv', ['jlc_cost.py', '--fab', str(self.folder), '--boards', '5']):
            self.assertEqual(jlc_cost.main(), 0)
        stock = dict(self.item, stockCount=4)
        with patch.object(jlc_stock, 'lookup', return_value=stock), patch.object(jlc_stock.time, 'sleep'), \
                patch('sys.argv', ['jlc_stock.py', '--fab', str(self.folder), '--boards', '1']):
            self.assertEqual(jlc_stock.main(), 0)
        self.assertFalse(jlc_stock.stock_report(self.parts(), 5, lambda _: stock)['ok'])
        with patch.object(check_procurement, 'verify_manifest'), \
                self.assertRaisesRegex(ValueError, 'quantity differs'):
            check_procurement.verify(self.folder)

    def test_verifier_rejects_invalid_order_quantities(self):
        for module in (jlc_cost, jlc_stock):
            with patch.object(module, 'lookup', return_value=self.item), patch.object(module.time, 'sleep'), \
                    patch('sys.argv', [module.__name__ + '.py', '--fab', str(self.folder)]):
                self.assertEqual(module.main(), 0)
        for name in ('cost_check.json', 'stock_check.json'):
            path = self.folder / name
            original = json.loads(path.read_text())
            for boards in (None, 0, -1, True, 1.5, '5'):
                path.write_text(json.dumps(dict(original, boards=boards)))
                with self.subTest(report=name, boards=boards), \
                        patch.object(check_procurement, 'verify_manifest'), \
                        self.assertRaisesRegex(ValueError, 'positive integer'):
                    check_procurement.verify(self.folder)
            path.write_text(json.dumps(original))


if __name__ == '__main__':
    unittest.main()

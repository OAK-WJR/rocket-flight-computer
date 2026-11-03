"""Patch-version portability must not hide netlist edits."""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'm3_design'))
from r10_sch_check import netlist_comparison_bytes as canonical

XML = b'''<export><design><source>m3.kicad_sch</source><tool>Eeschema 10.0.7</tool></design>
<components><comp ref="R1"><value>10k</value><property name="LCSC" value="C25744"/>
<property name="Sheetname" value="m3"/><sheetpath names="/" tstamps="/"/></comp>
<comp ref="R2"><property name="Sheetname" value="m3"/><sheetpath names="/sub/" tstamps="/id/"/></comp></components>
<nets><net name="3V3"><node ref="R1" pin="1"/></net></nets></export>'''


class NetlistPortability(unittest.TestCase):
    def test_supported_exporter_metadata(self):
        old = XML.replace(b'10.0.7', b'10.0.6')
        self.assertEqual(canonical(XML), canonical(old))

    def test_value_edit(self):
        self.assertNotEqual(canonical(XML), canonical(XML.replace(b'10k', b'1k')))

    def test_supplier_edit(self):
        self.assertNotEqual(canonical(XML), canonical(XML.replace(b'C25744', b'C00000')))

    def test_pin_edit(self):
        self.assertNotEqual(canonical(XML), canonical(XML.replace(b'pin="1"', b'pin="2"')))

    def test_net_edit(self):
        self.assertNotEqual(canonical(XML), canonical(XML.replace(b'3V3', b'GND')))

    def test_child_sheet_is_not_root_alias(self):
        self.assertNotEqual(canonical(XML), canonical(XML.replace(b'<comp ref="R2"><property name="Sheetname" value="m3"', b'<comp ref="R2"><property name="Sheetname" value="Root"')))

    def test_different_minor_version_not_normalized(self):
        self.assertNotEqual(canonical(XML), canonical(XML.replace(b'10.0.7', b'10.1.0')))

    def test_unknown_root_name_preserved(self):
        self.assertNotEqual(canonical(XML), canonical(XML.replace(b'value="m3"', b'value="Other"', 1)))

    def test_root_alias_is_still_compared(self):
        self.assertNotEqual(canonical(XML), canonical(XML.replace(b'value="m3"', b'value="Root"', 1)))

    def test_saved_native_exports_only_metadata(self):
        """The saved 216-component export is compared by the full board gate."""
        path = Path(__file__).resolve().parents[1] / 'm3_design/assembly_review/schematic.net.xml'
        data = path.read_bytes()
        exporter = re.search(rb'<tool>(Eeschema 10\.0\.\d+)</tool>', data)
        self.assertIsNotNone(exporter)
        alternate = b'Eeschema 10.0.6' if exporter[1] != b'Eeschema 10.0.6' else b'Eeschema 10.0.7'
        changed = data[:exporter.start(1)] + alternate + data[exporter.end(1):]
        self.assertNotEqual(data, changed)
        self.assertEqual(canonical(data), canonical(changed))


if __name__ == '__main__':
    unittest.main()

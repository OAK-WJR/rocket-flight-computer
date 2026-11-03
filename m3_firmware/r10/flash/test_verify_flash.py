"""Source mutations must not silently rebind an old firmware pin/part map."""
import copy
import csv
import io
from pathlib import Path
import unittest
import json
import xml.etree.ElementTree as ET
from verify_flash import contract,verify,verify_native_sources,NETLIST,PIN_TABLE

class FlashBinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        cls.root=Path(os.environ.get('R10_REPOSITORY',str(Path(__file__).resolve().parents[3])))
    def setUp(self):
        self.tree=ET.fromstring((self.root/NETLIST).read_bytes())
        self.rows=list(csv.DictReader(io.StringIO((self.root/PIN_TABLE).read_text()),delimiter='\t'))
    def reject(self):
        with self.assertRaises(ValueError):contract(self.tree,self.rows)
    def test_current_sources(self):
        self.assertEqual(verify(self.root),{'endpoints':16,'pins':6,'fitted_device':'W25Q128JVSIQ'})
    def test_part_not_silently_substituted(self):
        self.tree.find("./components/comp[@ref='U3']/fields/field[@name='Manufacturer Part']").text='W25Q128JVSIQG'
        self.reject()
    def test_wrong_supply(self):
        n=self.tree.find("./nets/net[@name='3V3']");node=n.find("node[@ref='U3']");n.remove(node)
        self.tree.find("./nets/net[@name='3V3A']").append(node);self.reject()
    def test_pullup_missing(self):
        n=self.tree.find("./nets/net[@name='QSPI_NCS']");n.remove(n.find("node[@ref='R10']"));self.reject()
    def test_pullup_changed(self):
        self.tree.find("./components/comp[@ref='R10']/value").text='100k';self.reject()
    def test_pin_swapped(self):
        self.tree.find("./nets/net[@name='QSPI_IO2']/node[@ref='U1']").set('pin','2');self.reject()
    def test_pinfunction_changed(self):
        self.tree.find("./nets/net[@name='QSPI_IO3']/node[@ref='U3']").set('pinfunction','RESET');self.reject()
    def test_bus_fanout_changed(self):
        ET.SubElement(self.tree.find("./nets/net[@name='QSPI_IO0']"),'node',ref='J99',pin='1');self.reject()
    def test_endpoint_duplicated(self):
        n=self.tree.find("./nets/net[@name='QSPI_CLK']");n.append(copy.deepcopy(n.find("node[@ref='U3']")));self.reject()
    def test_part_field_duplicated(self):
        n=self.tree.find("./components/comp[@ref='U3']/fields");n.append(copy.deepcopy(n.find("field[@name='LCSC']")));self.reject()
    def test_alternate_function_wrong(self):
        next(row for row in self.rows if row['pin']=='92')['mode_af']='AF9 QUADSPI_BK1_NCS';self.reject()
    def test_chip_select_initial_high_removed(self):
        next(row for row in self.rows if row['pin']=='92')['reset_contract']='unset';self.reject()
    def test_pin_row_duplicated(self):
        self.rows.append(copy.deepcopy(next(row for row in self.rows if row['pin']=='92')));self.reject()
    def test_pinned_register_reference_cannot_be_omitted(self):
        p=json.loads(Path(__file__).with_name('provenance.json').read_text());p['pinned_sources'].popitem()
        with self.assertRaises(ValueError):verify_native_sources(self.root,p)
    def test_pinned_register_reference_cannot_be_replaced(self):
        p=json.loads(Path(__file__).with_name('provenance.json').read_text())
        p['pinned_sources'][next(iter(p['pinned_sources']))]='0'*64
        with self.assertRaises(ValueError):verify_native_sources(self.root,p)
    def test_pinned_schema_required(self):
        p=json.loads(Path(__file__).with_name('provenance.json').read_text());p['schema']='unreviewed'
        with self.assertRaises(ValueError):verify_native_sources(self.root,p)

if __name__=='__main__':unittest.main(verbosity=2)

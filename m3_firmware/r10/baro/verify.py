"""Bind the portable MS5611 logic to native R10 source-part and I2C endpoints."""
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
NETLIST="m3_design/assembly_review/schematic.net.xml"
NET_SHA="535a8fdfe96c3a771a901db2bb9d2cd1a6674b001dfe1e18aa7d600e3aea7e9a"
PIN_TABLE="m3_design/assembly_review/sources/r10_design/pin_table.tsv"
PIN_SHA="b94133e61d553f5febb07c7c97977cd8b124634c6c19d0a2ce5b7fead304564a"
def sensor_contract(tree):
    part=tree.find("./components/comp[@ref='U5']")
    if part is None or part.findtext("value")!="MS561101BA03":
        raise ValueError("U5 fitted barometer changed")
    fields={f.get("name"):f.text for f in part.findall('./fields/field')}
    if fields.get("Manufacturer Part")!="MS561101BA03-50" or fields.get("LCSC")!="C15639":
        raise ValueError("U5 source part changed")
    expected={tuple(p.split('.')):net for net,pins in {
        "3V3A":["U5.1","U5.2"],"3V3":["R12.2","R13.2"],
        "GND":["U5.3","U5.4","U5.5","R64.2"],
        "BARO_SDO":["U5.6","R64.1"],
        "I2C1_SCL":["U1.95","U5.8","R12.1"],
        "I2C1_SDA":["U1.96","U5.7","R13.1"]}.items() for p in pins}
    actual={}
    for net in tree.findall('./nets/net'):
        for node in net.findall('node'):
            key=(node.get('ref'),node.get('pin'))
            if key in expected:
                if key in actual:raise ValueError("Duplicate barometer endpoint")
                actual[key]=net.get('name')
    if actual!=expected:raise ValueError("Native R10 barometer endpoint changed")
    return actual
def verify(root=ROOT):
    for name,expected in ((NETLIST,NET_SHA),(PIN_TABLE,PIN_SHA)):
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise ValueError("Reviewed R10 input changed: "+name)
    sensor_contract(ET.fromstring((root/NETLIST).read_bytes()))
    return True
if __name__=="__main__":
    verify();print("R10 barometer source and 16 endpoints verified; no hardware tested")

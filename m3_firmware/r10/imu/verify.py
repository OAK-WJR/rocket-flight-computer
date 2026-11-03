"""Check the official sensor driver and reviewed R10 pin-map provenance."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
COMMIT="842c809183352afbb6995729bc19f951bfee3db7"
PIN_TABLE="m3_design/assembly_review/sources/r10_design/pin_table.tsv"
PIN_SHA="b94133e61d553f5febb07c7c97977cd8b124634c6c19d0a2ce5b7fead304564a"
NETLIST="m3_design/assembly_review/schematic.net.xml"
NET_SHA="6ee0a063d14a3b9b977b09e0315df1d758ef13a4118d436b55443befd1b55bc4"
PINNED={"ism6hg256x_reg.c":"0d65ae15db47ed63d57ab0d2b7b945fd033dc4ff37abd3c09def5998b87354c1",
        "ism6hg256x_reg.h":"034002cf8af51c25a019f49709f3bac8fdba4a58f9e4c7ebc15bc5131675e75e",
        "LICENSE":"b54f36a43cf9b8f6292c8f0f3b4c267ebd59859587e0152c94305bc81dda68bc"}

def sensor_contract(tree):
    part=tree.find("./components/comp[@ref='U4']")
    if part is None or part.findtext("value")!="ISM6HG256X":
        raise ValueError("U4 is not the reviewed fitted IMU")
    fields={f.get("name"):f.text for f in part.findall("./fields/field")}
    if fields.get("Manufacturer Part")!="ISM6HG256XTR" or fields.get("LCSC")!="C51931514":
        raise ValueError("U4 fitted source part changed")
    expected={(ref,pin):net for net,pins in {
        "SPI1_SCK":(("U1","89"),("U4","13")),
        "SPI1_MISO":(("U1","90"),("U4","1")),
        "SPI1_MOSI":(("U1","91"),("U4","14")),
        "IMU_CS":(("U1","93"),("U4","12"))}.items() for ref,pin in pins}
    actual={}
    for net in tree.findall("./nets/net"):
        for node in net.findall("node"):
            key=(node.get("ref"),node.get("pin"))
            if key in expected:
                if key in actual:raise ValueError("Duplicate sensor pin")
                actual[key]=net.get("name")
    if actual!=expected:raise ValueError("Native R10 sensor pin map changed")
    return actual

def verify(root=ROOT):
    vendor=root/"m3_firmware/r10/vendor/ism6hg256x"
    manifest=json.loads((vendor/"manifest.json").read_text())
    if manifest.get("commit")!=COMMIT or manifest.get("files")!=PINNED:
        raise ValueError("ISM6HG256X source manifest changed")
    for file,expected in PINNED.items():
        if hashlib.sha256((vendor/file).read_bytes()).hexdigest()!=expected:
            raise ValueError("Pinned ST driver changed: "+file)
    if hashlib.sha256((root/PIN_TABLE).read_bytes()).hexdigest()!=PIN_SHA:
        raise ValueError("Reviewed R10 sensor pin table changed")
    raw=(root/NETLIST).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=NET_SHA:raise ValueError("Reviewed R10 netlist changed")
    sensor_contract(ET.fromstring(raw))
    return True
if __name__=="__main__":
    verify();print("Pinned ST driver and R10 pin table verified; no hardware tested")

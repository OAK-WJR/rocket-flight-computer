"""Check the candidate voltage core's actual R10 divider and reference wiring."""
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]
NETLIST='m3_design/assembly_review/schematic.net.xml'
NET_SHA='6ee0a063d14a3b9b977b09e0315df1d758ef13a4118d436b55443befd1b55bc4'
PIN_TABLE='m3_design/assembly_review/sources/r10_design/pin_table.tsv'
PIN_SHA='b94133e61d553f5febb07c7c97977cd8b124634c6c19d0a2ce5b7fead304564a'

def voltage_contract(tree):
    expected={tuple(p.split('.')):net for net,pins in {
        'VLOGIC':['R60.1'], 'VLOGIC_SENSE':['R60.2','R61.1','U1.30'],
        'CAM_5V':['R104.1'], 'CAM_5V_SENSE':['R104.2','R105.1','U1.35'],
        'GND':['R61.2','R105.2','U1.19'],
        '3V3':['U1.6'], '3V3A':['U1.20','U1.21']}.items() for p in pins}
    actual={}
    functions={'30':'PA6_30','35':'PB1_35','6':'VBAT_6','19':'VSSA_19','20':'VREF+_20','21':'VDDA_21'}
    for net in tree.findall('./nets/net'):
        for node in net.findall('node'):
            key=(node.get('ref'),node.get('pin'))
            if key not in expected:continue
            if key in actual:raise ValueError('Duplicate voltage endpoint')
            actual[key]=net.get('name')
            if key[0]=='U1' and node.get('pinfunction')!=functions[key[1]]:
                raise ValueError('R10 voltage MCU pin identity changed')
    if actual!=expected:raise ValueError('R10 voltage divider/reference endpoint changed')
    parts={
        'U1':('STM32H743VIT6','C5271084','STM32H743VIT6TR'),
        'R60':('100k','C25741','0402WGF1003TCE'),
        'R61':('10k','C25744','0402WGF1002TCE'),
        'R104':('10k','C25744','0402WGF1002TCE'),
        'R105':('1k','C11702','0402WGF1001TCE')}
    for ref,wanted in parts.items():
        matches=tree.findall("./components/comp[@ref='%s']"%ref)
        if len(matches)!=1:raise ValueError('Missing/duplicate voltage source part '+ref)
        part=matches[0];fields={f.get('name'):f.text for f in part.findall('./fields/field')}
        if (part.findtext('value'),fields.get('LCSC'),fields.get('Manufacturer Part'))!=wanted:
            raise ValueError('R10 voltage source part changed: '+ref)
    return actual

def verify(root=ROOT):
    for name,expected in ((NETLIST,NET_SHA),(PIN_TABLE,PIN_SHA)):
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Reviewed R10 voltage input changed: '+name)
    voltage_contract(ET.fromstring((root/NETLIST).read_bytes()))
    return True

if __name__=='__main__':
    verify();print('R10 voltage core: source parts and 14 endpoints verified; not linked or hardware tested')

"""Reviewed source binding for the read-only U3 diagnostic module.

No peripheral access and no claim of fitted-part authenticity or pin continuity.
"""
import csv
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET

NETLIST='m3_design/assembly_review/schematic.net.xml'
PIN_TABLE='m3_design/assembly_review/sources/r10_design/pin_table.tsv'
NET_SHA='6ee0a063d14a3b9b977b09e0315df1d758ef13a4118d436b55443befd1b55bc4'
PIN_SHA='b94133e61d553f5febb07c7c97977cd8b124634c6c19d0a2ce5b7fead304564a'
ROOT=Path(__file__).resolve().parents[3]

def verify_native_sources(root=ROOT,provenance=None):
    if provenance is None:
        provenance=json.loads(Path(__file__).with_name('provenance.json').read_text())
    expected={
        'm3_firmware/vendor/device/Include/stm32h743xx.h',
        'm3_firmware/vendor/hal/Src/stm32h7xx_hal_qspi.c',
        'm3_firmware/vendor/hal/Inc/stm32h7xx_hal_qspi.h',
        'm3_firmware/vendor/hal/Src/stm32h7xx_hal_rcc_ex.c',
    }
    if (provenance.get('schema')!='r10-bench-read-only-flash-provenance/v1' or
            set(provenance.get('pinned_sources',{}))!=expected):
        raise ValueError('Missing read-only flash register-source provenance')
    for name,digest in provenance['pinned_sources'].items():
        if hashlib.sha256((Path(root)/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Reviewed QSPI register/reference source changed: '+name)
    return True

ENDPOINTS={
    'QSPI_CLK':{'U1.36':'PB2_36','U3.6':'CLK_6'},
    'QSPI_IO0':{'U1.58':'PD11_58','U3.5':'DI/IO_{0}_5'},
    'QSPI_IO1':{'U1.59':'PD12_59','U3.2':'DO/IO_{1}_2'},
    'QSPI_IO2':{'U1.1':'PE2_1','U3.3':'~{WP}/IO_{2}_3'},
    'QSPI_IO3':{'U1.60':'PD13_60','U3.7':'~{HOLD}/~{RESET}/IO_{3}_7'},
    'QSPI_NCS':{'U1.92':'PB6_92','U3.1':'~{CS}_1','R10.1':None},
    '3V3':{'U3.8':'VCC_8','R10.2':None},'GND':{'U3.4':'GND_4'},
}
PINS={
    '1':('PE2','QSPI_IO2','AF9 QUADSPI_BK1_IO2'),
    '36':('PB2','QSPI_CLK','AF9 QUADSPI_CLK'),
    '58':('PD11','QSPI_IO0','AF9 QUADSPI_BK1_IO0'),
    '59':('PD12','QSPI_IO1','AF9 QUADSPI_BK1_IO1'),
    '60':('PD13','QSPI_IO3','AF9 QUADSPI_BK1_IO3'),
    '92':('PB6','QSPI_NCS','AF10 QUADSPI_BK1_NCS'),
}

def contract(tree,pin_rows):
    parts={
        'U3':('W25Q128JVSIQ','C97521','Winbond','W25Q128JVSIQ',
              'rocket:SOIC-8_L5.3-W5.3-P1.27-LS8.0-BL'),
        'R10':('10k','C25744','UNI-ROYAL(Uniroyal Elec)','0402WGF1002TCE','rocket:R0402'),
    }
    for ref,expected in parts.items():
        matches=tree.findall("./components/comp[@ref='%s']"%ref)
        if len(matches)!=1:raise ValueError('Missing/duplicate flash source part: '+ref)
        comp=matches[0];fields={}
        for f in comp.findall('./fields/field'):
            name=f.get('name')
            if name in fields:raise ValueError('Duplicate source part field: '+ref)
            fields[name]=f.text
        got=(comp.findtext('value'),fields.get('LCSC'),fields.get('Manufacturer'),
             fields.get('Manufacturer Part'),comp.findtext('footprint'))
        if got!=expected:raise ValueError('Flash source part changed: '+ref)

    wanted={ep:(name,fn) for name,eps in ENDPOINTS.items() for ep,fn in eps.items()}
    actual={};bus_names=set(ENDPOINTS)-{'3V3','GND'}
    for net in tree.findall('./nets/net'):
        name=net.get('name');nodes=net.findall('node')
        seen=set()
        for node in nodes:
            ep=node.get('ref','')+'.'+node.get('pin','')
            if ep in seen:raise ValueError('Duplicate flash net endpoint: '+ep)
            seen.add(ep)
            if name in bus_names and ep not in ENDPOINTS[name]:
                raise ValueError('Unreviewed additional flash bus endpoint: '+ep)
            if ep not in wanted:continue
            if ep in actual:raise ValueError('Endpoint on multiple nets: '+ep)
            actual[ep]=(name,node.get('pinfunction'))
    if actual!=wanted:raise ValueError('Flash data, supply or NCS pull-up endpoint changed')

    pins={}
    for row in pin_rows:
        pin=row.get('pin')
        if pin not in PINS:continue
        if pin in pins:raise ValueError('Duplicate flash pin-table row')
        pins[pin]=(row.get('port'),row.get('r10_net'),row.get('mode_af'))
        if pin=='92' and 'write the ODR high before the AF switch' not in row.get('reset_contract',''):
            raise ValueError('Flash chip-select initial-high contract changed')
    if pins!=PINS:raise ValueError('Reviewed flash pin or alternate function changed')
    return {'endpoints':len(actual),'pins':len(pins),'fitted_device':'W25Q128JVSIQ'}

def verify(root=ROOT):
    root=Path(root)
    verify_native_sources(root)
    for name,expected in ((NETLIST,NET_SHA),(PIN_TABLE,PIN_SHA)):
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Reviewed source changed; review before use: '+name)
    return contract(ET.fromstring((root/NETLIST).read_bytes()),
                    csv.DictReader(io.StringIO((root/PIN_TABLE).read_text()),delimiter='\t'))

if __name__=='__main__':
    import argparse,json
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path)
    print(json.dumps(verify(parser.parse_args().root),sort_keys=True))

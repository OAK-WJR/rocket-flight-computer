"""Source binding for the R10 microSD codec; no target or socket access."""
import csv
import hashlib
import io
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]
NETLIST='m3_design/assembly_review/schematic.net.xml'
PIN_TABLE='m3_design/assembly_review/sources/r10_design/pin_table.tsv'
NET_SHA='6ee0a063d14a3b9b977b09e0315df1d758ef13a4118d436b55443befd1b55bc4'
PIN_SHA='b94133e61d553f5febb07c7c97977cd8b124634c6c19d0a2ce5b7fead304564a'
ENDPOINTS={
    'SD_CS':{'J430.2':'CD_DAT3_CS_2','R460.1':None,'U1.81':'PD0_81'},
    'SD_SCK':{'J430.5':'CLK_5','U1.78':'PC10_78'},
    'SD_MISO':{'J430.7':'DAT0_DO_7','R462.1':None,'U1.79':'PC11_79'},
    'SD_MOSI':{'J430.3':'CMD_DI_3','R461.1':None,'U1.80':'PC12_80'},
    'SD_DAT1':{'J430.8':'DAT1_8','R463.1':None},
    'SD_DAT2':{'J430.1':'DAT2_1','R464.1':None},
    '3V3':{'J430.4':'VDD_4',**{'R%d.2'%r:None for r in range(460,465)},
           'C460.1':None,'C461.1':None},
    'GND':{'J430.6':'VSS_6','J430.9':'G2_9','J430.10':'G3_10',
           'J430.11':'G4_11','J430.12':'G1_12','C460.2':None,'C461.2':None},
}
PINS={'78':('PC10','SD_SCK','AF6 SPI3_SCK'),
      '79':('PC11','SD_MISO','AF6 SPI3_MISO'),
      '80':('PC12','SD_MOSI','AF6 SPI3_MOSI'),
      '81':('PD0','SD_CS','GPIO output push-pull; initialise high before output mode')}


def contract(tree,rows):
    parts={
        'J430':('472192001','C164170','MOLEX','472192001','rocket:M3_MICROSD_MOLEX_472192001'),
        'C460':('100nF 50V X7R 10%','C14663','YAGEO','CC0603KRX7R9BB104','rocket:C_0603_1608Metric'),
        'C461':('22uF 25V X7R 10%','C21397','Murata','GRM32ER71E226KE15L','rocket:M3_GRM32_1210'),
    }
    for ref in range(460,465):
        parts['R%d'%ref]=('10k 1%','C25804','UNI-ROYAL(Uniroyal Elec)',
                          '0603WAF1002T5E','rocket:R_0603_1608Metric')
    for ref,expected in parts.items():
        matches=tree.findall("./components/comp[@ref='%s']"%ref)
        if len(matches)!=1:raise ValueError('Missing/duplicate SD source part: '+ref)
        part=matches[0];fields={}
        for field in part.findall('./fields/field'):
            if field.get('name') in fields:raise ValueError('Duplicate SD source field: '+ref)
            fields[field.get('name')]=field.text
        got=(part.findtext('value'),fields.get('LCSC'),fields.get('Manufacturer'),
             fields.get('Manufacturer Part'),part.findtext('footprint'))
        if got!=expected:raise ValueError('Reviewed SD source part changed: '+ref)
    wanted={p:(net,fn) for net,pins in ENDPOINTS.items() for p,fn in pins.items()}
    actual={}
    for net in tree.findall('./nets/net'):
        name=net.get('name','')
        for node in net.findall('node'):
            p=node.get('ref','')+'.'+node.get('pin','')
            if name.startswith('SD_') and p not in ENDPOINTS.get(name,{}):
                raise ValueError('Additional SD bus endpoint: '+p)
            if node.get('ref')=='J430' and p not in wanted:
                raise ValueError('Unreviewed SD socket contact: '+p)
            if p not in wanted:continue
            if p in actual:raise ValueError('Duplicate SD endpoint: '+p)
            actual[p]=(name,node.get('pinfunction'))
    if actual!=wanted:raise ValueError('SD interface, pull-up, supply or shell endpoint changed')
    actual_pins={}
    for row in rows:
        p=row.get('pin')
        if p not in PINS:continue
        if p in actual_pins:raise ValueError('Duplicate SD pin-table row')
        actual_pins[p]=(row.get('port'),row.get('r10_net'),row.get('mode_af'))
        if p=='81' and 'no mechanical card-detect' not in row.get('reset_contract',''):
            raise ValueError('Reviewed SD CS/detect contract changed')
    if actual_pins!=PINS:raise ValueError('Reviewed SD GPIO or alternate-function map changed')
    return dict(endpoints=len(actual),pins=len(actual_pins),socket='472192001',
                independent_card_detect=False,native_adapter_implemented=False,hardware_tested=False)


def verify(root=ROOT):
    root=Path(root)
    for p,digest in ((NETLIST,NET_SHA),(PIN_TABLE,PIN_SHA)):
        if hashlib.sha256((root/p).read_bytes()).hexdigest()!=digest:
            raise ValueError('Reviewed SD input changed: '+p)
    return contract(ET.fromstring((root/NETLIST).read_bytes()),
                    csv.DictReader(io.StringIO((root/PIN_TABLE).read_text()),delimiter='\t'))


if __name__=='__main__':
    print(verify())

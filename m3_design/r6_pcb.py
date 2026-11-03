#!/usr/bin/env python3
"""Build the R6 placement from the reviewed R5 board and the native R6 netlist.

The source board is immutable and SHA-256 checked.  Unchanged circuitry, including
the CH1 pyro geometry and the repaired clock, MEMS and bypass copper, is retained.
Run with KiCad's Python. No git command or network access is used by this build.
"""
import argparse
import hashlib
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'm3_design'))
import r5_pcb as base

SOURCE_SHA = '6fc208d613dc2c1a6e9381ec3e1a5888c223ea6246336ae8320421272ca93a43'
PROJECT = ROOT / 'm3_design/assembly_review'
MM, mm = pcbnew.FromMM, pcbnew.ToMM
W, L = 46.0, 100.0
ACTUATOR = set('Q120 Q121 Q122 R120 R121 R122 R123 C120 TP121'.split())
RAW_SENSE = set('R124 R125 R177 R182 C122'.split())
ACT_INTERNAL = {'ACT_FET_S', 'ACT_GATE', 'ACT_DRV', 'ACT_EN'}
CH2_NETS = {'PYRO2_BUS', 'PYRO2_IGN', 'PYRO2_OUT', 'PYRO2_GATE', 'PYRO2_GATE_N',
            'PYRO2_CONT', 'PYRO2_CONT_MID', 'PYRO2_COLD', 'ARM2_SENSE',
            'ARM2_SENSE_MID', 'ARM2_ADC', 'PYRO2_ADC'}


def point(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def coordinates(p):
    return mm(p.x), mm(p.y)


def path(s):
    result = pcbnew.KIID_PATH()
    for part in s.split('/'):
        if part:
            result.push_back(pcbnew.KIID(part))
    return result


def footprint_library(name):
    lib, item = name.split(':', 1)
    if lib == 'rocket':
        return PROJECT / 'kilib/rocket.pretty', item
    local = PROJECT / 'kilib' / (lib + '.pretty')
    if local.is_dir():
        return local, item
    stock = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints') / (lib + '.pretty')
    if stock.is_dir():
        return stock, item
    raise RuntimeError('Missing footprint library: ' + name)


def detach(b, refs):
    """Remove pad leadouts of moved/replaced components; leave unrelated copper."""
    pads = [p for f in b.GetFootprints() if f.GetReference() in refs for p in f.Pads()]
    dead = []
    for t in b.GetTracks():
        ends = [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]
        if any(p.GetNetname() == t.GetNetname() and p.GetNetname() and
               (t.GetClass() == 'PCB_VIA' or p.IsOnLayer(t.GetLayer())) and
               any(p.HitTest(q) for q in ends) for p in pads):
            dead.append(t)
    for t in dead:
        b.Delete(t)


def _sync_component_metadata(f, node):
    """Copy native netlist fields without changing footprint identity or geometry."""
    f.SetValue(node.findtext('value', ''))
    fields = {field.attrib['name']: field.text or ''
              for field in node.findall('./fields/field')}
    # Current KiCad XML puts Datasheet in fields; older exports used a direct tag.
    if 'Datasheet' not in fields and node.find('datasheet') is not None:
        fields['Datasheet'] = node.findtext('datasheet', '')
    for name, value in fields.items():
        if name not in ('Footprint', 'Reference', 'Value'):
            f.SetField(name, value)
    for field in f.GetFields():
        field.SetVisible(False)


def sync_metadata(b, netlist):
    """Update existing footprints' hidden fields only; safe after routing.

    Does not replace footprints, assign nets, alter pads/copper, or save files.
    Missing schematic references fail before any board object is changed.
    """
    components = ET.parse(netlist).getroot().findall('./components/comp')
    footprints = {f.GetReference(): f for f in b.GetFootprints()}
    missing = sorted(node.attrib['ref'] for node in components
                     if node.attrib['ref'] not in footprints)
    if missing:
        raise RuntimeError('Metadata sync missing PCB references: ' + ', '.join(missing))
    for node in components:
        _sync_component_metadata(footprints[node.attrib['ref']], node)
    return len(components)


def synchronize(b, netlist):
    """Apply native schematic references, footprint IDs, metadata and pad nets."""
    root = ET.parse(netlist).getroot()
    components = {n.attrib['ref']: n for n in root.findall('./components/comp')}
    pin_nets = {}
    for node in root.findall('./nets/net'):
        name = node.attrib['name']
        if not b.FindNet(name):
            b.Add(pcbnew.NETINFO_ITEM(b, name))
        for pin in node.findall('node'):
            pin_nets[(pin.attrib['ref'], pin.attrib['pin'])] = name
    removed = {f.GetReference() for f in b.GetFootprints()
               if f.GetReference() not in components and not f.GetReference().startswith('TH')}
    detach(b, removed)
    for f in list(b.GetFootprints()):
        if f.GetReference() in removed:
            b.Delete(f)
    root_uuid = b.FindFootprintByReference('U1').GetPath().AsString().split('/')[1]
    added, changed = [], []
    for ref, node in sorted(components.items()):
        name = node.findtext('footprint')
        if not name:
            raise RuntimeError('No footprint for ' + ref)
        f = b.FindFootprintByReference(ref)
        current = None if f is None else str(f.GetFPID().GetLibNickname()) + ':' + str(f.GetFPID().GetLibItemName())
        if current != name:
            old = f
            if old:
                detach(b, {ref})
            lib, item = footprint_library(name)
            f = pcbnew.FootprintLoad(str(lib), item)
            if f is None:
                raise RuntimeError('Cannot load ' + name)
            f.SetFPID(pcbnew.LIB_ID(*name.split(':', 1)))
            f.SetReference(ref)
            b.Add(f)
            if old:
                if old.IsFlipped():
                    f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
                f.SetOrientationDegrees(old.GetOrientationDegrees())
                f.SetPosition(old.GetPosition())
                b.Delete(old)
                changed.append(ref)
            else:
                f.SetPosition(point(60 + len(added) % 8 * 6, 5 + len(added) // 8 * 6))
                added.append(ref)
        _sync_component_metadata(f, node)
        sheet = node.find('sheetpath').attrib['tstamps']
        f.SetPath(path('/' + root_uuid + sheet + node.findtext('tstamps')))
        for p in f.Pads():
            name = pin_nets.get((ref, p.GetNumber()))
            p.SetNet(b.FindNet(name) if name else b.FindNet(0))
        if ref.startswith('TP') or ref == 'J2':
            f.SetAttributes(f.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        for p in f.Pads():
            if ref.startswith('TP'):
                p.SetLocalClearance(MM(1.0))
            elif p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and p.GetNetname() == 'RAW_ACT':
                p.SetLocalClearance(MM(0.3))
            if ref.startswith(('R', 'C')) and p.GetNetname() == 'GND' and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                if max(mm(p.GetSize().x), mm(p.GetSize().y)) <= 2.0:
                    p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_THERMAL)
                    # Minimum 0.25 mm gap / 0.30 mm spoke come from m3.kicad_dru.
    print('schematic removed:', ' '.join(sorted(removed)))
    print('schematic replaced:', ' '.join(changed))
    print('schematic added:', ' '.join(added))
    return set(added), set(changed)


def move_components(b):
    # Preserve every internal actuator-switch segment while moving its complete
    # small-signal network; rederive only the power pours and external feed.
    for t in list(b.GetTracks()):
        if t.GetNetname() in ACT_INTERNAL:
            t.Move(point(0, 60))
    detach(b, ACTUATOR | RAW_SENSE | {'J1', 'C29', 'D120', 'D123', 'C100', 'R100', 'TP120', 'TP89', 'C120', 'R80'})
    for ref in ACTUATOR:
        b.FindFootprintByReference(ref).Move(point(0, 60))
    for ref in RAW_SENSE:
        b.FindFootprintByReference(ref).Move(point(-1, -45))
    for ref, x, y, rot, side in (
        ('J1', 23, 92.4, 180, 'F'),
        ('C29', 19.2, 18.5, -90, 'F'),
        ('D120', 32, 65, -90, 'F'),
        ('D123', 13.7, 61.8, 0, 'F'),
        ('J9', 42.7, 24, -90, 'F'),
        ('J2', 43, 58.65, 90, 'F'),
        ('C100', 42, 35.9, 0, 'B'),
        ('R100', 43, 38.65, 0, 'B'),
        ('TP120', 9, 69, 0, 'B'),
        ('C120', 3.5, 82, 0, 'B'),
        ('R80', 16.3, 6.45, 0, 'B'),
        ('R165', 3.3, 20.3, 90, 'F'),
        ('TH3', 1.4, 94, 0, 'F'),
    ):
        if b.FindFootprintByReference(ref):
            base.place(b, ref, x, y, rot, side)


def remove_obsolete_copper(b):
    used_nets = {p.GetNetname() for f in b.GetFootprints() for p in f.Pads() if p.GetNetname()}
    for t in list(b.GetTracks()):
        if t.GetNetname() in CH2_NETS or t.GetNetname() not in used_nets:
            b.Delete(t)
            continue
        pts = [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else [t.GetStart(), t.GetEnd()]
        if t.GetNetname() == 'RAW_ACT' and all(mm(p.y) < 50 for p in pts):
            b.Delete(t)
    for z in list(b.Zones()):
        if z.GetNetname() in CH2_NETS or z.GetZoneName().startswith('TP123'):
            b.Delete(z)


def power_zones(b):
    """Keep the two high-current paths on separate layers across the forward bay.

    BAT_IN: broad In2 strip and parallel outer crossbar from J1 to Q120.
    RAW_ACT: F.Cu forward strip, Q121 to the existing servo column and J124.
    Native fills and the later DC solve include all antipads and terminal lands.
    """
    full = dict(clr=0.3, minw=0.3, conn=pcbnew.ZONE_CONNECTION_FULL)
    base.add_zone(b, 'BAT_IN', (pcbnew.In2_Cu,),
                  [(0.3, 0.3), (15, 0.3), (15, 14.6), (9.9, 14.6),
                   (9.9, 62), (14, 66.1), (14, 88.6), (32.2, 88.6),
                   (32.2, 97.5), (8.9, 97.5), (8.9, 94), (0.3, 94)],
                  6, 'R6_BAT_IN_In2', **full)
    base.add_zone(b, 'BAT_IN', (pcbnew.F_Cu,), base.rect(8.9, 85.6, 32.2, 97.5),
                  31, 'R6_BAT_IN_crossbar_F', **full)
    base.add_zone(b, 'RAW_ACT', (pcbnew.F_Cu,),
                  [(0.3, 63.2), (8.6, 63.2), (8.6, 70.3), (11.8, 70.3),
                   (11.8, 75), (8.6, 75), (8.6, 94), (0.3, 94)],
                  32, 'R6_RAW_ACT_F', **full)
    # Old actuator input/output pours will be replaced by new current paths.
    for z in list(b.Zones()):
        if z.GetZoneName() in ('BAT_IN_B', 'ACT_FET_S_B', 'RAW_ACT_B'):
            z.Move(point(0, 60))
        if z.GetZoneName() in ('BAT_IN_In2', 'RAW_ACT_In2'):
            b.Delete(z)


def place_new(b, added):
    """Port block and compact top-side telemetry supply, clear of retained R5 parts."""
    table = {
        'J130': (42.7, 34.5, -90, 'F'),
        'J131': (42.7, 44.5, -90, 'F'),
        'U16': (10, 7, 0, 'F'),
        'C177': (7.75, 7.20, 90, 'F'),
        'C178': (9.1, 4.5, 0, 'F'),
        'R195': (12.35, 7, -90, 'F'),
        'R192': (10, 1.5, 0, 'F'),
        'R193': (10, 3, 0, 'F'),
        'R205': (34, 17, 0, 'F'),
        'U14': (21.5, 5.5, 0, 'F'),
        'C170': (20, 9.3, 0, 'F'),
        'L4': (27, 4.5, 0, 'F'),
        'C173': (21.5, 2.5, 180, 'F'),
        'C171': (27, 9.5, 180, 'F'),
        'C172': (14.8, 3.3, 90, 'F'),
        'R190': (18.05, 1.5, 0, 'F'),
        'R206': (18.05, 3.5, 0, 'F'),
        'R191': (18.05, 5.5, 0, 'F'),
        'C174': (14.9, 6.4, 0, 'F'),
        'U15': (10, 10.5, 180, 'F'),
        'C175': (10, 13.3, 0, 'F'),
        'C176': (10, 15.5, 0, 'F'),
        'R194': (14, 16.3, 0, 'F'),
        'TP130': (14, 10, 0, 'F'),
        'D130': (36.5, 34.5, 0, 'F'),
        'D131': (36.5, 44.5, 0, 'F'),
        'R196': (39.2, 31.5, 0, 'F'),
        'R197': (39.2, 33, 0, 'F'),
        'R198': (39.2, 34.5, 0, 'F'),
        'R199': (39.2, 36, 0, 'F'),
        'R200': (39.2, 37.5, 0, 'F'),
        'R201': (39.2, 43.5, 0, 'F'),
        'R202': (39.2, 45, 0, 'F'),
        'R203': (34, 32.5, 90, 'F'),
        'R204': (38.9, 38.9, 45, 'F'),
        'C179': (36.5, 38, 0, 'F'),
        'C180': (36.5, 48, 0, 'F'),
    }
    for ref, values in table.items():
        if b.FindFootprintByReference(ref):
            base.place(b, ref, *values)
    remaining = sorted(added - table.keys())
    if remaining:
        raise RuntimeError('Unplaced R6 components: ' + ', '.join(remaining))
    # The diagonal spokes reach both sides of the local GND pour after routing.
    ground = next(p for p in b.FindFootprintByReference('R204').Pads() if p.GetNumber() == '2')
    ground.SetThermalSpokeAngle(pcbnew.EDA_ANGLE(45, pcbnew.DEGREES_T))


def title(b):
    block = b.GetTitleBlock()
    block.SetTitle('M3 flight computer — R6, CAD candidate')
    block.SetRevision('M3-ASSY-R6')
    for d in list(b.GetDrawings()):
        if d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            b.Delete(d)


def build(source, netlist, output):
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA:
        raise RuntimeError('Reviewed R5 source hash changed')
    pcbnew.KIID.SeedGenerator(6101)
    b = pcbnew.LoadBoard(str(source))
    added, changed = synchronize(b, netlist)
    remove_obsolete_copper(b)
    move_components(b)
    place_new(b, added)
    power_zones(b)
    title(b)
    b.BuildConnectivity()
    # Loading an immutable reference without a sibling project otherwise saves
    # KiCad defaults over the actual project's reviewed design rules.
    pcbnew.SaveBoard(str(output), b, True)
    print('R6 placement saved:', output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('netlist', type=Path)
    parser.add_argument('--output', type=Path, default=PROJECT / 'm3.kicad_pcb')
    args = parser.parse_args()
    build(args.source, args.netlist, args.output)

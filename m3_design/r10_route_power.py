"""R10 local buck/LDO/logic power loops, explicit pad-checked polylines.

Placement: sources/r10_design/power_place.tsv. Root owns rail trunks, input
protection routing and status signals unless explicitly included below. Ground
vias require the final ground pours; an unfilled intermediate has dangling vias.
"""
import csv
from pathlib import Path

import pcbnew
import r9_power
from r10_route import Translated, xy

HERE = Path(__file__).resolve().parent
PLACEMENT = HERE / 'assembly_review/sources/r10_design/power_place.tsv'


def placement_asserts(d):
    for row in csv.DictReader(PLACEMENT.open(), delimiter='\t'):
        f = d.board.FindFootprintByReference(row['ref'])
        assert f, row['ref']
        expected = (round(float(row['x']),4), round(float(row['y']),4))
        assert xy(f.GetPosition()) == expected, (row['ref'], xy(f.GetPosition()), expected)
        assert abs((f.GetOrientationDegrees()-float(row['rot'])+180) % 360-180) < .001
        assert f.IsFlipped() == (row['side'] == 'B')


def logic(d):
    t = Translated(d, (-7, -5))
    # R9 local regulator loop, with the changed hold-up and test point branches
    # regenerated below rather than silently retaining their old endpoints.
    for net, layer, width, pts in r9_power.LOGIC_TRACKS:
        if net == 'VLOGIC' and (layer == 'F' or pts[0] in [(44.6, 74.8),(40.0,69.6)]):
            continue
        if net == '3V3' and pts[-1] == (40.0,82.24):
            pts = pts[:-1] + [(40.0,81.24),(41.0,82.24)]
        if net == '3V3' and pts[-1] == r9_power.V_3V3:
            pts = [pts[0], (41.0,78.9)]
        t.track(net, layer, width, pts)
    for net, at, size in r9_power.LOGIC_VIAS:
        if at not in [r9_power.V_TP83,r9_power.V_HOLDUP,r9_power.V_3V3]:
            t.via(net, at, size)
    d.via('3V3',(34,73.9),(.6,.3))
    d.via('VLOGIC',(37.6,69.8),(.6,.3))
    d.pad('C84.1', net='VLOGIC', at=(38.5,70.75))
    d.track('VLOGIC','F',.4,[(37.6,69.8),(38.5,69.8),(38.5,70.75)])
    d.track('VLOGIC','B',.4,[(37.6,69.8),(37.6,73.2),(44.5,73.2)])
    d.via('VLOGIC',(44.5,73.2),(.6,.3))
    # Local input1, USB input2 and mux control resistors/capacitors.
    d.track('RAW_PROTECTED','B',.3,[(32.3,62.175),(32.3,63.2)])
    d.via('RAW_PROTECTED',(32.3,63.2),(.6,.3))
    d.link('RAW_PROTECTED','F',.4,'C97.1','C82.1',[(32.3,63.2),(32.3,67.4)])
    d.track('RAW_PROTECTED','F',.4,[(33.9,67.4),(43.9,67.4),(44.5,68),(44.5,69)])
    d.track('USB_LIMITED','B',.4,[(31.05,49.65),(34.4,53),(34.4,56.85),(33.05,58.2),(33.05,59.2)])
    d.link('USB_LIMITED','B',.3,'C98.1','U11.7',[(32.3,59.95)])
    d.link('USB_LIMITED','B',.3,'C98.1','R87.1',[(33.05,58.2),(30,58.2)])
    d.link('USB_OVLO','B',.2,'R87.2','R88.1')
    d.link('USB_OVLO','B',.2,'U11.5','R87.2')
    d.link('LOGIC_ILIM','B',.2,'U11.10','R86.1',[(34.325,61.25)])
    d.link('LOGIC_SS','B',.2,'U11.11','C85.1',[(34.3,61.75),(35.125,62.575)])
    grounds = [(.4,[(33.95,68),(35.75,68)]),(.4,[(34.9,68),(34.9,68.75)]),
               (.4,[(35,75.28),(35,76.24),(36,77.24)]),(.4,[(36.3,71.8),(35.2,71.8)]),
               (.4,[(33.8,62.25),(33.8,63.25),(33.8,63.9)]),
               (.2,[(31.5,60.75),(31.5,60.2)]),(.2,[(31.5,61.75),(31.5,62.25),(31.5,63.35)])]
    for width, pts in grounds:
        d.track('GND','B',width,pts)
    d.track('GND','F',.4,[(33.8,63.25),(33.8,64.4),(33.9,64.4)])
    d.track('GND','F',.4,[(32.3,59.625),(33.8,61.125),(33.8,63.25)])
    d.track('GND','B',.2,[(31.5,60.2),(31.5,59.2)])
    d.track('GND','B',.4,[(35,76.24),(36,76.24)])
    for at in [(34.9,68.75),(36,76.24),(35.2,71.8),(33.8,63.25),(31.5,60.2),(31.5,63.35)]:
        d.via('GND',at,(.6,.3))


BUCK_TRACKS = [
    ('RAW_PROTECTED','B',.3,[(40.8,51),(41.75,51),(43,51)]),
    ('RAW_PROTECTED','F',1.0,[(43,50.6),(43,51)]),
    ('RAW_PROTECTED','F',1.0,[(43,51),(40.5,53.5),(40.5,56.5),(41.5,57.5)]),
    ('PORT_SW','B',.4,[(40.8,53.2),(40.8,55.25)]),
    ('PORT_SW','B',.4,[(37,54.75),(40.8,54.75)]),
    ('PORT_BST','B',.3,[(39.85,53.2),(37,53.2)]),
    ('PORT_5V3','B',1.0,[(40.8,59.95),(40.8,60.8),(41.5,61.5)]),
    ('PORT_5V3','F',1.0,[(41.5,61.5),(41.5,65)]),
    ('PORT_FB_TOP','F',.2,[(35.675,52.4),(35.675,50.8)]),
    ('PORT_FB','F',.2,[(37.325,50.8),(36.8,50.8),(35.675,49.675),(35.675,49.2)]),
    ('PORT_FB','F',.2,[(37.325,50.8),(38.05,50.8)]),
    ('PORT_FB','B',.2,[(38.05,50.8),(39.65,50.8),(39.85,51)]),
    ('PORT_5V3','F',.2,[(37.325,52.4),(38.5,53.575),(38.5,54.8),(35.2,58.1),(35.2,62.5),(40.5,62.5),(41.5,61.5)]),
    ('GND','B',.4,[(41.75,53.2),(43.6,53.2)]),
    ('GND','F',.4,[(43,53.6),(43.2,53.6),(43.6,53.2)]),
    ('GND','F',.4,[(44.5,57.5),(44.5,58.8)]),
    ('GND','F',.4,[(44.5,61.5),(44.5,62.8)]),
    ('GND','F',.4,[(44.5,65),(44.5,66.3)]),
    ('GND','F',.2,[(37.325,49.2),(38.2,49.2)]),
]
BUCK_VIAS = [('RAW_PROTECTED',(43,51),(.6,.3)),('PORT_5V3',(41.5,61.5),(.6,.3)),
             ('PORT_FB',(38.05,50.8),(.5,.3)),('GND',(43.6,53.2),(.6,.3)),
             ('GND',(44.5,58.8),(.6,.3)),('GND',(44.5,62.8),(.6,.3)),
             ('GND',(44.5,66.3),(.6,.3)),('GND',(38.2,49.2),(.5,.3))]
LDO_TRACKS = [
    ('PORT_5V3','B',.2,[(29.15,16.5),(29.15,17),(29.65,17.5)]),
    ('PORT_5V3','B',.4,[(29.65,17.5),(32,17.5)]),
    ('PORT_5V3','B',.2,[(29.15,15.5),(30.5,15.5),(30.5,17.5)]),
    ('PORT_LDO_SS','B',.2,[(29.15,16),(29.8,16)]),
    ('PORT_LDO_SS','F',.2,[(29.8,16),(30.08,16)]),
    ('PORT_4V8','B',.2,[(26.85,16.5),(26.85,17),(26.2,17)]),
    ('PORT_4V8','B',.4,[(26.2,17),(25.9,17.3),(24,17.3),(24,19.2)]),
    ('PORT_4V8','B',.25,[(24,19.2),(25.8,19.2),(26.3,19.7),(26.3,22.3),(26.475,22.3)]),
    ('PORT_LDO_FB','B',.2,[(25.625,12),(26.2,12),(26.925,12),(27.7,11.225)]),
    ('PORT_LDO_FB','F',.2,[(26.2,12),(26.2,15.7),(25.9,16)]),
    ('PORT_LDO_FB','B',.2,[(25.9,16),(26.85,16)]),
    ('PORT_4V8','B',.2,[(23.975,12),(23.975,12.8)]),
    ('PORT_4V8','F',.2,[(23.975,12.8),(22.4,14.375),(22.4,17.3)]),
    ('PORT_4V8','B',.2,[(22.4,17.3),(24,17.3)]),
    ('GND','B',.2,[(26.85,15.5),(28,15.5)]),
    ('GND','B',.2,[(29.15,15),(28,15),(28,15.5)]),
    ('GND','B',.4,[(24,14.3),(25.5,14.3)]),
    ('GND','B',.4,[(24,22.2),(24,23.5)]),
    ('GND','B',.4,[(32,14.5),(32,13.2)]),
    ('GND','F',.2,[(30.92,16),(31.6,16)]),
    ('GND','B',.2,[(27.7,9.575),(27.7,8.8)]),
    ('GND','B',.2,[(28.125,22.3),(28.8,22.3)]),
]
LDO_VIAS = [('PORT_LDO_SS',(29.8,16)),('PORT_LDO_FB',(26.2,12)),('PORT_LDO_FB',(25.9,16)),
            ('PORT_4V8',(23.975,12.8)),('PORT_4V8',(22.4,17.3)),
            ('GND',(28,15.25)),('GND',(28,16.75)),('GND',(25.5,14.3)),
            ('GND',(24,23.5)),('GND',(32,13.2)),('GND',(31.6,16)),
            ('GND',(27.7,8.8)),('GND',(28.8,22.3))]


def draw(d):
    placement_asserts(d)
    logic(d)
    for ref, num, net, at in [('U400','5','PORT_SW',(40.8,53.2)),('L400','1','PORT_SW',(40.8,55.25)),
                               ('U401','1','PORT_4V8',(26.85,17)),('U401','10','PORT_5V3',(29.15,17))]:
        d.pad(ref,num,net,at)
    for row in BUCK_TRACKS + LDO_TRACKS:
        d.track(*row)
    for row in BUCK_VIAS:
        d.via(*row)
    for net, at in LDO_VIAS:
        d.via(net,at)

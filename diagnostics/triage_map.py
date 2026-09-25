"""Read the current saved PCB for bench probe locations; no CAD mutations."""
import hashlib
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'm3_design'))
from check_design import inspect, xy

# Net assignments are deliberately named independently of the CAD generator.
TEST_POINTS = {
    'TP70.1':'RAW_PROTECTED', 'TP71.1':'CAM_INPUT_LIMITED', 'TP72.1':'CAM_5V',
    'TP73.1':'CAM_ILIM', 'TP74.1':'GND', 'TP75.1':'CAM_RX_WIRE', 'TP76.1':'CAM_TX_WIRE',
    'TP80.1':'BAT_IN', 'TP81.1':'RAW_PROTECTED', 'TP82.1':'USB_LIMITED', 'TP83.1':'VLOGIC',
    'TP84.1':'BAT_ENABLE', 'TP85.1':'BAT_FAULT_N', 'TP86.1':'USB_FAULT_N',
    'TP87.1':'LOGIC_SOURCE_ST', 'TP88.1':'GND', 'TP89.1':'BAT_ILIM',
    'TP90.1':'CAM_IO_3V3', 'TP91.1':'CAM_UART_OE', 'TP92.1':'VBUS_SENSE',
}
EXTRA_POINTS = {'J2.1':'GND','J2.4':'NRST','J2.5':'3V3','C28.1':'VBUS',
                'C6.1':'VLOGIC','C10.1':'3V3A','C19.1':'VCAP1','C20.1':'VCAP2',
                'R61.1':'VLOGIC_SENSE','R63.1':'V3V3_SENSE'}


def read_board(path, expected_sha):
    path = Path(path); raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('PCB file does not match the selected firmware revision')
    root, fps, values, nets = inspect(raw.decode())
    found = {ref+'.'+p.items[1].atom for ref,f in fps.items() if ref.startswith('TP') for p in f.children('pad')}
    if found != set(TEST_POINTS):
        raise ValueError('Unexpected test point population')
    for endpoint,net in {**TEST_POINTS,**EXTRA_POINTS,'U10.1':'VBUS','U10.6':'USB_LIMITED',
                         'U11.7':'USB_LIMITED','U11.1':'VLOGIC'}.items():
        if nets.get(endpoint) != net:
            raise ValueError('Probe or power-path net mismatch: '+endpoint)

    def point(endpoint):
        ref,number = endpoint.split('.'); f = fps[ref]
        pads = [p for p in f.children('pad') if p.items[1].atom == number]
        if len(pads) != 1: raise ValueError('Ambiguous probe pad '+endpoint)
        if f.children('layer')[0].items[1].atom != 'F.Cu':
            raise ValueError('Bottom-side probe needs a separately reviewed transform')
        x,y = xy(f,'at'); px,py = xy(pads[0],'at'); at = f.children('at')[0].value()
        angle = math.radians(float(at[3])) if len(at)>3 else 0
        return [round(x+px*math.cos(angle)+py*math.sin(angle),6),
                round(y-px*math.sin(angle)+py*math.cos(angle),6)]

    points = {}
    for endpoint,net in {**TEST_POINTS,**EXTRA_POINTS}.items():
        ref = endpoint.split('.')[0]
        ground = 'TP88.1' if ref in {f'TP{i}' for i in range(80,90)} else \
                 'TP74.1' if ref in {f'TP{i}' for i in range(70,77)} | {'TP90','TP91'} else 'J2.1'
        points[endpoint] = dict(pad=endpoint,net=net,xy_mm=point(endpoint),side='TOP',
            ground=ground,ground_xy_mm=point(ground),dedicated_testpad=endpoint in TEST_POINTS,
            measurement=None)
    edges=[]
    for kind in ('gr_line','gr_arc'):
        for n in root.children(kind):
            if n.children('layer')[0].items[1].atom=='Edge.Cuts':
                edges += [xy(n,k) for k in ('start','end')]
    if not edges:raise ValueError('No board outline')
    bounds=[min(x for x,y in edges),min(y for x,y in edges),max(x for x,y in edges),max(y for x,y in edges)]
    components={ref:dict(xy_mm=list(xy(f,'at')),value=values[ref]) for ref,f in fps.items()}
    return dict(board_sha256=expected_sha,coordinate_frame='PCB TOP view; x right, y down, millimetres; not a mirrored bottom view',
                bounds_mm=bounds,points=points,components=components)


def measurement_binding(mapping, original):
    # Preserve existing measurement semantics, but resolve every coordinate
    # again. New power points become blank observations, not new PASS criteria.
    binding={**original,'probes':{}}
    endpoints={n:p['probe'] for n,p in original['probes'].items()}
    endpoints.update({n:e for e,n in TEST_POINTS.items() if n not in endpoints and n!='GND'})
    for net,endpoint in endpoints.items():
        p=mapping['points'][endpoint]
        if p['net']!=net:raise ValueError('Measurement binding net mismatch')
        binding['probes'][net]=dict(probe=endpoint,board_xy_mm=p['xy_mm'],ground=p['ground'],ground_xy_mm=p['ground_xy_mm'])
    return binding

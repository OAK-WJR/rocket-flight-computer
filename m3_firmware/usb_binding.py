"""Read the USB revision's actual CAD; do not relabel an old board binding."""
import hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'m3_design'))
from check_design import inspect,xy
from check_usb import check
from check_uart import native_netlist

def make_binding():
    folder=ROOT/'m3_design/usb_review';board=folder/'m3.kicad_pcb'
    digest=hashlib.sha256(board.read_bytes()).hexdigest()
    verification=json.loads((folder/'verification_usb.json').read_text())
    if not verification['ok'] or digest!=verification['board_sha256']:
        raise ValueError('USB board is not the native-verified revision')
    result=check(board.read_text(),folder)
    if not result['ok']:raise ValueError(result['issues'])
    native_netlist(folder)
    _,fps,_,nets=inspect(board.read_text())
    def point(endpoint):
        ref,num=endpoint.split('.');f=fps[ref]
        p=next(x for x in f.children('pad') if x.items[1].atom==num)
        x,y=xy(f,'at');px,py=xy(p,'at');at=f.children('at')[0].value()
        a=math.radians(float(at[3])) if len(at)>3 else 0
        return [round(x+px*math.cos(a)+py*math.sin(a),6),round(y-px*math.sin(a)+py*math.cos(a),6)]
    probes={}
    for net,endpoint in {'VBUS':'C28.1','VLOGIC':'C6.1','3V3':'J2.5','3V3A':'C10.1',
       'VCAP1':'C19.1','VCAP2':'C20.1','NRST':'J2.4','VLOGIC_SENSE':'R61.1','V3V3_SENSE':'R63.1',
       'CAM_5V':'TP72.1','CAM_IO_3V3':'TP90.1','CAM_UART_OE':'TP91.1',
       'CAM_RX_WIRE':'TP75.1','CAM_TX_WIRE':'TP76.1','VBUS_SENSE':'TP92.1'}.items():
        if nets[endpoint]!=net:raise ValueError('Probe net changed: '+endpoint)
        probes[net]={'probe':endpoint,'board_xy_mm':point(endpoint),'ground':'J2.1','ground_xy_mm':point('J2.1')}
    return {'profile':'M3-USB-R1','board_sha256':digest,'gnss_dnp':True,'probes':probes,
      'binding_note':'Expected CAD identity only. USB divider and D+/D- pins independently checked; no assembly enrollment or hardware qualification.'}

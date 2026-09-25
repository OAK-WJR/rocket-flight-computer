"""Bind firmware to the actual fitted GNSS candidate, not a relabeled DNP board."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'m3_design'))
from check_gnss import check
from check_uart import native_netlist
from usb_binding import make_binding as usb_binding

def make_binding():
    folder=ROOT/'m3_design/gnss_review';board=folder/'m3.kicad_pcb'
    digest=hashlib.sha256(board.read_bytes()).hexdigest()
    verification=json.loads((folder/'verification_gnss.json').read_text())
    if not verification['ok'] or digest!=verification['board_sha256']:raise ValueError('GNSS candidate is not verified')
    for name,sha in verification['inputs_sha256'].items():
        if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=sha:raise ValueError('Changed GNSS CAD input '+name)
    result=check(board.read_text(),folder)
    if not result['ok']:raise ValueError(result['issues'])
    native_netlist(folder)
    binding=usb_binding()
    binding.update(profile='M3-GNSS-R1',board_sha256=digest,gnss_dnp=False,
        binding_note='Fitted SAM-M10Q ordinary reception/diagnostics candidate, UART6 PC6/PC7. No hardware/RF qualification.')
    return binding

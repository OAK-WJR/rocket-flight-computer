"""Bind input-only power monitoring to the exact saved three-net CAD revision."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'m3_design'))
from check_status import check
from check_uart import native_netlist
from gnss_binding import make_binding as gnss_binding
def make_binding():
    folder=ROOT/'m3_design/power_status_review';board=folder/'m3.kicad_pcb'
    digest=hashlib.sha256(board.read_bytes()).hexdigest()
    verification=json.loads((folder/'verification_status.json').read_text())
    if not verification['ok'] or digest!=verification['board_sha256']:raise ValueError('Status CAD not verified')
    for n,d in verification['inputs_sha256'].items():
        if hashlib.sha256((folder/n).read_bytes()).hexdigest()!=d:raise ValueError('Changed CAD input '+n)
    result=check(board.read_text(),folder)
    if not result['ok']:raise ValueError(result['issues'])
    native_netlist(folder);binding=gnss_binding()
    binding.update(profile='M3-PDIAG-R1',board_sha256=digest,
        binding_note='Ordinary input-only power status, full bench records/USB/GNSS; no physical qualification.')
    return binding

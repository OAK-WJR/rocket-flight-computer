"""Approve only the reviewed LED assembly delta, retaining all PDIAG GPIO roles."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'m3_design'))
from check_assembly import check
from check_uart import native_netlist
from status_binding import make_binding as status_binding

def make_binding():
    f=ROOT/'m3_design/assembly_review';board=f/'m3.kicad_pcb'
    digest=hashlib.sha256(board.read_bytes()).hexdigest()
    proof=json.loads((f/'verification_assembly.json').read_text())
    if not proof['ok'] or proof['board_sha256']!=digest:raise ValueError('Unverified assembly CAD')
    for name,d in proof['inputs_sha256'].items():
        if hashlib.sha256((f/name).read_bytes()).hexdigest()!=d:raise ValueError('Changed assembly input '+name)
    result=check(board.read_text(),f)
    if not result['ok']:raise ValueError(result['issues'])
    native_netlist(f);binding=status_binding()
    binding.update(profile='M3-ASSY-R1',board_sha256=digest,
        binding_note='Same input-only PDIAG software and GPIO roles; four LED lands and assembly metadata corrected. No physical qualification.')
    return binding

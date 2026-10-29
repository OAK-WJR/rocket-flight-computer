#!/usr/bin/env python3
"""R8's committed board for the suites that test R8's build tools on R8's board.

The R8-era suites (test_r8_place, test_r8_power, test_r8_ground, test_r8_route and test_reference_audit) each need
R8's built board (test_fab_validation used it too until R9 step 9 made the R9 fab package, R9_DECISIONS D-S9-05). Once R9 step 3 has built the R9 board in the worktree, board() hands them R8's committed project
instead: m3.kicad_pcb, m3.kicad_pro, m3.kicad_dru and the sheets from git commit 9c8179b (R8's own design rules: R9's
rule G also reports R8's known GATE_N via, r9_step1_handoff.md) in one temporary folder per process, with the
worktree's kilib and library tables linked beside it. While the worktree still holds R8's board (SHA-256 checked),
board() returns that file, as before.
"""
import atexit
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'm3_design/assembly_review'
R8_COMMIT = '9c8179b'
R8_SHA = 'cc044ea0922ff826df19af9d9726d92c096ab2b127025b55d123d8772e5fb4a7'
_FOLDER = []


def _git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, check=True).stdout


def board():
    """Path of R8's board (the worktree's file while it is R8's, else R8's committed project in a temporary folder)."""
    here = PROJECT / 'm3.kicad_pcb'
    if here.is_file() and hashlib.sha256(here.read_bytes()).hexdigest() == R8_SHA:
        return here
    if not _FOLDER:
        folder = Path(tempfile.mkdtemp(prefix='r8_record_'))
        atexit.register(shutil.rmtree, folder, True)
        rel = 'm3_design/assembly_review'
        names = [Path(n).name for n in _git('ls-tree', '--name-only', R8_COMMIT, f'{rel}/').decode().split()]
        for name in names:
            if name.startswith('m3.kicad_') or name.endswith('.kicad_sch') or name == 'schematic.net.xml':
                (folder / name).write_bytes(_git('show', f'{R8_COMMIT}:{rel}/{name}'))
        for name in ('kilib', 'fp-lib-table', 'sym-lib-table'):
            (folder / name).symlink_to(PROJECT / name)
        got = hashlib.sha256((folder / 'm3.kicad_pcb').read_bytes()).hexdigest()
        assert got == R8_SHA, f'git {R8_COMMIT} board is {got[:16]}, not R8'
        _FOLDER.append(folder)
    return _FOLDER[0] / 'm3.kicad_pcb'

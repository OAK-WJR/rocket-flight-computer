#!/usr/bin/env python3
"""The REQUIREMENTS M2 review sweep on the R9 board: R8's sweep (sources/r8_design/step9/m2_sweep.py, imported
unchanged) with route_check's profile r9 and no rigid copper (R9 is a clean sheet: nothing is inherited, so the
sweep's "rigid" markers are all false). Its output feeds docs/R9_VALIDATION.md "R9 deviations for owner acceptance"
part C.

usage: <KiCad python3> -I m3_design/assembly_review/sources/r9_design/step10/m2_sweep_r9.py [BOARD] [--json OUT]
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('m2_sweep', HERE.parents[1] / 'r8_design/step9/m2_sweep.py')
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)
_set = M.rc.set_profile
M.rc.set_profile = lambda _profile: _set('r9')          # R8's main() asks for 'r8'
M.r8_power_check.rigid_items = lambda board: []
M.RIGID_REFS = set()
M.STRIP_GND_Y = -1.0

if __name__ == '__main__':
    sys.exit(M.main())

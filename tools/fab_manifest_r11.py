"""R11 fab package binding (D-R11-08): tools/fab_manifest.py's binding, verification and content checks for
m3_design/r11/m3.kicad_pcb and its package m3_design/r11/fab/, with the S-4 content check run by tools/check_r11.py and
check_r11.py itself bound among the inputs. A separate file because tools/fab_manifest.py's own SHA-256 is one of the
inputs R10's frozen package is bound to: editing it would unbind R10.

usage: python3 tools/fab_manifest_r11.py [board]                  verify the binding (hashes only)
       python3 tools/fab_manifest_r11.py [board] --content        verify the binding, then run the content checks
       python3 tools/fab_manifest_r11.py [board] --bind RECORD    content checks on export_fab's record, then bind
"""
import argparse
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fab_manifest as fm                                        # noqa: E402

ROOT = fm.ROOT
R11_BOARD = ROOT / 'm3_design/r11/m3.kicad_pcb'
_base_inputs, _base_checks = fm.input_hashes, fm.content_checks


def input_hashes(board):
    result = _base_inputs(board)
    for name in ('check_r11.py', 'fab_manifest_r11.py'):
        result['tools/' + name] = fm.sha256(ROOT / 'tools' / name)
    return result


def content_checks(board, out, kicad_py):
    checks = _base_checks(board, out, kicad_py)
    label, argv = checks[0]
    assert label == 'S-4 BOM / CPL' and argv[2].endswith('check_r10.py'), checks[0]
    return [(label, argv[:2] + [str(ROOT / 'tools/check_r11.py')] + argv[3:])] + checks[1:]


def install():
    """Route fab_manifest's module-level functions through the R11 variants (they call each other by name)."""
    fm.input_hashes, fm.content_checks = input_hashes, content_checks


def main():
    install()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('board', nargs='?', type=Path, default=R11_BOARD)
    parser.add_argument('--out', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--bind', type=Path, metavar='RECORD')
    mode.add_argument('--content', action='store_true')
    args = parser.parse_args()
    out = args.out or args.board.parent / 'fab'
    try:
        if args.bind:
            path = fm.bind(args.board, out, args.bind)
            print(f'R11 fab manifest: bound {path.name} after the content checks')
        count = fm.verify_manifest(args.board, out)
        if args.content:
            failures = fm.run_content_checks(args.board, out)
            if failures:
                raise ValueError('content checks failed: ' + ', '.join(label for label, _ in failures))
    except (OSError, ValueError, KeyError, TypeError, AssertionError, subprocess.SubprocessError) as error:
        parser.exit(1, f'R11 fab manifest: FAIL: {error}\n')
    print(f'R11 fab manifest: OK; {count} outputs match the current CAD and export inputs'
          + ('; content checks pass' if args.content or args.bind else ''))


if __name__ == '__main__':
    main()

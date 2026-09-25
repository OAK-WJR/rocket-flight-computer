"""Generate explicit SYNTHETIC cases for review; no target connection."""
from pathlib import Path
from .engine import HERE, analyze, markdown
from .test_diagnostics import fixture, bench_fixture, BINDING
from .transport import atomic_json


def main():
    for name, regs, measurements in [
            ('blank_firmware', {}, None),
            ('filter_rail_missing', {}, {'3V3A': .05}),
            ('divider_swap', {}, {'VLOGIC_SENSE': 4.18}),
            ('wrong_chip', {'DBGMCU_IDCODE': 0x10000483}, None),
            ('partial_read', {'RCC_RSR': TimeoutError('synthetic timeout')}, None)]:
        path = HERE/'examples'/name
        path.mkdir(parents=True, exist_ok=False)
        s = fixture(regs)
        b = bench_fixture(s, measurements) if measurements else None
        atomic_json(path/'snapshot.json', s)
        if b: atomic_json(path/'bench.json', b)
        r = analyze(s, BINDING, b)
        atomic_json(path/'report.json', r)
        (path/'report.md').write_text(markdown(r))
        print(name, r['overall'], r['first_failed_check'])


if __name__ == '__main__':
    main()

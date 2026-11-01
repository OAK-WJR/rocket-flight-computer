"""Plot the shorted-igniter case from the ngspice suite (before and after R134).

Run m3_design/sim_r2/run.py first (needs ngspice), then:
    python3 m3_design/sim_r2/plot_short.py        # needs matplotlib
Writes docs/images/shorted_igniter_sim.png. Simulation only, not a bench measurement.
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / 'docs' / 'images' / 'shorted_igniter_sim.png'


def load(name):
    rows = (HERE / 'out' / f'{name}.dat').read_text().splitlines()
    head = rows[0].split()
    cols = {h: [] for h in head}
    for line in rows[1:]:
        for h, v in zip(head, line.split()):
            cols[h].append(float(v))
    return cols


cases = [('short_term_8v4_merged', 'before: no series resistor', '0.55'),
         ('short_term_8v4_asdrawn', 'after: 2 ohm in each channel (R134/R135)', '0.0')]
fig, (a, b) = plt.subplots(2, 1, figsize=(8, 5.2), sharex=True)
for name, label, grey in cases:
    d = load(name)
    t = [x * 1e3 for x in d['time']]
    a.plot(t, d['i(Vibw)'], color=grey, lw=1.4, label=label)
    b.plot(t, d['v(BAT_IN)'], color=grey, lw=1.4, label=label)
a.set_ylabel('igniter current (A)')
b.set_ylabel('battery input (V)')
b.axhline(5.0, color='0.3', lw=0.8, ls='--')
b.text(0.2, 5.15, '5 V: below this for > 3 ms the MCU may reset', fontsize=8)
b.set_xlabel('time (ms)')
a.set_title('Firing into a shorted igniter, 8.4 V pack (ngspice, simulated)', fontsize=10)
a.legend(fontsize=8, frameon=False)
for ax in (a, b):
    ax.spines[['top', 'right']].set_visible(False)
fig.tight_layout()
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=110)
print(OUT)

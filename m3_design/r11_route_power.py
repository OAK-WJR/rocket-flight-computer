"""R11 family `power` (stage C2, first part): the regulators' local control nets (r11_plan.md section 4; stageC2.md
section 4).

Explicit tables only (D-R11-07): each run below was drafted with a scratch maze aid on the board after `pyro` and frozen
here by hand (the build never searches). Board mm (x east, y forward from the aft edge, KiCad's y).

This first part draws the nets that close inside one regulator cell and need no In2 region: U9's dV/dt, ILIM and OVLO
legs (B.Cu), the BAT_DAMP damper (R166 / C89 / C95, F.Cu), U402's ILIM and U11's ILIM / soft-start. The distributed rails
(BAT_IN, RAW_PROTECTED, VLOGIC, 3V3, 3V3A, PORT_5V3, PORT_4V8, CAM_5V), the J400 / EN chain, the bucks' switch loops and
the In2 regions are stage C2's open items O-C2-1 ... (stageC2.md section 6): each needs a placement change first.
"""

NETS = ('BAT_DVDT', 'BAT_ILIM', 'BAT_OVLO', 'BAT_DAMP', 'CAM_ILIM', 'LOGIC_ILIM', 'LOGIC_SS')

RUNS = (
    # U9 (TPS25947, B.Cu): dV/dt to C81, ILIM to R84, OVLO to the R82 / R83 divider
    ('BAT_DVDT', 'B', 0.15, [('U9', '7'), (13.55, 8.4), ('C81', '1')]),
    ('BAT_ILIM', 'B', 0.15, [('U9', '9'), (16.0, 10.825), (17.4, 12.225)]),
    ('BAT_OVLO', 'B', 0.15, [('U9', '2'), (9.0, 10.825), ('R83', '1')]),
    ('BAT_OVLO', 'B', 0.15, [('R83', '1'), (6.8, 8.625)]),
    # the input damper: R166 (0.36 ohm) in series with C89 / C95 (22 uF), F.Cu north of R166's GND pad
    ('BAT_DAMP', 'F', 0.5, [('R166', '1'), (8.85, 11.95), (15.425, 11.95), ('C89', '2')]),
    ('BAT_DAMP', 'F', 0.5, [('C89', '2'), ('C95', '2')]),
    # U402 (camera switch) ILIM to R430, under the switch's body
    ('CAM_ILIM', 'F', 0.15, [('U402', '5'), (23.15, 9.4), (20.37, 12.18)]),
    # U11 (TPS2121) ILIM to R86, soft-start to C85
    ('LOGIC_ILIM', 'B', 0.15, [('U11', '10'), (15.85, 36.65), (15.85, 39.2), (15.5, 39.55)]),
    ('LOGIC_SS', 'B', 0.15, [('U11', '11'), (15.55, 37.45), (15.25, 37.75)]),
)


def draw(d):
    for net, layer, width, pts in RUNS:
        d.track(net, layer, width, [d.pad(p[0], p[1], net=net) if isinstance(p[0], str) else p for p in pts])

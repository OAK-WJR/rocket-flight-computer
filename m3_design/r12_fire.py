"""M3-ASSY-R12 S-10: the fire-net copper gaps (R12F5-TRI-01, tightened after the round 5 verifier, lane P2).

One definition, read by tools/check_r12.py (S-10 measures the board: tracks, vias, flashed pads, unflashed plated
barrels and every zone fill, on every copper layer, protected-net fills included) and by m3_design/r12_sch.py
(dru_rules(): the same classes and exceptions as DRC clearance rules, so DRC holds them too and every pour pulls back on
refill). Pure data and text, no pcbnew.

Fault model (R10 D-R26-02 / -04, AGENTS section 2.1): the bus is live from the on-rail check, so one bridge (solder, or
a later CAF / dendrite path) that raises Q124's gate, or that lets PYRO1_OUT sink current, fires an enabled match.

Default-deny: every foreign net counts against a protected net unless it is classed here with a calculated reason.
  * Q124's gate nets (PYRO1_GATE, PE4's PYRO1_GATE_N): GATE_MIN from every net except GND (holds the gate off), the
    gate pair itself and U1's NC balls (U1 pads whose net is unconnected-*: analog in reset, kept analog by firmware;
    every one within GATE_MIN is listed in S-10's evidence). Other parts' NC or unused pads, and copper with no net,
    count as foreign copper.
  * PYRO1_OUT: OUT_MIN from every net (3V3 / 3V3A as R10, every other rail, VLOGIC, MCU-pin nets and the low-side
    sinks ACT_DRV / BUZZ_OUT included) except GND (GND_MIN copper, FILL_MIN fills: R10 row 1 kept surface GND pairs
    near 0.18 mm), the pyro-network nets of NOT_A_PATH and the gate nets (their own, stricter, rule).
  * PYRO1_IGN (J121.2, RAW_ACT through R134 2 ohm): not a match-fire path, but a bridge to any lower net drives bus
    current through R134 (about 3.7 A, 27 W into the 2 W part with GND; Calculation): IGN_MIN copper, FILL_MIN fills,
    from every net but the match (PYRO1_OUT) and R134's own other end (RAW_ACT).
  * Measured exceptions (EXCEPTIONS): named item pairs, each with a floor at its measured gap (rounded down to 1 um)
    and a reason. A new item, or an excepted item that moves, is not excepted. A table pair missing from the board is a
    stale entry and fails S-10 too, so the record stays exact.
"""
import re

GATES = ('PYRO1_GATE', 'PYRO1_GATE_N')
OUT, IGN = 'PYRO1_OUT', 'PYRO1_IGN'
PROTECTED = GATES + (OUT, IGN)             # priority order: a pair is named from the first protected net it touches

GATE_MIN = 1.0585      # mm, R10 D-R26-04 (Q124's gate nets from 3V3 / 3V3A), widened to every raising net
OUT_MIN = 1.040        # mm, R10 D-R26-02 (PYRO1_OUT from 3V3 / 3V3A), widened to every net (default-deny)
GND_MIN = 0.25         # mm, PYRO1_OUT to GND copper (R10 row 1: 0.177 / 0.180 mm surface pairs)
FILL_MIN = 0.5         # mm, PYRO1_OUT to GND fills; PYRO1_IGN to every fill (J121.1 / J121.2 sat 0.10 mm from GND_pour_B)
IGN_MIN = 0.25         # mm, PYRO1_IGN to foreign copper (destructive, not a match-fire path)
DRU_GATE_MM = 1.06     # the DRU's gate figure (GATE_MIN rounded up to 10 um)
REACH = GATE_MIN + 0.01

# (protected net, foreign net): why one bridge between them is not a fire (or R134-overload) path. Calculations use the
# board's values (netlist): R126 220, R127 1k, R128 10k, R131 10k, R173 / R129 5.1k, R130 / R178 2k, D120 BAT54C.
NOT_A_PATH = {
    ('PYRO1_GATE', 'GND'): 'GND holds the gate off',
    ('PYRO1_GATE_N', 'GND'): 'GND holds the gate off',
    ('PYRO1_GATE', 'PYRO1_GATE_N'): 'the gate pair: a bridge only shorts R126 (220 ohm); PE4 still sets the gate',
    ('PYRO1_GATE_N', 'PYRO1_GATE'): 'the gate pair: a bridge only shorts R126 (220 ohm); PE4 still sets the gate',
    (OUT, IGN): 'the match\'s own terminals: a bridge shorts the match; with Q124 off no current flows, with Q124 on '
                'R134 limits it (the designed shorted-igniter case)',
    (OUT, 'PYRO1_COLD'): 'shorts R131 only: with the bus on PYRO1_OUT sits above 3V3, so D120 is reverse biased '
                         '(leakage only); with it off 3V3 reaches the match through D120 and then >= 10.2 kohm to GND '
                         'on either side: < 1 mA (Calculation)',
    (OUT, 'PYRO1_CONT_MID'): 'shorts R173 only: PYRO1_OUT then reaches PC0 through R129 5.1 kohm into R130 || R178 '
                             '1 kohm: <= 1.4 mA, PC0 <= 1.38 V at 8.4 V (Calculation)',
    (IGN, OUT): 'the match\'s own terminals (see PYRO1_OUT)',
    (IGN, 'RAW_ACT'): 'R134\'s own other end: a bridge only shorts R134; current flows only while Q124 conducts',
}
U1_NC = 'U1'          # only U1's NC balls are exempt (GPIOs, analog in reset (DS12110), kept analog by firmware)


def u1_nc(owner, net):
    return owner == U1_NC and net.startswith('unconnected-')


def one_way(protected, foreign, fill):
    """(limit mm or None, class) of foreign copper against a protected net; fill: either item is a zone fill."""
    if (protected, foreign) in NOT_A_PATH:
        return None, 'not a path'
    if protected in GATES:
        return GATE_MIN, 'gate'
    if protected == OUT:
        if foreign == 'GND':
            return (FILL_MIN if fill else GND_MIN), 'out-gnd'
        return OUT_MIN, 'out'
    if protected == IGN:
        return (FILL_MIN if fill else IGN_MIN), 'ign'
    return None, 'unprotected'


def pair_limit(net_a, owner_a, net_b, owner_b, fill):
    """S-10's limit for one pair of items of different nets: (limit, class, protected net) with limit None when the
    pair is not a path. Both directions count when both nets are protected; the stricter wins."""
    best = (None, 'unprotected', None)
    for pn, fn, fo in ((net_a, net_b, owner_b), (net_b, net_a, owner_a)):
        if pn not in PROTECTED:
            continue
        lim, cls = (None, 'U1 NC ball') if u1_nc(fo, fn) else one_way(pn, fn, fill)
        if best[2] is None or (lim is not None and (best[0] is None or lim > best[0])):
            best = (lim, cls, pn)
    return best


# Measured exceptions, grouped by reason: (protected item, foreign item, layer, floor mm). Item labels are
# check_r12.copper_items's; floors are the measured gaps on the board, rounded down to 1 um (tools: S-10's evidence).
WHY = {
    'D-R11-23': 'PE4\'s lane between U1\'s balls against 3V3 (U1.B2 / D2 and their dog-bones): fire-capable, the '
                'recorded D-R11-23 deviation (R12_VALIDATION row 25), unavoidable in the TFBGA-100 escape',
    'HSE_IN': 'HSE_IN has no DC drive: Y1, C25 15 pF to GND and only OSC_OUT\'s internal feedback resistor (about '
              '200 kohm, DS12110 typical: Inference); with PE4 high-Z that is <= 3.3 V x 0.95 k / 201 k = 16 mV, and '
              'HSE is off in reset (Calculation / Inference)',
    'HSE_OUT': 'OSC_OUT drives against PE4: while PE4 drives low (V_OL <= 0.4 V at 8 mA, DS12110) the gate stays <= '
               '0.39 V, below AO3400A V_GS(th) min 0.65 V, if OSC_OUT sources <= 8 mA (Inference, not '
               'characterised); HSE is off in reset. Depends on R12 firmware rule 3 (PE4 driven low before HSE is '
               'enabled; an HSE start failure or CSS event on the ground refuses)',
    'QSPI_IO2': 'fire-capable: R10 firmware rule 3 (R23-SAFETY-08) finds an IO2-against-PE4 fight puts 1.19-1.98 V '
                'on the gate (Inference); held only by R12 firmware rule 3 (QSPI rules, quad read-verify ground '
                'refusal) and the first-article X-ray / meter test',
    'BOOT0': 'BOOT0 is an input-only pin held by R5 10 kohm to GND and not on J2: no source can raise PE4 '
             '(Calculation)',
    'BAT_FAULT_N': 'U9 open-drain FLT with R89 10 kohm to 3V3, read by PC13 (ball A2, an input): with PE4 high-Z the '
                   'gate is <= 3.38 V x 0.952 k / 10.85 k x 10 / 10.22 = 0.29 V, below AO3400A V_GS(th) min 0.65 V '
                   '(Calculation: 3V3 +2.5 %, R89 -1 %, R127 +5 %); firmware never makes PC13 an output',
    'Q124': 'the AO3400A SOT-23\'s own gate (pin 1) and drain (pin 3) lands',
    'PYRO1_CONT': 'PYRO1_CONT is PC0\'s pin: a bridge puts PYRO1_OUT on PC0, whose input clamp then passes bus current '
                  'through the match into 3V3 (fire-capable or logic-destroying; Inference): the 0402 continuity '
                  'divider\'s own neighbours, surface, AOI-inspectable; owner acceptance',
}
EXCEPTIONS = {
    'D-R11-23': (
        ('U1.C3', 'U1.B2', 'F.Cu', 0.731),
        ('U1.C3', 'U1.D2', 'F.Cu', 0.731),
        ('U1.C3', 'track (20.2, 51.2)-(19.8, 50.8)', 'F.Cu', 0.881),
        ('U1.C3', 'track (20.2, 52.8)-(20.6, 53.2)', 'F.Cu', 0.881),
        ('U1.C3', 'via (20.6, 53.2)', 'F.Cu', 0.839),
        ('track (18.7, 51.4)-(18.7, 46.8)', 'track (20.2, 51.2)-(19.8, 50.8)', 'F.Cu', 1.000),
        ('track (18.7, 51.4)-(18.7, 46.8)', 'via (19.8, 50.8)', 'F.Cu', 0.825),
        ('track (18.9, 51.6)-(18.7, 51.4)', 'via (19.8, 50.8)', 'F.Cu', 0.929),
        ('track (20.6, 51.6)-(18.9, 51.6)', 'U1.B2', 'F.Cu', 0.150),
        ('track (20.6, 51.6)-(18.9, 51.6)', 'U1.D2', 'F.Cu', 0.950),
        ('track (20.6, 51.6)-(18.9, 51.6)', 'track (20.2, 51.2)-(19.8, 50.8)', 'F.Cu', 0.300),
        ('track (20.6, 51.6)-(18.9, 51.6)', 'via (19.8, 50.8)', 'F.Cu', 0.525),
        ('track (21, 52)-(20.6, 51.6)', 'U1.B2', 'F.Cu', 0.315),
        ('track (21, 52)-(20.6, 51.6)', 'U1.D2', 'F.Cu', 0.881),
        ('track (21, 52)-(20.6, 51.6)', 'track (20.2, 51.2)-(19.8, 50.8)', 'F.Cu', 0.465),
        ('track (21, 52)-(20.6, 51.6)', 'track (20.2, 52.8)-(20.6, 53.2)', 'F.Cu', 1.031),
        ('track (21, 52)-(20.6, 51.6)', 'via (19.8, 50.8)', 'F.Cu', 0.856),
        ('track (21, 52)-(20.6, 51.6)', 'via (20.6, 53.2)', 'F.Cu', 0.989),
    ),
    'HSE_IN': (
        ('track (18.7, 51.4)-(18.7, 46.8)', 'U1.C1', 'F.Cu', 0.672),
        ('track (18.7, 51.4)-(18.7, 46.8)', 'track (19.4, 52)-(16.2, 52)', 'F.Cu', 0.500),
        ('track (18.9, 51.6)-(18.7, 51.4)', 'U1.C1', 'F.Cu', 0.390),
        ('track (18.9, 51.6)-(18.7, 51.4)', 'track (19.4, 52)-(16.2, 52)', 'F.Cu', 0.300),
        ('track (20.6, 51.6)-(18.9, 51.6)', 'U1.C1', 'F.Cu', 0.150),
        ('track (20.6, 51.6)-(18.9, 51.6)', 'track (19.4, 52)-(16.2, 52)', 'F.Cu', 0.300),
        ('track (21, 52)-(20.6, 51.6)', 'U1.C1', 'F.Cu', 1.015),
    ),
    'PYRO1_CONT': (
        ('R173.1', 'R129.2', 'F.Cu', 0.464),
        ('R173.1', 'track (12.9, 47.1)-(12.1, 47.9)', 'F.Cu', 0.806),
        ('track (11.5, 46.7)-(12, 46.2)', 'R129.2', 'F.Cu', 0.816),
        ('track (11.5, 46.7)-(12, 46.2)', 'R130.1', 'F.Cu', 1.000),
        ('track (9.1, 46.7)-(11.5, 46.7)', 'R130.1', 'F.Cu', 1.000),
    ),
    'BOOT0': (
        ('track (18.7, 51.4)-(18.7, 46.8)', 'track (17.8, 48.2)-(16.7, 47.1)', 'F.Cu', 0.800),
        ('track (18.7, 51.4)-(18.7, 46.8)', 'via (17.8, 48.2)', 'F.Cu', 0.625),
    ),
    'HSE_OUT': (
        ('track (18.7, 51.4)-(18.7, 46.8)', 'track (19.02, 52.42)-(15.08, 52.42)', 'F.Cu', 0.920),
        ('track (18.7, 51.4)-(18.7, 46.8)', 'track (19.4, 52.8)-(19.02, 52.42)', 'F.Cu', 0.969),
        ('track (18.9, 51.6)-(18.7, 51.4)', 'U1.D1', 'F.Cu', 1.050),
        ('track (18.9, 51.6)-(18.7, 51.4)', 'track (19.02, 52.42)-(15.08, 52.42)', 'F.Cu', 0.720),
        ('track (18.9, 51.6)-(18.7, 51.4)', 'track (19.4, 52.8)-(19.02, 52.42)', 'F.Cu', 0.728),
        ('track (20.6, 51.6)-(18.9, 51.6)', 'U1.D1', 'F.Cu', 0.950),
        ('track (20.6, 51.6)-(18.9, 51.6)', 'track (19.02, 52.42)-(15.08, 52.42)', 'F.Cu', 0.720),
        ('track (20.6, 51.6)-(18.9, 51.6)', 'track (19.4, 52.8)-(19.02, 52.42)', 'F.Cu', 0.720),
    ),
    'QSPI_IO2': (
        ('U1.C3', 'track (21, 50.4)-(21.4, 50.8)', 'F.Cu', 1.015),
        ('U1.C3', 'via (21.4, 50.8)', 'F.Cu', 0.839),
        ('track (20.6, 51.6)-(18.9, 51.6)', 'U1.A3', 'F.Cu', 1.015),
        ('track (20.6, 51.6)-(18.9, 51.6)', 'track (21, 50.4)-(21.4, 50.8)', 'F.Cu', 1.031),
        ('track (20.6, 51.6)-(18.9, 51.6)', 'via (21.4, 50.8)', 'F.Cu', 0.856),
        ('track (21, 52)-(20.6, 51.6)', 'U1.A3', 'F.Cu', 1.015),
        ('track (21, 52)-(20.6, 51.6)', 'track (21, 50.4)-(21.4, 50.8)', 'F.Cu', 1.031),
        ('track (21, 52)-(20.6, 51.6)', 'via (21.4, 50.8)', 'F.Cu', 0.856),
    ),
    'BAT_FAULT_N': (
        ('track (20.6, 51.6)-(18.9, 51.6)', 'U1.A2', 'F.Cu', 0.950),
        ('track (21, 52)-(20.6, 51.6)', 'U1.A2', 'F.Cu', 1.015),
    ),
    'Q124': (
        ('Q124.1', 'Q124.3', 'F.Cu', 1.044),
    ),
}
EXCEPTION_NETS = {
    'Q124.1': 'PYRO1_GATE',
    'Q124.3': 'PYRO1_OUT',
    'R129.2': 'PYRO1_CONT',
    'R130.1': 'PYRO1_CONT',
    'R173.1': 'PYRO1_OUT',
    'U1.A2': 'BAT_FAULT_N',
    'U1.A3': 'QSPI_IO2',
    'U1.B2': '3V3',
    'U1.C1': 'HSE_IN',
    'U1.C3': 'PYRO1_GATE_N',
    'U1.D1': 'HSE_OUT',
    'U1.D2': '3V3',
    'track (11.5, 46.7)-(12, 46.2)': 'PYRO1_OUT',
    'track (12.9, 47.1)-(12.1, 47.9)': 'PYRO1_CONT',
    'track (17.8, 48.2)-(16.7, 47.1)': 'BOOT0',
    'track (18.7, 51.4)-(18.7, 46.8)': 'PYRO1_GATE_N',
    'track (18.9, 51.6)-(18.7, 51.4)': 'PYRO1_GATE_N',
    'track (19.02, 52.42)-(15.08, 52.42)': 'HSE_OUT',
    'track (19.4, 52)-(16.2, 52)': 'HSE_IN',
    'track (19.4, 52.8)-(19.02, 52.42)': 'HSE_OUT',
    'track (20.2, 51.2)-(19.8, 50.8)': '3V3',
    'track (20.2, 52.8)-(20.6, 53.2)': '3V3',
    'track (20.6, 51.6)-(18.9, 51.6)': 'PYRO1_GATE_N',
    'track (21, 50.4)-(21.4, 50.8)': 'QSPI_IO2',
    'track (21, 52)-(20.6, 51.6)': 'PYRO1_GATE_N',
    'track (9.1, 46.7)-(11.5, 46.7)': 'PYRO1_OUT',
    'via (17.8, 48.2)': 'BOOT0',
    'via (19.8, 50.8)': '3V3',
    'via (20.6, 53.2)': '3V3',
    'via (21.4, 50.8)': 'QSPI_IO2',
}


def exception_index(exceptions=None):
    """{(protected item, foreign item, layer): (floor, reason key)}."""
    exceptions = EXCEPTIONS if exceptions is None else exceptions
    return {(a, b, layer): (floor, key) for key, pairs in exceptions.items() for a, b, layer, floor in pairs}


# ---- DRU text ------------------------------------------------------------------------------------------------------
NOT_PROBE = ("!A.memberOfFootprint('TP*') && !B.memberOfFootprint('TP*') && !A.memberOfFootprint('J2') && "
             "!B.memberOfFootprint('J2')")
NOT_U1_NC = "!(B.memberOfFootprint('U1') && B.NetName == 'unconnected-*')"
EITHER_FILL = "(A.Type == 'Zone' || B.Type == 'Zone')"


def _is(side, nets):
    return '(' + ' || '.join(f"{side}.NetName == '{n}'" for n in nets) + ')'


def _not(side, nets):
    return ' && '.join(f"{side}.NetName != '{n}'" for n in nets)


def _excluded(protected):
    return tuple(sorted({f for (p, f) in NOT_A_PATH if p == protected}))


def item_condition(side, label, net):
    """A DRU condition naming one copper item by its check_r12 label (a pad, a via or a track)."""
    cond = f"{side}.NetName == '{net}'"
    m = re.fullmatch(r'via \(([-\d.]+), ([-\d.]+)\)', label)
    if m:
        return cond + f" && {side}.Type == 'Via' && {side}.Position_X == {m[1]}mm && {side}.Position_Y == {m[2]}mm"
    m = re.fullmatch(r'track \(([-\d.]+), ([-\d.]+)\)-\(([-\d.]+), ([-\d.]+)\)', label)
    if m:
        return cond + (f" && {side}.Type == 'Track' && {side}.Start_X == {m[1]}mm && {side}.Start_Y == {m[2]}mm && "
                       f"{side}.End_X == {m[3]}mm && {side}.End_Y == {m[4]}mm")
    m = re.fullmatch(r'([A-Z]+\d+)\.(\w+)', label)
    if m:
        return cond + f" && {side}.memberOfFootprint('{m[1]}') && {side}.Pad_Number == '{m[2]}'"
    raise ValueError(f'S-10 exception item {label!r} cannot be named in the DRU')


def dru_rules(exceptions=None, nets=None):
    """The DRU's S-10 rules, in order: (name, constraint, condition, comment, layer or None). KiCad applies the last
    matching rule, so the general rules come first and the item-pair exceptions after them; no general rule may match a
    pair another, stricter, general rule governs (the gate nets, PYRO1_OUT and PYRO1_IGN exclude each other)."""
    exceptions = EXCEPTIONS if exceptions is None else exceptions
    nets = EXCEPTION_NETS if nets is None else nets
    out_x = (OUT, 'GND') + GATES + _excluded(OUT)
    ign_x = (IGN,) + GATES + _excluded(IGN)
    rules = [
        ('S-10 Q124 gate nets to every raising net', f'clearance (min {DRU_GATE_MM}mm)',
         f"{_is('A', GATES)} && {_not('B', GATES + ('GND',))} && {NOT_U1_NC}",
         f'R10 D-R26-04 ({GATE_MIN} mm), default-deny: every net but GND, the gate pair and U1 NC balls '
         '(check_r12 S-10, m3_design/r12_fire.py)', None),
        ('S-10 PYRO1_OUT to every net', f'clearance (min {OUT_MIN:.2f}mm)',
         f"A.NetName == '{OUT}' && {_not('B', out_x)} && {NOT_U1_NC}",
         f'R10 D-R26-02 ({OUT_MIN:.3f} mm), default-deny: every net but GND, the gate nets (their own rule) and '
         'PYRO1_IGN / _COLD / _CONT_MID (check_r12 S-10)', None),
        ('S-10 PYRO1_OUT to GND', f'clearance (min {GND_MIN}mm)',
         f"A.NetName == '{OUT}' && B.NetName == 'GND' && {NOT_PROBE}",
         'R10 row 1 surface pairs 0.177 / 0.180 mm, R12 0.25 mm (check_r12 S-10)', None),
        ('S-10 PYRO1_OUT to GND fills', f'clearance (min {FILL_MIN}mm)',
         f"A.NetName == '{OUT}' && B.NetName == 'GND' && {EITHER_FILL} && {NOT_PROBE}",
         'R12F5-TRI-01: J121.1 sat 0.101 mm from GND_pour_B (check_r12 S-10)', None),
        ('S-10 PYRO1_IGN to every net', f'clearance (min {IGN_MIN}mm)',
         f"A.NetName == '{IGN}' && {_not('B', ign_x)} && {NOT_U1_NC} && {NOT_PROBE}",
         'R134 overload: J121.2 sat 0.100 mm from GND_pour_B (round 5 verifier; check_r12 S-10)', None),
        ('S-10 PYRO1_IGN to fills', f'clearance (min {FILL_MIN}mm)',
         f"A.NetName == '{IGN}' && {_not('B', ign_x)} && {EITHER_FILL} && {NOT_PROBE}",
         'R134 overload: every pour >= 0.5 mm from J121.2 (check_r12 S-10)', None),
    ]
    for key, pairs in exceptions.items():
        for a, b, layer, floor in pairs:
            na, nb = nets[a], nets[b]
            rules.append((f'S-10 exception ({key}): {a} to {b} on {layer}', f'clearance (min {floor:.3f}mm)',
                          f'{item_condition("A", a, na)} && {item_condition("B", b, nb)}',
                          f'measured floor {floor:.3f} mm, reason {key} (check_r12 S-10, m3_design/r12_fire.py)',
                          layer))
    return rules


def dru_text(rule):
    name, constraint, condition, why, layer = rule
    return (f'# {why}\n(rule "{name}"\n' + (f'  (layer "{layer}")\n' if layer else '') +
            f'  (condition "{condition}")\n  (constraint {constraint}))')


# ---- the netlist's own classes (default-deny guard) ------------------------------------------------------------------
def netlist_classes(path):
    """Nets the schematic netlist marks as able to sink or source current: low-side switch drains (a FET's D whose S is
    on GND), open-drain / open-collector outputs, supply pins and inductor (L<n>) terminals, and every U1 pin."""
    import xml.etree.ElementTree as ET
    root = ET.parse(path).getroot()
    by_ref = {}
    for n in root.findall('./nets/net'):
        for p in n.findall('node'):
            by_ref.setdefault(p.get('ref'), []).append((n.get('name'), p.get('pinfunction') or '',
                                                        p.get('pintype') or ''))
    out = dict(sink=set(), open_drain=set(), supply=set(), mcu=set())
    for ref, pins in by_ref.items():
        role = {f.split('_')[0]: net for net, f, _ in pins}
        if ref.startswith('Q') and role.get('S') == 'GND' and 'D' in role:
            out['sink'].add(role['D'])
        for net, _, kind in pins:
            if net.startswith('unconnected-'):
                continue
            if kind.startswith(('open_collector', 'open_emitter')):
                out['open_drain'].add(net)
            if kind.startswith(('power_in', 'power_out')) or re.fullmatch(r'L\d+', ref):
                out['supply'].add(net)
            if ref == 'U1':
                out['mcu'].add(net)
    for v in out.values():
        v.discard('GND')
    return {k: sorted(v) for k, v in out.items()}


def guard(classes, not_a_path=None):
    """NOT_A_PATH entries (other than GND and the protected nets, which S-10 holds by their own class) whose foreign net the netlist marks as a sink or source:
    such a net can never be classed out of S-10."""
    bad = []
    for (p, f) in (NOT_A_PATH if not_a_path is None else not_a_path):
        if f == 'GND' or f in PROTECTED:
            continue
        hit = [k for k, v in classes.items() if f in v]
        if hit:
            bad.append(f'{p} / {f} is classed "not a path", but the netlist marks {f} as {" / ".join(hit)}')
    return bad

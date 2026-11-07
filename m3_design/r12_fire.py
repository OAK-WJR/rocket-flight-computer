"""M3-ASSY-R12 S-10: the fire-net copper gaps (R12F5-TRI-01, tightened after the round 5 verifier, lane P2; the
fire-state class review and the NC-ball scope of round 6, R12F6-TRI-01 / -02).

One definition, read by tools/check_r12.py (S-10 measures the board: tracks, vias, flashed pads, unflashed plated
barrels and every zone fill, on every copper layer, protected-net fills included) and by m3_design/r12_sch.py
(dru_rules(): the same classes and exceptions as DRC clearance rules, so DRC holds them too and every pour pulls back on
refill). Pure data and text, no pcbnew.

Fault model (R10 D-R26-02 / -04, AGENTS section 2.1): the bus is live from the on-rail check, so one bridge (solder, or
a later CAF / dendrite path) that raises Q124's gate, or that lets PYRO1_OUT sink current, fires an enabled match.
R12F6-TRI-01: a class is "not a path" only if it holds in every state: bus off, bus on with Q124 off, and a commanded
fire, while Q124 holds PYRO1_OUT near GND (about 0.05 V) and a bridge to PYRO1_OUT is a bridge to GND. fire_state_guard()
checks that last state on the netlist: every not-a-path net reaches every source (rail, MCU pin, IC or connector) only
through at least FIRE_SERIES_MIN of resistors.

Default-deny: every foreign net counts against a protected net unless it is classed here with a calculated reason.
  * Q124's gate nets (PYRO1_GATE, PE4's PYRO1_GATE_N): GATE_MIN from every net except GND (holds the gate off), the
    gate pair itself and U1's NC balls (U1 pads whose net is unconnected-*: analog in reset, kept analog by firmware;
    every one within GATE_MIN is listed in S-10's evidence). Other parts' NC or unused pads, and copper with no net,
    count as foreign copper. The NC-ball exemption is the gate nets' only (R12F6-TRI-02): its reason covers raising a
    gate, not sinking PYRO1_OUT's current or taking PYRO1_IGN's bus voltage, so an NC ball counts against
    PYRO1_OUT and PYRO1_IGN like any other net.
  * PYRO1_OUT: OUT_MIN from every net (3V3 / 3V3A as R10, every other rail, VLOGIC, MCU-pin nets and the low-side
    sinks ACT_DRV / BUZZ_OUT included) except GND (GND_MIN copper, FILL_MIN fills: R10 row 1 kept surface GND pairs
    near 0.18 mm), the pyro-network nets of NOT_A_PATH and the gate nets (their own, stricter, rule).
  * PYRO1_IGN (J121.2, RAW_ACT through R134 2 ohm): not a match-fire path, but a bridge to any lower net drives bus
    current through R134 (about 3.7 A, 27 W into the 2 W part with GND; Calculation): IGN_MIN copper, FILL_MIN fills,
    from every net but the match (PYRO1_OUT) and R134's own other end (RAW_ACT).
  * Pack-energy nets (PACK, round 6 verifier V-1 / V-2): every net that carries the pack's current with no
    current-limiting element, derived from the netlist by pack_nets() (default-deny: from the battery pad J1.1 through
    every part but capacitors, test points, resistors of at least PACK_R_LIMIT, MOSFET gates and the named limiter U9;
    an unclassified part on a pack net fails S-10): BAT_IN (the pack itself), ACT_FET_S (through Q120's channel or
    body diode, live even with J400 open) and RAW_ACT (through Q121 with the bus on). A bridge from one of them to GND
    (or to BAT_DAMP, 0.36 ohm to GND) shorts the unfused pack (R10 recorded about 23 A for RAW_ACT to GND, D-R21-05),
    and one to a logic or MCU-pin net puts up to 8.4 V on a 3.3 V pin and the 3V3 rail (logic-destroying, and the
    FMEA I-5 fire mechanism): PACK_MIN (R10 D-R26-02's 1.040 mm, the PYRO1_OUT figure, as the same rail-onto-logic
    mechanism) from every net, copper and fills alike, except the other pack nets, the bus switch gate ACT_GATE and the
    two resistor ends NOT_A_PATH names (each with a calculated reason, checked by pack_class_guard()).
  * FMEA I-5 rails (R12F7-TRI-01): every rail that can sit above 3V3, derived from the netlist by i5_rails(), against
    3V3 / 3V3A only (the MCU's supplies; U1's absolute maximum is 4.0 V). A bridge puts the rail on 3V3 and the
    over-driven MCU may drive PE4 (and PC1) high: fire-capable once the bus is on (Inference, R10's I-5 reasoning; R12
    has no 3V3 clamp). Pack-voltage rails (I5_PACK: U9's OUT RAW_PROTECTED, VLOGIC behind D5, and the converters'
    switch and bootstrap nodes, which swing to their VIN) take PACK_MIN, D-R12-137's own figure for pack voltage onto
    logic: U9's current limit (3.92-4.89 A) bounds the current of a short, not the voltage it puts on 3V3 (up to OVLO).
    Port-voltage rails (I5_PORT: the 5.4 V camera and 4.8 V port buck outputs, USB VBUS; <= 5.76 V) take I5_PORT_MIN,
    R10's 0.300 mm owner-row figure, with the residual exposure an owner-acceptance row.
  * U9's FLT (round 6 verifier V-1 follow-up, PACK_FLT): U9.4 sits beside U9.5 (BAT_IN) in its package, so its net
    U9_FLT reaches PC13 only through R95 10 kohm, with R89 on U9's side and D95 clamping PC13 (an FT pin) to 3V3;
    flt_guard() holds that on the netlist. The PACK_FLT pairs stay measured exceptions (U9's own pin is over-driven).
  * Measured exceptions (EXCEPTIONS): named item pairs, each with a floor at its measured gap (rounded down to 1 um)
    and a reason. A new item, or an excepted item that moves, is not excepted. A table pair missing from the board is a
    stale entry and fails S-10 too, so the record stays exact.
"""
import re

GATES = ('PYRO1_GATE', 'PYRO1_GATE_N')
OUT, IGN = 'PYRO1_OUT', 'PYRO1_IGN'
PACK = ('BAT_IN', 'ACT_FET_S', 'RAW_ACT')  # the pack-energy nets (pack_nets() must derive exactly these)
LOGIC = ('3V3', '3V3A')                    # the MCU's supplies (FMEA I-5's victims)
# FMEA I-5 (R12F7-TRI-01): i5_rails() must derive exactly these from the netlist (i5_guard())
I5_PACK = ('RAW_PROTECTED', 'VLOGIC', 'BST', 'SW_NODE', 'CAM_BST', 'CAM_SW', 'PORT_BST', 'PORT_SW')
I5_PORT = ('CAM_5V', 'PORT_4V8', 'VBUS')
PROTECTED = GATES + (OUT, IGN) + PACK + I5_PACK + I5_PORT   # priority order: a pair is named from the first protected net

GATE_MIN = 1.0585      # mm, R10 D-R26-04 (Q124's gate nets from 3V3 / 3V3A), widened to every raising net
OUT_MIN = 1.040        # mm, R10 D-R26-02 (PYRO1_OUT from 3V3 / 3V3A), widened to every net (default-deny)
GND_MIN = 0.25         # mm, PYRO1_OUT to GND copper (R10 row 1: 0.177 / 0.180 mm surface pairs)
FILL_MIN = 0.5         # mm, PYRO1_OUT to GND fills; PYRO1_IGN to every fill (J121.1 / J121.2 sat 0.10 mm from GND_pour_B)
IGN_MIN = 0.25         # mm, PYRO1_IGN to foreign copper (destructive, not a match-fire path)
PACK_MIN = 1.040       # mm, pack-energy nets from every net, copper and fills (R10 D-R26-02's PYRO1_OUT figure: the
#                        same pack-voltage-onto-logic mechanism, and an unfused pack short is no less severe; round 6 V-1)
I5_PORT_MIN = 0.300    # mm, port-voltage rails from 3V3 / 3V3A (R10 owner row 1's 0.300 mm; R12F7-TRI-01)
DRU_GATE_MM = 1.06     # the DRU's gate figure (GATE_MIN rounded up to 10 um)
REACH = GATE_MIN + 0.01

# (protected net, foreign net): why one bridge between them is not a fire (or R134-overload) path, in every state (bus
# off; bus on, Q124 off; a commanded fire, Q124 on). Calculations use the board's values (netlist): R126 220, R127 1k,
# R128 10k, R136 / R131 / R173 / R129 5.1k, R130 / R178 2k, D120 BAT54C; 3V3 at most 3.516 V (U2 LMR50410XDBVR PFM
# band, SLUSDW3A section 7.8, R12F6-TRI-03; that window's application at R12's VIN is an Inference, D-R12-139, so every
# figure resting on it is labelled "Calculation / Inference (3V3 window, D-R12-139)", R12F7-TRI-02); resistors at their
# drift ends (1 % + 100 ppm/K over 67 K: +/-1.67 %).
NOT_A_PATH = {
    ('PYRO1_GATE', 'GND'): 'GND holds the gate off (in a commanded fire PE4 then drives R126 220 ohm into GND, <= 17 mA, '
                           'and the fire fails: a hold-off, outside the unwanted-fire model)',
    ('PYRO1_GATE_N', 'GND'): 'GND holds the gate off (in a commanded fire PE4 then drives the bridge directly, above its '
                             'per-pin rating (Inference on damage), and the fire fails: a hold-off; 3V3 is not '
                             'collapsed)',
    ('PYRO1_GATE', 'PYRO1_GATE_N'): 'the gate pair: a bridge only shorts R126 (220 ohm); PE4 still sets the gate (in a '
                                    'fire it charges C126 220 nF directly: a transient, no sustained path)',
    ('PYRO1_GATE_N', 'PYRO1_GATE'): 'the gate pair: a bridge only shorts R126 (220 ohm); PE4 still sets the gate (in a '
                                    'fire it charges C126 220 nF directly: a transient, no sustained path)',
    (OUT, IGN): 'the match\'s own terminals: a bridge shorts the match; with Q124 off no current flows, with Q124 on '
                'R134 limits it (the designed shorted-igniter case)',
    (OUT, 'PYRO1_COLD'): 'shorts R131 only (R12F6-TRI-01): R136 5.1 kohm stays between 3V3 and the bridge. Bus on, Q124 '
                         'off: PYRO1_OUT sits above 3V3, so D120 is reverse biased (leakage only). Commanded fire, '
                         'Q124 on (PYRO1_OUT near GND): 3V3 -> R136 -> D120 -> bridge -> Q124 passes <= 3.516 V / '
                         '5.015 kohm = 0.71 mA (D120 V_F taken as 0), not U2\'s current limit. Bus off: 3V3 reaches the '
                         'match through R136 and D120, then R173 + R129 + R130 || R178 (11.2 kohm) to GND: <= 0.71 mA '
                         '(Calculation / Inference (3V3 window, D-R12-139))',
    (OUT, 'PYRO1_CONT_MID'): 'shorts R173 only: bus on, Q124 off, PYRO1_OUT reaches PC0 through R129 5.1 kohm into '
                             'R130 || R178 1 kohm: <= 1.41 mA, PC0 <= 1.42 V at 8.4 V (Calculation: 1.400 V with 1 % '
                             'parts, 1.416 V at the +/-1.67 % drift ends; R12F6-TRI-05). Commanded fire, Q124 on: '
                             'PYRO1_OUT is near GND, so PC0 reads near 0 V through R129 (no source on the node). Bus '
                             'off: the cold pull-up meets R129 + R130 || R178 (6.1 kohm) instead of 11.2 kohm, < 0.71 mA '
                             '(Calculation / Inference (3V3 window, D-R12-139))',
    (IGN, OUT): 'the match\'s own terminals (see PYRO1_OUT)',
    (IGN, 'RAW_ACT'): 'R134\'s own other end: a bridge only shorts R134. With Q124 off no current flows (the match and '
                      'Q124 block). With Q124 on, the current is limited only by the match, its leads and the loop '
                      '(the pack, Q120 / Q121 and the copper): about 3.1 A at 8.4 V with a sound match (round 6 triage, '
                      'Calculation / Inference on the match and loop resistance), and more into a match that shorts '
                      'after firing (R10 records about 12 A, Inference). U9 is not in this path: the bus is taken '
                      'from BAT_IN, U9\'s input (round 6 verifier V-3), so nothing on the board limits it; the pack '
                      'sags under the pulse while the logic sits behind U9 and C84 (Inference on pack ESR). Not an '
                      'unwanted fire (current flows only while PE4 commands Q124 on) and not a pack-energy pair '
                      '(the match stays in series); the bypass removes R134\'s shorted-match limit, as R10 recorded',
    # Pack-energy nets (round 6 verifier V-1 / V-2): the pairs below carry no overload in any state. pack_class_guard()
    # checks each foreign net on the netlist: it is no supply, MCU, open-drain or sink net, and it reaches every source
    # (rail, MCU pin, IC or transistor pin; GND counts) only through at least PACK_SERIES_MIN.
    ('BAT_IN', 'ACT_FET_S'): 'Q120\'s own channel: both nets are the pack (ACT_FET_S through Q120\'s body diode even '
                             'with J400 open), so a bridge carries no current beyond the load Q120 itself carries; it '
                             'only takes Q120\'s on-resistance out of the bus path. Not a fire: Q121 still switches the '
                             'bus, and Q124 with R128 still holds the match',
    ('BAT_IN', 'RAW_ACT'): 'bypasses Q120 / Q121: the bus is then live from the pack even with J400 open or PC1 low (no '
                           'overload: both sides are the pack). Not a fire alone: Q124 with R128 still holds the match '
                           '(the cold screen reads the bus live and refuses; FMEA H-6)',
    ('ACT_FET_S', 'BAT_IN'): 'Q120\'s own channel (see BAT_IN)',
    ('ACT_FET_S', 'RAW_ACT'): 'Q121\'s own channel: bypasses Q121, so the bus is live from the pack through Q120\'s '
                              'body diode even with J400 open (no overload: both sides are the pack). Not a fire alone: '
                              'Q124 with R128 still holds the match',
    ('RAW_ACT', 'BAT_IN'): 'bypasses Q120 / Q121 (see BAT_IN)',
    ('RAW_ACT', 'ACT_FET_S'): 'Q121\'s own channel (see ACT_FET_S)',
    ('BAT_IN', 'ACT_GATE'): 'the bus switch gate: a bridge sets Q120 / Q121 V_GS to about 0 V, so the bus cannot turn '
                            'on (a hold-off), and Q122 then sinks the pack only through R121 10 kohm: <= 8.4 V / '
                            '9.83 kohm = 0.86 mA (Calculation, R121 at its -1.67 % drift end)',
    ('ACT_FET_S', 'ACT_GATE'): 'the bus switch gate (R119 / R120 100 kohm\'s own other end): V_GS about 0 V, the bus '
                               'cannot turn on (a hold-off); Q122 sinks <= 0.86 mA through R121 10 kohm (Calculation)',
    ('RAW_ACT', 'ACT_GATE'): 'the bus switch gate, not a hold-off (R12F7-TRI-04). Bus off (PC1 low, Q122 off, or J400 '
                             'open with ACT_FET_S live through Q120\'s body diode): the bridge ties the gate node to '
                             'RAW_ACT, which its 11.2 kohm load holds low, so the node sits near 0.18 x ACT_FET_S (R119 '
                             '|| R120 50 kohm against the load) and Q120 / Q121 see V_GS about -0.82 x ACT_FET_S, far '
                             'past V_GS(th) -0.5 ... -1.3 V: both turn on, Q121 settles diode-connected and the bus goes '
                             'live (RAW_ACT about BAT_IN less 1 V) with PC1 low or J400 open (Calculation; the settling '
                             'point Inference). Bus on: the gate meets Q121\'s drain, so the bus is not held on '
                             'cleanly; Q122 sinks <= 0.86 mA through R121 10 kohm (Calculation). The consequence is the '
                             'bypass classes\' (BAT_IN / ACT_FET_S to RAW_ACT: a bus live without command, the carried '
                             'R10 row 2 latent fault the cold screen and the per-flight J121.2 < 0.1 V check see); no '
                             'overload, and not a fire alone: Q124 with R128 still holds the match',
    ('RAW_ACT', 'ARM1_SENSE_MID'): 'R132\'s own other end: a bridge only shorts R132 (5.1 kohm); R175 5.1 kohm and R133 '
                                   '|| R180 1 kohm still divide the bus, so PC5 <= 8.4 V x 1.017 / (5.015 + 1.017) = '
                                   '1.42 V and <= 1.42 mA (Calculation at the +/-1.67 % drift ends)',
    ('RAW_ACT', IGN): 'R134\'s own other end: PYRO1_IGN\'s class (IGN_MIN) holds the pair; a bridge only shorts R134 '
                      '(see PYRO1_IGN)',
}
U1_NC = 'U1'          # only U1's NC balls are exempt (GPIOs, analog in reset (DS12110), kept analog by firmware), and
#                       only against the gate nets (R12F6-TRI-02)
# R12F6-TRI-01: PYRO1_COLD_PU (R136 to D120's anode) is not classed out. A bridge from it to PYRO1_OUT bypasses D120 and
# R131 and leaves R136: <= 3.516 V / 5.015 kohm = 0.71 mA with Q124 on, and (8.4 - 3.22) V / 5.015 kohm <= 1.04 mA
# through the match into 3V3 with the bus on and Q124 off (3V3 at its drift minimum; Calculation / Inference (3V3 window,
# D-R12-139)), so it would qualify; it
# stays under default-deny (OUT_MIN, as every net) because the board keeps it 3.27 mm from PYRO1_OUT (Measured) and that
# keeps the record strict.


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
    if protected in PACK:
        return PACK_MIN, 'pack'
    if protected in I5_PACK:                     # R12F7-TRI-01: FMEA I-5, against the MCU's supplies only
        return (PACK_MIN, 'i5-pack') if foreign in LOGIC else (None, 'unprotected')
    if protected in I5_PORT:
        return (I5_PORT_MIN, 'i5-port') if foreign in LOGIC else (None, 'unprotected')
    return None, 'unprotected'


def pair_limit(net_a, owner_a, net_b, owner_b, fill):
    """S-10's limit for one pair of items of different nets: (limit, class, protected net) with limit None when the
    pair is not a path. Both directions count when both nets are protected; the stricter wins."""
    best = (None, 'unprotected', None)
    for pn, fn, fo in ((net_a, net_b, owner_b), (net_b, net_a, owner_a)):
        if pn not in PROTECTED:
            continue
        nc = pn in GATES and u1_nc(fo, fn)              # R12F6-TRI-02: the NC-ball exemption is the gate nets' only
        lim, cls = (None, 'U1 NC ball') if nc else one_way(pn, fn, fill)
        if best[2] is None or (lim is None and best[1] == 'unprotected') or \
                (lim is not None and (best[0] is None or lim > best[0])):
            best = (lim, cls, pn)
    return best


# Measured exceptions, grouped by reason: (protected item, foreign item, layer, floor mm). Item labels are
# check_r12.copper_items's; floors are the measured gaps on the board, rounded down to 1 um (tools: S-10's evidence).
WHY = {
    'D-R11-23': 'PE4\'s lane between U1\'s balls against 3V3 (U1.B2 / D2 and their dog-bones): fire-capable, the '
                'recorded D-R11-23 deviation (R12_VALIDATION row 25), unavoidable in the TFBGA-100 escape',
    'HSE_IN': 'HSE_IN has no DC drive: Y1, C25 15 pF to GND and only OSC_OUT\'s internal feedback resistor (about '
              '200 kohm, DS12110 typical: Inference); with PE4 high-Z that is <= 3.516 V (the 3V3 window maximum, R12F6-TRI-03) x '
              '0.95 k / 201 k = 17 mV, and HSE is off in reset (Calculation / Inference)',
    'HSE_OUT': 'OSC_OUT drives against PE4: while PE4 drives low (V_OL <= 0.4 V at 8 mA, DS12110) the gate stays <= '
               '0.39 V, below AO3400A V_GS(th) min 0.65 V, if OSC_OUT sources <= 8 mA (Inference, not '
               'characterised); HSE is off in reset. Depends on R12 firmware rule 3 (PE4 driven low before HSE is '
               'enabled; an HSE start failure or CSS event on the ground refuses)',
    'QSPI_IO2': 'fire-capable: R10 firmware rule 3 (R23-SAFETY-08) finds an IO2-against-PE4 fight puts 1.19-1.98 V '
                'on the gate (Inference); held only by R12 firmware rule 3 (QSPI rules, quad read-verify ground '
                'refusal) and the first-article X-ray / meter test',
    'BOOT0': 'BOOT0 is an input-only pin held by R5 10 kohm to GND and not on J2: no source can raise PE4 '
             '(Calculation)',
    'BAT_FAULT_N': 'PC13 (ball A2, an input) reads U9\'s open-drain FLT through R95 10 kohm, with R89 10 kohm to 3V3 on '
                   'U9\'s side (U9_FLT) and D95 from BAT_FAULT_N to 3V3 (PACK_FLT): with PE4 high-Z the gate is <= '
                   '3.516 V x 0.952 k / 20.75 k x 10 / 10.22 = 0.158 V (Calculation / Inference (3V3 window, '
                   'D-R12-139): 3V3 at its window maximum 3.516 V '
                   '(SLUSDW3A section 7.8 PFM band, R12F6-TRI-03 / -04), R89 and R95 -1 %, R127 +5 %), plus D95\'s '
                   'reverse leakage x 0.908 kohm x 10 / 10.22 (2 uA at 25 C, LCSC C37704: 1.8 mV; 0.089 V even at 100 '
                   'uA hot, Inference), below AO3400A V_GS(th) min 0.65 V; firmware never makes PC13 an output',
    'Q124': 'the AO3400A SOT-23\'s own gate (pin 1) and drain (pin 3) lands, unavoidable in the package (as C128\'s '
            'own lands): fire-capable (R12F7-TRI-05). With the bus on and Q124 off, a gate-drain bridge ties the gate to '
            'the bus-fed drain against R128 10 kohm (and R126 220 ohm into PE4); Q124 then runs diode-connected at V_GS '
            'about 1.8-2 V and passes about 1.6-2 A through the match, above the J-Tek 1.125 A all-fire, so it fires an '
            'enabled match (Calculation / Inference on the AO3400A transfer curve). Owner acceptance (R12_VALIDATION)',
    'PYRO1_CONT': 'PYRO1_CONT is PC0\'s pin: a bridge puts PYRO1_OUT on PC0, whose input clamp then passes bus current '
                  'through the match into 3V3 (fire-capable or logic-destroying; Inference): the 0402 continuity '
                  'divider\'s own neighbours, surface, AOI-inspectable; owner acceptance',
    # round 6 verifier V-1 / V-2: BAT_IN pairs under PACK_MIN, all in the pack-entry cell (J1, U9, its input capacitors
    # and dividers); each key names the consequence of one bridge. A part's own lands are unavoidable; the rest needs a
    # re-layout of the pack-entry cell (respin item). Every one is an owner-acceptance item (R12_VALIDATION).
    'PACK_GND': 'BAT_IN (the pack) to GND, or to BAT_DAMP (R166 0.36 ohm to GND): parts\' own lands (C80, C88, C96, '
                'R167, D8, C79 to BAT_DAMP, U9.5 to U9.8) and the input decoupling\'s GND returns beside the BAT_IN '
                'trunk. A bridge is an unfused pack short (tens of amps; through R166 about 23 A into a 2512 that opens; '
                'Calculation / Inference on pack ESR): BAT_IN collapses, the logic browns out once C84\'s hold-up is '
                'spent (in flight a reset, the tab to neutral, recovery on the Blue Jay) and there is no bus, so it is '
                'not a fire path. BAT_IN is live whenever the pack is connected, so a pre-existing bridge shows at the '
                'first pack connection (no power-up, the harness heats)',
    'PACK_EN': 'BAT_IN to U9\'s EN/UVLO (BAT_ENABLE): U9.5 to U9.1, the TPS259470A RPW package\'s own lands (R10 had the '
               'same pair). A bridge holds U9 on with J400 open, so J400 cannot turn the board off, and puts up to 8.4 V '
               'on EN (above its 6.5 V absolute maximum in TI SLVSFC9C, R10\'s citation; Inference for this variant): '
               'the per-flight switch-off check sees it (FMEA H-6). Not a fire by itself: PC1 and PE4 still hold the '
               'bus and the match',
    'PACK_SW': 'BAT_IN beside R80.2 (BAT_SW_SOURCE, J400.1\'s side of R80 470 kohm) and R80\'s own lands: a bridge only '
               'shorts R80. J400 still switches EN, which with J400 closed then sits at <= 8.4 V x 305 k / (462 k + '
               '305 k) = 3.34 V, under EN\'s 6.5 V (Calculation: R165 470 kohm, R81 300 kohm at the +/-1.67 % drift '
               'ends); J400\'s contact and its harness lead then carry the pack with no limit, so a chafe of that lead '
               'to GND shorts the pack (as PACK_GND)',
    'PACK_FLT': 'BAT_IN to U9\'s FLT (U9_FLT): U9.5 to U9.4 (the TPS259470A RPW package\'s own lands, 0.200 mm) and the '
                'BAT_IN fan-in under U9.4\'s corner. Round 6 verifier V-1 follow-up: PC13 (U1.A2, BAT_FAULT_N) now reads '
                'U9_FLT only through R95 10 kohm, with R89 10 kohm (3V3) on U9\'s side and D95 BAT54C (A1 BAT_FAULT_N, K '
                '3V3) clamping PC13, an FT pin with no positive injection (DS12110 Rev 8 Table 120 note 3; VIN max '
                'Min(VDD, ...) + 4.0 V, Table 119). A bridge puts the pack on U9_FLT; then R89 and R95 + D95 each pass '
                '<= (8.4 - 3.224) V / 9.833 kohm = 0.53 mA into 3V3 (Calculation / Inference (3V3 window, '
                'D-R12-139); 1.05 mA '
                'together; 1.70 mA each at the SMAJ12CA\'s '
                '19.9 V clamp, a transient), small beside the running MCU\'s supply current (Inference), and PC13 stays '
                '<= 3V3 + V_F(BAT54C) <= 3.516 + 0.8 = 4.32 V (Calculation / Inference (3V3 window, '
                'D-R12-139); V_F <= 800 mV at '
                '100 mA, LCSC C37704; with the board off '
                'PC13 sits V_F above the unpowered rail, under the FT pin\'s +4.0 V): no current into the pin beyond its '
                'leakage (Calculation / Inference (3V3 window, D-R12-139); resistors at the +/-1.67 % drift '
                'ends; flt_guard() '
                'checks the netlist). Not a '
                'fire and not logic-destroying. U9 itself is over-driven: U9_FLT above FLT\'s 6.5 V absolute maximum '
                '(TI SLVSFC9C section 6.1), and with a fault asserted FLT\'s pull-down (R_FLT 12.3 ohm typical, section '
                '6.5) sinks the pack (U9 damaged, open or short; Inference), the PACK_EN / PACK_U9 class; a shorted U9 '
                'is the PACK_OUT case. Owner acceptance (U9\'s own pin, as PACK_U9)',
    'PACK_OUT': 'BAT_IN to U9\'s OUT (RAW_PROTECTED): U9.5 to U9.6 (own lands, 0.200 mm) and the OUT fan-out beside the IN '
                'bar. A bridge bypasses U9: the logic converters are fed from the pack with no current limit, OVLO or '
                'fault latch (no overload by itself; a later downstream fault is then unlimited). Not a fire',
    'PACK_U9': 'BAT_IN to U9\'s analog control pins and their dividers: OVLO (U9.2; R82 1 Mohm\'s own lands; R83), '
               'BAT_OVLO_B (the R83 / R93 node), dVdt (U9.7, C81), ILIM (U9.9, R84 / R94) and the no-connect AUXOFF / '
               'ITIMER pins (U9.3, U9.10). A bridge drives a high-impedance U9 input to the pack: OVLO / OVLO_B trip '
               'U9\'s over-voltage turn-off (the board goes dark; in flight a brown-out reset), and dVdt / ILIM / '
               'AUXOFF / ITIMER may be over-driven (U9 damaged, open or short; Inference: the pins\' absolute maxima '
               'were not re-read). Not a fire (a shorted U9 is the PACK_OUT case)',
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
    # ---- pack-energy exceptions (generated from the board by the round 6 lane P3 scan; floors measured)
    'PACK_GND': (
        ('track (10.4, 9)-(13.3, 9)', 'R167.2', 'F.Cu', 0.130),
        ('track (9.9, 9.5)-(10.4, 9)', 'R167.2', 'F.Cu', 0.137),
        ('track (10.4, 9)-(13.3, 9)', 'via (11.55, 9.6)', 'F.Cu', 0.175),
        ('C79.1', 'via (17.6, 18.9)', 'F.Cu', 0.190),
        ('track (14, 15.1)-(15.3, 15.1)', 'C88.2', 'F.Cu', 0.190),
        ('track (14.9, 10.5)-(14.9, 12.9)', 'C96.2', 'F.Cu', 0.200),
        ('track (5, 19.3)-(5, 23.3)', 'C80.2', 'F.Cu', 0.200),
        ('track (10.4, 9)-(13.3, 9)', 'track (10.9, 9.6)-(11.55, 9.6)', 'F.Cu', 0.250),
        ('C79.1', 'track (17.6, 18.3)-(17.6, 18.9)', 'F.Cu', 0.265),
        ('track (14, 15.1)-(15.3, 15.1)', 'track (15.3, 15.94)-(15.3, 16.8)', 'F.Cu', 0.290),
        ('R167.1', 'R167.2', 'F.Cu', 0.294),
        ('track (14.9, 12.9)-(13.1, 14.7)', 'C96.2', 'F.Cu', 0.310),
        ('C88.1', 'C88.2', 'F.Cu', 0.340),
        ('track (15.3, 15.1)-(16.6, 15.1)', 'C88.2', 'F.Cu', 0.390),
        ('track (9.9, 9.5)-(10.4, 9)', 'track (10.9, 9.6)-(11.55, 9.6)', 'F.Cu', 0.427),
        ('C88.1', 'track (15.3, 15.94)-(15.3, 16.8)', 'F.Cu', 0.440),
        ('track (10.4, 9)-(13.3, 9)', 'via (12.12, 8.1)', 'F.Cu', 0.475),
        ('track (15.3, 15.1)-(16.6, 15.1)', 'track (15.3, 15.94)-(15.3, 16.8)', 'F.Cu', 0.490),
        ('R167.1', 'track (10.9, 9.6)-(11.55, 9.6)', 'F.Cu', 0.497),
        ('track (10.4, 9)-(13.3, 9)', 'D402.2', 'F.Cu', 0.500),
        ('track (9.9, 9.5)-(10.4, 9)', 'D402.2', 'F.Cu', 0.500),
        ('C79.1', 'C81.2', 'F.Cu', 0.555),
        ('C96.1', 'C88.2', 'F.Cu', 0.573),
        ('track (10.4, 9)-(13.3, 9)', 'track (10.7, 8.1)-(12.12, 8.1)', 'F.Cu', 0.575),
        ('R167.1', 'D8.2', 'F.Cu', 0.580),
        ('C79.1', 'via (16.5, 18.2)', 'F.Cu', 0.600),
        ('track (13.2, 18.4)-(14.4, 19.6)', 'track (14.85, 21)-(13.2, 21)', 'F.Cu', 0.600),
        ('track (14.4, 19.6)-(16.4, 19.6)', 'track (14.85, 21)-(13.2, 21)', 'F.Cu', 0.600),
        ('track (14.4, 19.6)-(16.4, 19.6)', 'track (16.4, 22.55)-(14.85, 21)', 'F.Cu', 0.600),
        ('C79.1', 'R84.2', 'F.Cu', 0.601),
        ('track (9.9, 9.5)-(10.4, 9)', 'track (10.7, 8.1)-(12.12, 8.1)', 'F.Cu', 0.623),
        ('track (13.2, 18.4)-(14.4, 19.6)', 'track (16.4, 22.55)-(14.85, 21)', 'F.Cu', 0.670),
        ('C79.1', 'track (16, 18.2)-(16.5, 18.2)', 'F.Cu', 0.675),
        ('U9.5', 'C88.2', 'F.Cu', 0.688),
        ('U9.5', 'U9.8', 'F.Cu', 0.700),
        ('track (15.3, 15.1)-(16.6, 15.1)', 'U9.8', 'F.Cu', 0.719),
        ('track (14.4, 19.6)-(16.4, 19.6)', 'C81.2', 'F.Cu', 0.730),
        ('track (9.9, 9.5)-(10.4, 9)', 'D8.2', 'F.Cu', 0.750),
        ('C79.1', 'track (14.85, 21)-(13.2, 21)', 'F.Cu', 0.752),
        ('C79.1', 'track (16.4, 22.55)-(14.85, 21)', 'F.Cu', 0.752),
        ('track (14.4, 19.6)-(16.4, 19.6)', 'via (17.6, 18.9)', 'F.Cu', 0.764),
        ('C96.1', 'track (15.3, 15.94)-(15.3, 16.8)', 'F.Cu', 0.769),
        ('track (14.4, 19.6)-(16.4, 19.6)', 'via (16.5, 18.2)', 'F.Cu', 0.778),
        ('track (14.4, 19.6)-(16.4, 19.6)', 'track (17.6, 18.3)-(17.6, 18.9)', 'F.Cu', 0.839),
        ('track (14.4, 19.6)-(16.4, 19.6)', 'track (16, 18.2)-(16.5, 18.2)', 'F.Cu', 0.850),
        ('track (9.9, 9.5)-(10.4, 9)', 'via (11.55, 9.6)', 'F.Cu', 0.872),
        ('track (16.1, 12.5)-(14.6, 14)', 'C96.2', 'F.Cu', 0.875),
        ('U9.5', 'track (15.3, 15.94)-(15.3, 16.8)', 'F.Cu', 0.906),
        ('D8.1', 'via (10.8, 13.3)', 'F.Cu', 0.925),
        ('track (14.6, 14.5)-(14.3, 14.8)', 'C88.2', 'F.Cu', 0.951),
        ('track (13.2, 18.4)-(14.4, 19.6)', 'C95.2', 'F.Cu', 0.976),
        ('track (14.4, 19.6)-(16.4, 19.6)', 'C95.2', 'F.Cu', 0.976),
        ('D8.1', 'track (10.8, 12.8)-(10.8, 13.3)', 'F.Cu', 1.000),
        ('track (14.6, 10.2)-(14.9, 10.5)', 'C96.2', 'F.Cu', 1.025),
        ('R167.1', 'D402.2', 'F.Cu', 1.031),
    ),
    'PACK_EN': (
        ('U9.5', 'U9.1', 'F.Cu', 0.200),
        ('U9.5', 'track (18, 14.3)-(18, 12.3)', 'F.Cu', 0.550),
    ),
    'PACK_SW': (
        ('track (13.3, 9)-(14.1, 9.8)', 'R80.2', 'F.Cu', 0.483),
        ('track (10.4, 9)-(13.3, 9)', 'R80.2', 'F.Cu', 0.528),
        ('R80.1', 'R80.2', 'F.Cu', 0.850),
    ),
    'PACK_FLT': (
        ('track (15.3, 15.1)-(16.6, 15.1)', 'U9.4', 'F.Cu', 0.150),
        ('U9.5', 'U9.4', 'F.Cu', 0.200),
        ('track (15.3, 15.1)-(16.6, 15.1)', 'track (16.6, 14.45)-(16.6, 13.6)', 'F.Cu', 0.350),
        ('U9.5', 'track (16.6, 14.45)-(16.6, 13.6)', 'F.Cu', 0.400),
        ('track (14, 15.1)-(15.3, 15.1)', 'U9.4', 'F.Cu', 0.473),
        ('C88.1', 'U9.4', 'F.Cu', 0.539),
        ('track (16.1, 12.5)-(14.6, 14)', 'via (16.6, 13.6)', 'F.Cu', 0.706),
        ('R82.1', 'via (16.6, 13.6)', 'F.Cu', 0.716),
        ('track (16.1, 12.5)-(14.6, 14)', 'track (16.6, 14.45)-(16.6, 13.6)', 'F.Cu', 0.831),
        ('R82.1', 'track (16.6, 14.45)-(16.6, 13.6)', 'F.Cu', 0.841),
        ('track (14, 15.1)-(15.3, 15.1)', 'track (16.6, 14.45)-(16.6, 13.6)', 'F.Cu', 0.953),
        ('C88.1', 'track (16.6, 14.45)-(16.6, 13.6)', 'F.Cu', 1.005),
    ),
    'PACK_OUT': (
        ('U9.5', 'track (18.9, 15.6)-(19.725, 15.6)', 'F.Cu', 0.131),
        ('track (15.3, 15.1)-(16.6, 15.1)', 'U9.6', 'F.Cu', 0.150),
        ('U9.5', 'U9.6', 'F.Cu', 0.200),
        ('U9.5', 'track (17.3, 15.6)-(18.9, 15.6)', 'F.Cu', 0.200),
        ('track (14, 15.1)-(15.3, 15.1)', 'U9.6', 'F.Cu', 0.473),
        ('track (15.3, 15.1)-(16.6, 15.1)', 'track (17.3, 15.6)-(18.9, 15.6)', 'F.Cu', 0.510),
        ('C88.1', 'U9.6', 'F.Cu', 0.539),
        ('U9.5', 'C82.1', 'F.Cu', 0.650),
    ),
    'PACK_U9': (
        ('R82.1', 'track (16.2, 11.5)-(17, 12.3)', 'F.Cu', 0.166),
        ('U9.5', 'U9.2', 'F.Cu', 0.200),
        ('U9.5', 'U9.3', 'F.Cu', 0.200),
        ('R82.1', 'R82.2', 'F.Cu', 0.294),
        ('track (15.3, 15.1)-(16.6, 15.1)', 'U9.3', 'F.Cu', 0.295),
        ('track (16.1, 12.5)-(14.6, 14)', 'R82.2', 'F.Cu', 0.447),
        ('R82.1', 'R83.1', 'F.Cu', 0.460),
        ('R82.1', 'track (17.5, 12.87)-(17.03, 12.4)', 'F.Cu', 0.477),
        ('track (16.1, 12.5)-(14.6, 14)', 'track (16.2, 11.5)-(17, 12.3)', 'F.Cu', 0.477),
        ('R82.1', 'R83.2', 'F.Cu', 0.546),
        ('U9.5', 'track (17.5, 14.3)-(17.5, 12.87)', 'F.Cu', 0.550),
        ('track (16.1, 12.5)-(14.6, 14)', 'R83.1', 'F.Cu', 0.630),
        ('track (16.1, 12.5)-(14.6, 14)', 'track (17.5, 12.87)-(17.03, 12.4)', 'F.Cu', 0.635),
        ('track (15.3, 15.1)-(16.6, 15.1)', 'U9.7', 'F.Cu', 0.650),
        ('track (15.3, 15.1)-(16.6, 15.1)', 'U9.2', 'F.Cu', 0.673),
        ('U9.5', 'U9.10', 'F.Cu', 0.700),
        ('U9.5', 'U9.7', 'F.Cu', 0.700),
        ('U9.5', 'U9.9', 'F.Cu', 0.700),
        ('track (14, 15.1)-(15.3, 15.1)', 'U9.7', 'F.Cu', 0.767),
        ('track (14.6, 10.2)-(14.9, 10.5)', 'R93.1', 'F.Cu', 0.787),
        ('track (14.9, 10.5)-(14.9, 12.9)', 'R83.1', 'F.Cu', 0.787),
        ('track (14.9, 10.5)-(14.9, 12.9)', 'R93.1', 'F.Cu', 0.787),
        ('C88.1', 'U9.7', 'F.Cu', 0.800),
        ('track (16.1, 12.5)-(14.6, 14)', 'R83.2', 'F.Cu', 0.852),
        ('R82.1', 'track (17, 11.3)-(16.2, 10.5)', 'F.Cu', 0.894),
        ('track (15.3, 15.1)-(16.6, 15.1)', 'track (17.5, 14.3)-(17.5, 12.87)', 'F.Cu', 0.904),
        ('R82.1', 'track (17.5, 14.3)-(17.5, 12.87)', 'F.Cu', 0.966),
        ('track (15.3, 15.1)-(16.6, 15.1)', 'U9.9', 'F.Cu', 0.967),
        ('track (14.6, 10.2)-(14.9, 10.5)', 'R83.1', 'F.Cu', 0.970),
        ('track (14.6, 10.2)-(14.9, 10.5)', 'track (17, 11.3)-(16.2, 10.5)', 'F.Cu', 1.000),
        ('track (14.9, 10.5)-(14.9, 12.9)', 'track (16.2, 11.5)-(17, 12.3)', 'F.Cu', 1.000),
        ('track (14.9, 10.5)-(14.9, 12.9)', 'track (17, 11.3)-(16.2, 10.5)', 'F.Cu', 1.000),
        ('track (15.3, 15.1)-(16.6, 15.1)', 'track (16.6, 16.4)-(15.9, 17.1)', 'F.Cu', 1.000),
        ('R80.1', 'R93.1', 'F.Cu', 1.012),
    ),
    # ---- end pack-energy exceptions
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
    # ---- pack-energy items (generated with the exceptions above)
    'C79.1': 'BAT_IN',
    'C80.2': 'GND',
    'C81.2': 'GND',
    'C82.1': 'RAW_PROTECTED',
    'C88.1': 'BAT_IN',
    'C88.2': 'GND',
    'C95.2': 'BAT_DAMP',
    'C96.1': 'BAT_IN',
    'C96.2': 'GND',
    'D402.2': 'GND',
    'D8.1': 'BAT_IN',
    'D8.2': 'GND',
    'R167.1': 'BAT_IN',
    'R167.2': 'GND',
    'R80.1': 'BAT_IN',
    'R80.2': 'BAT_SW_SOURCE',
    'R82.1': 'BAT_IN',
    'R82.2': 'BAT_OVLO',
    'R83.1': 'BAT_OVLO',
    'R83.2': 'BAT_OVLO_B',
    'R84.2': 'GND',
    'R93.1': 'BAT_OVLO_B',
    'U9.1': 'BAT_ENABLE',
    'U9.10': 'unconnected-(U9-ITIMER-Pad10)',
    'U9.2': 'BAT_OVLO',
    'U9.3': 'unconnected-(U9-AUXOFF-Pad3)',
    'U9.4': 'U9_FLT',
    'U9.5': 'BAT_IN',
    'U9.6': 'RAW_PROTECTED',
    'U9.7': 'BAT_DVDT',
    'U9.8': 'GND',
    'U9.9': 'BAT_ILIM',
    'track (10.4, 9)-(13.3, 9)': 'BAT_IN',
    'track (10.7, 8.1)-(12.12, 8.1)': 'GND',
    'track (10.8, 12.8)-(10.8, 13.3)': 'GND',
    'track (10.9, 9.6)-(11.55, 9.6)': 'GND',
    'track (13.2, 18.4)-(14.4, 19.6)': 'BAT_IN',
    'track (13.3, 9)-(14.1, 9.8)': 'BAT_IN',
    'track (14, 15.1)-(15.3, 15.1)': 'BAT_IN',
    'track (14.4, 19.6)-(16.4, 19.6)': 'BAT_IN',
    'track (14.6, 10.2)-(14.9, 10.5)': 'BAT_IN',
    'track (14.6, 14.5)-(14.3, 14.8)': 'BAT_IN',
    'track (14.85, 21)-(13.2, 21)': 'BAT_DAMP',
    'track (14.9, 10.5)-(14.9, 12.9)': 'BAT_IN',
    'track (14.9, 12.9)-(13.1, 14.7)': 'BAT_IN',
    'track (15.3, 15.1)-(16.6, 15.1)': 'BAT_IN',
    'track (15.3, 15.94)-(15.3, 16.8)': 'GND',
    'track (16, 18.2)-(16.5, 18.2)': 'GND',
    'track (16.1, 12.5)-(14.6, 14)': 'BAT_IN',
    'track (16.2, 11.5)-(17, 12.3)': 'BAT_OVLO',
    'track (16.4, 22.55)-(14.85, 21)': 'BAT_DAMP',
    'track (16.6, 14.45)-(16.6, 13.6)': 'U9_FLT',
    'track (16.6, 16.4)-(15.9, 17.1)': 'BAT_DVDT',
    'track (17, 11.3)-(16.2, 10.5)': 'BAT_OVLO_B',
    'track (17.3, 15.6)-(18.9, 15.6)': 'RAW_PROTECTED',
    'track (17.5, 12.87)-(17.03, 12.4)': 'BAT_OVLO',
    'track (17.5, 14.3)-(17.5, 12.87)': 'BAT_OVLO',
    'track (17.6, 18.3)-(17.6, 18.9)': 'GND',
    'track (18, 14.3)-(18, 12.3)': 'BAT_ENABLE',
    'track (18.9, 15.6)-(19.725, 15.6)': 'RAW_PROTECTED',
    'track (5, 19.3)-(5, 23.3)': 'BAT_IN',
    'track (9.9, 9.5)-(10.4, 9)': 'BAT_IN',
    'via (10.8, 13.3)': 'GND',
    'via (11.55, 9.6)': 'GND',
    'via (12.12, 8.1)': 'GND',
    'via (16.5, 18.2)': 'GND',
    'via (16.6, 13.6)': 'U9_FLT',
    'via (17.6, 18.9)': 'GND',
    # ---- end pack-energy items
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


def _at(side, prop, value):
    """A coordinate test within 0.5 um: check_r12 labels print 6 significant digits, and the board can hold a routed
    coordinate 1 nm off its table value (16.4 mm is stored as 16.399999 mm), which an exact '==' never matches."""
    v = float(value)
    return f"{side}.{prop} >= {v - 0.0005:.4f}mm && {side}.{prop} <= {v + 0.0005:.4f}mm"


def item_condition(side, label, net):
    """A DRU condition naming one copper item by its check_r12 label (a pad, a via or a track). A pad label names every
    pad of that number on the footprint (U9's L-shaped pins are two pads each): its pairs share one floor, their least."""
    cond = f"{side}.NetName == '{net}'"
    m = re.fullmatch(r'via \(([-\d.]+), ([-\d.]+)\)', label)
    if m:
        return cond + f" && {side}.Type == 'Via' && {_at(side, 'Position_X', m[1])} && {_at(side, 'Position_Y', m[2])}"
    m = re.fullmatch(r'track \(([-\d.]+), ([-\d.]+)\)-\(([-\d.]+), ([-\d.]+)\)', label)
    if m:
        return cond + (f" && {side}.Type == 'Track' && {_at(side, 'Start_X', m[1])} && {_at(side, 'Start_Y', m[2])} && "
                       f"{_at(side, 'End_X', m[3])} && {_at(side, 'End_Y', m[4])}")
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
         f"A.NetName == '{OUT}' && {_not('B', out_x)}",
         f'R10 D-R26-02 ({OUT_MIN:.3f} mm), default-deny: every net but GND, the gate nets (their own rule) and '
         'PYRO1_IGN / _COLD / _CONT_MID; U1 NC balls count (R12F6-TRI-02; check_r12 S-10)', None),
        ('S-10 PYRO1_OUT to GND', f'clearance (min {GND_MIN}mm)',
         f"A.NetName == '{OUT}' && B.NetName == 'GND' && {NOT_PROBE}",
         'R10 row 1 surface pairs 0.177 / 0.180 mm, R12 0.25 mm (check_r12 S-10)', None),
        ('S-10 PYRO1_OUT to GND fills', f'clearance (min {FILL_MIN}mm)',
         f"A.NetName == '{OUT}' && B.NetName == 'GND' && {EITHER_FILL} && {NOT_PROBE}",
         'R12F5-TRI-01: J121.1 sat 0.101 mm from GND_pour_B (check_r12 S-10)', None),
        ('S-10 PYRO1_IGN to every net', f'clearance (min {IGN_MIN}mm)',
         f"A.NetName == '{IGN}' && {_not('B', ign_x)} && {NOT_PROBE}",
         'R134 overload: J121.2 sat 0.100 mm from GND_pour_B (round 5 verifier); U1 NC balls count (R12F6-TRI-02; '
         'check_r12 S-10)', None),
        ('S-10 PYRO1_IGN to fills', f'clearance (min {FILL_MIN}mm)',
         f"A.NetName == '{IGN}' && {_not('B', ign_x)} && {EITHER_FILL} && {NOT_PROBE}",
         'R134 overload: every pour >= 0.5 mm from J121.2 (check_r12 S-10)', None),
    ]
    # the pack-energy nets (round 6 verifier V-1 / V-2), after the PYRO1_IGN rules so a pack net's 1.04 mm wins over
    # IGN's 0.25 mm against it; the gate nets keep their own, stricter, rule (excluded here)
    for net in PACK:
        x = (net,) + GATES + _excluded(net)
        rules.append((f'S-10 {net} (pack energy) to every net', f'clearance (min {PACK_MIN:.2f}mm)',
                      f"A.NetName == '{net}' && {_not('B', x)}",
                      f'round 6 V-1 / V-2 ({PACK_MIN:.3f} mm, R10 D-R26-02\'s figure), default-deny, fills too: every net '
                      f'but the gate nets and {" / ".join(_excluded(net))} (check_r12 S-10)', None))
    # FMEA I-5 (R12F7-TRI-01): the rails above 3V3 (i5_rails()) against the MCU's supplies only; no general rule above
    # matches these pairs (none of them is a gate, PYRO1_OUT, PYRO1_IGN or pack net)
    for net in I5_PACK + I5_PORT:
        lim, why = ((PACK_MIN, 'pack voltage behind U9, D-R12-137\'s PACK_MIN') if net in I5_PACK else
                    (I5_PORT_MIN, 'port voltage, R10 owner row 1\'s figure'))
        rules.append((f'S-10 {net} (I-5 rail) to 3V3 / 3V3A', f'clearance (min {lim:.2f}mm)',
                      f"A.NetName == '{net}' && {_is('B', LOGIC)}",
                      f'R12F7-TRI-01 FMEA I-5 ({lim:.3f} mm, {why}): a bridge puts the rail on the MCU supply '
                      '(check_r12 S-10)', None))
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


# ---- the commanded-fire state (R12F6-TRI-01) -------------------------------------------------------------------------
# While Q124 conducts, PYRO1_OUT is GND, so a bridge from PYRO1_OUT to a not-a-path net f joins f to GND. f must then
# reach every source only through resistors: at least FIRE_SERIES_MIN (R136 / R129 5.1 kohm; 3.516 V / 5.015 kohm =
# 0.71 mA, Calculation / Inference (3V3 window, D-R12-139), under BAT54C I_F 200 mA and negligible on 3V3).
# Round 6 found the cold pull-up's D120 anode on 3V3 itself:
# a bridge across R131 put 3V3 through D120 into Q124 with no resistor (U2's 1.075-1.6 A current limit).
FIRE_SERIES_MIN = 5.0e3     # ohm, nominal
COLD = 'PYRO1_COLD'
# Part classes of the netlist walks, default-deny (round 6 verifier V-4): a capacitor (C<n>, two pins) carries no DC and a
# one-pin test point or hole (TP / H / MH / FID) carries nothing; a resistor (R<n>, two pins) counts at its value only
# when the value parses; diodes, inductors and beads (D / L / FB, any pin count) and every other two-pin part (fuses F,
# jumpers JP, LEDs, an unparsed resistor, any unknown prefix) count as 0 ohm, either way; every other part (ICs,
# transistors, connectors, crystals, buzzers, resistor arrays, unknown multi-pin parts) is a source on every pin.
_CAP = re.compile(r'^C\d+$')
_INERT = re.compile(r'^(TP|H|MH|FID)\d+$')
_RES = re.compile(r'^R\d+$')
_PASS = re.compile(r'^(D|L|FB)\d+$')
_FET = re.compile(r'^Q\d+$')


def ohms(value):
    """A resistor Value's first token ('5.1k', '10k 1%', '2R', '4k7', '220') in ohms; None if unreadable."""
    m = re.fullmatch(r'(\d+(?:\.\d+)?)([RrkKmM]?)(\d*)', (value or '').split()[0] if (value or '').split() else '')
    if not m:
        return None
    mult = {'': 1, 'R': 1, 'r': 1, 'k': 1e3, 'K': 1e3, 'M': 1e6, 'm': 1e-3}[m[2]]
    return float(m[1] + ('.' + m[3] if m[3] else '')) * mult if m[2] or not m[3] else None


def part_kind(ref, value, pins):
    """'cap', 'inert', 'res' (a parsed value), 'pass' (0 ohm between all its nets) or 'source' (default-deny)."""
    if _CAP.match(ref) and len(pins) == 2:
        return 'cap'
    if _INERT.match(ref) and len(pins) == 1:
        return 'inert'
    if _RES.match(ref) and len(pins) == 2 and ohms(value) is not None:
        return 'res'
    if _PASS.match(ref) or len(pins) == 2:
        return 'pass'
    return 'source'


def read_netlist(path, functions=False):
    """({ref: value}, {ref: {pin: net}}[, {ref: {pin: pinfunction}}]) from a KiCad XML netlist."""
    import xml.etree.ElementTree as ET
    root = ET.parse(path).getroot()
    values = {c.get('ref'): (c.findtext('value') or '') for c in root.findall('./components/comp')}
    pins, funcs = {}, {}
    for n in root.findall('./nets/net'):
        for p in n.findall('node'):
            pins.setdefault(p.get('ref'), {})[p.get('pin')] = n.get('name')
            funcs.setdefault(p.get('ref'), {})[p.get('pin')] = p.get('pinfunction') or ''
    return (values, pins, funcs) if functions else (values, pins)


def _gate(funcs, ref, pin):
    """A MOSFET's insulated gate: a Q<n> pin whose pinfunction is G (G_1 ...)."""
    return bool(_FET.match(ref)) and re.match(r'^G(_|$)', funcs.get(ref, {}).get(pin, '')) is not None


def series_to_sources(path, start, classes=None, stop=(OUT, 'GND'), sinks=(), insulated_gates=False):
    """{source net: least series resistance (ohm)} from net `start`, walking the part classes of part_kind() (a resistor
    at its value, a 0-ohm part either way), never entering `stop` and not walking on past a source. A source is a net
    the netlist marks as supply, open-drain or MCU (netlist_classes), a net in `sinks`, or one with a pin of a 'source'
    part (insulated_gates: a MOSFET's gate pin does not make its net a source; its drain and source pins do)."""
    import heapq
    values, pins, funcs = read_netlist(path, functions=True)
    classes = netlist_classes(path) if classes is None else classes
    marked = set(classes.get('supply', ())) | set(classes.get('open_drain', ())) | set(classes.get('mcu', ()))
    edges, source = {}, set(marked) | set(sinks)
    for ref, pp in pins.items():
        kind = part_kind(ref, values.get(ref), pp)
        if kind == 'source':
            source.update(n for pin, n in pp.items() if n and not n.startswith('unconnected-')
                          and not (insulated_gates and _gate(funcs, ref, pin)))
        if kind not in ('res', 'pass'):
            continue
        nets = sorted({n for n in pp.values() if n and not n.startswith('unconnected-')})
        w = ohms(values.get(ref)) if kind == 'res' else 0.0
        for a in nets:
            for b in nets:
                if a != b:
                    edges.setdefault(a, []).append((b, w))
    best, heap, out = {start: 0.0}, [(0.0, start)], {}
    while heap:
        d, n = heapq.heappop(heap)
        if d > best.get(n, float('inf')):
            continue
        if n in source and n not in stop:
            out[n] = min(out.get(n, float('inf')), d)
            if n != start:
                continue                                 # the nearest source on a path is the one that counts
        for m, w in edges.get(n, ()):
            if m in stop or d + w >= best.get(m, float('inf')):
                continue
            best[m] = d + w
            heapq.heappush(heap, (d + w, m))
    return out


def fire_state_guard(path, not_a_path=None, classes=None):
    """(issues, evidence): every NOT_A_PATH (PYRO1_OUT, f) class holds with Q124 conducting (f reaches no source through
    less than FIRE_SERIES_MIN), and the cold pull-up diode's anode is never on 3V3 or another source itself."""
    classes = netlist_classes(path) if classes is None else classes
    issues, ev = [], {}
    for (p, f) in sorted(NOT_A_PATH if not_a_path is None else not_a_path):
        if p != OUT or f == 'GND' or f in PROTECTED:
            continue
        reach = series_to_sources(path, f, classes)
        ev[f] = {n: round(r, 1) for n, r in sorted(reach.items(), key=lambda kv: (kv[1], kv[0]))[:4]}
        low = sorted((r, n) for n, r in reach.items() if r < FIRE_SERIES_MIN)
        for r, n in low:
            issues.append(f'{OUT} / {f} is classed "not a path", but with Q124 conducting a bridge joins {n} to GND '
                          f'through only {r:g} ohm (fire-state guard, >= {FIRE_SERIES_MIN:g} ohm; R12F6-TRI-01)')
    values, pins = read_netlist(path)
    sources = set(classes.get('supply', ())) | set(classes.get('mcu', ())) | {'3V3', '3V3A'}
    diodes = sorted(ref for ref, pp in pins.items() if ref.startswith('D') and COLD in pp.values())
    if not diodes:
        issues.append(f'no cold pull-up diode on {COLD} (R12F6-TRI-01 guard)')
    for ref in diodes:
        for pin, net in sorted(pins[ref].items()):
            if net == COLD or not net or net.startswith('unconnected-'):
                continue
            ev[f'{ref}.{pin}'] = net
            if net in sources:
                issues.append(f'{ref}.{pin} (the cold pull-up diode\'s anode) is on {net} itself: it must reach 3V3 '
                              f'only through a resistor (R136; R12F6-TRI-01)')
                continue
            r = series_to_sources(path, net, classes, stop=(OUT, 'GND', COLD)).get('3V3')
            if r is not None and r < FIRE_SERIES_MIN:
                issues.append(f'{ref}.{pin} ({net}) reaches 3V3 through only {r:g} ohm (>= {FIRE_SERIES_MIN:g} ohm, '
                              'R12F6-TRI-01)')
    return issues, ev


# ---- the pack-energy nets (round 6 verifier V-1 / V-2) ----------------------------------------------------------------
# pack_nets() derives them, default-deny: from the battery pad PACK_SOURCE through every part that can carry the pack's
# current unlimited. It does not cross a capacitor, a one-pin test point, a resistor of at least PACK_R_LIMIT (R134 2 ohm:
# PYRO1_IGN behind it has its own class; every other resistor on a pack net is >= 5.1 kohm), a MOSFET's insulated gate,
# GND (the return) or a named limiter (PACK_LIMITERS). A transistor conducts drain to source either way (channel or body
# diode); a diode, inductor or any other two-pin part conducts at 0 ohm either way; any other part on a pack net (an IC
# or connector not named here, a resistor array, an unknown multi-pin part) is a finding.
PACK_SOURCE = ('J1', '1')      # the battery wire pad (BAT_IN); J1.2 is GND
PACK_R_LIMIT = 2.0             # ohm, R134's value
PACK_SERIES_MIN = FIRE_SERIES_MIN   # ohm: a classed-out net reaches every source only through this (<= 8.4 V / 5.015
#                                     kohm = 1.68 mA at the -1.67 % drift end; Calculation)
PACK_LIMITERS = {
    'U9': 'TPS259470A eFuse: BAT_IN is its IN pin; OUT (RAW_PROTECTED) is behind its current limit (3.92-4.89 A) and '
          'fault latch, which bound the current of a short from OUT (the unfused-pack-short half of the pack class); its '
          'other pins are control pins, not a current path from IN. The limit does not bound the voltage: OUT still '
          'carries the pack (up to OVLO) onto any net it is bridged to, so RAW_PROTECTED is an FMEA I-5 rail held from '
          '3V3 / 3V3A at PACK_MIN (I5_PACK, i5_rails(); R12F7-TRI-01)',
}


def pack_nets(path):
    """(sorted pack-energy nets, issues): the nets the pack reaches with no current-limiting element (see above)."""
    values, pins, funcs = read_netlist(path, functions=True)
    on = {}
    for ref, pp in pins.items():
        for pin, net in pp.items():
            on.setdefault(net, []).append((ref, pin))
    ref0, pin0 = PACK_SOURCE
    start = pins.get(ref0, {}).get(pin0)
    if not start:
        return [], [f'pack source {ref0}.{pin0} not in the netlist']
    seen, todo, issues = {start}, [start], []
    while todo:
        net = todo.pop()
        for ref, pin in sorted(set(on.get(net, ()))):
            if ref == ref0 or ref in PACK_LIMITERS:
                continue
            pp = pins[ref]
            kind = part_kind(ref, values.get(ref), pp)
            if kind in ('cap', 'inert') or (kind == 'res' and ohms(values.get(ref)) >= PACK_R_LIMIT):
                continue
            if _FET.match(ref):
                f = {p: (funcs[ref].get(p) or '')[:1] for p in pp}
                if sorted(f.values()) != ['D', 'G', 'S']:
                    issues.append(f'{ref} on pack net {net} has pin functions {f}: not a classified MOSFET')
                    continue
                if f[pin] == 'G':
                    continue                              # an insulated gate carries no current
                join = [pp[p] for p in pp if f[p] in ('D', 'S')]
            elif kind in ('res', 'pass'):
                join = list(pp.values())
            else:
                issues.append(f'{ref} ({values.get(ref)}) on pack net {net} is not a classified part (default-deny: '
                              'name it in PACK_LIMITERS with a reason, or class it)')
                continue
            for m in join:
                if m and m != 'GND' and not m.startswith('unconnected-') and m not in seen:
                    seen.add(m)
                    todo.append(m)
    return sorted(seen), issues


def pack_guard(path, classes=None, not_a_path=None):
    """(issues, evidence): the netlist's pack-energy nets are exactly PACK, and every pack not-a-path class's foreign
    net (other than a protected net, held by its own class) reaches every source, GND included, only through at least
    PACK_SERIES_MIN (MOSFET gates insulated)."""
    classes = netlist_classes(path) if classes is None else classes
    derived, issues = pack_nets(path)
    for n in sorted(set(derived) - set(PACK)):
        issues.append(f'{n} carries the pack\'s current with no limiting element (pack_nets) but S-10 does not hold it '
                      '(add it to r12_fire.PACK)')
    for n in sorted(set(PACK) - set(derived)):
        issues.append(f'{n} is held as a pack-energy net but the netlist no longer reaches it from the pack')
    ev = {'pack_nets': derived}
    for (p, f) in sorted(NOT_A_PATH if not_a_path is None else not_a_path):
        if p not in PACK or f in PROTECTED:
            continue
        reach = series_to_sources(path, f, classes, stop=PACK, sinks=('GND',), insulated_gates=True)
        ev[f'{p} / {f}'] = {n: round(r, 1) for n, r in sorted(reach.items(), key=lambda kv: (kv[1], kv[0]))[:4]}
        for n, r in sorted(reach.items(), key=lambda kv: (kv[1], kv[0])):
            if r < PACK_SERIES_MIN:
                issues.append(f'{p} / {f} is classed "not a path", but a bridge puts the pack on {n} through only '
                              f'{r:g} ohm (pack guard, >= {PACK_SERIES_MIN:g} ohm; round 6 V-1)')
    return issues, ev


# ---- U9's FLT and PC13 (round 6 verifier V-1 follow-up, PACK_FLT) ---------------------------------------------------
# U9.4 (FLT) sits 0.200 mm from U9.5 (BAT_IN) in the TPS259470A package, so the PACK_FLT pairs stay measured exceptions
# (U9's own pin is over-driven: owner acceptance, as PACK_U9). What makes them neither logic-destroying nor fire-capable
# is the netlist: the net on U9.4 carries no MCU pin and reaches every MCU-pin net and 3V3 only through at least
# PACK_SERIES_MIN (R95 to PC13, R89 to 3V3), and every MCU-pin net it reaches has a diode clamp to 3V3 (PC13 is an FT
# pin: no positive injection, so a series resistor alone would leave it at the pack voltage). flt_guard() checks that.
FLT_PIN = ('U9', '4')          # TPS259470A FLT (open drain)
FLT_CLAMP_RAIL = '3V3'


def flt_guard(path, classes=None):
    """(issues, evidence): U9's FLT net is no MCU-pin net, reaches every MCU-pin net and 3V3 only through at least
    PACK_SERIES_MIN of resistors (diodes count 0 ohm, MOSFET gates insulated, GND and the pack nets not crossed), and
    each MCU-pin net it reaches carries a diode whose anode is on that net and whose cathode is on FLT_CLAMP_RAIL."""
    classes = netlist_classes(path) if classes is None else classes
    values, pins, funcs = read_netlist(path, functions=True)
    ref, pin = FLT_PIN
    flt = pins.get(ref, {}).get(pin)
    if not flt or flt.startswith('unconnected-'):
        return [f'{ref}.{pin} (FLT) is not on a net (PACK_FLT guard)'], {}
    issues, ev = [], {'flt_net': flt}
    mcu = set(classes.get('mcu', ()))
    if flt in mcu:
        issues.append(f'{ref}.{pin} (FLT, beside U9.5 BAT_IN) is on {flt}, an MCU-pin net: the pack reaches the MCU with '
                      'no series resistor (PACK_FLT)')
    reach = series_to_sources(path, flt, classes, stop=PACK + ('GND',), insulated_gates=True)
    ev['series_ohm'] = {n: round(r, 1) for n, r in sorted(reach.items(), key=lambda kv: (kv[1], kv[0])) if n != flt}
    for n, r in sorted(reach.items(), key=lambda kv: (kv[1], kv[0])):
        if n == flt:
            continue
        if (n in mcu or n == FLT_CLAMP_RAIL) and r < PACK_SERIES_MIN:
            issues.append(f'{flt} (U9 FLT, beside BAT_IN) reaches {n} through only {r:g} ohm (PACK_FLT guard, >= '
                          f'{PACK_SERIES_MIN:g} ohm)')
    rails = set(classes.get('supply', ())) | {FLT_CLAMP_RAIL, '3V3A'}
    reached_mcu = sorted(n for n in reach if n in mcu and n != flt and n not in rails)     # MCU signal pins only
    if not reached_mcu:
        issues.append(f'{flt} (U9 FLT) reaches no MCU pin: PC13 cannot read the fault (PACK_FLT guard)')
    for m in reached_mcu:
        clamps = []
        for d, pp in sorted(pins.items()):
            if not _PASS.match(d) or not d.startswith('D'):
                continue
            fn = funcs.get(d, {})
            anodes = {p for p, f in fn.items() if f.split('_')[0].startswith('A')}
            cathodes = {p for p, f in fn.items() if f.split('_')[0].startswith('K')}
            if any(pp.get(p) == m for p in anodes) and any(pp.get(p) == FLT_CLAMP_RAIL for p in cathodes):
                clamps.append(d)
        ev[f'clamp {m}'] = clamps
        if not clamps:
            issues.append(f'{m} (an MCU pin reached from U9 FLT) has no diode clamp to {FLT_CLAMP_RAIL} (anode on {m}, '
                          'cathode on 3V3): an FT pin takes no positive injection, so a BAT_IN-to-FLT bridge would leave '
                          'it at the pack voltage (PACK_FLT guard)')
    return issues, ev


# ---- FMEA I-5: rails above 3V3 (R12F7-TRI-01) --------------------------------------------------------------------------
# A bridge from a rail above 3V3 to 3V3 / 3V3A drives the MCU's supply over its 4.0 V absolute maximum (DS12110); an
# over-driven MCU may drive PE4 (and PC1), which is fire-capable once the bus is on (Inference, R10 FMEA I-5). i5_rails()
# derives the rails from the netlist, default-deny over the netlist's supply nets:
#   * pack voltage: U9's OUT (PACK_LIMITERS: the current limit does not bound the voltage), every net a diode's anode
#     on such a net reaches at its cathode, and a converter's switch (SW) and bootstrap (CB / VBST) nodes when its VIN
#     is on such a net (the switch node swings to VIN, the bootstrap node sits about 5 V above it);
#   * port voltage: every regulated rail of r12_windows.json whose drift maximum is above 3V3's, and USB VBUS (a
#     connector pin named VBUS), carried through diodes and converters the same way (a pack-voltage net stays pack);
#   * every other netlist supply net must be 3V3 / 3V3A, a pack-energy net (PACK, held from every net) or a named rail
#     below 3V3 (I5_BELOW).
I5_BELOW = {
    'VCAP1': 'U1\'s core regulator output (about 1.2 V, DS12110): below 3V3, no I-5 route',
    'VCAP2': 'U1\'s core regulator output (about 1.2 V, DS12110): below 3V3, no I-5 route',
}
I5_SWITCH_PINS = ('SW', 'CB', 'VBST', 'BST', 'BOOT')     # converter pins that follow VIN (pin-function stem)
WINDOWS = __import__('pathlib').Path(__file__).resolve().parent / 'r12/design/r12_windows.json'


def i5_rails(path, windows=None):
    """({'pack': [...], 'port': [...]}, issues): the netlist nets above 3V3 that one bridge can put on 3V3 / 3V3A (see
    above). windows: r12_windows.json's dict (default: the committed file)."""
    import json
    values, pins, funcs = read_netlist(path, functions=True)
    rails = (json.loads(WINDOWS.read_text()) if windows is None else windows)['rails']
    v33 = next((v['drift']['max_V'] for k, v in rails.items() if k.split(' (')[0] == '3V3'), None)
    issues = [] if v33 is not None else ['r12_windows.json has no 3V3 rail (I-5 guard)']
    nets = {n for pp in pins.values() for n in pp.values() if n and not n.startswith('unconnected-')}

    def stem(ref, pin):
        return (funcs.get(ref, {}).get(pin) or '').split('_')[0].upper()
    pack = {pins[r][p] for r in PACK_LIMITERS for p in pins.get(r, {}) if stem(r, p) == 'OUT'}
    if not pack:
        issues.append('no OUT pin on a PACK_LIMITERS part (I-5 guard)')
    port = {k.split(' (')[0] for k, v in rails.items()
            if v33 is not None and k.split(' (')[0] in nets and k.split(' (')[0] not in LOGIC
            and v['drift']['max_V'] > v33}
    port |= {n for r, pp in pins.items() for p, n in pp.items() if stem(r, p) == 'VBUS' and n in nets}
    for raised in (pack, port):
        grow = True
        while grow:
            grow = False
            for ref, pp in sorted(pins.items()):
                if ref.startswith('D'):
                    src = {pp[p] for p in pp if stem(ref, p).startswith('A')}
                    dst = {pp[p] for p in pp if stem(ref, p).startswith('K')}
                elif ref.startswith('U') and ref != 'U1' and ref not in PACK_LIMITERS:
                    src = {pp[p] for p in pp if stem(ref, p) == 'VIN'}
                    dst = {pp[p] for p in pp if stem(ref, p) in I5_SWITCH_PINS}
                else:
                    continue
                if src & raised:
                    new = {n for n in dst if n in nets and n != 'GND'} - raised
                    if new:
                        raised |= new
                        grow = True
    port -= pack
    for n in sorted((pack | port) & set(LOGIC)):
        issues.append(f'{n} is reached from a rail above 3V3 through a part (not a bridge): I-5 guard')
    pack -= set(LOGIC) | set(PACK)
    port -= set(LOGIC) | set(PACK)
    classes = netlist_classes(path)
    for n in sorted(set(classes['supply']) - pack - port - set(LOGIC) - set(PACK) - set(I5_BELOW)):
        issues.append(f'supply net {n} is in no I-5 class (default-deny: an I-5 rail, a pack net or I5_BELOW with a '
                      'reason)')
    return dict(pack=sorted(pack), port=sorted(port)), issues


def i5_guard(path, windows=None):
    """(issues, evidence): the netlist's I-5 rails are exactly I5_PACK and I5_PORT (R12F7-TRI-01)."""
    derived, issues = i5_rails(path, windows)
    for cls, held in (('pack', I5_PACK), ('port', I5_PORT)):
        for n in sorted(set(derived[cls]) - set(held)):
            issues.append(f'{n} can sit above 3V3 ({cls} voltage, i5_rails) but S-10 does not hold it from 3V3 / 3V3A '
                          f'(add it to r12_fire.I5_{cls.upper()})')
        for n in sorted(set(held) - set(derived[cls])):
            issues.append(f'{n} is held as an I-5 {cls}-voltage rail but the netlist no longer derives it')
    return issues, dict(derived, limits=dict(pack=PACK_MIN, port=I5_PORT_MIN), victims=list(LOGIC))

"""IPC-2152 temperature rise of a copper conductor, the fit the R7 and R8 records use (plain Python, no pcbnew).

dT = K * I^a * W^b * Th^c (W and Th in mil): Brooks & Adam's curve fits to the IPC-2152 charts, as in KiCad's track
width calculator; external K, a, b, c = 215.3, 2.0, -1.15, -1.0; internal 200, 1.9, -1.10, -1.52. No plane credit, so
an upper bound (M3_R7 "High-current copper: IPC-2152 estimate"; about half with the In1 plane credit, Inference).
Copper: 35 um outer, 30 um inner (the ordered JLC041611-7628 stack-up, M1). R8_DECISIONS D12 sets the R8 thresholds:
RAW_ACT and BAT_IN necks <= 20 C, ACT_FET_S <= 30 C at 7.7 A (REQUIREMENTS F4).
"""
FIT = {'external': (215.3, 2.0, -1.15, -1.0), 'internal': (200.0, 1.9, -1.10, -1.52)}
TH_MIL = {'F.Cu': 35 / 25.4, 'B.Cu': 35 / 25.4, 'In1.Cu': 30 / 25.4, 'In2.Cu': 30 / 25.4}
AMPS = 7.7
D12_MAX_RISE = {'RAW_ACT': 20.0, 'BAT_IN': 20.0, 'ACT_FET_S': 30.0}   # C at AMPS (R8_DECISIONS D12)


def _fit(layer):
    return FIT['external' if layer in ('F.Cu', 'B.Cu') else 'internal']


def ipc_dt(width_mm, layer, amps=AMPS):
    """Temperature rise (C) of a conductor width_mm wide on `layer` carrying `amps`."""
    k, a, b, c = _fit(layer)
    return k * amps ** a * (width_mm / 0.0254) ** b * TH_MIL[layer] ** c


def ipc_width(dt, layer, amps=AMPS):
    """Width (mm) on `layer` that rises dt C at `amps`."""
    k, a, b, c = _fit(layer)
    return (dt / (k * amps ** a * TH_MIL[layer] ** c)) ** (1 / b) * 0.0254

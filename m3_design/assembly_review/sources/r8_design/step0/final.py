"""Score the decided R8 pin map (F1) and its near alternatives on the annulus model."""
import collections, pinmodel as m
WEST = {'LED_RED': (6.0, 47.0), 'LED_YEL': (6.0, 50.0)}
def run(tag, moves, west=True, detail=False):
    saved = dict(m.DEST)
    if west: m.DEST.update(WEST)
    a = m.base(); a.update(moves); c, pairs = m.crossings(a, detail=True)
    print(f'{tag:44s} crossings {c:3d} flyline {m.flyline(a):4.0f} mm')
    if detail:
        for p in pairs: print('   ', p)
    m.DEST.clear(); m.DEST.update(saved)
F1 = {'LED_RED': 86, 'LED_YEL': 88, 'VBUS_SENSE': 65, 'BAT_FAULT_N': 28, 'LOGIC_SOURCE_ST': 29, 'CAM_UART_OE': 31,
      'CAM_FAULT_N': 41, 'CAM_PWR_EN': 42, 'BUZZ_DRV': 7}
run('R7 pins at rot 0 (reference)', {k: v for k, v in m.R7.items()}, west=False)
run('H0 + UART7 + PE9 only (LEDs PA6/PA7, VBUS PC8)', {'LED_YEL': 30, 'LED_RED': 31, 'VBUS_SENSE': 65}, west=False)
run('F1 decided map', F1, detail=True)
run('F1 with LEDs PD0/PD1', dict(F1, LED_RED=81, LED_YEL=82))
run('F1 with BUZZ PC15', dict(F1, BUZZ_DRV=9))
run('F1 with CAM_EN PE14', dict(F1, CAM_PWR_EN=44))
run('B-like: LEDs east PA6/PA7, OE PE14', dict(F1, LED_YEL=30, LED_RED=31, CAM_UART_OE=44), west=False)
run('H1 fallback (SCK PB13, NSS PB12) on F1', dict(F1, RADIO_SCK_MCU=52, RADIO_NSS=51))

"""R11 family `signals` (stage C1b, D-R11-44): the camera port's MCU side (U1 to the U12 buffer, U402's enable and
fault, the camera-supply sense divider) and the buffer's port side and isolated supply (U12 / U13 to J9's clamps).
Explicit tables only (D-R11-07), frozen in r11_escape.py; the escapes are pinned in r11_fanout.tsv (stageC1b.md)."""

NETS = ('CAM_PWR_EN', 'CAM_5V_SENSE', 'CAM_FAULT_N', 'CAM_UART_OE', 'CAM_MCU_TX', 'CAM_MCU_RX', 'CAM_TX_BUFFER', 'CAM_IO_3V3')
# D-R11-49: CAM_RX_BUFFER stays pending (extra_vias: four vias across the CAM_5V path, stageC1b.md section 8); C4:
# forced, an allowlist request to the gate lane (stageC4.md section 4)


def draw(d):
    import r11_escape
    r11_escape.draw(d, 'signals')

"""R8 step 0: annulus crossing model for U1 follow-on pin moves (U1 rotation 0 at (23, 45), B seed floorplan).

Same method as the connectivity survey's annulus.py: crossings = inversions between U1 package order and the
angular order of each signal's destination seen from U1's centre, minimised over the cut. Destinations are part
centres from partial/b0_place_final.tsv; RF lanes use the strip-mouth entry x (y 23.5) in the lane order the modules
force. Dives (QSPI, HSE, NRST, BOOT0, ARM1_SENSE_MCU, V3V3/VLOGIC sense) are excluded. A planning model, not routing.
"""
import itertools, math, sys

CX, CY = 23.0, 45.0
def pinxy(n):
    if 1 <= n <= 25:  return (17 + (n - 1) * 0.5, 52.55)
    if 26 <= n <= 50: return (30.55, 51 - (n - 26) * 0.5)
    if 51 <= n <= 75: return (29 - (n - 51) * 0.5, 37.45)
    return (15.45, 39 + (n - 76) * 0.5)
PORT = {}
for n, p in {1: 'PE2', 2: 'PE3', 3: 'PE4', 4: 'PE5', 5: 'PE6', 7: 'PC13', 8: 'PC14', 9: 'PC15', 12: 'PH0', 13: 'PH1',
             15: 'PC0', 16: 'PC1', 17: 'PC2_C', 18: 'PC3_C', 22: 'PA0', 23: 'PA1', 24: 'PA2', 25: 'PA3', 28: 'PA4',
             29: 'PA5', 30: 'PA6', 31: 'PA7', 32: 'PC4', 33: 'PC5', 34: 'PB0', 35: 'PB1', 36: 'PB2', 37: 'PE7',
             38: 'PE8', 39: 'PE9', 40: 'PE10', 41: 'PE11', 42: 'PE12', 43: 'PE13', 44: 'PE14', 45: 'PE15', 46: 'PB10',
             47: 'PB11', 51: 'PB12', 52: 'PB13', 53: 'PB14', 54: 'PB15', 55: 'PD8', 56: 'PD9', 57: 'PD10', 58: 'PD11',
             59: 'PD12', 60: 'PD13', 61: 'PD14', 62: 'PD15', 63: 'PC6', 64: 'PC7', 65: 'PC8', 66: 'PC9', 67: 'PA8',
             68: 'PA9', 69: 'PA10', 70: 'PA11', 71: 'PA12', 72: 'PA13', 76: 'PA14', 77: 'PA15', 78: 'PC10', 79: 'PC11',
             80: 'PC12', 81: 'PD0', 82: 'PD1', 83: 'PD2', 84: 'PD3', 85: 'PD4', 86: 'PD5', 87: 'PD6', 88: 'PD7',
             89: 'PB3', 90: 'PB4', 91: 'PB5', 92: 'PB6', 93: 'PB7', 95: 'PB8', 96: 'PB9', 97: 'PE0', 98: 'PE1'}.items():
    PORT[n] = p

ENTRY = {'RADIO_NRST': 36.6, 'RADIO_DIO1': 32.4, 'RADIO_SCK_MCU': 24.6, 'RADIO_NSS': 24.3, 'RADIO_MOSI_MCU': 24.0,
         'RADIO_MISO_MCU': 23.7, 'RADIO_BUSY': 23.4, 'RADIO_RXEN': 23.1,
         'GNSS_RESET_N': 14.8, 'GNSS_TP_MCU': 9.3, 'GNSS_RXD_MCU': 8.2, 'GNSS_TXD_MCU': 7.1}
DEST = {k: (x, 23.5) for k, x in ENTRY.items()}
DEST.update({
    'USB_DM': (11.0, 33.4), 'USB_DP': (11.0, 33.8), 'SWDIO': (9.5, 42.3), 'SWCLK': (9.5, 42.9),
    'SPI1_SCK': (10.0, 53.4), 'SPI1_MISO': (10.0, 53.6), 'SPI1_MOSI': (10.0, 53.8), 'IMU_CS': (10.0, 54.0),
    'IMU_INT1': (10.0, 54.4), 'I2C1_SCL': (10.6, 60.0), 'I2C1_SDA': (10.6, 60.4),
    'SERVO1_MCU': (27.5, 60.0), 'SERVO2_MCU': (28.0, 60.0), 'SERVO3_MCU': (28.5, 60.0), 'SERVO4_MCU': (29.0, 60.0),
    'PYRO1_GATE_N': (16.8, 70.0), 'PYRO1_CONT_MCU': (18.4, 70.0),
    'RAW_ACT_SENSE_MCU': (33.0, 47.4), 'CAM_5V_SENSE': (33.0, 44.6),
    'CAM_MCU_TX': (34.6, 45.0), 'CAM_MCU_RX': (34.6, 45.4), 'CAM_UART_OE': (34.6, 46.0),
    'CAM_PWR_EN': (31.6, 32.6), 'CAM_FAULT_N': (34.0, 34.6),
    'LED_RED': (40.6, 51.6), 'LED_YEL': (40.6, 54.0), 'BUZZ_DRV': (16.5, 63.8), 'PULLPIN': (13.8, 72.2),
    'BAT_FAULT_N': (41.0, 88.0), 'LOGIC_SOURCE_ST': (35.6, 57.0), 'USB_FAULT_N': (12.4, 38.0),
    'VBUS_SENSE': (12.4, 30.0),
})
R7 = {'QSPI_IO2': 1, 'PYRO1_GATE_N': 3, 'CAM_UART_OE': 7, 'PULLPIN': 8, 'PYRO1_CONT_MCU': 15,
      'SERVO1_MCU': 22, 'SERVO2_MCU': 23, 'SERVO3_MCU': 24, 'SERVO4_MCU': 25, 'BUZZ_DRV': 29,
      'RAW_ACT_SENSE_MCU': 34, 'CAM_5V_SENSE': 35, 'LED_YEL': 37, 'LED_RED': 38, 'RADIO_RXEN': 45,
      'CAM_MCU_TX': 46, 'CAM_MCU_RX': 47, 'RADIO_NSS': 51, 'RADIO_SCK_MCU': 52, 'RADIO_MISO_MCU': 53,
      'RADIO_MOSI_MCU': 54, 'RADIO_BUSY': 55, 'RADIO_NRST': 56, 'RADIO_DIO1': 57, 'GNSS_TP_MCU': 61,
      'VBUS_SENSE': 62, 'GNSS_RXD_MCU': 63, 'GNSS_TXD_MCU': 64, 'GNSS_RESET_N': 65, 'USB_DM': 70, 'USB_DP': 71,
      'SWDIO': 72, 'SWCLK': 76, 'BAT_FAULT_N': 81, 'LOGIC_SOURCE_ST': 82, 'CAM_PWR_EN': 84, 'CAM_FAULT_N': 85,
      'USB_FAULT_N': 87, 'SPI1_SCK': 89, 'SPI1_MISO': 90, 'SPI1_MOSI': 91, 'IMU_CS': 93, 'I2C1_SCL': 95,
      'I2C1_SDA': 96, 'IMU_INT1': 98}
R7.pop('QSPI_IO2')
H0 = {'RADIO_SCK_MCU': 46, 'RADIO_NSS': 47, 'RADIO_MOSI_MCU': 53, 'RADIO_MISO_MCU': 54, 'RADIO_RXEN': 56,
      'RADIO_NRST': 39, 'RADIO_DIO1': 45, 'GNSS_RESET_N': 61, 'GNSS_TP_MCU': 62, 'CAM_MCU_TX': 38, 'CAM_MCU_RX': 37}

def ang(p):
    return math.atan2(p[1] - CY, p[0] - CX)

def crossings(assign, detail=False):
    sigs = sorted(assign, key=lambda s: -ang(pinxy(assign[s])))  # package order = decreasing pin angle
    th = [-ang(DEST[s]) for s in sigs]
    n = len(sigs); best = None
    for c in range(n):
        seq = [(th[(c + i) % n] - th[c]) % (2 * math.pi) for i in range(n)]
        inv = 0; pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                if seq[i] > seq[j] + 1e-9:
                    inv += 1
                    if detail: pairs.append((sigs[(c + i) % n], sigs[(c + j) % n]))
        if best is None or inv < best[0]:
            best = (inv, pairs)
    return best

def octi(a, b):
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1]); return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)

def flyline(assign):
    return sum(octi(pinxy(p), DEST[s]) for s, p in assign.items())

def base():
    a = dict(R7); a.update(H0); return a

if __name__ == '__main__':
    a = base()
    print('R7 pins (rot 0, B seed):', crossings(dict(R7))[0], f'{flyline(R7):.0f} mm')

"""Camera power addition for the single-board M3 candidate.

Connections are authored from manufacturer pin tables, not reverse-engineered
from a PCB. This revision does not claim that the camera UART electrical levels
are known: J9.3/4 end at accessible characterization pads, not MCU GPIO.
"""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'm3_core'
REVISION = 'M3-CAM-R1'
BASE_BOARD_SHA256 = 'cd647b9400a4e2bfca729b0c96e97cb2fb97ec3455387bfe58a5aeb008527f72'

# Separate enable and fault GPIO. Both are unused in CORE-R3. Pin names are
# resolved through the pinned ST symbol, with a separate numeric cross-check.
MCU_ADDITIONS = {'PD3': 'CAM_PWR_EN', 'PD4': 'CAM_FAULT_N'}
MCU_NUMBERS = {'PD3': '84', 'PD4': '85'}

# [LCSC, footprint, value, function]. Empty LCSC means sourcing is OPEN,
# never an inferred orderable part number. Precision/voltage requirements
# are also machine-readable below, so a value-only BOM is not sufficient.
PARTS = {
 'U7':['C1849463','M3_TPS2595_DSG','TPS259570DSGR','Camera input eFuse; latch-off after thermal shutdown'],
 'U8':['C2071868','M3_AP63200_TSOT26','AP63200WU-7','Dedicated adjustable camera buck'],
 'L3':['','M3_SRP5030TA','10uH','Bourns SRP5030TA-100M; 128mR max at 25C'],
 'J9':['C2915641','M3_DB128V_4P','CAM 5V / GND / RX / TX','4-position screw terminal; UART characterization only in R1'],
 'R70':['','R_0603_1608Metric','1.78k 0.1%','Input current limit; manufacturer-characterized resistance'],
 'R71':['','R_0603_1608Metric','172k 0.1%','Output feedback upper arm; dedicated camera voltage headroom'],
 'R72':['','R_0603_1608Metric','30.9k 0.1%','Output feedback lower arm'],
 'R74':['','R_0603_1608Metric','1k','Enable series isolation'],
 'R75':['','R_0603_1608Metric','10k','eFuse enable defaults OFF'],
 'R76':['','R_0603_1608Metric','10k','Open-drain fault pull-up on MCU side'],
 'R77':['','R_0603_1608Metric','1k','Fault line series isolation'],
 'R78':['','R_0603_1608Metric','10k','Camera output discharge / external-meter load'],
 'C70':['','C_0603_1608Metric','3.3nF 25V','eFuse input slew rate; maximum specified CdVdt'],
 'C71':['','C_0603_1608Metric','100nF 25V','eFuse local input bypass'],
 'C72':['','C_1206_3216Metric','22uF 25V X7R','Buck input capacitance; effective C still to verify'],
 'C73':['','C_1206_3216Metric','22uF 25V X7R','Buck input capacitance; effective C still to verify'],
 'C74':['','C_0603_1608Metric','100nF 25V','Bootstrap capacitor, between BST and SW'],
 'C75':['','C_1206_3216Metric','22uF 25V X7R','Camera output capacitor'],
 'C76':['','C_1206_3216Metric','22uF 25V X7R','Camera output capacitor'],
 'C77':['','C_0603_1608Metric','100pF C0G','Feed-forward capacitor across upper feedback resistor'],
}

PINS = {
 'U7':{'1':'CAM_DVDT','2':'CAM_EN','3':'RAW_PROTECTED','4':'RAW_PROTECTED',
       '5':'CAM_INPUT_LIMITED','6':'CAM_FLT_RAW','7':'CAM_ILIM','8':'GND','9':'GND'},
 'U8':{'1':'CAM_FB','2':'CAM_INPUT_LIMITED','3':'CAM_INPUT_LIMITED',
       '4':'GND','5':'CAM_SW','6':'CAM_BST'},
 'J9':{'1':'CAM_5V','2':'GND','3':'CAM_RX_TEST','4':'CAM_TX_TEST'},
}

TWO_PIN = {
 'L3':('CAM_SW','CAM_5V'),
 'R70':('CAM_ILIM','GND'),
 'R71':('CAM_5V','CAM_FB'), 'R72':('CAM_FB','GND'),
 'R74':('CAM_PWR_EN','CAM_EN'), 'R75':('CAM_EN','GND'),
 'R76':('3V3','CAM_FAULT_N'), 'R77':('CAM_FAULT_N','CAM_FLT_RAW'),
 'R78':('CAM_5V','GND'),
 'C70':('CAM_DVDT','GND'), 'C71':('RAW_PROTECTED','GND'),
 'C72':('CAM_INPUT_LIMITED','GND'), 'C73':('CAM_INPUT_LIMITED','GND'),
 'C74':('CAM_SW','CAM_BST'), 'C75':('CAM_5V','GND'),
 'C76':('CAM_5V','GND'), 'C77':('CAM_5V','CAM_FB'),
}
PINS.update({r:dict(zip('12',nets)) for r,nets in TWO_PIN.items()})
PROBES = {
 'TP70':('RAW_PROTECTED','Protected battery branch input; NOT a battery connector'),
 'TP71':('CAM_INPUT_LIMITED','eFuse output / buck input'),
 'TP72':('CAM_5V','Regulated camera output at the PCB'),
 'TP73':('CAM_ILIM','Current monitor; use >=10Mohm probe, never short'),
 'TP74':('GND','Local measurement ground'),
 'TP75':('CAM_RX_TEST','J9.3 from camera TX: characterize logic level first'),
 'TP76':('CAM_TX_TEST','J9.4 to camera RX: no MCU connection in this revision'),
}
for ref,(net,description) in PROBES.items():
    PARTS[ref]=['','M3_TestPad_1.5',net,description]
    PINS[ref]={'1':net}

NUMERIC = {
 'r_feedback_upper_ohm':172000., 'r_feedback_lower_ohm':30900.,
 'r_feedback_tolerance':0.001, 'feedback_ref_min_v':0.792,
 'feedback_ref_typ_v':0.800, 'feedback_ref_max_v':0.808,
 'r_ilim_ohm':1780., 'r_ilim_tolerance':0.001,
 'ilim_min_at_nominal_r_a':1.09, 'ilim_typ_at_nominal_r_a':1.17,
 'ilim_max_at_nominal_r_a':1.24,
 'efuse_ron_max_ohm':0.053, 'input_min_v':6., 'input_max_v':8.4,
 'inductor_h':10e-6, 'inductor_tolerance':0.20,
 'inductor_dcr_max_25c_ohm':0.128,
 'inductor_irms_25c_a':2.75, 'inductor_isat_25c_a':3.5,
 'switch_frequency_hz':500000., 'switch_frequency_spread':0.06,
 'buck_peak_limit_min_a':2.5, 'buck_peak_limit_max_a':3.1,
 'output_cap_nominal_f':44e-6, 'input_cap_nominal_f':44e-6,
 'output_bleeder_ohm':10000., 'rated_camera_load_a':1.,
 'manual_camera_current_a':0.45,
 # Explicit project assumptions, not guaranteed component specifications.
 'minimum_efficiency_assumption':0.85,
 'cable_round_trip_max_ohm':0.10, 'output_effective_cap_min_assumption_f':22e-6,
 'pcb_camera_path_max_ohm_assumption':0.04,
 'ripple_and_static_model_allowance_v':0.02,
}

SHEETS = {
 'camera_power': 'U7 U8 L3 C70 C71 C72 C73 C74 C75 C76 C77 R70 R71 R72 R74 R75 R76 R77 R78 TP70 TP71 TP73'.split(),
 'camera_connector': 'J9 TP72 TP74 TP75 TP76'.split(),
}

def full_parts():
    return {**json.loads((BASE/'parts.json').read_text()), **PARTS}

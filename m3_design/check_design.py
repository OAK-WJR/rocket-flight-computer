#!/usr/bin/env python3
"""Independent camera contract/corner checks against the serialized candidate.

These checks qualify a CAD artifact and conditional DC estimates, not hardware
stability, loop compensation, thermal performance or full M3 functionality.
"""
import hashlib, json, math, re, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'quality_audit'))
from sexpr import read, properties
import camera_intent as c


def value(text):
    m=re.match(r'^([\d.]+)\s*([kmunp]?)',text)
    if not m:raise ValueError('Not a numeric component value: '+text)
    return float(m[1])*{'':1,'k':1e3,'m':1e-3,'u':1e-6,'n':1e-9,'p':1e-12}[m[2]]


def xy(n,key):return tuple(float(v.atom) for v in n.children(key)[0].items[1:3])


def inspect(text):
    root=read(text);fps={properties(f)['Reference'].items[2].atom:f for f in root.children('footprint')}
    vals={r:properties(f)['Value'].items[2].atom for r,f in fps.items()}
    pin={}
    for ref,f in fps.items():
        for p in f.children('pad'):
            if p.items[1].atom:pin[ref+'.'+p.items[1].atom]=p.children('net')[0].items[1].atom if p.children('net') else None
    return root,fps,vals,pin


def check(text,folder=None,core_offset_y=40.):
    root,fps,vals,pin=inspect(text);issues=[]
    def require(ok,msg):
        if not ok:issues.append(msg)
    # This checklist deliberately names electrical roles independently of the
    # generator's PINS table. It catches a consistent but wrong table/board.
    required={
      'U7.1':'CAM_DVDT','U7.2':'CAM_EN','U7.3':'RAW_PROTECTED','U7.4':'RAW_PROTECTED',
      'U7.5':'CAM_INPUT_LIMITED','U7.6':'CAM_FLT_RAW','U7.7':'CAM_ILIM','U7.8':'GND','U7.9':'GND',
      'U8.1':'CAM_FB','U8.2':'CAM_INPUT_LIMITED','U8.3':'CAM_INPUT_LIMITED','U8.4':'GND','U8.5':'CAM_SW','U8.6':'CAM_BST',
      'J9.1':'CAM_5V','J9.2':'GND','J9.3':'CAM_RX_TEST','J9.4':'CAM_TX_TEST',
      'U1.84':'CAM_PWR_EN','U1.85':'CAM_FAULT_N',
      'R70.1':'CAM_ILIM','R70.2':'GND','R71.1':'CAM_5V','R71.2':'CAM_FB','R72.1':'CAM_FB','R72.2':'GND',
      'R74.1':'CAM_PWR_EN','R74.2':'CAM_EN','R75.1':'CAM_EN','R75.2':'GND',
      'R76.1':'3V3','R76.2':'CAM_FAULT_N','R77.1':'CAM_FAULT_N','R77.2':'CAM_FLT_RAW',
      'R78.1':'CAM_5V','R78.2':'GND','C74.1':'CAM_SW','C74.2':'CAM_BST',
      'C77.1':'CAM_5V','C77.2':'CAM_FB','L3.1':'CAM_SW','L3.2':'CAM_5V',
      'TP70.1':'RAW_PROTECTED','TP71.1':'CAM_INPUT_LIMITED','TP72.1':'CAM_5V','TP73.1':'CAM_ILIM','TP74.1':'GND',
      'TP75.1':'CAM_RX_TEST','TP76.1':'CAM_TX_TEST',
    }
    for p,n in required.items():require(pin.get(p)==n,'Camera pin contract: '+p)
    for r in ('C71','C72','C73','C75','C76'):
        require(pin.get(r+'.2')=='GND','Bypass ground: '+r)
    require({p for p,n in pin.items() if n=='CAM_RX_TEST'}=={'J9.3','TP75.1'},'Unqualified camera RX connected outside test pads')
    require({p for p,n in pin.items() if n=='CAM_TX_TEST'}=={'J9.4','TP76.1'},'Unqualified camera TX connected outside test pads')
    require(vals.get('U7')=='TPS259570DSGR','eFuse variant differs; thermal latch behavior not preserved')
    require(vals.get('U8')=='AP63200WU-7','Adjustable 500kHz regulator required')
    for ref,expected in [('R70',1780),('R74',1000),('R75',10000),('R76',10000),('R77',1000),('R78',10000)]:
        require(math.isclose(value(vals[ref]),expected,rel_tol=1e-8),'Protection/control value: '+ref)
    for ref in ('R70','R71','R72'):require('0.1%' in vals[ref],'Precision grade absent: '+ref)
    require(math.isclose(value(vals['L3']),10e-6,rel_tol=1e-8),'L3 is not 10uH')
    for ref in ('C72','C73','C75','C76'):
        require('25V' in vals[ref] and 'X7R' in vals[ref] and math.isclose(value(vals[ref]),22e-6),'Capacitor specification: '+ref)
    # Manufacturer-land transcription, independent of footprint generator.
    pads={r:{p.items[1].atom:p for p in f.children('pad')} for r,f in fps.items()}
    def land(ref,num,wanted,size):
        q=pads[ref][str(num)]
        require(xy(q,'at')==wanted and xy(q,'size')==size,'Manufacturer land geometry: %s.%s'%(ref,num))
    for num,x,y in [(1,-.95,-.75),(2,-.95,-.25),(3,-.95,.25),(4,-.95,.75),(5,.95,.75),(6,.95,.25),(7,.95,-.25),(8,.95,-.75)]:land('U7',num,(x,y),(.5,.25))
    land('U7',9,(0,0),(.9,1.6))
    for num,x,y in [(1,-1.1,-.95),(2,-1.1,0),(3,-1.1,.95),(4,1.1,.95),(5,1.1,0),(6,1.1,-.95)]:land('U8',num,(x,y),(1,.7))
    for i in range(1,5):
        q=pads['J9'][str(i)];require(abs(xy(q,'at')[0]-(-7.62+5.08*(i-1)))<1e-6,'J9 pitch/order')
        require(float(q.children('drill')[0].items[1].atom)==1.6,'J9 finished hole must be 1.6 mm')
    for r,f in fps.items():
        props=properties(f)
        require(props.get('LCSC').items[2].atom==props.get('LCSC Part').items[2].atom,'Conflicting distributor fields: '+r)
        for m in f.children('model'):
            name=m.items[1].atom
            require(name.startswith('${KIPRJMOD}/'),'Non-portable 3D path: '+r)
            if folder and name.startswith('${KIPRJMOD}/'):require((folder/name.split('}/',1)[1]).is_file(),'Missing model: '+r)
        require(bool(f.children('attr')),'Missing assembly classification: '+r)
        if r in c.PROBES:
            attr=f.children('attr')[0].value()
            require('exclude_from_bom' in attr and 'exclude_from_pos_files' in attr,'Test pad included in assembly: '+r)
            require(not any('F.Paste' in q.children('layers')[0].value() for q in f.children('pad')),'Test pad has solder paste: '+r)
    # Retained copper is compared by UUID, including all dimensions/layers/nets.
    baseline=(c.BASE/'review/m3_core.kicad_pcb').read_text();old=read(baseline)
    for kind in ('segment','via'):
        actual={q.children('uuid')[0].items[1].atom:q for q in root.children(kind)}
        for q in old.children(kind):
            ident=q.children('uuid')[0].items[1].atom;a=actual.get(ident)
            require(a is not None,'Lost retained CORE copper: '+ident)
            if a is None:continue
            for key in ('start','end') if kind=='segment' else ('at',):
                x,y=xy(q,key);ax,ay=xy(a,key)
                require(abs(ax-x)<1e-6 and abs(ay-y-core_offset_y)<1e-6,'Moved retained CORE route: '+ident)
            for key in ('width','layer','net') if kind=='segment' else ('size','drill','layers','net'):
                av=a.children(key)[0].value();qv=q.children(key)[0].value()
                same=math.isclose(float(av[1]),float(qv[1]),rel_tol=1e-10) if key in ('width','size','drill') else av==qv
                require(same,'Changed retained CORE copper: '+ident)
    n=c.NUMERIC;ru=value(vals['R71']);rl=value(vals['R72']);tol=n['r_feedback_tolerance']
    vtyp=.8*(1+ru/rl);vmin=.792*(1+ru*(1-tol)/(rl*(1+tol)));vmax=.808*(1+ru*(1+tol)/(rl*(1-tol)))
    dc_floor=vmin-n['rated_camera_load_a']*(n['cable_round_trip_max_ohm']+n['pcb_camera_path_max_ohm_assumption'])
    require(dc_floor-n['ripple_and_static_model_allowance_v']>=5.,'Camera minimum voltage below 5V under declared loss assumptions')
    require(vmax<5.4,'Camera output differs from reviewed 5V-class setpoint')
    pout=vmax*n['rated_camera_load_a'];eta=n['minimum_efficiency_assumption'];vbat=n['input_min_v'];ron=n['efuse_ron_max_ohm']
    # Pout = eta * Iin * (Vin - Iin*Ron); lower root is the normal operating branch.
    iin=(vbat-math.sqrt(vbat*vbat-4*ron*pout/eta))/(2*ron)
    limit_est=.04+(n['ilim_min_at_nominal_r_a']-.04)/(1+n['r_ilim_tolerance'])
    require(iin<limit_est,'Conditional input current exceeds eFuse minimum limit')
    lmin=value(vals['L3'])*(1-n['inductor_tolerance']);fmin=n['switch_frequency_hz']*(1-n['switch_frequency_spread'])
    ripple=vmax*(1-vmax/n['input_max_v'])/(lmin*fmin)
    peak=n['rated_camera_load_a']+ripple/2
    require(peak<n['buck_peak_limit_min_a'] and peak<n['inductor_isat_25c_a'],'Inductor peak-current check')
    estimates={'output_nominal_v':vtyp,'output_static_min_v':vmin,'output_static_max_v':vmax,
      'camera_min_after_cable_and_pcb_at_1a_v':dc_floor,'camera_min_with_20mv_allowance_v':dc_floor-.02,
      'input_current_at_6v_1a_output_eta85_a':iin,
      'ilim_lower_estimate_including_resistor_tolerance_a':limit_est,'inductor_ripple_pp_a':ripple,'inductor_peak_at_1a_a':peak,
      'inductor_copper_loss_25c_at_1a_w':(1+ripple*ripple/12)*n['inductor_dcr_max_25c_ohm'],
      'r70_power_at_max_ilim_w':(.304e-3*n['ilim_max_at_nominal_r_a'])**2*value(vals['R70']),
      'unqualified':['efficiency minimum','DC capacitor bias and aging','PFM/no-load regulation','dynamic load/current-limit interactions',
                    'temperature/current derating','input reverse energy and surge','recording startup/current waveform','MCU firmware','UART compatibility']}
    return {'ok':not issues,'issues':issues,'footprints':len(fps),'nominally_fitted_parts':len(fps)-len(c.PROBES)-1,
      'scope':'Camera pin contract, retained CORE copper, nominal lands, conditional DC estimates',
      'estimates':estimates,'fabrication_release':False,'hardware_tested':False}


if __name__=='__main__':
    folder=HERE/'review';board=folder/'m3.kicad_pcb';result=check(board.read_text(),folder)
    result['board_sha256']=hashlib.sha256(board.read_bytes()).hexdigest()
    (folder/'camera_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Camera artifact checks:',result['ok'],result['issues'])
    raise SystemExit(0 if result['ok'] else 1)

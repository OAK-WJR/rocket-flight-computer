* models.inc - M3-ASSY-R2 actuator-band simulation models (ngspice)
* Every number is from the named datasheet; level-1 fits are two-point fits of RDS(on).
* Level-1 has no sub-threshold conduction: gate safety is judged against VGS(th) min,
* never against simulated drain current alone.
*
* --- AON6403 P-ch, AOS datasheet Rev 2.1 Sep 2023 ---
* VGS(th) -1.2/-1.7/-2.2 V; RDS(on) 3.5/4.3 mOhm @-4.5 V, 2.6/3.1 @-10 V; Ciss 7.6 nF, Crss 1.05 nF @-15 V
* Fit Rds = RD + 1/(KP*(|Vgs|-|VTO|)):  TYP VTO=-1.7 KP=212 RD=1.9m -> 3.3m @-4.5 V, 2.5m @-10 V
*                                        SLOW VTO=-2.2 KP=212 RD=2.4m -> 4.3m @-4.5 V, 3.0m @-10 V
.model PM_TYP  PMOS(LEVEL=1 VTO=-1.7 KP=212 RD=1.9m  IS=1e-20)
.model PM_SLOW PMOS(LEVEL=1 VTO=-2.2 KP=212 RD=2.4m  IS=1e-20)
.model PM_FAST PMOS(LEVEL=1 VTO=-1.2 KP=212 RD=1.9m  IS=1e-20)
.model DBODY6403 D(IS=4.4p N=1.0 RS=1.5m BV=30 IBV=1m)
.subckt AON6403 d g s
Rg  g  gi 2
M1  d  gi s s PM_TYP
Cgs gi s  6.5n
Cgd gi d  1.5n
Cds d  s  2n
Db  d  s  DBODY6403
.ends
.subckt AON6403S d g s
Rg  g  gi 2
M1  d  gi s s PM_SLOW
Cgs gi s  6.5n
Cgd gi d  1.5n
Cds d  s  2n
Db  d  s  DBODY6403
.ends
*
* --- AON7524 N-ch, AOS datasheet Rev 1.1 Oct 2023 ---
* VGS(th) 0.4/0.8/1.2 V; RDS(on) 3.0/4.0 mOhm @4.5 V, 4.4/5.8 @2.5 V; Rg 1.5/3.0/4.5 ohm
* Fig. 8 at VDS=0: Ciss ~2.6 nF, Crss ~450 pF, Coss ~2.4 nF.  Constant Cgd = 450 pF is the
* 0 V value, i.e. the worst case for Miller coupling at every VDS.
* Fit: TYP VTO=0.8 KP=227 RD=1.81m -> 4.4m @2.5 V, 3.0m @4.5 V
*      MAX VTO=1.2 KP=259 RD=2.83m -> 5.8m @2.5 V, 4.0m @4.5 V
*      MIN VTO=0.4 (weakest-threshold part, used for the plug-insertion case)
.model NM_TYP NMOS(LEVEL=1 VTO=0.8 KP=227 RD=1.81m IS=1e-20)
.model NM_MAX NMOS(LEVEL=1 VTO=1.2 KP=259 RD=2.83m IS=1e-20)
.model NM_MIN NMOS(LEVEL=1 VTO=0.4 KP=227 RD=1.81m IS=1e-20)
.model DBODY7524 D(IS=1e-11 N=1.0 RS=5m BV=30 IBV=1m)
.subckt AON7524 d g s
Rg  g  gi 3
M1  d  gi s s NM_TYP
Cgs gi s  2150p
Cgd gi d  450p
Cds d  s  1950p
Db  s  d  DBODY7524
.ends
.subckt AON7524MAX d g s
Rg  g  gi 3
M1  d  gi s s NM_MAX
Cgs gi s  2150p
Cgd gi d  450p
Cds d  s  1950p
Db  s  d  DBODY7524
.ends
.subckt AON7524MIN d g s
Rg  g  gi 1.5
M1  d  gi s s NM_MIN
Cgs gi s  2150p
Cgd gi d  450p
Cds d  s  1950p
Db  s  d  DBODY7524
.ends
*
* --- AO3400A N-ch, AOS Rev 3.1 Jul 2023 (fit carried over from the R1 buzzer study) ---
.model AO3400A_TYP NMOS(LEVEL=1 VTO=1.05 KP=80 RD=0.0154 IS=1e-20)
*
* --- BAT54 family (Vishay 86410): VF 0.24 V @0.1 mA, 0.32 V @1 mA, 0.40 V @10 mA, 0.8 V @100 mA ---
.model BAT54 D(IS=4.3n N=1 RS=3.6 CJO=10p BV=30 IBV=2u)
*
* --- SMBJ9.0CA bidirectional TVS on BAT_IN: VBR 10.0 V min, VC 15.4 V @ IPP ---
.model TVS9 D(IS=1p N=1 RS=0.15 BV=10.5 IBV=1m CJO=1n)
*
* --- STM32H743 push-pull pin, DS12110 Rev 5 Table 60 (VOL <= 0.4 V @ 8 mA, <= 1.3 V @ 20 mA) ---
* weakest legal driver; FT pins have no diode to VDD, a diode to VSS only
.model NDRV NMOS(LEVEL=1 VTO=1.15  KP=10.26m IS=1e-30)
.model PDRV PMOS(LEVEL=1 VTO=-1.15 KP=10.26m IS=1e-30)
.model DPINLO D(IS=1e-14 N=1 RS=1)
*
* --- SRV05-4 (onsemi): steering diodes VF 1.2 V max @15 mA; internal TVS VBR 6 V min ---
.model DSTEER D(IS=1.56e-13 N=1.3 RS=0.3 CJO=3p)
.model DTVS6  D(IS=1e-14 N=1 RS=4 BV=6 IBV=1m CJO=5p)

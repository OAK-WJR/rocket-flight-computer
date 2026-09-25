"""Report power evidence without turning an open-drain HIGH into power-good."""
MASK=0x53
FAULTS={1:'BATTERY_EFUSE',16:'CAMERA_EFUSE',64:'USB_LIMITER'}
def measurement(w):
    flags,gpio,history,sampled,event,count,gap=w[153:160]
    age=(w[5]-sampled)&0xffffffff
    observed=flags&7==7 and age<=100
    low=(~gpio)&MASK;seen=history&0xffff
    return dict(flags=flags,gpiod_idr=gpio,history=history,sampled_ms=sampled,age_ms=age,
       last_event_ms=event,irq_count_lower_bound=count,max_tick_gap_ms=gap,
       current_inputs_valid=observed,configuration_error_seen=bool(flags&32),
       active_fault_signals=[v for bit,v in FAULTS.items() if low&bit] if observed else None,
       fault_signals_seen=[v for bit,v in FAULTS.items() if seen&bit],
       source_report=('USB_OR_OUTPUT_HIZ' if gpio&2 else 'BATTERY_IN2_SELECTED') if observed else 'UNKNOWN',
       source_voltage_verified=False,hardware_qualified=False,
       note='HIGH is not power-good. A low fault signal localizes a protection channel, not its unique root cause. Tick/IRQ gaps are not independent wall-clock or pulse-width measurements.')
def checks(samples,live):
    rows=[measurement(s['words']) for s in samples];b=rows[-1]
    valid=live and b['current_inputs_valid']
    result=[('POWER_MONITOR','PASS' if valid and not b['configuration_error_seen'] else 'FAIL' if b['configuration_error_seen'] else 'INCONCLUSIVE',
      f"flags=0x{b['flags']:x}; sample age={b['age_ms']}ms; observed maximum tick gap={b['max_tick_gap_ms']}ms",
      'Confirm input configuration and probe TP85/86/87; masked interrupts can hide elapsed wall time.'),
     ('POWER_FAULT_SIGNALS','FAIL' if valid and b['active_fault_signals'] else 'INFO' if valid else 'INCONCLUSIVE',
      f"active={b['active_fault_signals']}; observed history={b['fault_signals_seen']}",
      'Compare branch voltage/current and temperature; FLT alone cannot distinguish overload, heat, reverse current or a wiring fault.'),
     ('POWER_FAULT_HISTORY','FAIL' if b['fault_signals_seen'] else 'INFO',str(b['fault_signals_seen']),
      'A transient or startup fault remains recorded after recovery. Empty history does not prove no fault occurred.'),
     ('POWER_SOURCE','INFO' if valid else 'INCONCLUSIVE',b['source_report'],
      'TPS2121 ST HIGH also means output high-Z. Check input and VLOGIC voltages with independent instruments.'),
     ('POWER_DYNAMIC_TEST','NOT_TESTED','Power switching, load steps, heating and absolute fault-pulse capture have no physical test results.','')]
    for a,b in zip(rows,rows[1:]):
        if a['history']&b['history']!=a['history'] or b['irq_count_lower_bound']<a['irq_count_lower_bound']:
            result.append(('POWER_HISTORY_CLEARED','FAIL','Status history/counter decreased within a capture; reset, corruption or wrong firmware.',''));break
    return result,rows

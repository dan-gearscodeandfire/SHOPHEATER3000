# Automatic Control Algorithm — Design

*Created: 2026-02-22*
*Updated: 2026-02-22 (post-Session 3, fan hardware findings)*

---

## System Overview

**Actuators (what the algorithm controls):**
- Fans: ON/OFF only (relay-switched 12V DC). No proportional speed control.
- Diversion valve: on/off (adds cold reservoir to the loop; radiator stays in loop)
- Main loop valve: on/off

**Fan hardware note:** The fans are 2-wire Atulban 12V 90W BLDC units drawing ~16A combined. They have internal BLDC drivers that expect clean DC voltage — PWM on the power line causes erratic behavior. The motor driver previously used is inadequate (under-rated for 16A, wrong control method for BLDC). Fans should be switched via a 30–40A automotive relay controlled by a Pi GPIO pin through a transistor (e.g., 2N2222 + flyback diode). Proportional speed control would require a high-current DC-DC buck converter, which is unnecessary given the data findings below.

**Sensors (inputs to the algorithm):**
- water_hot (heater outlet)
- water_mix (radiator inlet)
- water_cold (radiator outlet / pump inlet)
- water_reservoir
- air_cool (shop ambient / radiator intake)
- air_heated (radiator output)
- delta_water_heater (water_hot − water_cold)
- delta_water_radiator (water_mix − water_cold)
- flow_rate (GPM)

---

## Key Data Findings Informing the Design

1. **Fan speed does not affect water-side cooling.** Tested at 70%, 100%, and 0% (brief). The water-to-metal convective boundary is the rate-limiting step; the air side has excess capacity. Fan speed is purely a comfort control — it determines how much heat reaches the shop air, not how much leaves the water.

2. **Diversion is the only thermal safety mechanism.** Adding the cold reservoir is the only way to actively cool the water. Everything else (fan speed, flow rate) either doesn't help or isn't controllable.

3. **Flow rate is safety-critical and must be monitored.** A clogged gunk trap reduced flow from 2.5 to 0.67 GPM in Session 2. Low flow at high temps = danger.

4. **Radiator effectiveness depends on flow rate and fill state.** Properly purged full radiator: 59–74% at 2.75–3.75 GPM. Incompletely filled: ~30%. The algorithm cannot assume a fixed effectiveness.

5. **The predictive safety rule works.** In Session 3, hot + delta_heater reached 209°F — the proposed "hot + delta > 190" trigger would have correctly fired.

---

## Starting Conditions

- Water is cool and uniform in temperature
- Main loop: OPEN (on)
- Diversion: CLOSED (off)
- Fans: OFF

---

## Algorithm States

### Phase 1: Cold Start / Waiting

**Condition:** water_hot < FAN_ON_THRESHOLD

**Actions:**
- Fans: OFF
- Diversion: OFF
- Main loop: ON

The heater is warming up. Circulating water through the main loop ensures the radiator and piping warm evenly, preventing localized boiling at the heater.

### Phase 2: Heat Delivery

**Condition:** water_hot >= FAN_ON_THRESHOLD

**Actions:**
- Fans: ON (full 12V via relay)
- Diversion: OFF
- Main loop: ON

Fans switch on at a single threshold. No proportional staging — the BLDC fans are on/off only. The threshold should be high enough that the radiator has meaningful heat to deliver (data shows ~10°F delta_radiator at mix ~80°F, meaningful output above ~100°F).

### Phase 3: Safety — Diversion Activation

**Activation condition (ANY triggers diversion ON):**
1. water_hot >= 180°F
2. water_hot + delta_water_heater >= 190°F (predictive: next-pass estimate)
3. flow_rate < FLOW_MIN_THRESHOLD while water_hot > 120°F (pump failure protection)

**Rationale:** Condition 2 is predictive — if the current temperature rise per pass would push the next reading past 190°F, act now. Condition 3 catches pump/gunk trap failures before they become dangerous.

**Deactivation condition:**
- water_hot < 160°F AND at least DIVERSION_MIN_HOLD seconds since activation

**Hysteresis:** The 20°F deadband (activate at 180, deactivate at 160) prevents rapid on/off cycling. The minimum hold ensures the reservoir absorbs meaningful heat.

### Phase 4: Cooling / Fire Dying

**Condition:** water_hot drops below FAN_OFF_THRESHOLD and trending downward

**Actions:**
- Fans: OFF

No point blowing lukewarm air into the shop. Once the water is too cool to provide useful heat, shut the fans off. Hysteresis: fans turn on at FAN_ON_THRESHOLD, turn off at FAN_OFF_THRESHOLD (lower), preventing rapid cycling near the boundary.

---

## Safety Constraints

1. **Water must NEVER reach boiling (212°F).** The 180°F diversion trigger provides a 32°F safety margin.
2. **Both valves must never be closed simultaneously.** Already enforced in existing software (safety interlock in `set_main_loop` and `set_diversion`).
3. **Diversion is the primary thermal safety mechanism.** Fan speed does not affect water-side cooling.
4. **Flow rate must be monitored.** Loss of flow at high temps is a critical failure mode.

---

## Parameters

| Parameter | Proposed Value | Notes |
|-----------|---------------|-------|
| FAN_ON_THRESHOLD | 110°F | Radiator producing useful heat |
| FAN_OFF_THRESHOLD | 90°F | Below this, air output isn't useful. 20°F hysteresis band. |
| DIVERSION_ON_TEMP | 180°F | Hard safety trigger |
| DIVERSION_PREDICTIVE | 190°F | water_hot + delta_heater threshold |
| DIVERSION_OFF_TEMP | 160°F | Deactivation threshold |
| DIVERSION_MIN_HOLD | 120s | Minimum time diversion stays on (TBD — pending diversion test) |
| FLOW_MIN_THRESHOLD | 0.5 GPM | Pump failure / gunk trap clog detection |

---

## Implementation Approach

The algorithm runs as a periodic check inside a dedicated `automatic_control_loop()`, executing every 5 seconds. It only acts when `control_mode == 'automatic'`. Manual mode overrides everything.

```
every 5 seconds:
    if control_mode != 'automatic':
        return

    read sensor data

    # SAFETY FIRST — diversion
    if water_hot >= 180 OR (water_hot + delta_heater >= 190):
        activate diversion
        record activation time
    elif flow_rate < 0.5 AND water_hot > 120:
        activate diversion
        record activation time
        log WARNING: low flow
    elif water_hot < 160 AND (time since activation > DIVERSION_MIN_HOLD):
        deactivate diversion

    # Fan control (on/off relay)
    if water_hot >= FAN_ON_THRESHOLD:
        fans ON
    elif water_hot < FAN_OFF_THRESHOLD:
        fans OFF
    # Between FAN_OFF and FAN_ON: maintain current state (hysteresis)
```

---

## Hardware TODO

- [ ] Replace motor driver with 30–40A automotive relay for fan control
- [ ] Wire relay coil through transistor (2N2222 or similar) + flyback diode to Pi GPIO
- [ ] Test relay switching from Pi GPIO
- [ ] Verify fans start reliably with relay-switched 12V

---

## Pending Tests

- **Controlled diversion cycle** (see `next_test.md`): needed to validate DIVERSION_MIN_HOLD and DIVERSION_OFF_TEMP parameters, and to characterize reservoir thermal capacity.

---

## Future Considerations

- **Shop temperature target**: if air_cool reaches a user-defined setpoint, turn fans off to maintain temperature rather than overheat the shop.
- **Reservoir temperature tracking**: when diversion is active, monitor reservoir temp to detect when the reservoir is "spent" (approaching mix temp, no longer absorbing useful heat).
- **Radiator health monitoring**: if delta_radiator / (mix − air_cool) is persistently below 50% at normal flow, alert for possible air in radiator.
- **Proportional fan control** (future, optional): would require a 20A+ DC-DC buck converter. Data shows this is a comfort feature, not a safety or efficiency feature.

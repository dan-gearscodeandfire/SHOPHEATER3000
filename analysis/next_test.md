# Upcoming Tests

---

## Test A: Fan Speed Validation — 5V DC vs 12V DC (DO THIS FIRST)

**Purpose:** Determine whether fan speed actually affects water-side delta_radiator. Prior Session 1 data (70% vs 100% PWM) is unreliable because PWM feeding an internal BLDC driver produces unpredictable results, and the radiator was only half-filled. This test uses clean DC at known voltages on the properly purged full radiator.

### Protocol

1. Wire fans to **5V DC** (clean, not PWM)
2. Build a fire, main loop only, let the system reach **~120–130°F** and stabilize
3. Record at steady state for **3–5 minutes**
4. Compare delta_radiator and effectiveness to Session 3 baseline (12V DC, same radiator, similar flow and temps)

### What this tells us

- If delta_radiator is **the same** at 5V and 12V: fan speed truly doesn't matter for water cooling, and on/off relay control at 12V is the correct automation design.
- If delta_radiator is **lower** at 5V: there IS a fan speed threshold that affects the water side. The automation may need two speeds (5V quiet / 12V full) or at minimum must ensure fans are at 12V during high-heat conditions.

### What to compare against

Session 3 at ~2.75 GPM, 12V DC, mix ~120°F: effectiveness was **70–74%**, delta_radiator ~52°F at gradient ~73°F.

---

## Test B: Controlled Diversion Cycle

**Purpose:** Characterize the diversion system's response time, reservoir thermal capacity, and recovery dynamics — the three unknowns needed to set the automation safety parameters.

---

## Test B Protocol

1. Build a moderate fire, **main loop only**, fans at 12V, let the system reach **~130–140°F** and **stabilize** (delta_heater roughly constant for 2+ minutes)
2. Record the steady baseline for **2–3 minutes** (don't touch anything)
3. **Activate diversion.** Leave it on for **5 minutes.** Don't change anything else.
4. **Deactivate diversion.** Observe recovery for **5 minutes.**
5. If the fire is still going and temps are safe, let it climb back up and **repeat once more.**

## What to observe

- **Response time:** How many seconds after diversion activates before hot_water starts dropping?
- **Reservoir capacity:** How much does reservoir temp rise? At what point does it stop absorbing useful heat?
- **Recovery dynamics:** After deactivation, how fast do temperatures climb back?
- **Steady-state with diversion:** Does the system find a new equilibrium, or does it keep cooling?

## What this informs (automation parameters)

| Parameter | What this test determines |
|-----------|-------------------------|
| DIVERSION_ON_TEMP | Whether 180°F trigger gives enough time for diversion to act |
| DIVERSION_OFF_TEMP | How far temps drop during a 5-min hold → sets deactivation threshold |
| DIVERSION_MIN_HOLD | How long diversion needs to stay on to be effective |
| Reservoir "spent" detection | Whether reservoir temp can be used to decide if diversion is still useful |

---

## Test C: Fan Off -> On -> Off Step Test (repeatable timing)

**Purpose:** Quantify fan-state impact with clean step changes and fixed timing, separating true fan effects from thermal lag and combustion drift.

### Protocol

1. Main loop only, no diversion, flow valve fixed.
2. Bring system to **~130-140F mix** and hold for **2 minutes**.
3. **Fans OFF for 3 minutes** (long enough to see full no-airflow trend).
4. **Fans ON (12V) for 3 minutes**.
5. **Fans OFF again for 3 minutes**.
6. Keep fire management as constant as possible throughout.

### What to log/compare

- Segment averages for each 3-minute block:
  - `delta_water_radiator`
  - `delta_water_heater`
  - `delta_air`
  - `eps_rad = delta_water_radiator / (water_mix - air_cool)`
  - `flow_rate`
- Transition response time:
  - Seconds from fan toggle to first clear trend change in `delta_air`
  - Seconds from fan toggle to first clear trend change in `water_cold`

### Success criteria

- **OFF blocks** should reproduce low extraction behavior (small `delta_air`, reduced `delta_water_radiator`, hotter return water).
- **ON block** should rapidly reverse those trends and recover `eps_rad`.
- If the second OFF block matches the first OFF block at similar temperatures, fan-state causality is confirmed.

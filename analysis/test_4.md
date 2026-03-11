# Session 5 Incident Analysis — 2026-03-01

**Source:** `data_logs/session_2026-03-01_17-55-04.csv`  
**Incident type:** Overheat with steam venting and manual water refill  
**Operator note:** Steam discharged from heater safety steam port; reservoir/loop water was depleted and cold water was manually added.

---

## 1. Clear Timeline of Events

All values below are direct checkpoints from the log.

| Time | State/Action | Hot (F) | Mix (F) | Cold (F) | dHeater (F) | dRad (F) | dAir (F) | Flow (GPM) | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 17:55:12-17:59:22 | Idle baseline, main loop | ~46 | ~47 | ~47 | ~-1 to 0 | ~0.1 | ~1.0 | ~2.25-2.30 | System stable, no heat input yet |
| 17:59:30 | Burn starts ramping | 56.4 | 53.6 | 47.1 | 9.3 | 6.5 | 0.9 | 2.57 | Initial heat arrival |
| 18:00:40 | Fast heat-up | 124.5 | 122.0 | 64.1 | 60.4 | 57.9 | 1.0 | 2.84 | Strong heater and radiator deltas |
| 18:01:50 | Mid-ramp | 140.8 | 140.9 | 114.2 | 26.6 | 26.7 | 0.1 | 2.94 | Return water rising quickly |
| 18:03:40 | High temp, still circulating | 191.0 | 192.2 | 154.5 | 36.5 | 37.7 | -2.5 | 2.45 | Near-critical bulk temps |
| 18:03:55 | **Flow collapse begins** | 197.7 | 198.5 | 158.7 | 39.0 | 39.8 | 10.6 | 0.28 | First near-zero-flow reading |
| 18:04:03 | **Zero-flow reached** | 199.3 | 199.4 | 158.4 | 40.9 | 41.0 | 14.2 | 0.00 | Circulation effectively lost |
| 18:04:42 | Overheat progression | 202.3 | 192.2 | 152.8 | 49.5 | 39.4 | 12.8 | 0.43 | Still mostly no flow |
| 18:05:45 | Severe condition | 204.6 | 207.5 | 140.9 | 63.7 | 66.6 | 9.4 | 0.00 | Thermal stress increasing |
| 18:06:00 | Severe condition | 205.4 | 208.4 | 135.2 | 70.2 | 73.2 | 7.4 | 0.00 | Mix peak appears |
| 18:06:16 | **Peak hot / peak heater delta** | **205.9** | 208.4 | 129.5 | **76.4** | 78.9 | 6.8 | 0.00 | Worst logged point |
| 18:06:24 | **Diversion enabled** (`div=True`) | 197.0 | 182.3 | 128.6 | 68.4 | 53.7 | 6.0 | 0.00 | Cooling intervention starts |
| 18:06:57 | Rapid crash while diverted | 115.6 | 86.0 | 119.0 | -3.4 | -33.0 | 4.8 | 0.00 | Sensor order reverses under mixing |
| 18:08:24 | Recovery transient | 77.8 | 69.8 | 99.8 | -22.0 | -30.0 | 3.4 | 3.37 | Flow resumes briefly/spikes |
| 18:11:48 | Post-refill recovery visible | 116.7 | 59.0 | 51.0 | 65.7 | 8.0 | 1.6 | 2.66 | Fresh cool water likely entering loop |
| 18:12:43 | Stabilizing diverted cooling | 102.0 | 77.9 | 49.7 | 52.3 | 28.2 | 5.8 | 2.71 | Reservoir warming and active exchange |
| 18:14:18 | Back to main loop (`div=False`) | 91.5 | 84.2 | 54.3 | 37.2 | 29.9 | 7.9 | 2.75 | Recovery to controlled operation |

---

## 2. Key Quantitative Findings

1. **Long low-flow window at the worst time**
   - `flow < 0.5 GPM` for 48 samples (first at `18:03:55`, last at `18:11:17`)
   - `flow == 0.0 GPM` for 41 samples (first at `18:04:03`, last at `18:11:09`)

2. **Bulk water exceeded 200F during no-flow condition**
   - `hot >= 200F` from `18:04:42` to `18:06:16`
   - Peak `hot`: **205.9F**
   - Peak `mix`: **208.4F**

3. **Heater/radiator deltas became extreme**
   - `delta_water_heater` peaked at **76.4F**
   - `delta_water_radiator` peaked at **78.9F**
   - These values are consistent with a badly destabilized loop, not normal circulating equilibrium.

4. **Diversion reduced temperature quickly once engaged**
   - Diversion first true at `18:06:24`
   - Hot water dropped sharply over the next ~30-60 seconds.

---

## 3. Interpretation of the Steam Event

Your explanation is consistent with the telemetry:

- The dominant failure mode appears to be **loss of liquid circulation due to boiling/steam formation in the heater coil**.
- In two-phase (steam + liquid) conditions, a paddle/turbine flow meter can report near-zero despite ongoing pump effort.
- Bulk sensor readings near ~200F can coexist with **local boiling at hotter coil surfaces**, causing steam vent discharge.
- Manual water addition aligns with the later recovery pattern (cold-side temperatures and reservoir behavior shift markedly after the event).

---

## 4. Practical Lessons from This Run

1. **Flow is the primary safety sentinel** for this failure mode.
2. **Overheat can become critical before extremely high bulk temperatures are reached** if circulation collapses.
3. **Diversion helped**, but it was activated after prolonged low/zero-flow; earlier action is likely required in similar burns.
4. **Steam venting did its job** as a safety relief, and manual refill was necessary to restore stable operation.

---

## 5. Suggested Immediate Post-Incident Checks (Before Next Burn)

- Verify loop water volume at start and confirm no hidden leaks.
- Inspect heater coil and near-heater plumbing for heat damage.
- Inspect pump and strainer/trap for blockage after steam exposure.
- Validate that flow sensor behavior is understood in two-phase conditions.
- Confirm diversion path and steam outlet are unobstructed.

---

## 6. Recommended Safety Trigger Thresholds (Post-Incident)

These are conservative interim thresholds based on this run, where flow collapse preceded sustained 200F+ bulk temperatures.

### Primary triggers (flow-first logic)

1. **Critical flow-collapse trigger**
   - Condition: `flow_rate < 0.5 GPM` for >=10 seconds while `water_hot >= 170F`
   - Action: Force **diversion ON**, force **fans ON**, raise critical alert.

2. **Hard zero-flow trigger**
   - Condition: `flow_rate <= 0.1 GPM` for >=5 seconds while `water_hot >= 160F`
   - Action: Immediate critical state (same as above), inhibit return to normal until flow recovers.

### Temperature backup triggers (if flow sensor is unreliable)

3. **Predictive overheat trigger**
   - Condition: `water_hot + delta_water_heater >= 190F`
   - Action: Diversion ON + fans ON.

4. **Absolute hot-water trigger**
   - Condition: `water_hot >= 185F`
   - Action: Diversion ON + fans ON, independent of control mode.

5. **Emergency trigger**
   - Condition: `water_hot >= 195F` OR `water_mix >= 200F`
   - Action: Emergency cooldown posture; do not wait for additional confirmation.

### Recovery/unlatch guidance

6. **Minimum hold**
   - Keep diversion active for at least **120 seconds** once a critical trigger fires.

7. **Safe release conditions (all must be true)**
   - `water_hot < 165F`
   - `flow_rate > 1.5 GPM` stable for >=30 seconds
   - `delta_water_heater` trending down, not up

8. **Relatch rule**
   - If any critical trigger reappears during cooldown, immediately relatch to critical state.

### Why these values

- In this incident, first near-zero flow occurred around **197-199F** and then progressed into sustained no-flow with steam venting.
- Flow-based triggers therefore need to fire **well before** the 200F region.
- Temperature-only thresholds are still required as backup, but flow collapse should be treated as the earliest high-confidence warning for boil-off risk.

---

## 7. Operator Design Thoughts and Assessment

### Proposed thought 1

**Statement:** Fans should be on 12V long before `water_hot` nears 190F.

**Assessment:** Agree. This incident supports early fan engagement as a default safety posture.

- Practical recommendation: force fans to 12V by the time `water_hot` reaches **150-160F**, not near 190F.
- Also add a predictive condition: if `water_hot` is below 150F but `delta_water_heater` is climbing rapidly, preemptively switch fans to 12V.

### Proposed thought 2

**Statement:** There should be a mechanism for measuring rate of change in `delta_water_heater` to identify when fire is building.

**Assessment:** Strongly agree. Rate-of-change is one of the earliest indicators of combustion acceleration.

- Compute a smoothed slope:
  - `roc_dh = d/dt(delta_water_heater)` over a rolling 30-60 second window.
- Require persistence (for example, 2-3 consecutive windows) to avoid single-sample noise triggers.
- Track both magnitude and acceleration:
  - `roc_dh` (first derivative)
  - optional `d/dt(roc_dh)` (second derivative) for fast runaways.

### Proposed thought 3

**Statement:** Fans should be invoked when `f(rate_of_change(delta_water_heater), water_cold)` approaches a cut-off value.

**Assessment:** Agree with a minor refinement: use this as an **early fan trigger**, but keep hard flow/temperature cutoffs as primary safety interlocks.

- Suggested early-warning index:
  - `risk_index = a * roc_dh + b * (water_cold - cold_baseline)`
- Trigger fan-to-12V when `risk_index` crosses threshold for >=20-30 seconds.
- Keep non-negotiable hard triggers independent of this function:
  - low-flow/zero-flow triggers
  - absolute hot/mix emergency limits

### Integration guidance

Use a layered control strategy:

1. **Layer 1 (anticipatory):** `risk_index` turns fans on early.
2. **Layer 2 (protective):** flow + predictive temperature rules activate diversion.
3. **Layer 3 (emergency):** hard limits latch cooldown regardless of model output.

This gives early comfort/safety response without relying on one derived metric during chaotic two-phase events.

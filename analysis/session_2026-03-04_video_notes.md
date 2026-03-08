# Session Video Notes — 2026-03-04

Source file: `data_logs/session_2026-03-04_17-26-12.csv`

## Quick summary

- Duration: ~133.6 minutes (948 samples)
- Control mode: Automatic for 98.8% of run
- Peak temperatures:
  - `water_hot`: **172.5F**
  - `water_mix`: **174.2F**
  - `water_cold`: **96.7F**
- Flow stability: **2.24-2.78 GPM** (avg ~2.50 GPM)
- No critical safety events:
  - No `water_hot >= 183F`
  - No `water_hot >= 193F`
  - No low-flow/high-temp collapse signature

---

## Video talking points (short version)

1. This was a strong fire with clean circulation and no flow collapse.
2. Automatic mode escalated fan output early (to 12V) before critical bulk temperatures.
3. Peak water temperature remained controlled at 172.5F.
4. Heat rejection rose to nearly 100k BTU/hr in the hottest window.
5. System stepped down smoothly into a long stable cooldown.

---

## Timeline (for on-screen callouts)

- **17:26:23** — Session start (`water_hot` ~106.6F, diversion initially open from startup)
- **17:26:50** — Diversion closes; system settles into main-loop operation
- **17:41:22** — Fan transitions **5V -> 12V**
  - `water_hot` ~124.7F
  - `delta_heater` ~47.3F
  - This is anticipatory control, not emergency response
- **17:45:52** — `water_hot` first crosses 170F
- **17:46:43** — Peak `water_hot` **172.5F**
- **17:58:15** — Fan transitions **12V -> 5V** as heat output declines
- **19:03:40** — Fan enters OFF/5V probe cycling regime around ~100F hot water
- **19:39:57** — Session end, stable moderate conditions

---

## Thermodynamic interpretation

### 1) Heat input vs heat rejection stayed balanced at high fire

During early high-fire:

- Avg `delta_heater`: **57.5F**
- Avg `delta_radiator`: **58.0F**

These are nearly equal, which indicates the loop was rejecting heat at almost the same rate the heater was adding it. That explains why the run stayed controlled despite high burn intensity.

### 2) Absolute heat transfer increased strongly with temperature

Using `BTU/hr ~= 500 * flow_rate * delta_water_radiator`:

- Mix 100-120F: ~**39k BTU/hr**
- Mix 120-140F: ~**66k BTU/hr**
- Mix 140-175F: ~**99k BTU/hr**

As water-air temperature difference increased, heat transfer rose sharply, as expected from convection-driven heat exchange.

### 3) Radiator effectiveness was strong in this run

Water-side effectiveness proxy:

- `eps_rad = delta_radiator / (water_mix - air_cool)`

Observed:

- Mix 100-120F: `eps_rad` ~**0.58**
- Mix 120-140F: `eps_rad` ~**0.70**
- Mix 140-175F: `eps_rad` ~**0.71**

This suggests strong exchanger performance and airflow support during high-load windows.

### 4) Air-side metric nuance

`delta_air` rose with heat load (good), but normalized air-side effectiveness (`eps_air`) decreased slightly at highest temperatures. This is consistent with absolute heat transfer rising while available thermal gradient grows even faster.

---

## Automatic control behavior notes

- Fan distribution over whole run:
  - OFF: 25.2%
  - 5V: 61.9%
  - 12V: 12.9%
- High-risk proxy (`water_hot + delta_heater >= 190`) occurred 87 samples.
- In those samples, fan was always **12V** in automatic mode.
- No diversion relatch was needed beyond startup normalization.

Interpretation: predictive/anticipatory logic did most of the work, avoiding escalation to hard emergency thresholds.

---

## Suggested narration lines

### Main takeaway (15-20s)

"This burn got aggressive, but the loop stayed stable. Automatic mode ramped airflow to 12V early, held peak hot water at 172.5F, and avoided any low-flow steam-collapse behavior."

### Thermodynamics explainer (20-30s)

"At high fire, the heater delta and radiator delta were almost identical, which means heat added and heat rejected were closely matched. That balance is why temperature rise stayed controlled even while total transfer approached about 100,000 BTU per hour."

### Control strategy explainer (15-20s)

"The system didn’t wait for absolute overheat. It used predictive signals like heater delta and trend rate to escalate fan speed before hard limits were reached."

---

## On-screen annotation suggestions

- At 17:41:22: "Auto: 5V -> 12V (predictive trigger)"
- At 17:46:43: "Peak hot water: 172.5F (below diversion threshold)"
- During high-fire window: "Heat rejection ~99k BTU/hr (avg)"
- During cooldown: "Step-down to 5V with stable flow"


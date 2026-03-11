# Session 4 Analysis — 2026-02-28

**Sources:**
- `data_logs/session_2026-02-28_17-56-26.csv`
- `data_logs/session_2026-02-28_18-18-07.csv`
- `data_logs/session_2026-02-28_18-29-47.csv`

**Context from today:**
- First session used both radiator fans on a higher-current supply.
- Flow was roughly constant and mostly in the 2.8-3.0 GPM range (small drift with temperature/viscosity).
- Reservoir diversion/mix mode was not used for the analysis windows (main loop only).

---

## 1. Definitions Used

- Water-side radiator effectiveness:
  - `eps_rad = delta_water_radiator / (water_mix - air_cool)`
- Air-side normalized effectiveness:
  - `eps_air = delta_air / (water_mix - air_cool)`
- Heat rejected to radiator:
  - `BTU/hr ~= 500 * flow_rate * delta_water_radiator`

Notes:
- Startup transients with tiny gradients and sensor lag were excluded when needed.
- Main-loop samples (`diversion_state=False`, `flow_mode=main`) were used for comparisons.

---

## 2. Session A — `17-56-26` (fan-on baseline, broad temp range)

Main observations:
- Flow was stable around **2.88 GPM avg**.
- Overall water-side radiator effectiveness was **~0.61**.
- In hotter operation (`mix 120-150F`), effectiveness was **~0.58**.
- Air-side normalized effectiveness was **~0.32** overall.
- Average radiator heat rejection in analyzed window was **~60.8k BTU/hr** (higher in hotter periods).

Interpretation:
- Radiator performance is much better than the old ~0.30 era and lands in the same general band as recent fully functional runs.
- Efficiency decreases somewhat at higher heat load (expected), but remains strong.

---

## 3. Session B — `18-18-07` (repeatability check, 100-110F hold)

This run stayed in a tight operating band:
- `mix`: **101.3-109.4F**
- flow: **2.79-2.93 GPM**
- `air_cool`: **56.3-58.1F**

Results:
- `eps_rad`: **0.614 avg** (range about 0.592-0.667)
- `eps_air`: **0.306 avg**
- Heat rejection: **~43.1k BTU/hr**

Consistency with Session A:
- Session A restricted to `mix 100-110F` gave:
  - `eps_rad ~0.625`, flow `~2.82 GPM`, BTU `~43.2k BTU/hr`
- Session B matches this very closely.

Interpretation:
- Strong repeatability at moderate temperatures and similar flow.
- No evidence of large drift in radiator behavior between these two runs.

---

## 4. Session C — `18-29-47` (fans off -> on; possible off again)

This file shows a clear transition signature despite `fan_speed=0` in the log.

### Phase 1: fans effectively off (start to ~18:35:36)
- `delta_air` decayed from ~8.4F to ~1.7F while water temperature rose.
- `delta_water_radiator` sat around ~9-11F.
- `eps_rad` averaged **~0.13**.
- `delta_water_heater` stayed low (~8-11F).

### Transition: around ~18:35:44
- Very abrupt rise in air-side and water-side extraction:
  - `delta_air`: ~4.2 -> 8.0 -> 11.1 -> 13.7 -> 17+ F
  - `delta_water_radiator`: ~9 -> 10 -> 13 -> 20 -> 26 -> 32+ F
  - `water_cold` dropped rapidly, indicating strong renewed radiator cooling.

### Phase 2: fan-on cooling period
- Full post-switch period average:
  - `eps_rad ~0.49`, `eps_air ~0.31`, flow ~2.81 GPM
- Later stabilized sub-window (`18:37:00-18:44:19`):
  - `eps_rad ~0.52`, flow ~2.79 GPM

### "Off again" at end?
- No clear second off event is visible.
- Late data still resembles active fan cooling rather than no-airflow behavior.

Interpretation:
- In this run, fan state had a major practical impact on both air-side and water-side extraction.
- With fans off long enough, return water rises and heater delta collapses.

---

## 5. Why Heater Delta Dropped with Fans Off

Heater delta is:
- `delta_water_heater = water_hot - water_cold`

When fans were off, radiator rejection dropped, so return water (`water_cold`) became much hotter.
That directly reduced per-pass heater lift, so `delta_water_heater` fell.

In short:
- less radiator cooling -> hotter return water -> smaller heater gradient -> lower heater delta.

---

## 6. What We Learned Today

1. At ~2.8-2.9 GPM and normal fan-on operation, radiator effectiveness is repeatable around **0.61** in the 100-110F range.
2. At higher temperatures/loads, water-side effectiveness remains good but trends lower (~0.58 in 120-150F range).
3. Extended fan-off operation can drastically reduce heat extraction (down to ~0.13 in this test window).
4. Turning fans back on produces a rapid recovery in both air delta and water-side radiator delta.
5. Heater delta behavior tracks return-water temperature exactly as expected from loop thermodynamics.

---

## Addendum: 5V vs 12V Fan Observation

Using matched temperature bands from available logs, 12V fan operation appears to transfer more heat than 5V:

- Around `mix 100-110F`:
  - 5V sessions: ~43k BTU/hr, `eps_rad ~0.61-0.63`
  - 12V session: ~59k BTU/hr, `eps_rad ~0.72`
- Around `mix 120-140F`:
  - 5V session: ~63k BTU/hr, `eps_rad ~0.58`
  - 12V session: ~89k BTU/hr, `eps_rad ~0.66`

Interpretation:
- The trend is consistent with higher airflow (12V) increasing both water-side extraction and total shop heat transfer.
- This is still not a perfectly controlled A/B (ambient, fire profile, and some flow differences), so the magnitude should be treated as provisional until a dedicated fixed-condition 5V-vs-12V test is run.

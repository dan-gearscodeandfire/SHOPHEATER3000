# Radiator Heat Dissipation Analysis — test_0

**Source file**: `data_logs/session_2026-02-17_19-33-00.csv`
**Run date/time**: February 17, 2026, 19:33:00 – 20:38:54 (~65 minutes)
**Analysis date**: February 15, 2026

---

## Session Overview

- **Duration**: 65 minutes, 498 data points (~8 sec intervals)
- **Fan speeds used**: 70%, 83%, 85%, 100%
- **Flow modes**: main, mix, diversion
- **Ambient air (air_cool)**: rose from 41.0 to 48.2°F over the session
- **Water mix temp range**: 41.0 to 194.0°F
- **Flow rate**: 2.45 GPM (cold) to 3.41 GPM (hot) — viscosity effect

---

## 1. Radiator Heat Dissipation vs. Mix Temperature

`delta_water_radiator` (= water_mix - water_cold) is the primary measure of heat extracted by the radiator. It scales strongly with mix temperature, as expected from a larger temperature differential driving heat transfer:

| Mix Temp (°F) | Approx delta_radiator | Approx delta_air | Conditions |
|---|---|---|---|
| ~75 | 8–9°F | 5–6°F | 70% fan, cooling phase |
| ~100 | 15–16°F | 7–10°F | either fan speed |
| ~120 | 20–25°F | 11–15°F | either fan speed |
| ~135 | 25–28°F | 14–17°F | 70% fan, heating phase |
| ~150 | 28–30°F | 17–19°F | 70% fan |
| ~175+ | 39–43°F | 18–21°F | 100% fan, peak heat |

The relationship is roughly **linear**: for every ~10°F increase in mix temp above ~60°F, delta_radiator increases by approximately 5–6°F. This makes sense — the radiator heat transfer is driven by the temperature difference between water and air.

---

## 2. Fan Speed Effect — Not As Big As Expected

This is the most interesting finding. Comparing similar mix temperatures at different fan speeds reveals that **going from 70% to 100% fan does NOT yield a proportional increase in heat dissipation**:

**Example at mix ~118°F, air_cool ~44–45°F:**
- **70% fan** (row ~243, heating phase): delta_radiator = 25.1°F, delta_air = 11.1°F, flow = 3.27 GPM
- **100% fan** (row ~131, cooling phase): delta_radiator = 18.6°F, delta_air = 13.0°F, flow = 3.27 GPM

**Example at mix ~133°F, air_cool ~44–47°F:**
- **70% fan** (row ~255): delta_radiator = 27.8°F, delta_air = 14.5°F, flow = 3.30 GPM
- **100% fan** (row ~118): delta_radiator = 24.3°F, delta_air = 12.3°F, flow = 3.31 GPM

Key takeaway: **increasing fan speed from 70% to 100% produces noticeably lower air delta** (the air passes through too fast to absorb as much heat per unit volume), and the water-side delta is only marginally different. The total heat transfer rate (airflow × delta_air) increases modestly, maybe 10–20%, but far less than the 43% increase in fan power.

Put differently: **70% fan speed appears to be near the sweet spot for this radiator** — the air dwells long enough to extract heat efficiently, while still providing good total airflow. Running at 100% burns more energy for diminishing returns.

---

## 3. Cold Air Temperature Effect

Air_cool crept from 41°F (start) to 48°F (end) as the shop warmed up. This reduces the driving temperature differential on the air side:

- At air_cool 42°F, mix 133°F: delta_air = ~6.5°F (row ~102, transient)
- At air_cool 44.6°F, mix 133°F: delta_air = ~14.5°F (row ~255, steady)
- At air_cool 48.2°F, mix 140°F: delta_air = ~35°F (row ~458, mix mode)

The air_cool effect is confounded by different flow modes and system states, but the general trend is clear: **as the shop warms up, the radiator becomes less effective at heating the air further** because the temperature differential shrinks. This is the expected diminishing-returns behavior of any heating system.

---

## 4. Flow Mode Has a Massive Effect

The data captures several flow mode transitions:

- **Main only** (rows 2–365): Hot water goes directly through the radiator. Mix temps track the heater output closely. Delta_radiator can reach 30–43°F at high temps.
- **Diversion mode** (rows 370–415): The cold tank/reservoir is added to the loop (the radiator remains in the loop). Mix temp **crashes from 194°F to 82°F in ~2 minutes** (rows 365–376) as the cold reservoir water enters circulation, then slowly recovers as the reservoir warms up. Delta_radiator goes deeply negative during the transition.
- **Mix mode** (rows 416–481): Both paths open. Temps stabilize at moderate levels with delta_radiator ~24–25°F and notably high delta_air values (34–36°F) because the radiator is warm from both supply paths.

---

## 5. Other Notable Observations

- **Flow rate correlates with temperature**: 2.45 GPM at 41°F up to 3.41 GPM at 100°F+ (lower viscosity at higher water temp = faster flow). This is a passive amplifier — hotter water flows faster AND has a bigger temperature differential, so heat delivery to the radiator scales super-linearly with source temperature.

- **Thermal lag**: After a fan speed change, it takes 2–3 minutes for delta_air to stabilize. For example, after switching from 70 to 100% at row 101, delta_air actually *dropped* initially before settling.

- **Missing readings**: Row 27 and row 361 have missing `air_heated` values — likely a sensor read timeout. Rare but worth noting if you build alerting.

---

---

## 6. Delta Heater — Measurement Error & Corrected Values

### The Problem: water_mix > water_hot

In main flow mode, `water_mix` reads **higher** than `water_hot` in roughly 85–90% of all readings. This is physically impossible (mix is downstream of hot), so any row where mix > hot has an invalid raw `delta_water_heater`. The hot sensor lags behind mix, likely due to sensor placement or thermal mass.

The error magnitude varies dramatically with system state:

| Condition | Typical (mix − hot) error | Example rows |
|---|---|---|
| Cold start / steady low temp | 0.3–1.6°F | 8–64 |
| First heating ramp (cold start) | **5–44°F** | 65–100 |
| First cooling phase | 1–33°F (slowly closing) | 101–190 |
| Second heating ramp (warm start) | 0.2–5°F | 221–365 |
| Quasi-steady state (warm) | 0.1–1.0°F | 232–260 |
| Diversion mode | **Valid** (hot >> mix) | 370–415 |

The worst case is row 90: hot = 57.0°F, mix = 94.1°F — a 37°F gap. The hot sensor simply cannot keep up during rapid heating from a cold start.

### Correction rule

When mix > hot, the corrected delta_heater = **mix − cold** (= delta_radiator). This gives the best available estimate of heater output at the radiator, though it sacrifices visibility into pipe losses between the heater and the radiator inlet.

### First heating cycle — corrected values (70% fan, main mode)

| Row | Hot | Mix | Cold | Raw Δ heater | **Corrected Δ heater** | Δ radiator |
|-----|-----|-----|------|-------------|----------------------|------------|
| 75 | 44.2 | 50.9 | 45.7 | −1.5 | **5.2** | 5.2 |
| 80 | 45.3 | 56.3 | 47.0 | −1.7 | **9.3** | 9.3 |
| 85 | 49.1 | 75.2 | 51.2 | −2.1 | **24.0** | 24.0 |
| 90 | 57.0 | 94.1 | 63.0 | −6.0 | **31.1** | 31.1 |
| 93 | 63.6 | 106.7 | 72.3 | −8.7 | **34.4** | 34.4 |
| 95 | 68.1 | 112.1 | 78.8 | −10.7 | **33.3** | 33.3 |
| 100 | 79.7 | 123.8 | 93.4 | −13.7 | **30.4** | 30.4 |

Note: corrected Δ heater = Δ radiator by definition in these rows. The raw values are completely unusable — they are negative, implying the heater is *cooling* the water.

### Second heating cycle — corrected values (70% fan, main mode, high temps)

| Row | Hot | Mix | Cold | Raw Δ heater | **Corrected Δ heater** | Δ radiator |
|-----|-----|-----|------|-------------|----------------------|------------|
| 348 | 153.5 | 154.4 | 119.7 | 33.8 | **34.7** | 34.7 |
| 353 | 168.0 | 169.7 | 129.9 | 38.1 | **39.8** | 39.8 |
| 358 | 178.4 | 180.5 | 138.4 | 40.0 | **42.1** | 42.1 |
| 362 | 185.0 | 188.6 | 145.2 | 39.8 | **43.4** | 43.4 |
| 365 | 187.9 | 193.1 | 150.1 | 37.8 | **43.0** | 43.0 |

The raw values are closer here (the error is only 1–5°F during the second ramp since the system was already warm), but still understated. Corrected peak delta_heater reaches **~43°F at mix ~190°F**.

---

## 7. Valid Delta Heater Readings (hot ≥ mix)

The best cluster of valid readings (where hot ≥ mix, no correction needed) occurs during the second heating cycle at moderate ramp rates (rows 232–253). These are the "gold standard" rows:

| Row | Hot | Mix | Cold | Δ heater | Δ radiator | **Δ heater − Δ radiator** |
|-----|-----|-----|------|----------|------------|--------------------------|
| 232 | 103.4 | 103.1 | 78.6 | 24.8 | 24.5 | 0.3 |
| 241 | 114.9 | 114.8 | 90.5 | 24.4 | 24.3 | 0.1 |
| 243 | 117.8 | 117.5 | 92.4 | 25.4 | 25.1 | 0.3 |
| 244 | 119.4 | 119.3 | 93.5 | 25.9 | 25.8 | 0.1 |
| 246 | 122.1 | 122.0 | 95.8 | 26.3 | 26.2 | 0.1 |
| 248 | 124.3 | 123.8 | 98.0 | 26.3 | 25.8 | 0.5 |
| 250 | 127.0 | 126.5 | 100.2 | 26.8 | 26.3 | 0.5 |
| 253 | 130.4 | 130.1 | 103.0 | 27.4 | 27.1 | 0.3 |

Key insight: **delta_heater exceeds delta_radiator by only 0.1–0.5°F**. This means the piping between the hot sensor and the radiator inlet loses almost no heat — the system is very well insulated or the pipe run is short.

At steady state, the energy balance holds: virtually all heat the heater adds is removed by the radiator.

---

## 8. Delta Heater in Diversion Mode

Diversion mode produces the most reliable raw delta_heater readings because cold reservoir water enters the loop, driving mix far below hot. These readings reveal heater behavior under load:

| Row | Hot | Mix | Cold | Reservoir | Δ heater | Δ radiator | Notes |
|-----|-----|-----|------|-----------|----------|------------|-------|
| 370 | 191.9 | 167.0 | 146.5 | 41.0 | 45.4 | 20.5 | Just switched |
| 373 | 191.6 | 82.4 | 131.1 | 54.5 | 60.5 | −48.7 | Cold slug at radiator |
| 375 | 186.7 | 83.3 | 100.1 | 67.1 | 86.6 | −16.8 | Cold slug at cold sensor |
| 376 | 184.3 | 86.0 | 90.3 | 73.4 | 94.0 | −4.3 | Peak spread |
| 380 | 149.5 | 99.5 | 80.5 | 99.5 | 69.0 | 19.0 | Stabilizing |
| 390 | 134.0 | 113.9 | 91.7 | 115.7 | 42.3 | 22.2 | Approaching balance |
| 400 | 139.1 | 122.0 | 98.0 | 126.5 | 41.1 | 24.0 | Near new steady state |
| 410 | 139.6 | 130.1 | 104.4 | 133.7 | 35.2 | 25.7 | Reservoir warming |
| 415 | 140.2 | 132.8 | 106.7 | 136.4 | 33.5 | 26.1 | Reservoir nearly caught up |

Observations:

- **Delta_heater − delta_radiator = heat absorbed by reservoir.** At row 380, the heater puts in 69.0°F delta but the radiator only extracts 19.0°F — the remaining 50°F delta is warming the cold reservoir water. By row 415, the gap narrows to 7.4°F as the reservoir catches up to loop temperature.
- **Delta_radiator goes deeply negative** (−48.7°F at row 373) when the cold slug from the reservoir hits the radiator. It recovers to positive within ~2 minutes (row 377).
- **The heater cools rapidly** from 192°F to 134°F once the cold reservoir water arrives — a ~58°F drop in the hot sensor over 3 minutes (rows 370–386). This shows the heater's thermal mass is limited; it cannot maintain temperature against the sudden cold load.

---

## 9. Delta Heater vs. Mix Temperature — Overall Pattern

Combining corrected and valid readings across both heating cycles, the relationship between corrected delta_heater and mix temperature is:

| Mix Temp (°F) | Corrected Δ heater | Phase |
|---|---|---|
| ~50 | 5–6°F | Early ramp |
| ~75 | 24–25°F | Mid ramp |
| ~95 | 30–31°F | Fast ramp |
| ~105 | 24–27°F | Steady rise (second cycle) |
| ~120 | 25–26°F | Steady rise |
| ~130 | 27–28°F | Steady rise |
| ~150 | 28–29°F | Approaching equilibrium |
| ~170 | 39–40°F | High-temp ramp |
| ~190 | 43–44°F | Peak output |

The corrected Δ heater plateaus at **~27–28°F during the middle of the second heating cycle** (mix 120–150°F), then climbs steeply above 150°F as the heater's firebox gets hot enough to sustain larger differentials. This suggests the heater has two operating regimes:

1. **Moderate output (~25–28°F delta)** at mix 100–150°F — the fire is building, output is limited.
2. **High output (~35–43°F delta)** at mix 150–190°F — the firebox is at full temperature and the heater transfers heat efficiently.

---

## 10. Rough BTU Estimates

Using Q = flow_rate × 8.34 lb/gal × delta_T × 60 min/hr:

| Condition | Flow (GPM) | Corrected Δ heater | Estimated BTU/hr |
|---|---|---|---|
| Moderate (mix ~130°F) | 3.29 | 27°F | ~44,500 |
| High (mix ~170°F) | 3.23 | 40°F | ~64,700 |
| Peak (mix ~190°F) | 3.22 | 43°F | ~69,300 |
| Diversion transient (row 376) | 2.89 | 94°F | ~136,000* |

*The diversion transient number is not real steady-state output — it reflects stored thermal energy being released against the cold reservoir slug, not sustainable heater capacity.

**Realistic sustained heater output: ~45,000–70,000 BTU/hr** depending on water temperature and fire intensity.

---

## Summary / Recommendations

1. **70% fan speed is surprisingly efficient.** It produces nearly the same water-side heat extraction as 100% and heats the air to a higher outlet temperature. You likely don't need 100% fan except during rapid warm-up.

2. **Mix temp is the dominant variable.** Radiator output is almost entirely governed by how hot the water entering it is. All other factors are secondary.

3. **Rising ambient air temp reduces effectiveness**, but this is the intended behavior — the shop is getting warmer. Once air_cool reaches ~50–55°F, expect delta_air to flatten significantly.

4. **For maximum heat output to the shop**, main flow mode at 70% fan with the highest sustainable water temp gives the best heat-per-watt-of-fan-power.

5. **The hot sensor is unreliable during heating ramps.** Raw delta_heater is negative or severely understated whenever the system is heating up. Use corrected delta_heater (mix − cold) when mix > hot. Practically, **delta_radiator is the most trustworthy measure of system heat transfer** in main mode.

6. **Pipe losses are negligible.** Valid readings (hot ≥ mix) show delta_heater exceeds delta_radiator by only 0.1–0.5°F — almost all heater output reaches the radiator.

7. **The heater has two output regimes**: ~25–28°F delta at moderate temps (mix 100–150°F), ramping to ~35–43°F delta above 150°F. Sustained output is roughly 45,000–70,000 BTU/hr.

8. **In diversion mode, the reservoir absorbs the majority of heater output** initially (up to ~72%), tapering as it warms. The radiator still dissipates heat, but at reduced delta (~20–26°F) compared to main mode at similar hot temps.

---
---

# Part 2: Corrected Dataset Observations

**Corrected file**: `data_logs/session_2026-02-17_19-33-00_corrected.csv`
**Correction applied**: For all rows before 20:00:00 (203 rows), `water_hot` was replaced with `water_mix` and `delta_water_heater` was recalculated as `water_mix − water_cold`. This accounts for the hot sensor being poorly positioned prior to a mid-session physical adjustment at approximately 19:56–20:00.

All observations below are derived from the corrected dataset. Delta air is excluded due to poor probe placement; cold air (air_cool) is treated as reliable.

---

## 11. Delta Heater Now Equals Delta Radiator in Pre-Adjustment Rows

Since the correction sets hot = mix for the first 203 rows, delta_heater and delta_radiator are identical throughout the first heating cycle. This means we are measuring heat transfer at the radiator in both columns. The true heater output was likely somewhat higher (some heat lost in piping), but the radiator measurement is the best available proxy.

Post-adjustment (row 205+), the two columns are independent again and allow genuine comparison.

---

## 12. Corrected Delta Heater vs. Mix Temperature — Full Session

The corrected data reveals a clearer picture of how the system's thermal delta scales across the full temperature range:

| Time | Mix (°F) | Cold (°F) | Δ heater | Δ radiator | Fan | Mode | Notes |
|------|----------|-----------|----------|------------|-----|------|-------|
| 19:41 | 44.6 | 43.0 | 1.6 | 1.6 | 70% | main | Heat just arriving |
| 19:43 | 67.1 | 48.9 | 18.2 | 18.2 | 70% | main | Rapid ramp |
| 19:45 | 106.7 | 72.3 | 34.4 | 34.4 | 70% | main | First cycle peak Δ |
| 19:46 | 123.8 | 93.4 | 30.4 | 30.4 | 70% | main | Δ dropping — cold catching up |
| 19:47 | 134.6 | 104.3 | 30.3 | 30.3 | 100% | main | Fan increased, peak mix |
| 19:50 | 118.4 | 99.8 | 18.6 | 18.6 | 100% | main | System cooling |
| 19:55 | 80.6 | 70.1 | 10.5 | 10.5 | 100% | main | Low temps, fan still at 100% |
| 19:58 | 71.6 | 63.7 | 7.9 | 7.9 | 70% | main | Approaching inter-cycle trough |
| 20:03 | 103.4 | 78.6 | 24.8 | 24.5 | 70% | main | Second ramp, valid hot sensor |
| 20:06 | 130.4 | 103.0 | 27.4 | 27.1 | 70% | main | Steady rise |
| 20:11 | 151.3 | 123.3 | 28.0 | 28.4 | 70% | main | Second cycle equilibrium |
| 20:17 | 134.6 | 112.1 | 21.9 | 22.5 | 70% | main | Fire dying, cooling |
| 20:18 | 148.1 | 115.4 | 32.0 | 32.7 | 70% | main | Fire restoked |
| 20:20 | 180.5 | 138.4 | 40.0 | 42.1 | 100% | main | Peak session output |
| 20:21 | 193.1 | 150.1 | 37.8 | 43.0 | 100% | main | Highest mix temp |

The corrected first-cycle peak delta (34.4°F at row 93) now matches the magnitude of the second cycle's mid-range output, confirming the correction is consistent.

---

## 13. The Heater's Characteristic Output Curve

The corrected data reveals three distinct heater regimes:

**Regime 1 — Building fire (Δ heater 0–20°F)**
Mix temps 41–70°F. The fire is just getting started. Heat is absorbed by the thermal mass of the firebox, water jacket, and piping faster than it reaches the sensors. Delta rises rapidly as the heat front propagates through the loop.

**Regime 2 — Moderate fire (Δ heater 24–28°F)**
Mix temps 100–150°F. The fire is established but at moderate intensity. This is the plateau observed during the second heating cycle (rows 232–295), where delta_heater holds remarkably steady at ~25–28°F for nearly 10 minutes while mix temp rises from 103 to 152°F. The heater is adding a fixed amount of energy per pass; rising mix temp just means both hot and cold are shifting upward together.

**Regime 3 — Full fire (Δ heater 32–43°F)**
Mix temps 150–193°F. The firebox is at full temperature. Delta_heater climbs sharply as the fire can now sustain a larger differential against the hotter water. This is the regime seen in rows 338–365, with deltas reaching 40+°F.

The transition from Regime 2 to 3 appears to occur around **mix = 145–155°F**, and corresponds to the firebox reaching combustion temperatures where radiant heat transfer dominates.

---

## 14. Cold Air Temperature (Air_Cool) — Shop Warming Rate

**Note on air_cool sensor placement**: The intake sensor is near a hole to the outside, so it reads closer to outdoor ambient than true shop temperature. However, outdoor temperatures were *falling* during this test session, so the observed rise in air_cool represents genuine shop warming — and likely *understates* it, since the sensor was fighting a declining outdoor baseline. Delta_air (heated − cool) is a reasonable measure of radiator air-side output.

Air_cool reads in ~0.9°F steps (0.5°C DS18B20 resolution):

| Time | Air_cool (°F) | Cumulative gain | Phase |
|------|--------------|-----------------|-------|
| 19:33 | 41.0 | — | Cold shop |
| 19:35 | 41.9 | +0.9 | System barely heating |
| 19:45 | 42.8 | +1.8 | First ramp completing |
| 19:47 | 43.7 | +2.7 | Fan at 100% |
| 19:49 | 44.6 | +3.6 | Fastest warming phase |
| 20:07 | 45.5 | +4.5 | Second ramp underway |
| 20:11 | 46.4 | +5.4 | |
| 20:13 | 47.3 | +6.3 | |
| 20:21 | 48.2 | +7.2 | Peak ambient |
| 20:38 | 47.3–48.2 | +6.3–7.2 | Oscillating near end |

**Shop warming rate**: 7.2°F over 65 minutes = **0.11°F/min average**. However, the rate was front-loaded:
- First 16 minutes (19:33–19:49): +3.6°F → **0.23°F/min** — radiator dumping heat into cold shop air
- Next 22 minutes (19:49–20:11): +1.8°F → **0.08°F/min** — diminishing returns as shop warms
- Final 27 minutes (20:11–20:38): +1.8°F → **0.07°F/min** — approaching steady state

This diminishing rate is expected: as the shop approaches the radiator's output capacity, the rate of warming asymptotes. At 48°F the shop is still far below the water temps, so the limit here is likely the radiator's air-side capacity, not the heater's water-side output.

---

## 15. Flow Rate vs. Temperature — Viscosity Plateau

Corrected data confirms the flow rate rises with temperature but **plateaus above ~120°F**:

| Mix temp (°F) | Flow rate (GPM) |
|---|---|
| 41 | 2.45 |
| 60 | 2.75 |
| 80 | 3.00 |
| 100 | 3.15 |
| 120 | 3.25 |
| 140 | 3.30 |
| 160+ | 3.20–3.25 |

The flow rate gains ~33% from cold to 120°F (2.45 → 3.25 GPM), then flattens. Above 120°F, viscosity improvements no longer translate to higher flow, suggesting the pump's head curve or pipe friction become the bottleneck.

This plateau means heat delivery at high temps is driven almost entirely by delta_heater, not by increasing flow. Q = flow × Δ, and since flow saturates, Q scales linearly with delta above ~120°F.

---

## 16. Delta Heater vs. Delta Radiator Gap — Post-Adjustment

After the sensor fix (row 205+), the gap (delta_heater − delta_radiator) reveals how the system behaves at different operating points:

| Condition | Typical gap (hot − mix) | Interpretation |
|---|---|---|
| Slow ramp, mix 100–130°F | +0.1 to +0.5°F | Hot slightly leads mix — physically correct, small pipe loss |
| Near equilibrium, mix 130–150°F | −0.4 to +0.3°F | Oscillates around zero — sensors are well matched |
| Fast ramp, mix 150–190°F | −0.7 to −5.2°F | Mix leads hot again — sensor lag at high ramp rates |
| Diversion mode | +20 to +94°F | Hot >> mix — cold reservoir water depresses mix |

Even after adjustment, the mix sensor still outruns hot during fast ramps, though the error is 5–10× smaller than before (max 5°F vs 44°F). For practical purposes, the post-adjustment data at mix < 150°F is fully trustworthy. Above 150°F during fast ramps, delta_radiator is the more reliable number.

---

## 17. Diversion Mode — Reservoir as Thermal Battery

The corrected data shows the reservoir charging cycle cleanly:

| Time | Hot | Reservoir | Mix | Cold | Δ heater | Δ radiator | Reservoir absorbing |
|------|-----|-----------|-----|------|----------|------------|---------------------|
| 20:22:04 | 192.5 | 41.9 | 123.8 | 142.6 | 49.9 | −18.8 | 68.7°F (hot − mix) |
| 20:22:43 | 184.3 | 73.4 | 86.0 | 90.3 | 94.0 | −4.3 | 98.3°F |
| 20:23:15 | 149.5 | 99.5 | 99.5 | 80.5 | 69.0 | 19.0 | 50.0°F |
| 20:24:42 | 134.0 | 116.6 | 114.8 | 92.4 | 41.6 | 22.4 | 19.2°F |
| 20:26:24 | 139.9 | 130.1 | 125.6 | 100.6 | 39.3 | 25.0 | 14.3°F |
| 20:27:51 | 140.2 | 136.4 | 132.8 | 106.7 | 33.5 | 26.1 | 7.4°F |

The reservoir warmed from **41°F to 136°F in ~6 minutes** — a 95°F gain. At an estimated 5 gallons, that's roughly 4,000 BTU stored. By row 415, the reservoir (136.4°F) had nearly caught up to mix (132.8°F), meaning the diversion path was no longer absorbing significant heat and the system could return to equilibrium.

---

## 18. Late-Session Steady State (Rows 440–466, Mix Mode)

The most stable period in the entire session. Both valves open, fire at moderate output, shop reaching thermal equilibrium:

- **Hot**: 138.3–142.6°F (tight 4°F band)
- **Mix**: 139.1–141.8°F
- **Cold**: 114.6–116.5°F
- **Δ heater**: 23.7–26.2°F (avg ~25°F)
- **Δ radiator**: 23.5–25.5°F (avg ~24.5°F)
- **Air_cool**: 47.3–48.2°F
- **Flow**: 2.85–2.96 GPM
- **Fan**: 100%, both valves open

At this steady state, **~25°F of delta at ~2.9 GPM ≈ 36,300 BTU/hr**. This is the system's equilibrium output with a moderate fire and the shop at ~48°F. The radiator is extracting essentially all of the heater's output (gap < 1°F).

---

## 19. Late-Session Cooling & Fire Decay (Rows 467–498)

From row 467 onward, the fire appears to be dying:
- Hot drops from 138.3 to 126.5°F over ~4 minutes
- Delta_heater falls from 23.7 to 17.3°F
- Multiple flow mode switches (mix → diversion → mix → diversion) indicate manual attempts to manage declining heat

By the final reading (row 498): hot = 126.5°F, mix = 131.0°F, cold = 109.2°F. Notably, **mix > hot by 4.5°F** — the hot water leaving the heater is cooler than the water arriving at the radiator. This means the fire is no longer adding heat; the system's thermal mass is the sole heat source, and the piping between hot and mix sensors is actually warming the water slightly (residual pipe heat). The heater has effectively gone out or dropped below useful output.

---

## Updated Summary / Recommendations (Corrected Data)

1. **Delta_radiator is the single most reliable metric** for system heat transfer throughout the session, regardless of hot sensor position.

2. **The heater has three output regimes**: building (0–20°F Δ), moderate (24–28°F Δ at mix 100–150°F), and full fire (32–43°F Δ above 150°F). The transition to full output around 150°F mix appears to be when the firebox reaches peak combustion temperature.

3. **Flow rate plateaus above 120°F mix** at ~3.25 GPM. Above this point, heat delivery is controlled entirely by the temperature delta, not flow.

4. **The shop warmed 7.2°F (41→48°F) in 65 minutes**, with the fastest gains in the first 15 minutes (0.23°F/min) and diminishing returns thereafter (0.07°F/min).

5. **Pipe losses between heater and radiator are negligible** — confirmed at 0.1–0.5°F by post-adjustment valid readings.

6. **The reservoir charges rapidly** (41→136°F in 6 minutes) and acts as a thermal battery. In diversion mode, it absorbs 42–72% of heater output initially, tapering as it approaches loop temperature.

7. **System equilibrium in mix mode** settles at ~25°F Δ, ~2.9 GPM, producing ~36,000 BTU/hr with a moderate fire and 48°F shop ambient.

8. **Fire decay is detectable** when mix exceeds hot — this signals the heater is no longer contributing net heat to the loop.

---
---

# Part 3: Main Mode Only (Diversion Off)

All observations below use the corrected dataset, filtered to rows where `diversion_state = False` (flow_mode = main). This is rows 2–365 plus a brief return at rows 417–421. The reservoir is out of the loop; it's a simple heater → radiator → return circuit.

---

## 20. Main-Mode Timeline & Phases

| Phase | Rows | Time | Fan | Mix range (°F) | Δ heater range | Event |
|-------|------|------|-----|----------------|----------------|-------|
| Cold start | 2–9 | 19:33–19:34 | 100% | 41.0–41.9 | −0.8 to −0.1 | System cold, no heat yet |
| Idle warm | 10–64 | 19:34–19:41 | 70% | 41.9–43.7 | −0.6 to 0.8 | Fire just lit, barely producing |
| Ramp 1 | 65–100 | 19:41–19:46 | 70% | 44.6–123.8 | 1.6 to 34.4 | First heating cycle |
| Cool 1 (fast) | 101–173 | 19:46–19:55 | 100% | 134.6→79.7 | 30.3→10.5 | Fire fading, high fan |
| Cool 1 (slow) | 174–204 | 19:55–20:00 | 70% | 78.8→68.9 | 10.0→8.1 | Sensor adjusted here |
| Ramp 2 | 205–291 | 20:00–20:11 | 70% | 70.7→151.7 | 9.9→28.3 | Second heating cycle |
| Cool 2 | 292–335 | 20:11–20:17 | 70% | 151.7→134.6 | 27.5→19.9 | Fire declining |
| Ramp 3 | 336–365 | 20:17–20:21 | 70→100% | 133.7→193.1 | 21.6→40.0 | Fire restoked, peak output |

---

## 21. Delta Heater Peaks Mid-Ramp, Not at Peak Mix Temp

This is counterintuitive but consistent across both heating cycles. The largest delta occurs when the heat front first arrives and cold return is still cool — not when mix temp is highest:

**First ramp (corrected):**
- Peak Δ heater: **34.4°F** at row 93 (mix = 106.7°F, cold = 72.3°F)
- At peak mix 123.8°F (row 100): Δ heater = 30.4°F — **4°F lower**
- Why: cold return is catching up (93.4°F vs 72.3°F), narrowing the differential

**Second ramp:**
- Δ heater holds at 24–28°F across mix 103–152°F — the plateau masks this effect
- But looking at the transition into Ramp 3 (row 338–348): Δ heater jumps from 23.3 to 33.8°F while cold barely moves (110.9→119.7°F) — this is the heat front arriving again after the fire was restoked

**Practical implication**: If you're monitoring the system for "is the fire catching?" — watch for delta_heater rising above 30°F. That's the signal that significant heat is being delivered.

---

## 22. The 25–28°F Delta Plateau (Main Mode, Moderate Fire)

The most striking feature of the second ramp (rows 232–291) is how stable delta_heater remains while mix climbs 50°F:

| Row | Mix (°F) | Cold (°F) | Δ heater | Δ radiator |
|-----|----------|-----------|----------|------------|
| 232 | 103.1 | 78.6 | 24.8 | 24.5 |
| 243 | 117.5 | 92.4 | 25.4 | 25.1 |
| 253 | 130.1 | 103.0 | 27.4 | 27.1 |
| 260 | 136.4 | 109.5 | 26.9 | 26.9 |
| 270 | 142.7 | 115.1 | 26.9 | 27.6 |
| 280 | 147.2 | 119.0 | 27.5 | 28.2 |
| 291 | 151.7 | 123.3 | 28.0 | 28.4 |

**Delta barely moves (24.8 → 28.0) while mix rises 48.6°F.** Hot and cold are simply shifting upward together, with the heater adding a nearly constant ~26°F per pass. This is the heater at a fixed moderate burn rate — the firebox temperature is stable and the heat transfer into the water jacket is roughly constant regardless of water inlet temperature (within this range).

---

## 23. Full-Fire Breakout Above 150°F Mix

During Ramp 3 (rows 336–365), the fire was restoked and deltas break well above the 25–28°F plateau:

| Row | Mix (°F) | Cold (°F) | Δ heater | Δ radiator | Fan |
|-----|----------|-----------|----------|------------|-----|
| 338 | 134.6 | 110.9 | 23.3 | 23.7 | 70% |
| 344 | 145.4 | 113.8 | 31.7 | 31.6 | 70% |
| 348 | 154.4 | 119.7 | 33.8 | 34.7 | 70% |
| 353 | 169.7 | 129.9 | 38.1 | 39.8 | 100% |
| 358 | 180.5 | 138.4 | 40.0 | 42.1 | 100% |
| 362 | 188.6 | 145.2 | 39.8 | 43.4 | 100% |
| 365 | 193.1 | 150.1 | 37.8 | 43.0 | 100% |

Delta_radiator jumps from 23.7 to **43.4°F** — nearly double the plateau. The fire at full intensity can sustain 40+°F differentials. Note that delta_heater and delta_radiator diverge at the top (37.8 vs 43.0 at row 365), which is the mix-sensor-leads-hot artifact at fast ramp rates; the true heater delta is likely closer to the 43°F radiator number.

---

## 24. Fan Speed Has Minimal Effect on Water-Side Deltas in Main Mode

Three fan speed transitions occurred in main mode:

**70% → 100% at row 101 (mix ~125.6°F):**
- Row 100 (70%): Δ heater = 30.4, Δ radiator = 30.4
- Row 101 (100%): Δ heater = 29.9, Δ radiator = 29.9
- Row 105 (100%): Δ heater = 27.9, Δ radiator = 27.9
- No jump — delta was already declining as the fire faded

**100% → 70% at row 174 (mix ~78.8°F):**
- Row 173 (100%): Δ = 10.5
- Row 174 (70%): Δ = 10.0
- Smooth continuation, no discontinuity

**70% → 83% → 85% → 100% during Ramp 3 (rows 349–353):**
- Row 348 (70%): Δ radiator = 34.7
- Row 349 (83%): Δ radiator = 36.1
- Row 350 (85%): Δ radiator = 37.2
- Row 353 (100%): Δ radiator = 39.8
- Delta is rising, but this is the fire ramping — the fan changes are coincidental to the heating trend

**Conclusion**: In main mode, fan speed changes do not produce measurable step changes in delta_heater or delta_radiator. The water-side heat transfer is governed by fire intensity and water flow, not air-side fan speed. The fan determines how efficiently that heat reaches the shop air, but the water loop doesn't "know" what the fan is doing.

---

## 25. Cold Return Temp & Radiator Extraction Fraction

In main mode, cold = mix − Δ_radiator. The radiator removes a fraction of the heat before returning water to the heater. Looking at what percentage of the mix temperature the radiator extracts (Δ_radiator / mix):

| Mix (°F) | Δ radiator | Cold (°F) | Extraction % |
|-----------|------------|-----------|-------------|
| 50 | 5 | 45 | 10% |
| 75 | 9 | 66 | 12% |
| 100 | 15 | 85 | 15% |
| 120 | 25 | 95 | 21% |
| 135 | 28 | 107 | 21% |
| 150 | 28 | 122 | 19% |
| 170 | 40 | 130 | 24% |
| 190 | 43 | 147 | 23% |

These values blend different fan speeds, air_cool temperatures, and heating/cooling phases. A more controlled analysis (Part 4, Section 28) shows the extraction fraction is **not a fixed constant** — it ranges from 17–22% and is sensitive to air_cool. The table above should be treated as approximate.

---

## 26. BTU Output in Main Mode

Q = flow_rate × 8.34 lb/gal × Δ_radiator × 60 min/hr

| Phase | Flow (GPM) | Δ radiator | BTU/hr | Mix (°F) |
|-------|-----------|------------|--------|----------|
| First ramp peak | 3.31 | 34.4 | ~57,000 | 107 |
| First cycle, peak mix | 3.36 | 30.3 | ~51,000 | 135 |
| Second ramp, plateau | 3.30 | 26.3 | ~43,400 | 127 |
| Second peak | 3.31 | 28.4 | ~47,000 | 152 |
| Third ramp, full fire | 3.23 | 42.1 | ~68,000 | 181 |
| Session peak | 3.22 | 43.4 | ~70,000 | 189 |

The main-mode-only BTU range is **43,000–70,000 BTU/hr**, depending on fire intensity. The moderate-fire plateau delivers ~43–47k; a fully stoked fire pushes to ~68–70k.

---

## 27. Air_cool Progression in Main Mode Only

All shop warming in this session occurred during main mode (diversion and mix modes happened later when the shop was already warm):

| Time | Air_cool | Main-mode Δ radiator at that time | Shop warming driver |
|------|----------|------------------------------------|-------------------|
| 19:33 | 41.0°F | 0 (cold start) | None |
| 19:43 | 41.9°F | 18–34°F (ramp 1) | First heat arriving |
| 19:46 | 42.8°F | 28–30°F (peak 1) | Strong output |
| 19:48 | 43.7°F | 25–30°F (cooling) | Still high Δ |
| 19:49 | 44.6°F | 19–21°F | Declining Δ |
| 20:07 | 45.5°F | 27–28°F (ramp 2) | Moderate fire |
| 20:11 | 46.4°F | 28°F (peak 2) | Plateau |
| 20:13 | 47.3°F | 22–24°F (cooling) | Declining |
| 20:21 | 48.2°F | 43°F (ramp 3) | Full fire |

The shop gained its first 3.6°F (41→44.6) in ~16 minutes while main-mode delta was 20–34°F. The next 3.6°F (44.6→48.2) took ~32 minutes. This 2× slowdown is the classic diminishing return: as the shop warms, the temperature differential between the radiator and the shop air shrinks, reducing heat transfer per unit time even if the water-side delta remains the same.

---

## Main-Mode Summary

1. **The heater's moderate output (25–28°F Δ) is remarkably stable** across a wide mix range (100–150°F). It adds a fixed ~26°F per pass at a moderate burn rate.

2. **Full fire doubles the delta** — from 26 to 43°F — and is sustainable above 150°F mix.

3. **Fan speed does not affect water-side deltas.** Fan controls how much heat goes from the radiator into the air; it does not change how much heat enters or leaves the water.

4. **The radiator's extraction fraction is ~17–22%**, not a fixed constant. It varies with air_cool (see Part 4, Section 28). Earlier estimates of 20–24% did not control for confounding variables.

5. **Main-mode BTU output ranges from 43k (moderate fire) to 70k (full fire).**

6. **Peak delta occurs mid-ramp, not at peak mix temp**, because the cold return lags behind. Watch delta_heater > 30°F as a "fire is fully caught" signal.

7. **The shop warmed 7.2°F on main mode alone**. The first half of the gain came twice as fast as the second half — diminishing returns driven by air_cool approaching the radiator's effective output ceiling at the given fire intensity.

---
---

# Part 4: Controlled Analysis — Main Mode Only, Corrected Data

This section supersedes any conflicting observations in Parts 1–3. All data is from the corrected dataset, filtered to `diversion_state = False` (main mode only), excluding cold-start rows below 60°F mix. Heating/cooling phase confounds are identified where they exist.

---

## 28. Delta Radiator as a Function of Mix Temp, Fan Speed, and Air_cool

### Fan Speed: No measurable effect

The only mix band with adequate sample sizes at both 70% and 100% fan is 120–140°F:

| Fan | Avg Δ radiator | Avg mix (°F) | Avg air_cool (°F) | n |
|-----|---------------|-------------|-------------------|---|
| 70% | 25.4 | 132.8 | 45.8 | 38 |
| 100% | 25.3 | 130.2 | 44.0 | 31 |

**Delta_radiator is identical (25.4 vs 25.3°F)** despite a 30% difference in fan speed. The 100% data even had cooler intake air (44.0 vs 45.8), which should favor higher extraction — yet the result is the same.

Apparent differences in other mix bands (80–100 and 100–120) are confounded by heating/cooling phase: the 70% data comes from heating ramps (large Δ because cold return hasn't caught up), while the 100% data comes from cooling phases (smaller Δ because the system has equilibrated). These are not valid fan speed comparisons.

**Conclusion: Fan speed does not affect water-side delta_radiator.** This is confirmed both by the controlled comparison above and by the absence of any step change at fan speed transitions (Section 24).

### Air_cool: Real secondary effect (~1.5°F Δ radiator per 1°F air_cool)

Best controlled comparison — 70% fan, mix 120–140°F band, similar average mix temps:

| Air_cool (°F) | Avg Δ radiator | Avg mix (°F) | n |
|--------------|---------------|-------------|---|
| 44.6 | 27.0 | 129.4 | 16 |
| 45.5 | 27.4 | 138.2 | 3 |
| 47.3 | 22.9 | 136.1 | 17 |

A **2.7°F rise in air_cool (44.6 → 47.3) reduced Δ radiator by 4.1°F** (27.0 → 22.9). Ratio: approximately **1.5°F less Δ radiator per 1°F warmer intake air**.

This makes physical sense: the radiator's heat transfer is driven by the temperature gradient between the water and the air flowing over the fins. Warmer intake air shrinks that gradient, reducing heat extraction from the water.

### Mix Temp: Dominant driver

At 70% fan, air_cool ~44.6°F (controlled):

| Mix band (°F) | Avg Δ radiator | Avg mix (°F) | n |
|---------------|---------------|-------------|---|
| 60–80 | 9.0 | 72.1 | 48 |
| 80–100 | 24.5 | 93.4 | 9 |
| 100–120 | 24.9 | 111.5 | 13 |
| 120–140 | 27.0 | 129.4 | 16 |

Delta_radiator scales steeply from 60–100°F mix (9 → 25°F), then plateaus at ~25–27°F above 100°F during moderate fire. The plateau reflects the heater's fixed moderate-burn output, not a radiator limit — when the fire is stoked harder (Ramp 3), deltas break through to 40+°F at mix 160–190°F.

### Extraction fraction is not constant

Earlier sections estimated the radiator removes a fixed 20–24% of mix temperature. The controlled analysis shows the extraction fraction varies:

| Condition | Extraction (Δrad / mix) |
|-----------|------------------------|
| 70% fan, air_cool 44.6, mix 120–140 | 20–21% |
| 70% fan, air_cool 47.3, mix 120–140 | 17–18% |
| 100% fan, air_cool 44.0, mix 120–140 | 19–20% |
| 100% fan, air_cool 47.3, mix 160–180 | 23–24% |

The range is **17–24%**, driven primarily by air_cool. Warmer intake air reduces the fraction; hotter mix temps at full fire increase it. It is not a fixed radiator property.

---

## 29. Hierarchy of Influence on Delta Radiator (Main Mode)

Based on the controlled analysis:

1. **Mix temperature / fire intensity** — dominant. Determines the baseline delta. Moderate fire: 25–28°F plateau. Full fire: 35–43°F.
2. **Air_cool (intake air temperature)** — secondary. ~1.5°F reduction in Δ radiator per 1°F warmer intake. Material effect over the 7°F range observed in this session.
3. **Fan speed** — **no measurable effect** on water-side delta. Confirmed at the only cleanly comparable operating point (120–140°F mix) and by absence of step changes at speed transitions.
4. **Heating vs cooling phase** — confounds comparisons across time. During ramps, cold return lags behind mix, inflating Δ radiator. During cooling, the system equilibrates and Δ shrinks. This must be controlled for when comparing any two operating points.

---
---

# Part 5: Empirical Formulas for Radiator Cooling

*This section supersedes conflicting estimates in earlier parts. All data: corrected dataset, main mode only (diversion off), mix ≥ 60°F. n = 290 readings.*

---

## 30. Regression Models — Summary

Four models were fit to predict `delta_water_radiator`. Fan speed was tested and excluded (adds < 2% to R²; coefficient effectively zero).

| # | Formula | R² | Notes |
|---|---------|-----|-------|
| 1 | Δrad = 0.253 × (T_mix − T_air) + 3.8 | 0.746 | Simple, one variable |
| 2 | Δrad = 0.297 × (T_mix − T_air) | 0.719 | Proportional (no intercept) |
| 3 | Δrad = 0.308 × T_mix − 2.30 × T_air + 90 | 0.813 | Best fit |
| 4 | Δrad = (1.92 − 0.035 × T_air) × (T_mix − T_air) | 0.713 | Variable effectiveness |

All temperatures in °F. T_mix = water_mix, T_air = air_cool (intake).

---

## 31. Recommended Formulas

### Rule-of-thumb (easy to remember):

> **Δ_radiator ≈ 0.30 × (T_mix − T_air_cool)**

The radiator removes roughly **30% of the water-to-air temperature gradient** per pass. R² = 0.72–0.75 depending on intercept. Good enough for quick mental math.

**Examples** (at air_cool = 45°F):

| T_mix (°F) | Gradient | Predicted Δrad | Predicted T_cold |
|------------|----------|---------------|-----------------|
| 80 | 35 | 10.5 | 69.5 |
| 100 | 55 | 16.5 | 83.5 |
| 120 | 75 | 22.5 | 97.5 |
| 140 | 95 | 28.5 | 111.5 |
| 160 | 115 | 34.5 | 125.5 |
| 180 | 135 | 40.5 | 139.5 |

### More accurate (accounts for air_cool sensitivity):

> **Δ_radiator ≈ 0.31 × T_mix − 2.30 × T_air_cool + 90**

R² = 0.81. This captures the observation that air_cool has a disproportionate effect — **each 1°F rise in intake air reduces Δrad by 2.3°F**, far more than the 0.31°F gained per 1°F rise in mix. Physically, warmer intake air shrinks both the temperature gradient driving heat transfer and the convective efficiency.

**Examples:**

| T_mix (°F) | T_air_cool (°F) | Predicted Δrad |
|------------|----------------|---------------|
| 120 | 42 | 24.0 |
| 120 | 48 | 10.2 |
| 140 | 42 | 30.2 |
| 140 | 48 | 16.4 |
| 160 | 42 | 36.4 |
| 160 | 48 | 22.6 |
| 180 | 45 | 42.0 |

### Phase correction:

The models assume steady-state conditions. In practice:

- During **heating ramps** (mix rising): actual Δrad runs **~4°F higher** than predicted (cold return hasn't caught up yet)
- During **cooling/coasting** (mix falling): actual Δrad runs **~3°F lower** than predicted (system has equilibrated)
- At **steady state**: predictions are within ±2°F

---

## 32. What the Formulas Mean Physically

The simple formula `Δrad ≈ 0.30 × (T_mix − T_air)` is a classic **heat exchanger effectiveness** equation. It says the radiator converts 30% of the maximum possible temperature drop (water inlet to air inlet) into actual water cooling per pass. This 30% is determined by:

- Radiator surface area (currently using **half** the radiator)
- Water flow rate (~3.3 GPM at operating temp)
- Air flow rate (fan speed — but as shown, changes within the 70–100% range tested had no measurable water-side effect)

**Doubling the radiator surface area** (using the full radiator) would increase the effectiveness coefficient. In heat exchanger theory, effectiveness does not scale linearly with area — it follows a diminishing-returns curve. A reasonable estimate for doubling area from ε = 0.30 would be ε ≈ 0.45–0.55, meaning:

> **Full radiator estimate: Δ_radiator ≈ 0.50 × (T_mix − T_air_cool)**

At T_mix = 150°F, T_air = 45°F: Δrad ≈ 52°F (vs ~31°F with half radiator). That would bring the cold return down to ~98°F, roughly doubling the heat extraction as expected.

---

## 33. Applicability and Limitations

These formulas are based on a single session with:

- Half the radiator active
- Air_cool range: 42–48°F (a 6°F window)
- Mix range: 60–190°F
- Fan speed: 70–100% (no data at lower speeds)
- Flow rate: 2.8–3.5 GPM (varies with water temp/viscosity)

The formulas will break down outside these ranges. In particular:

- At very low mix temps (< 60°F), the radiator delta approaches zero and the proportional model loses accuracy.
- The large air_cool coefficient (−2.30) in Model 3 was fit over a narrow 6°F air range. Extrapolating to air_cool = 70°F would predict negative deltas, which is nonphysical. For warmer shop conditions, the proportional model (0.30 × gradient) is safer.
- Flow rate is not included as a variable — it covaries with mix temp in this dataset (hotter water = lower viscosity = higher flow). A session at constant temperature but varying flow would be needed to isolate that effect.

Additional sessions at different operating points (especially varying air_cool over a wider range and using the full radiator) would refine the coefficients.

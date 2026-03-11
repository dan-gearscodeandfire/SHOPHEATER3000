# Session 2 Analysis — 2026-02-22

**Source:** `data_logs/session_2026-02-22_15-34-42.csv`
**Duration:** 15:34–16:05 (~31 minutes)
**Conditions:** Full radiator (adjusted to complete fill during session), fans wired direct to 12V (fan_speed=0% in data is misleading — fans were running continuously at full voltage)

---

## 1. Session Overview

Single burn session that took a while to start. Two key physical changes occurred during the session:

1. **Radiator topped off** (~15:37): Air bled from radiator and filled completely with water, doubling effective surface area from previous session's half-fill.
2. **Pump slowdown** (~15:51 onward): Flow rate declined from 2.54 GPM to 0.67 GPM and never recovered. Cause uncertain — could be pump issue, added resistance from full radiator, or both.

### Timeline

| Time | Event | Hot (°F) | Mix (°F) | Flow (GPM) |
|------|-------|----------|----------|------------|
| 15:34:50 | Session start, pump off | 39.1 | 39.2 | 0.0 |
| 15:35:58 | Pump on | 39.1 | 39.2 | 0.45 |
| 15:37:29 | Diversion opened (radiator fill/air bleed) | 37.9 | 37.4 | 1.81 |
| 15:40:08 | Diversion closed — flow now reduced | 39.8 | 43.7 | 1.44 |
| 15:44:13 | Heat arriving at radiator | 40.8 | 43.7 | 1.32 |
| 15:48:33 | Mix crosses 100°F | 99.2 | 102.2 | 2.11 |
| 15:50:47 | Peak flow rate | 120.9 | 121.1 | 2.54 |
| 15:51:03 | Flow starts declining (pump issue begins) | 123.6 | 123.8 | 2.43 |
| 15:51:38 | Diversion opened (2nd time, safety) | 138.8 | 135.5 | 2.44 |
| 15:53:20 | Peak hot temperature | 165.7 | 131.9 | 1.44 |
| 15:56:23 | Diversion closed, back to main | 135.8 | 111.2 | 1.04 |
| 16:05:54 | Session end (cooling) | 84.2 | 81.5 | 0.69 |

---

## 2. Radiator Fill Event — 15:37:29

The first diversion event was used to bleed air and completely fill the radiator with water.

**Evidence of increased hydraulic resistance:**

| Condition | Flow (GPM) | Water temp |
|-----------|-----------|-----------|
| Before fill (main mode, cold water) | 1.81–1.82 | ~37°F |
| After fill (main mode, cold water) | 1.44 | ~39°F |
| Previous session (half radiator, cold water) | 2.8–3.2 | ~39°F |

The full radiator reduced cold-water flow by ~0.4 GPM (~20%) compared to immediately before. Compared to the previous session's half-radiator baseline (2.8–3.2 GPM), the reduction is ~50%.

---

## 3. Pump Slowdown — Starting ~15:51:03

Flow began declining while still in main mode, before the second diversion was opened.

| Time | Flow (GPM) | Mode | Notes |
|------|-----------|------|-------|
| 15:50:47 | 2.54 | main | Peak flow |
| 15:51:03 | 2.43 | main | First decline |
| 15:51:11 | 2.34 | main | Continuing |
| 15:51:38 | 2.44 | mix | Diversion opened |
| 15:52:09 | 2.08 | mix | Steep decline begins |
| 15:53:20 | 1.44 | mix | Peak hot temp |
| 15:55:42 | 1.10 | mix | |
| 15:56:23 | 1.04 | main | Diversion closed |
| 15:58:45 | 0.90 | main | |
| 16:02:10 | 0.79 | main | |
| 16:05:54 | 0.69 | main | Session end |

The decline is monotonic and never recovers, even as water cools (which should increase viscosity and normally reduce flow — yet in the previous session, the viscosity effect increased flow with temperature). This suggests a pump issue rather than a purely hydraulic cause.

**Post-session finding:** A fair amount of debris/buildup was found in the gunk trap immediately before the flow meter and pump. This is a likely contributor to (or the primary cause of) the flow decline — particulate accumulation restricting flow to the pump inlet.

---

## 4. Radiator Performance at 2.5 GPM (Full Radiator)

During the heating phase at peak flow (~15:48 to 15:51), main mode only:

| Time | Mix (°F) | Cold (°F) | Δrad (°F) | Air_cool (°F) | Gradient (°F) | Effectiveness | Flow (GPM) |
|------|----------|-----------|-----------|--------------|--------------|--------------|------------|
| 15:48:10 | 89.6 | 62.6 | 27.0 | 38.3 | 51.3 | 52.6% | 1.91 |
| 15:48:41 | 104.0 | 69.3 | 34.7 | 38.3 | 65.7 | 52.8% | 2.17 |
| 15:49:13 | 107.6 | 81.0 | 26.6 | 38.3 | 69.3 | 38.4% | 2.47 |
| 15:49:52 | 117.5 | 90.0 | 27.5 | 38.3 | 79.2 | 34.7% | 2.48 |
| 15:50:24 | 119.3 | 95.4 | 23.9 | 39.2 | 80.1 | 29.8% | 2.52 |
| 15:50:47 | 121.1 | 97.6 | 23.5 | 39.2 | 81.9 | 28.7% | 2.54 |
| 15:51:27 | 130.1 | 99.4 | 30.7 | 39.2 | 90.9 | 33.8% | 2.45 |

At steady state (15:50, ~2.5 GPM), effectiveness was **29–35%** — only marginally higher than the previous session's 30% with half the radiator. Doubling the radiator surface area added ~2–5 percentage points at this flow rate. The water moves too quickly for the extra surface area to extract meaningfully more heat.

Previous session formula: Δrad ≈ 0.30 × (mix − air_cool). Actual at 2.5 GPM: ratio = 0.29–0.34. The formula still holds approximately at this flow rate.

---

## 5. Radiator Performance at 0.8 GPM (Full Radiator, Pump Slowed)

After diversion was closed and the pump had slowed (15:56 onward), main mode cooling phase:

| Time | Mix (°F) | Cold (°F) | Δrad (°F) | Air_cool (°F) | Gradient (°F) | Effectiveness | Flow (GPM) |
|------|----------|-----------|-----------|--------------|--------------|--------------|------------|
| 15:57:33 | 126.5 | 49.4 | 77.1 | 41.0 | 85.5 | 90.2% | 0.91 |
| 15:59:40 | 119.3 | 47.3 | 72.0 | 41.0 | 78.3 | 92.0% | 0.85 |
| 16:01:38 | 104.0 | 46.5 | 57.5 | 41.0 | 63.0 | 91.3% | 0.78 |
| 16:03:45 | 92.3 | 45.6 | 46.7 | 41.0 | 51.3 | 91.0% | 0.72 |
| 16:05:54 | 81.5 | 44.8 | 36.7 | 41.0 | 40.5 | 90.6% | 0.69 |

At ~0.8 GPM, effectiveness was a remarkably stable **90–92%** across the entire mix range (80–127°F). The radiator extracts over 90% of the available thermal gradient, bringing the cold return to within 4–6°F of shop ambient.

Updated formula at this flow rate: **Δrad ≈ 0.91 × (mix − air_cool)**.

This is 3× the previous session's coefficient.

---

## 6. Effectiveness vs Flow Rate (Controlled Comparison)

Filtering to main mode, mix 100–130°F, air_cool ~39–41°F to control for temperature:

| Flow bin | n | Avg Effectiveness | Avg Δrad (°F) | Avg Mix (°F) | Avg Flow (GPM) |
|----------|---|------------------|--------------|-------------|----------------|
| > 2.5 GPM | 8 | 30.9% | 24.4 | 118.3 | 2.52 |
| 2.0–2.5 GPM | 14 | 39.0% | 28.6 | 113.3 | 2.38 |
| < 1.0 GPM | 44 | 91.0% | 68.9 | 116.8 | 0.85 |

Flow rate is the dominant variable. At similar temperatures, reducing flow from 2.5 to 0.85 GPM tripled the radiator's effectiveness from 31% to 91%.

---

## 7. BTU Output Comparison

Despite vastly different effectiveness, total heat delivery is similar because lower flow × higher delta ≈ higher flow × lower delta:

| Regime | Flow (GPM) | Avg Δrad (°F) | Effectiveness | BTU/hr |
|--------|-----------|-------------|--------------|--------|
| 2.5 GPM, mix ~120°F | 2.50 | 25 | 31% | ~31,000 |
| 0.85 GPM, mix ~120°F | 0.85 | 73 | 91% | ~31,000 |
| 0.75 GPM, mix ~95°F | 0.75 | 48 | 90% | ~18,000 |

At the same input temperature, both flow regimes deliver approximately the same BTU/hr to the shop. The low-flow regime's advantage is that the cold return is much cooler (47°F vs 95°F), meaning the heater receives maximally cooled water — better for safety.

The BTU drops at lower mix temps because the thermal gradient shrinks, not because of efficiency loss.

---

## 8. Snapshot at 15:50 — Peak Flow, Thermal Equilibrium

At 15:50, the system was at peak flow and approaching thermal equilibrium:

| Sensor | Value |
|--------|-------|
| water_hot | 116–122°F |
| water_mix | 118–122°F |
| water_cold | 91–98°F |
| water_reservoir | 41.0°F (untouched) |
| air_cool | 38–39°F |
| air_heated | 46–48°F |
| delta_heater | 22–26°F |
| delta_radiator | 23–27°F |
| delta_air | 7.5–9°F |
| flow | 2.45–2.54 GPM |

Delta_heater ≈ delta_radiator ≈ 24–25°F. The heater was adding heat at almost exactly the rate the radiator was removing it, resulting in slowly climbing temperatures. The system was approaching steady state at this fire intensity.

---

## 9. Comparison with Session 1 (2026-02-17)

| Parameter | Session 1 (half radiator) | Session 2 (full radiator) |
|-----------|--------------------------|--------------------------|
| Radiator fill | Half | Full |
| Fan control | Software (70–100%) | Wired direct 12V |
| Peak flow | 3.3+ GPM | 2.54 GPM |
| Late-session flow | 2.8–3.5 GPM | 0.67–0.91 GPM |
| Effectiveness at ~2.5 GPM | ~30% | ~31% |
| Effectiveness at ~0.8 GPM | No data | ~91% |
| Peak hot temp | 190°F | 165.7°F |
| Delta_air at ~120°F mix | 8–10°F | 7.5–9°F |
| Formula (Δrad) | 0.30 × (mix − air) | 0.30 at 2.5 GPM; 0.91 at 0.8 GPM |

Key finding: **at the same flow rate (~2.5 GPM), the full radiator performed almost identically to the half radiator.** The dramatic improvement (31% → 91%) came entirely from the reduced flow rate, not the doubled surface area. At high flow, water spends too little time in the radiator for additional surface area to matter.

---

## 10. Implications for the Automatic Algorithm

1. **Flow rate is a critical variable** that must be monitored. The formulas from Session 1 are only valid at ~2.5 GPM. At 0.8 GPM, the radiator removes 3× more heat per pass.

2. **The pump slowdown is a concern.** If this is a recurring issue, the algorithm needs a flow-rate safety check. If flow drops below a threshold while water is hot, the system could overheat at the heater (less circulation = more time in the firebox per pass).

3. **Low flow + full radiator is actually excellent for cooling safety** — the cold return approaches ambient, so the heater gets the coldest possible water back. But it's only safe if the flow doesn't stop entirely.

4. **The radiator surface area doubled but only mattered at low flow.** If the pump is repaired and flow returns to 2.5+ GPM, expect effectiveness to return to ~30–35%, similar to Session 1.

5. **Previous formulas need a flow-rate term.** A general model would be:
   - At flow > 2.0 GPM: Δrad ≈ 0.30 × (mix − air_cool)
   - At flow ~ 1.0 GPM: Δrad ≈ 0.60 × (mix − air_cool)  *(interpolated)*
   - At flow < 0.9 GPM: Δrad ≈ 0.91 × (mix − air_cool)

---

## 11. Air-Side Performance

With fans wired direct to 12V throughout the session:

| Mix (°F) | Air_cool (°F) | Air_heated (°F) | Δair (°F) |
|----------|-------------|----------------|-----------|
| 85 | 38.3 | 41.7 | 3.4 |
| 105 | 38.3 | 43.0 | 4.7 |
| 120 | 39.2 | 48.0 | 8.8 |
| 130 | 39.2 | 51.4 | 12.2 |
| 132 (peak, mix mode) | 40.1 | 55.1 | 15.0 |
| 125 (cooling, 0.8 GPM) | 41.0 | 50.9 | 9.9 |
| 100 (cooling, 0.8 GPM) | 41.0 | 48.8 | 7.8 |

Delta_air peaked at 15°F during the high-temperature mix-mode phase and settled to 8–10°F during the 0.8 GPM cooling phase. Comparable to Session 1 at similar water temperatures, confirming the direct-wired fans delivered similar airflow to the software-controlled 70–100% range.

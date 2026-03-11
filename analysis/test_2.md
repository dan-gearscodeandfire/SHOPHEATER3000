# Session 3 Analysis — 2026-02-22 (Evening)

**Source:** `data_logs/session_2026-02-22_19-33-27.csv`
**Duration:** 19:33–19:59 (~26 minutes)
**Conditions:** Full radiator (properly purged since Session 2), gunk trap cleaned, fans wired direct to 12V (100% equivalent; fan_speed=0% in data is incorrect). Flow was manually adjusted by valve at least twice during the session. Two brief fan-off tests (~20s to ~1 min each) were performed.

---

## 1. Session Overview

| Time | Event | Hot (°F) | Mix (°F) | Flow (GPM) |
|------|-------|----------|----------|------------|
| 19:33:36 | Session start (warm from prior session) | 45.4 | 44.6 | 1.90 |
| 19:37:26 | Heat arriving at radiator | 42.6 | 44.6 | 2.10 |
| 19:41:18 | Mix crosses 100°F | 98.3 | 100.4 | 2.59 |
| 19:46:18 | Pre-jump peak | 139.7 | 140.0 | 2.82 |
| 19:46:25 | **Manual flow increase** | 139.9 | 140.9 | 3.87 |
| 19:46:33 | Peak mix temperature | 140.8 | 141.8 | 3.73 |
| ~19:47:44 | First fan-off test (Δair drops while mix stable) | 137.4 | 138.2 | 3.77 |
| 19:51:57 | **Manual flow decrease** | 115.3 | 114.8 | 2.82 |
| ~19:52:28 | Second fan-off test (probable) | 117.4 | 116.6 | 2.74 |
| 19:57–19:59 | Steady-state equilibrium | 119–120 | 120.2 | 2.75 |
| 19:59:42 | Session end | 118.4 | 118.4 | 2.76 |

---

## 2. Three Flow Regimes (Manual Valve Adjustments)

| Regime | Time window | Avg flow | Avg mix | Avg cold | Avg Δrad | Effectiveness | BTU/hr |
|--------|------------|----------|---------|----------|----------|--------------|--------|
| ~2.8 GPM | 19:41–19:46 | 2.76 | 121.8 | 62.8 | 59.1 | **74%** | ~81k |
| ~3.75 GPM | 19:46–19:51 | 3.75 | 131.6 | 80.2 | 51.4 | **59%** | ~97k |
| ~2.75 GPM | 19:52–19:59 | 2.76 | 114.7 | 67.1 | 47.6 | **70%** | ~66k |

Higher flow = more BTU despite lower effectiveness per pass. The 3.75 GPM regime delivered ~97k BTU/hr vs ~81k at 2.75 GPM.

---

## 3. Radiator Effectiveness — Full Radiator, Properly Purged

This is the first session with a confirmed, fully operational radiator (all air bled, full water fill). The results are dramatically different from Sessions 1 and 2.

| Session | Radiator state | Flow (GPM) | Effectiveness | Δrad formula |
|---------|---------------|-----------|--------------|-------------|
| 1 (Feb 17) | Half fill | 2.5–3.3 | **30%** | Δrad ≈ 0.30 × gradient |
| 2 (Feb 22 PM) | Incomplete fill | 2.5 | **31%** | Δrad ≈ 0.31 × gradient |
| 2 (Feb 22 PM) | Incomplete fill | 0.85 | **91%** | Δrad ≈ 0.91 × gradient |
| **3 (Feb 22 EVE)** | **Full, purged** | **2.75** | **70–74%** | **Δrad ≈ 0.72 × gradient** |
| **3 (Feb 22 EVE)** | **Full, purged** | **3.75** | **57–60%** | **Δrad ≈ 0.59 × gradient** |

The properly purged full radiator is **2.3× more effective** than Sessions 1–2 at comparable flow rates. Session 2's mid-session fill left significant air pockets that crippled performance.

---

## 4. Heater Output

This session had a much more intense fire than Session 2:

| Session | Peak Δ_heater | Peak flow | Peak BTU input |
|---------|-------------|----------|---------------|
| 2 (Feb 22 PM) | 26°F | 2.54 GPM | ~33k BTU/hr |
| **3 (Feb 22 EVE)** | **69.5°F** | **2.82 GPM** | **~98k BTU/hr** |

The fire was roughly 3× more intense, reaching 98k BTU/hr input to the water.

---

## 5. Fan-Off Tests

Two brief fan-off periods were performed. The clearest signature is at **19:47:44**: air_heated dropped from 67.4°F to ~62°F over ~40 seconds while mix was stable at 137–138°F. Air effectiveness dropped from 23.7% to ~19%.

The fan-off tests did not produce measurable changes in water-side deltas (Δ_radiator), confirming the earlier finding that fan speed does not affect water-side heat extraction over short periods.

**Why fan speed doesn't affect water-side cooling:** The rate-limiting step for heat leaving the water is the **water-to-metal convective boundary** — how fast heat can transfer from the moving water into the aluminum fins. This is governed by flow velocity, contact area, and the water-metal temperature difference. It is largely independent of what happens on the air side of the metal. As long as the fans keep the fin surface meaningfully cooler than the water (which even modest airflow or natural convection achieves), the water-side extraction rate is unchanged. Fan speed controls how efficiently the extracted heat then moves from the aluminum into the shop air, but the aluminum fins were never thermally saturated in any test — they always had excess capacity to accept heat from the water.

This explains why **flow rate** is the dominant variable: slower flow = more dwell time at the water-metal interface = more heat extracted per pass. And why **doubling the radiator surface area** roughly doubled effectiveness — it doubled the contact area at the bottleneck. Fan speed, operating on the non-bottleneck air side, has no measurable water-side effect in the 0–100% range tested (though sustained fan-off for many minutes would eventually saturate the fins and change this).

---

## 5b. Radiator Saturation — When Would the Air Side Become the Bottleneck?

The fin surface temperature at steady state is governed by the heat balance between the water and air sides:

> **h_water × (T_water − T_fin) = h_air × A_ratio × (T_fin − T_air)**

Solving for T_fin:

> **T_fin = (h_water × T_water + h_air × A_ratio × T_air) / (h_water + h_air × A_ratio)**

The radiator becomes "saturated" — water can no longer dump heat effectively — when **T_fin approaches T_water**, i.e., when the metal is nearly as hot as the water passing through it. This occurs when:

> **h_air × A_ratio << h_water**

**Variables that determine saturation:**

| Input | Symbol | Effect |
|-------|--------|--------|
| Fan speed / airflow | h_air | Lower airflow → lower h_air → closer to saturation |
| Fin surface area ratio | A_ratio | More fins → harder to saturate (multiplies h_air) |
| Water flow rate | h_water | Faster flow → higher h_water → easier to saturate (more heat loaded in per unit time) |
| Water-to-air gradient | T_water − T_air | Larger gradient → more heat per unit area to dissipate |

**Current operating point:** This radiator operates well below saturation with fans on. The large fin area (A_ratio) multiplied by even modest h_air exceeds h_water. The fins have more capacity to reject heat to air than the water has capacity to load heat into the metal. This is why fan speed changes (70–100%, and even brief 0% tests) produce no measurable water-side effect — T_fin stays well below T_water regardless.

**When would saturation occur?** Sustained fans-off for multiple minutes would allow T_fin to rise toward T_water as natural convection alone cannot dissipate the heat fast enough. The exact time depends on the thermal mass of the aluminum and the heat load, but based on the ~40-second fan-off test showing only a modest air_heated decline, saturation likely requires **2+ minutes of zero airflow** at operating temperatures. At that point, delta_radiator would begin to decline as the driving force (T_water − T_fin) shrinks.

---

## 6. Safety Observations

**Peak temperatures:** Hot reached 140.8°F, well below the 180°F diversion trigger proposed in the automatic plan. No safety concern at any point during this session.

**Thermal headroom at peak fire:** At the peak (19:46:18), Δ_heater was 69.5°F and hot was 139.7°F. Predictive safety check: hot + Δ_heater = 139.7 + 69.5 = **209°F** — this would have triggered the proposed "hot + delta > 190" safety rule. If the fire had continued intensifying without intervention, temperatures could have climbed dangerously fast.

**Radiator as safety device:** At 2.75 GPM, the full radiator removes 70–74% of the thermal gradient per pass. This means water returning to the heater is much cooler than in Sessions 1–2 (cold ~63–67°F vs ~95–99°F). Cooler return water absorbs more heat from the firebox per pass, providing a larger thermal buffer before boiling.

**Flow rate matters for safety:** At 3.75 GPM, BTU removal was ~97k/hr. If the pump slows (as in Session 2) or flow is restricted, BTU removal drops and temperatures will climb faster. Flow monitoring should be part of the automatic safety logic.

---

## 7. Updated Effectiveness Model

Combining all three sessions, effectiveness as a function of flow rate (full, purged radiator):

| Flow (GPM) | Effectiveness (ε) | Formula |
|-----------|-------------------|---------|
| 0.85 | 91% | Δrad ≈ 0.91 × (mix − air_cool) |
| 2.75 | 72% | Δrad ≈ 0.72 × (mix − air_cool) |
| 3.75 | 59% | Δrad ≈ 0.59 × (mix − air_cool) |

For automation, flow rate must be a monitored input. A single effectiveness constant is insufficient — the radiator behaves very differently at 1 GPM vs 4 GPM.

---

## 8. Key Takeaways for Automation

1. **The full, purged radiator is a capable heat exchanger** — 59–74% effectiveness at normal flow rates. This is more than adequate for shop heating and provides a solid safety margin.

2. **Higher flow = more total BTU delivered** even though per-pass extraction drops. If the goal is maximum heating, run the pump at full flow. If the goal is maximum water cooling per pass (safety), restrict flow — but total heat removal may drop.

3. **The "hot + delta_heater > 190" predictive trigger would have fired during this session** (209°F at peak). This is appropriate — that fire intensity could have been dangerous if sustained. Diversion activation at that point would have been correct.

4. **Flow rate is a safety-critical variable.** The automatic algorithm should monitor flow and raise an alert (or activate diversion) if flow drops below a threshold while water is hot.

5. **Fan speed does not affect water-side safety on short timescales.** Brief fan outages (20–60s) produced no measurable water temperature change. Fan control is a comfort feature, not a safety feature.

6. **Air purging matters enormously.** The difference between an incompletely filled and a properly purged radiator is 30% vs 72% effectiveness — the system should detect and/or warn about poor radiator performance (e.g., if Δrad/gradient is persistently below 50% at normal flow, suspect air in the radiator).

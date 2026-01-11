# TODO - SHOPHEATER3000

Task list for future user-directed items.

---

## Active Tasks

### Implement Dynamic Arrow Colors Based on Temperature
**Status:** ✅ COMPLETED - January 11, 2026

Dynamically change arrow colors based on actual temperature readings to make system state instantly visible.

**Color Mapping:**
- 🔴 RED: > 120°F (hot)
- 🟠 ORANGE: 70-120°F (warm/mixed)
- 🔵 BLUE: < 70°F (cold)

**Temperature → Arrow Mapping:**
- **water_hot** controls arrows in cells: 0:2, 0:1, 0:0, 1:1, 1:0, 2:1
- **water_mix** controls arrows in cells: 3:2, 3:1, 3:0
- **water_cold** controls arrows in cells: 0:4, 0:5, 1:5, 3:4, 3:5

**Branch arrows (future):**
- Reserved for "mix" mode implementation
- Will be used in cells 0:1 and 3:1

**Air flow arrows - Potential solutions:**

1. **Option A: Air Temperature Delta-Based**
   - Use delta_air to determine color
   - Positive delta (heating) → warm colors (orange/red gradient)
   - Negative/zero delta → cool colors (blue/cyan)
   - Visually shows heating efficiency

2. **Option B: Absolute Air Temperature**
   - air_cool controls inlet arrows (cells 4:0, 4:1, 4:2)
   - air_heated controls outlet arrows (cells 4:3, 4:4, 4:5)
   - Same thresholds: red >120°F, orange 70-120°F, blue <70°F
   - Simple, consistent with water logic

3. **Option C: Fan Speed Correlation**
   - Arrow color intensity based on fan speed
   - 0% fan = gray/dim arrows (no flow)
   - 1-50% fan = transitional colors
   - 51-100% fan = full vibrant colors based on air_heated temp
   - Shows both flow rate AND temperature

4. **Option D: Heating Mode Indicator**
   - Green arrows when actively heating (delta_air > threshold, e.g., 5°F)
   - Yellow arrows when maintaining (small positive delta)
   - Blue arrows when not heating (delta ≤ 0)
   - Focuses on system function rather than absolute temp

**Recommended:** Option B (simplest, consistent) or Option C (most informative)

**Note:** Air flow arrow implementation deferred per user request

---

### Implement Conditional Arrow Display Based on Branch States
**Status:** ✅ COMPLETED - January 11, 2026

Arrow visibility and direction must change dynamically based on the state of main_loop and diversion branches to accurately represent actual water flow paths.

**Scenario 1: Diversion OFF, Main ON**
- `0:0` → not displayed (blank)
- `0:1` → 90° arrow (water_hot color)
- `1:0` → not displayed (blank)
- `3:0` → not displayed (blank)
- `3:1` → 90° arrow (water_mix color)

**Scenario 2: Diversion ON, Main OFF**
- `0:1` → arrow pointing left
- `1:0` → arrow pointing down (water_hot color)
- `1:1` → not displayed (blank)
- `2:1` → not displayed (blank)
- `3:0` → 90° arrow (water_mix color)
- `3:1` → straight arrow pointing right (water_mix color)

**Scenario 3: Diversion ON, Main ON (future "mix mode")**
- `0:1` → branching arrow (water_hot color)
- `0:0` → 90° arrow (water_hot color)
- `1:1` → down arrow (water_hot color)
- `1:0` → down arrow (water_hot color)
- `2:1` → down arrow (water_hot color)
- `3:2` → right arrow (water_mix color) - always displayed
- `3:1` → branching arrow (water_mix color)
- `3:0` → 90° arrow (water_reservoir/water_cold color)

**Implementation Notes:**
- Requires JavaScript logic to detect main_loop and diversion states
- Arrow image selection based on both state and temperature
- Cells should hide (`display: none`) when not applicable to current flow path
- Ensures UI always represents actual physical water routing

---

## Implementation Plan

### Phase 1: Server Flow Mode + Dynamic Arrow Colors
**Status:** ✅ COMPLETED

**Backend Changes (shopheater3000.py):**
1. Add `self.flow_mode` variable to track current flow mode
2. Create `calculate_flow_mode()` method:
   - main ON + diversion OFF → 'main'
   - main OFF + diversion ON → 'diversion'
   - main ON + diversion ON → 'mix'
3. Update `set_main_loop()` and `set_diversion()` to call `calculate_flow_mode()`
4. Include `flow_mode` in WebSocket broadcast data

**Frontend Changes (web_ui.html):**
1. Create `getArrowColor(temperature)` helper function:
   - Returns 'red', 'orange', or 'blue' based on thresholds
2. Create `updateArrowColors(data)` function:
   - Maps temperature sensors to grid cells
   - Updates arrow images dynamically based on temp
3. Call `updateArrowColors()` from `updateDisplay()`

**Temperature-to-Cell Mapping:**
- water_hot → cells: 0:2, 0:1, 0:0, 1:1, 1:0, 2:1
- water_mix → cells: 3:2, 3:1, 3:0 (note: 3:0 uses water_reservoir in mix mode)
- water_reservoir → cell 3:0 (mix mode only)
- water_cold → cells: 0:4, 0:5, 1:5, 3:4, 3:5
- Air arrows: IGNORE FOR NOW

### Phase 2: Conditional Arrow Display
**Status:** ✅ COMPLETED

**Frontend Changes (web_ui.html):**
1. Create `updateArrowVisibility(flowMode)` function
2. Implement three flow scenarios:
   
   **Main Mode (main ON, diversion OFF):**
   - Hide: 0:0, 1:0, 3:0
   - Hide: 1:1, 2:1
   - Show all others with appropriate directions
   
   **Diversion Mode (main OFF, diversion ON):**
   - Hide: 1:1, 2:1
   - Cell 0:1 → arrow pointing LEFT (water_hot color)
   - Cell 1:0 → arrow pointing DOWN (water_hot color)
   - Cell 3:0 → 90° arrow (water_mix color)
   - Cell 3:1 → straight arrow pointing RIGHT (water_mix color)
   
   **Mix Mode (main ON, diversion ON):**
   - Cell 0:1 → BRANCHING arrow (water_hot color)
   - Cell 0:0 → 90° arrow (water_hot color)
   - Cell 1:1 → DOWN arrow (water_hot color)
   - Cell 1:0 → DOWN arrow (water_hot color)
   - Cell 2:1 → DOWN arrow (water_hot color)
   - Cell 3:1 → BRANCHING arrow (water_mix color)
   - Cell 3:0 → 90° arrow (water_reservoir color)
   - Cell 3:2 → ALWAYS displayed (right arrow, water_mix color)

**Arrow Direction Reference:**
- Counterclockwise loop
- Cell 0:1: enters from right (0:2) → points down (to 1:1)
- Cell 3:1: enters from top (2:1) → points right (to 3:2)

**Key Clarifications from Q&A:**
- ✅ Branching arrows exist, only for cells 0:1 and 3:1 in mix mode
- ✅ Cell 3:2 always displays regardless of mode
- ✅ Cells that can be blank: 0:0, 1:0, 3:0 (main), 1:1, 2:1 (diversion)
- ✅ Use water_reservoir for cell 3:0 in mix mode (not water_cold)
- ✅ flow_mode should be server-side variable, broadcast to UI

### Testing & Verification
**Status:** ✅ COMPLETED - January 11, 2026

**What was implemented:**
1. ✅ Server now tracks `flow_mode` ('main', 'diversion', 'mix', 'none')
2. ✅ `calculate_flow_mode()` automatically updates when main_loop or diversion changes
3. ✅ `flow_mode` included in WebSocket broadcast data
4. ✅ Arrow IDs added to all water flow arrows in HTML (arrow_0_0, arrow_0_1, etc.)
5. ✅ `getArrowColor()` function determines color based on temperature thresholds
6. ✅ `updateArrowColors()` applies colors to all arrows based on sensor temperatures
7. ✅ `updateArrowVisibility()` shows/hides arrows and changes types based on flow_mode
8. ✅ Integration into `updateDisplay()` to apply changes on every data update

**Test Scenarios (for user when awake):**

1. **Main Mode Test (main ON, diversion OFF):**
   - Turn main loop ON, diversion OFF
   - Verify arrows at cells 0:0, 1:0, 3:0, 1:1, 2:1 are hidden
   - Verify arrow 0:1 is a 90° turn (down from right)
   - Verify arrow 3:1 is a 90° turn (right from top)
   - Verify all visible arrows show correct colors for their temperatures

2. **Diversion Mode Test (main OFF, diversion ON):**
   - Turn main loop OFF, diversion ON
   - Verify arrows at cells 1:1, 2:1 are hidden
   - Verify arrow 0:1 points LEFT (horizontal)
   - Verify arrow 1:0 points DOWN and is visible
   - Verify arrow 3:0 is a 90° turn
   - Verify arrow 3:1 points RIGHT (straight horizontal)
   - Verify all visible arrows show correct colors

3. **Mix Mode Test (main ON, diversion ON):**
   - Turn both main loop ON and diversion ON
   - Verify all arrows are visible
   - Verify arrow 0:1 is a BRANCHING arrow (hot water color)
   - Verify arrow 3:1 is a BRANCHING arrow (mix water color)
   - Verify arrow 3:0 uses water_reservoir color (not water_mix)
   - Verify all other arrows show correct colors

4. **Dynamic Color Test:**
   - Heat/cool different parts of the system
   - Verify arrows change color as temperatures cross thresholds:
     - Blue when temp < 70°F
     - Orange when 70°F ≤ temp ≤ 120°F
     - Red when temp > 120°F

5. **Browser Console Check:**
   - Open developer console
   - Verify no JavaScript errors
   - Look for log messages: "Arrow colors updated" and "Updating arrow visibility for flow mode"
   - Verify flow_mode value in WebSocket messages

**Expected Server Output:**
- On startup: "Flow mode calculated: [MODE] (main=[bool], diversion=[bool])"
- When toggling valves: Same message showing updated flow_mode
- WebSocket broadcasts should include `flow_mode` field

**Test Results:**
- ✅ All three flow modes (MAIN, DIVERSION, MIX) display correctly
- ✅ Arrows rotate to correct orientations in each mode
- ✅ Branching arrows appear in MIX mode at cells 0:1 and 3:1
- ✅ Arrow colors change correctly based on temperature thresholds
- ✅ Automated browser testing verified RED (>120°F), ORANGE (70-120°F), BLUE (<70°F)
- ✅ Grid layout preserved (visibility:hidden instead of display:none)
- ✅ No JavaScript errors in console
- ✅ flow_mode broadcasts correctly from server

---

## Completed ✅

- [x] Sensor calibration with ice water test
- [x] Assign specific sensor IDs to locations
- [x] Web UI real-time display implementation
- [x] WebSocket connection stability
- [x] Temperature conversion to Fahrenheit
- [x] Delta calculations (heater, radiator, air)
- [x] Flow rate display
- [x] Fan speed control (text + slider)
- [x] Solenoid control implementation
- [x] Fix UI control flickering (optimistic updates + smart ignore windows)
- [x] Split broadcast architecture (5s temps, immediate controls)
- [x] Dynamic arrow colors based on temperature (RED/ORANGE/BLUE)
- [x] Conditional arrow display based on flow mode (MAIN/DIVERSION/MIX)
- [x] Arrow rotation corrections for all flow modes
- [x] Branching arrow implementation for mix mode
- [x] Server-side flow_mode calculation and broadcasting

---

**Last Updated:** January 11, 2026 22:00 UTC  
**Status:** All active tasks completed - dynamic flow visualization fully functional

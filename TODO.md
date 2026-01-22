# TODO - SHOPHEATER3000

Task list for future user-directed items.

---

## Active Tasks

### Test Arrow Display at Higher Temperatures
**Status:** 🔲 PENDING

Verify that arrow colors and orientations display correctly at higher temperatures (orange and red thresholds).

**Temperature Thresholds:**
- 🔵 BLUE: < 70°F (cold)
- 🟠 ORANGE: 70-120°F (warm/mixed)
- 🔴 RED: > 120°F (hot)

**Test Cases:**
1. **Orange Arrow Test (70-120°F):**
   - Heat water to 70-120°F range
   - Verify arrows change from blue to orange
   - Test in all three flow modes (main, diversion, mix)
   - Verify 90° corner arrows (cells 0:0, 0:1, 0:5, 3:0, 3:1, 3:5) rotate correctly

2. **Red Arrow Test (>120°F):**
   - Heat water above 120°F
   - Verify arrows change from orange to red
   - Test in all three flow modes
   - Verify 90° corner arrows rotate correctly

3. **Temperature Transition Test:**
   - As water heats up, verify smooth color transitions
   - Blue → Orange at 70°F threshold
   - Orange → Red at 120°F threshold
   - As water cools, verify reverse transitions

**Cells to Watch:**
- **Hot water path:** 0:0, 0:1, 0:2, 1:1, 2:1 (use water_hot color)
- **Mix water path:** 3:0, 3:1, 3:2 (use water_mix/reservoir color)
- **Cold water path:** 0:4, 0:5, 1:5, 3:4, 3:5 (use water_cold color - always blue)

---

### Verify Arrow Orientation in All Modes
**Status:** 🔲 PENDING

Confirm all arrows display correct flow direction in each mode at all temperatures.

**Expected Arrow Orientations:**

| Cell | Main Mode | Diversion Mode | Mix Mode |
|------|-----------|----------------|----------|
| 0:0 | Hidden | 90° (right→down) | 90° (right→down) |
| 0:1 | 90° (right→down) | Straight (→left) | Branch (T-junction) |
| 0:5 | 90° (left→up) | 90° (left→up) | 90° (left→up) |
| 3:0 | Hidden | 90° (top→right) | 90° (top→right) |
| 3:1 | 90° (top→right) | Straight (→right) | Branch (T-junction) |
| 3:5 | 90° (right→down) | 90° (right→down) | 90° (right→down) |

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
- [x] **Critical safety feature: Both valves default OPEN on startup**
- [x] **Safety override: Prevents both valves from closing simultaneously**
- [x] **Fixed 90° arrow image base orientations (blue/orange aligned with red)**
- [x] **Corrected arrow rotations for cells 0:0, 0:1, 0:5, 3:0, 3:1, 3:5**

---

**Last Updated:** January 22, 2026  
**Status:** Arrow corrections complete - pending temperature testing at higher values

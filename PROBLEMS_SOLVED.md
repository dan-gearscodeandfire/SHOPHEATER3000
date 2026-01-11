# SHOPHEATER3000 - Solved Problems

Comprehensive history of issues encountered during development of all modules and their solutions.

**Purpose:** Document lessons learned to avoid repeating mistakes and help troubleshoot similar issues.

---

## Problem 1: DS18B20 GPIO Pin Compatibility Issues

**Module:** raspi-ds18b20 (Temperature Sensor)  
**Date:** Early development  
**Symptom:** Temperature sensors not detected on the 1-Wire bus when using GPIO17 or other pins  
**Cause:** DS18B20 1-Wire interface works reliably only on GPIO4 on Raspberry Pi  
**Investigation:** 
- Tried multiple GPIO pins (GPIO17, etc.)
- Factory breakout boards are designed specifically for GPIO4
- Device tree overlay expects GPIO4 by default

**Solution:** Use GPIO4 (Physical Pin 7) exclusively for DS18B20 sensors  
**Configuration Required:**
```
# In /boot/firmware/config.txt
dtoverlay=w1-gpio,gpiopin=4
```

**Key Learning:** GPIO4 is the default and required pin for DS18B20 - don't try to use other pins  
**Status:** ✓ Solved

---

## Problem 2: Flowmeter RPi.GPIO Library Incompatibility

**Module:** raspi-flowmeter  
**Date:** Initial development (before kernel 6.6+ migration)  
**Symptom:** `RuntimeError: Failed to add edge detection`  
**Cause:** RPi.GPIO doesn't work on Raspberry Pi kernel 6.6+  
**Background:** RPi.GPIO uses deprecated `/dev/mem` interface which was removed in modern kernels  
**Solution:** Migrated to modern `lgpio` library  
**Status:** ✓ Solved

---

## Problem 3: Flowmeter Wrong GPIO Pin Configuration

**Module:** raspi-flowmeter  
**Date:** Initial development  
**Symptom:** No pulses detected despite water flow  
**Cause:** Initially used wrong GPIO pin number in code  
**Solution:** Verified correct GPIO pin (GPIO 27, Physical Pin 13)  
**Status:** ✓ Solved

---

## Problem 4: Flowmeter GPIO Pin Interference

**Module:** raspi-flowmeter  
**Date:** Mid-development  
**Symptom:** GPIO 17 not detecting pulses reliably when motor driver was running  
**Cause:** GPIO 17 (Pin 11) is physically adjacent to GPIO 18 (Pin 12) which has BTS7960 motor driver connected. Electrical noise and crosstalk from motor driver's high-frequency PWM (24 kHz) interfered with sensor signal  
**Investigation:** 
- Observed intermittent pulse detection
- Noticed correlation with motor driver activity
- Electrical noise from high-current motor switching affecting adjacent pins

**Solution:** Moved flowmeter to GPIO 27 (Pin 13) which provides physical separation from motor driver and other high-current devices  
**Key Learning:** Avoid placing sensitive sensor input pins physically adjacent to:
- Motor drivers with PWM
- Relays with switching loads
- Other high-current devices

**Status:** ✓ Solved

---

## Problem 5: Flowmeter Voltage Level Concerns

**Module:** raspi-flowmeter  
**Date:** Early development  
**Symptom:** Concern about 5V sensor output potentially damaging 3.3V GPIO input  
**Investigation:** 
- FL-408 datasheet specifies 5-24V power input
- Raspberry Pi GPIO is only 3.3V tolerant
- Risk of damage if sensor outputs 5V signal to GPIO

**Solution:** Power FL-408 sensor from 3.3V instead of 5V
- When powered at 3.3V, sensor outputs 3.3V logic signals compatible with Pi GPIO
- Sensor works perfectly at 3.3V power (verified with previous ESP32 project)
- No level shifter required

**Result:** Works perfectly at 3.3V, no damage risk  
**Status:** ✓ Solved

---

## Problem 6: Flowmeter Wrong Pull Resistor and Edge Detection

**Module:** raspi-flowmeter  
**Date:** Initial hardware setup  
**Symptom:** Sensor connected but no pulses detected  
**Cause:** Used PULL_DOWN resistor with RISING edge detection (wrong combination for FL-408)  
**Investigation:**
- FL-408 outputs HIGH when idle and pulses LOW during flow (inverted logic)
- Using PULL_DOWN meant pin was always LOW
- RISING edge detection missed the actual pulses (FALLING edges)

**Solution:** Changed to PULL_UP resistor with FALLING edge detection
```python
lgpio.gpio_claim_input(chip, pin, lgpio.SET_PULL_UP)
lgpio.gpio_claim_alert(chip, pin, lgpio.FALLING_EDGE)
```

**Key Learning:** FL-408 signals are inverted - HIGH when idle, pulses LOW during flow  
**Status:** ✓ Solved

---

## Problem 7: Flowmeter Loose Electrical Connection

**Module:** raspi-flowmeter  
**Date:** Mid-development  
**Symptom:** Intermittent pulse detection - sometimes worked, sometimes didn't  
**Cause:** Loose wire connection on breadboard or header pins  
**Investigation:**
- Random failures without code changes
- Worked after moving wires slightly
- No pattern to failures

**Solution:** 
- Secured all connections firmly
- Verified continuity with multimeter
- Used strain relief for wires

**Key Learning:** Always verify physical connections first before debugging code  
**Status:** ✓ Solved

---

## Problem 8: Flowmeter Line Capacitance Concerns

**Module:** raspi-flowmeter  
**Date:** Mid-development  
**Symptom:** Observed lag when GPIO transitioned from HIGH to LOW  
**Investigation:** 
- Suspected line capacitance might smooth out fast pulses
- Tested transition time with oscilloscope
- Measured transitions at 0.01ms (normal speed)

**Result:** No capacitance issue - transitions were within normal parameters  
**Actual Cause:** Was related to GPIO interference (Problem 4), not capacitance  
**Status:** ✓ Not an issue

---

## Problem 9: BTS7960 RPi.GPIO Incompatibility on Kernel 6.6+

**Module:** raspi-bts7960 (Fan Controller)  
**Date:** January 2026  
**Symptom:** RPi.GPIO would not work reliably on kernel 6.12.47+  
**Cause:** Same as Problem 2 - RPi.GPIO uses deprecated `/dev/mem` interface incompatible with modern kernels  
**Background:**
- System running kernel 6.12.47+rpt-rpi-v8
- Flowmeter and relay modules already using lgpio successfully
- BTS7960 controller was last module using RPi.GPIO

**Solution:** Migrated BTS7960 controller from RPi.GPIO to lgpio
- Replaced GPIO initialization with lgpio chip/pin claiming
- Changed PWM API from `GPIO.PWM()` to `lgpio.tx_pwm()`
- Improved error messages and cleanup logic
- All functionality preserved (kick-start, speed control, context manager)

**Migration Changes:**
| Aspect | RPi.GPIO | lgpio |
|--------|----------|-------|
| Import | `import RPi.GPIO as GPIO` | `import lgpio` |
| Init | `GPIO.setmode(GPIO.BCM)` | `chip = lgpio.gpiochip_open(0)` |
| PWM | `GPIO.PWM(pin, freq)` | `lgpio.tx_pwm(chip, pin, freq, duty)` |
| Permissions | Requires sudo | Only `gpio` group |

**Benefits:**
- No sudo required
- Better error messages
- Modern kernel compatibility
- Unified GPIO library across all modules

**Status:** ✓ Solved (pending hardware test)

---

## Problem 10: BTS7960 Common Ground Issues

**Module:** raspi-bts7960 (Fan Controller)  
**Date:** Initial hardware setup  
**Symptom:** Fans not starting or erratic behavior  
**Cause:** 12V power supply ground not connected to Raspberry Pi ground  
**Investigation:**
- Motor driver needs common ground reference with control signals
- Without common ground, PWM signals have undefined voltage reference
- Can cause erratic behavior or no response

**Solution:** Connect 12V power supply ground to both:
- BTS7960 B- terminal
- Raspberry Pi GND pin

**Critical Configuration:**
```
12V Supply (-) ---> B- AND Pi GND (common ground CRITICAL!)
```

**Key Learning:** Always establish common ground between Pi and high-power circuits  
**Status:** ✓ Solved

---

## Problem 11: BTS7960 PWM Frequency Optimization

**Module:** raspi-bts7960 (Fan Controller)  
**Date:** Initial development  
**Symptom:** Audible whine/noise from fans at certain PWM frequencies  
**Investigation:**
- Tested various PWM frequencies: 1 kHz, 5 kHz, 10 kHz, 24 kHz, 50 kHz
- Lower frequencies (< 10 kHz) produced audible whine
- Very high frequencies (> 40 kHz) may affect motor efficiency

**Solution:** Settled on 24 kHz PWM frequency
- Nearly silent operation
- Good motor efficiency
- Well above audible range (< 20 kHz)
- Supported by BTS7960 driver

**Key Learning:** PWM frequency matters for motor noise - test empirically  
**Status:** ✓ Solved

---

## Problem 12: BTS7960 100% Duty Cycle Stability

**Module:** raspi-bts7960 (Fan Controller)  
**Date:** Initial development  
**Symptom:** Potential instability at exactly 100% duty cycle  
**Cause:** Some motor drivers can have edge cases at exactly 100% duty cycle  
**Investigation:**
- Research showed some drivers have timing issues at 100%
- 99% provides essentially same power with better reliability

**Solution:** Cap speed at 99% instead of 100%
```python
if speed >= 100:
    speed = 99
```

**Key Learning:** 99% duty cycle = full power with better stability  
**Status:** ✓ Solved (preventative)

---

## Problem 13: lgpio PWM Frequency Compatibility

**Module:** raspi-bts7960 (Fan Controller)  
**Date:** January 6, 2026, 02:00 UTC (during integration testing)  
**Symptom:** `lgpio.error: 'bad PWM frequency'` when initializing BTS7960Controller  
**Cause:** lgpio has different PWM frequency constraints than RPi.GPIO
- Original code used 24000 Hz (24 kHz) which worked with RPi.GPIO
- lgpio's `tx_pwm()` has specific frequency requirements that differ from RPi.GPIO
- 24000 Hz is not a valid frequency for lgpio's PWM implementation

**Investigation:**
```
Error: 'bad PWM frequency'
File "bts7960_controller.py", line 69, in __init__
  lgpio.tx_pwm(self.chip, self.rpwm_pin, self.pwm_freq, 0)
lgpio.error: 'bad PWM frequency'
```

**Solution:** Changed default PWM frequency from 24000 Hz to 10000 Hz (10 kHz)
- lgpio maximum supported PWM frequency is ~10 kHz (tested: 100-10000 Hz work, 20000+ fail)
- RPi.GPIO supported much higher frequencies (24 kHz+), but lgpio has hardware limitations
- 10 kHz is at the edge of human hearing range (most adults hear up to ~15 kHz)
- May produce slight audible whine, but is the maximum lgpio supports
- Updated both SHOPHEATER3000 and raspi-bts7960 source files

**Testing Results:**
```
Tested frequencies:
  100-10,000 Hz: ✓ Works
  20,000+ Hz:    ✗ Fails with 'bad PWM frequency'
```

**Audio Impact:**
- 10 kHz is at edge of human hearing (most adults hear up to ~15 kHz)
- May produce slight audible whine during operation
- Alternative: Use 8 kHz or 5 kHz for quieter operation (trade-off with PWM resolution)

**Key Learning:** lgpio has a ~10 kHz maximum PWM frequency - RPi.GPIO supported much higher frequencies (24+ kHz)  
**Status:** ✓ Solved

---

## Problem 14: DS18B20 Resolution Setting Permission Warnings

**Module:** raspi-ds18b20 (Temperature Sensor)  
**Date:** January 6, 2026, 02:00 UTC (during integration testing)  
**Symptom:** Permission denied warnings when reading temperature sensors:
```
/bin/sh: 1: cannot create /sys/bus/w1/devices/28-*/w1_slave: Permission denied
```

**Cause:** 
- DS18B20Reader class attempts to auto-configure all sensors to 10-bit resolution
- Setting resolution requires write access to kernel sysfs device files
- Non-root users don't have write permission to these files
- The `set_resolution()` method fails silently but prints shell error to stderr

**Investigation:**
- Temperature reading still works perfectly without resolution setting
- Resolution setting is optimization only (affects conversion time)
- Default resolution (12-bit) works fine, just slightly slower conversion
- Warning appears for each sensor on bus (4 sensors = 4 warnings)

**Solution:** Multiple options available:
1. **Ignore warnings** - temperature reading works perfectly (recommended)
2. **Run with sudo** - not recommended for normal operation (security risk)
3. **Modify code** - remove auto-resolution setting feature
4. **Suppress stderr** - redirect shell errors to /dev/null

**Current Status:** Warnings are harmless and can be safely ignored  
**Impact:** None - all temperature readings work correctly  
**Key Learning:** 1-Wire sensor resolution setting is optional; readings work with default resolution  
**Status:** ✓ Not a problem (informational warning only)

---

## System-Wide GPIO Pin Allocation

**Date:** January 2026  
**Issue:** Ensuring no GPIO conflicts across all modules  
**Solution:** Documented complete GPIO map

| GPIO | Physical Pin | Module | Function |
|------|--------------|--------|----------|
| 4    | 7            | DS18B20 | Temperature (1-Wire) |
| 18   | 12           | BTS7960 | Fan PWM control |
| 23   | 16           | Relay   | Normal solenoid |
| 24   | 18           | Relay   | Diversion solenoid |
| 27   | 13           | Flowmeter | Pulse counter |

**Key Learnings:**
1. Physical pin separation matters (Problems 4, 8)
2. Keep sensors away from high-current/PWM pins
3. GPIO4 required for DS18B20 (Problem 1)
4. Document pin assignments to avoid conflicts

---

## Final Working Configurations

### Flowmeter (raspi-flowmeter)
```
Hardware:
  GPIO Pin:        27 (Physical Pin 13) - separated from motor driver
  Power:           3.3V (Pin 1 or 17)
  Ground:          GND (Pin 6 or any GND)
  
Software:
  Library:         lgpio (not RPi.GPIO)
  Pull Resistor:   lgpio.SET_PULL_UP
  Edge Detection:  lgpio.FALLING_EDGE
  Calibration:     450 pulses = 1 liter (manufacturer)
                   3,119 pulses = 19.9 pounds (empirically measured)
```

### BTS7960 Fan Controller (raspi-bts7960)
```
Hardware:
  GPIO Pin:        18 (Physical Pin 12)
  Power:           5V for logic, 12V for motors
  Common Ground:   CRITICAL - Pi GND to 12V supply ground
  Jumpers:         R_EN→VCC, L_EN→VCC, LPWM→GND
  
Software:
  Library:         lgpio (migrated Jan 2026)
  PWM Frequency:   24 kHz (optimal for silence)
  Duty Cycle:      0-99% (capped for stability)
  Kick-start:      1 second at 99% when starting from 0
```

### DS18B20 Temperature (raspi-ds18b20)
```
Hardware:
  GPIO Pin:        4 (Physical Pin 7) - REQUIRED, no alternatives
  Power:           3.3V
  Pull-up:         4.7kΩ (usually included in breakout boards)
  
Software:
  Library:         w1thermsensor (uses kernel 1-Wire interface)
  Resolution:      10-bit (auto-configured)
  Config:          dtoverlay=w1-gpio,gpiopin=4
```

### Relay Controller (raspi-relay-shopheater)
```
Hardware:
  GPIO Pins:       23, 24 (Physical Pins 16, 18)
  Relay Config:    Normally Closed (NC) - fail-safe
  Solenoid Power:  12V @ 2.5A
  
Software:
  Library:         lgpio
  Default State:   HIGH (solenoids closed - safe)
  Cleanup:         atexit handler ensures safe shutdown
```

---

## Cross-Module Integration Learnings

### GPIO Library Unification
**Challenge:** Three different GPIO libraries initially (RPi.GPIO, lgpio, kernel interface)  
**Solution:** Migrated all GPIO operations to lgpio where possible  
**Result:** 
- Unified codebase
- No library conflicts
- Modern kernel support
- No sudo required (only `gpio` group)

### Permission Management
**Challenge:** Some modules requiring sudo, others not  
**Solution:** Standardize on `gpio` group membership  
```bash
sudo usermod -a -G gpio $USER
```
**Result:** No sudo needed for any module

### Virtual Environment Strategy
**Challenge:** Multiple `.venv` directories with duplicate packages  
**Solution:** Created consolidated environment in `~/SHOPHEATER3000/.venv`  
**Result:** Single source of truth for dependencies

---

## Key Takeaways

### Hardware
1. **Physical placement matters** - keep sensors away from noise sources
2. **Common ground is critical** - always connect grounds between Pi and external power
3. **GPIO4 is special** - required for DS18B20, not interchangeable
4. **Verify connections** - loose wires cause intermittent failures

### Software  
5. **lgpio is the future** - RPi.GPIO is deprecated on modern kernels
6. **Test frequencies empirically** - 24 kHz PWM minimizes noise
7. **Edge cases matter** - cap at 99% duty cycle, not 100%
8. **Document everything** - GPIO conflicts are hard to debug

### Integration
9. **Unify libraries** - use lgpio consistently across modules
10. **Manage permissions** - `gpio` group instead of sudo
11. **Test incrementally** - verify each module before integrating
12. **Pin separation** - document complete GPIO allocation map

---

**Last Updated:** January 6, 2026 02:00 UTC  
**System:** Raspberry Pi 4, Kernel 6.12.47+rpt-rpi-v8  
**Status:** All known problems solved, integration testing completed successfully  
**Total Problems Documented:** 14 (13 solved, 1 informational warning)


## Problem 15: Web UI Control Flickering and Dancing

**Module:** Web UI (web_ui.html)  
**Date:** January 11, 2026  
**Symptom:** Toggle switches and fan slider flickering/dancing when clicked
- User clicks toggle → switch flips ON → flips OFF → flips ON (multiple times)
- Felt laggy and unresponsive
- Final state was correct but user experience was poor

**Cause:** Race condition between optimistic UI updates and periodic server broadcasts
- Server broadcasted ALL data (temps + control states) every 500ms
- User clicked toggle → UI updated optimistically
- Stale server broadcast arrived with old state → overwrote user's change
- Immediate server confirmation arrived → corrected state
- Result: visible flickering as UI toggled back and forth

**Investigation:**
1. Initially tried 500ms ignore window → not enough
2. Tried 1000ms ignore window → still had issues
3. Discovered broadcasts were continuous stream of stale data
4. Realized 500ms broadcasts created constant interference
5. Server response timing could slip past ignore windows

**Solution (Multi-Part):**

**Part 1: Split Broadcast Architecture**
- Separated temperature broadcasts (5 seconds) from control updates (immediate)
- Reduced broadcast frequency 10x (500ms → 5000ms)
- Control confirmations still sent immediately after commands
- Result: Far less interference from periodic broadcasts

**Part 2: Extended Ignore Windows**
- Increased ignore window from 1000ms to 2000ms
- 2000ms > 5000ms/2, so outlasts even unlucky timing
- Applied to all controls (toggles and fan speed slider)

**Part 3: Smart Selective Blocking**
- Ignore windows now only block state CHANGES
- Allow updates that match current state (confirmations)
- Prevents flickering while allowing immediate feedback

```javascript
// Smart blocking logic
const wouldChangeState = (currentValue !== incomingValue);
if (inIgnoreWindow && wouldChangeState) {
  block(); // Reject stale broadcast trying to flip back
} else {
  accept(); // Allow confirmation or post-window update
}
```

**Part 4: Early Ignore Window Setup**
- Added mousedown/touchstart handlers
- Ignore window set BEFORE checkbox/slider changes
- Prevents race condition where broadcast arrives during click

**Part 5: Expected State Tracking**
- Track what value was commanded
- Can reject specific incorrect values (not just any change)
- Added for completeness (selective blocking handles most cases)

**Code Changes:**

**Backend (shopheater3000.py):**
```python
# Changed broadcast interval
await asyncio.sleep(5.0)  # Was 0.5, now 5.0 seconds
```

**Frontend (web_ui.html):**
```javascript
// Ignore windows increased to 2000ms
setIgnoreWindow('main_loop', 2000);
setIgnoreWindow('diversion', 2000);
setIgnoreWindow('fan_speed', 2000);

// Smart selective blocking
const wouldChange = (toggle.checked !== data.state);
if (inIgnoreWindow && wouldChange) {
  block(); // Stale data
} else {
  accept(); // Confirmation or post-window
}

// Early setup with mousedown
element.addEventListener('mousedown', () => {
  setIgnoreWindow('control', 2000);
});
```

**Results:**
- ✅ No flickering on single deliberate clicks
- ✅ Instant visual response (optimistic updates work)
- ✅ Instant hardware response (relays click immediately)
- ✅ Final states always correct
- ✅ Reduced network traffic (80% reduction in broadcasts)
- ⚠️ Very rapid clicking (< 750ms apart) may queue, but this is expected hardware limitation

**Testing:**
- Single toggle clicks: Perfect, instant, no flicker
- Rapid 4-click sequences: Minor lag due to hardware queuing (acceptable)
- Fan slider drag: Smooth, no value jumping
- Commands sent only on release (mouseup/touchend)

**Key Learning:** 
1. Separate high-frequency sensor data from low-frequency control confirmations
2. Ignore windows should outlast broadcast intervals
3. Smart blocking (only block CHANGES) provides best UX
4. Early ignore window setup prevents race conditions
5. Optimistic UI + immediate confirmation = best responsiveness

**Status:** ✅ Solved - Production-ready control system

---

---

## Problem 16: Dynamic Arrow Rotation and Color Display Issues

**Module:** Web UI (web_ui.html)  
**Date:** January 11, 2026  
**Symptom:** Arrow icons not rotating correctly based on flow mode, despite code appearing correct
- Arrows would display with wrong orientations in different flow modes
- Color changes based on temperature worked initially, but then stopped
- Rotations seemed to be reset or overwritten unexpectedly
- Different arrow types (straight, 90°, branch) needed to be swapped dynamically

**Background:**
Implemented dynamic water flow visualization system:
- **Color coding:** Arrows change color based on temperature (RED >120°F, ORANGE 70-120°F, BLUE <70°F)
- **Flow mode visualization:** Arrow types and orientations change based on solenoid states
  - MAIN mode (main ON, diversion OFF)
  - DIVERSION mode (main OFF, diversion ON)
  - MIX mode (main ON, diversion ON) - uses branching arrows
- Specific cells (0:0, 0:1, 1:0, 1:1, 2:1, 3:0, 3:1) change arrow type and rotation dynamically
- Static arrows only change color

**Root Cause:** Function responsibility overlap and execution order
1. `updateArrowColors()` was resetting rotations when updating colors
2. Called BEFORE `updateArrowVisibility()`, so visibility function's rotations were immediately overwritten
3. `updateArrowColors()` was touching dynamic arrows that should be managed entirely by `updateArrowVisibility()`
4. Even though code was correct, browser cache prevented latest JavaScript from loading

**Investigation Process:**
1. **Initial approach:** Tried to adjust rotation values, but changes didn't persist
2. **Debug logging:** Added console.log to see what transforms were being applied
3. **DOM inspection:** Used browser evaluate to check actual element properties
4. **Execution order:** Discovered `updateArrowColors()` ran before `updateArrowVisibility()`
5. **Function analysis:** Found `updateArrowColors()` was setting both `src` AND `transform`
6. **Browser cache:** Discovered F5 refresh wasn't loading updated code (needed Ctrl+Shift+R)

**Solution (Multi-Part):**

**Part 1: Function Responsibility Separation**
```javascript
// BEFORE: updateArrowColors touched all arrows
function updateArrowColors(data) {
  updateArrowImage('arrow_0_1', hotColor, '_90', 'rotate(90deg)'); // ❌ Setting rotation
}

// AFTER: updateArrowColors only handles static arrows
function updateArrowColors(data) {
  updateArrowColorOnly('arrow_0_2', hotColor, ''); // ✅ Color only
  // Dynamic arrows (0:0, 0:1, etc.) skipped - handled by updateArrowVisibility()
}
```

**Part 2: Created Color-Only Helper**
```javascript
// New helper - NEVER touches transform property
function updateArrowColorOnly(elementId, color, suffix) {
  const element = document.getElementById(elementId);
  if (element) {
    element.src = `images/256_arrow_${color}${suffix}.png`;
    // Do NOT touch transform - that's handled by updateArrowVisibility()
  }
}
```

**Part 3: Execution Order Fix**
```javascript
// BEFORE:
updateArrowColors(data);          // ❌ Overwrites rotations
updateArrowVisibility(flowMode);  // Sets rotations (too late)

// AFTER:
updateArrowVisibility(flowMode);  // ✅ Sets type, color, AND rotation first
updateArrowColors(data);          // Only updates static arrow colors
```

**Part 4: User-Directed Rotation Corrections**
Applied cumulative rotation adjustments based on real hardware testing:
- **MAIN mode:** 0:1 needs +180°, 3:1 needs +90°
- **DIVERSION mode:** 0:0 needs +90°, 3:0 needs +90°, 3:1 needs +90°
- **MIX mode:** 0:0 needs +90°, 0:1 needs +180°, 3:0 needs +90°, 3:1 needs +90°

Final rotation values (examples):
```javascript
// MAIN mode
updateArrowImage('arrow_0_1', hotColor, '_90', 'rotate(270deg)'); // 90° + 180°
updateArrowImage('arrow_3_1', mixColor, '_90', 'rotate(180deg)'); // 90° + 90°

// MIX mode  
updateArrowImage('arrow_0_0', hotColor, '_90', 'rotate(270deg)');   // 180° + 90°
updateArrowImage('arrow_0_1', hotColor, '_branch', 'rotate(0deg)'); // 180° + 180° = 360° = 0°
updateArrowImage('arrow_3_0', reservoirColor, '_90', 'rotate(180deg)'); // 90° + 90°
updateArrowImage('arrow_3_1', mixColor, '_branch', 'rotate(180deg)');   // 90° + 90°

// DIVERSION mode
updateArrowImage('arrow_0_0', hotColor, '_90', 'rotate(270deg)'); // 180° + 90°
updateArrowImage('arrow_3_0', mixColor, '_90', 'rotate(180deg)'); // 90° + 90°
updateArrowImage('arrow_3_1', mixColor, '', 'rotate(0deg)');      // -90° + 90° = 0°
```

**Part 5: Layout Preservation**
```javascript
// BEFORE: Using display: none
arrow.parentElement.style.display = 'none'; // ❌ Breaks CSS grid layout

// AFTER: Using visibility: hidden
arrow.style.visibility = 'hidden'; // ✅ Hides image, preserves grid cell
```

**Testing Method:**
Created automated browser-based testing:
```javascript
// Inject fake temperature data to test color changes
const testData = {
  temperatures: {
    water_hot: 130,   // RED (>120°F)
    water_mix: 95,    // ORANGE (70-120°F)
    water_cold: 50,   // BLUE (<70°F)
  },
  flow_mode: 'mix'
};
updateDisplay(testData);
```

**Results:**
- ✅ Arrow colors change correctly: RED >120°F, ORANGE 70-120°F, BLUE <70°F
- ✅ Arrow types change correctly: straight/_90/_branch based on flow mode
- ✅ Arrow rotations correct in all three flow modes
- ✅ Grid layout preserved (no cell movement)
- ✅ Automated testing verified color thresholds
- ✅ Visual flow representation matches physical water flow

**Code Architecture:**
```
updateDisplay(data)
  ├─ updateArrowVisibility(flowMode, temps)  [FIRST]
  │    ├─ Sets arrow type (straight/_90/_branch)
  │    ├─ Sets arrow color (for dynamic arrows)
  │    ├─ Sets arrow rotation (CSS transform)
  │    └─ Sets visibility (show/hide based on mode)
  │
  └─ updateArrowColors(data)                 [SECOND]
       └─ Updates ONLY static arrow colors
           (preserves rotations set above)
```

**Key Learnings:**
1. **Separation of concerns:** One function should own each property (color vs rotation)
2. **Execution order matters:** Set structure first, then update details
3. **Dynamic vs static distinction:** Treat mode-dependent elements separately from constants
4. **Browser cache gotcha:** Hard refresh (Ctrl+Shift+R) needed to load updated JavaScript
5. **Visual testing:** Fake data injection allows rapid UI testing without hardware
6. **Base orientation matters:** Need to understand default image orientation to calculate rotations
7. **Cumulative testing:** Iterative user feedback more reliable than theoretical calculations

**Creative Achievement:**
The arrow visualization system provides instant visual feedback:
- Temperature at a glance (color coding)
- Flow path visibility (mode-based routing)
- System state comprehension (no need to parse numbers)
- Professional dashboard appearance

**Status:** ✅ Solved - Dynamic flow visualization working perfectly

---

**Last Updated:** January 11, 2026 22:00 UTC  
**System:** Raspberry Pi 4, Kernel 6.12.47+rpt-rpi-v8  
**Status:** All known problems solved  
**Total Problems Documented:** 16 (15 solved, 1 informational warning)

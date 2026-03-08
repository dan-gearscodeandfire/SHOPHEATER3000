# SHOPHEATER3000

Integrated shop heater control system combining multiple Raspberry Pi GPIO modules with real-time web interface.

**Created:** January 6, 2026  
**Last Updated:** March 2, 2026  
**Status:** ✅ Production-ready with automatic control, dynamic UI, data logging, and historical analysis tools

---

## ⚠️ CRITICAL SAFETY REQUIREMENT

**NEVER close both solenoid valves simultaneously!**

- **At least ONE valve must ALWAYS be open** (Main Loop OR Diversion OR Both)
- Closing both valves creates a dangerous error state with no circulation path
- Can cause pump damage, pressure buildup, or system failure

**System Protections:**
- ✅ Server startup defaults to BOTH valves OPEN (safe state)
- ✅ Automatic safety override prevents both valves from closing
- ✅ If attempting to close one valve while the other is closed, the system automatically opens the other valve

**Valid Configurations:**
- ✅ Main Loop ON, Diversion OFF (main mode)
- ✅ Main Loop OFF, Diversion ON (diversion mode)
- ✅ Main Loop ON, Diversion ON (mix mode)
- ❌ Main Loop OFF, Diversion OFF (**DANGEROUS - PREVENTED BY SYSTEM**)

---

## Quick Navigation

**⚠️ SAFETY FIRST:**
- [Critical Safety Requirement](#️-critical-safety-requirement) - **READ THIS FIRST**

**Getting Started:**
- [Overview](#overview) - System overview
- [Web UI Quick Start](#web-ui-quick-start) - Get the interface running
- [Automatic Control Mode](#automatic-control-mode) - Fan/valve automation logic and thresholds
- [Setup Instructions](#setup-instructions) - Hardware and software setup

**Documentation:**
- [PROBLEMS_SOLVED.md](PROBLEMS_SOLVED.md) - Complete troubleshooting history
- [TODO.md](TODO.md) - User-directed task list
- [UI_REORGANIZATION.md](UI_REORGANIZATION.md) - UI structure and data management
- [ARROW_ROTATIONS.md](ARROW_ROTATIONS.md) - Visual flow diagram logic

---

## Overview

This project integrates four separate codebases into a unified shop heater control system with real-time web interface.

**Hardware Modules:**
1. **raspi-bts7960** - Legacy fan control module (kept for historical reference)
2. **raspi-ds18b20** - Temperature sensing (1-Wire sensors)
3. **raspi-flowmeter** - Water flow measurement (pulse counter)
4. **raspi-relay-shopheater** - Solenoid valve control (relay switching)

**Key Features:**
- **Automatic Control Mode:**
  - Closed-loop fan and valve control with predictive safety logic
  - Fans OFF until shop air is warm (comfort gate), then 5V, escalating to 12V
  - Automatic diversion when predicted water temperature approaches unsafe levels
  - Emergency flow-collapse detection with immediate protective response
  - Live status panel on Controls page showing predictions, decisions, and timers
- **Multi-Page Web UI:**
  - Dashboard: Real-time monitoring with dynamic visual flow diagram
  - Controls: Dedicated control interface for solenoids, fan, and modes (Manual/Automatic)
  - Live Graph: Dynamic charting of selected parameters
  - Data Explorer: Browse and manage historical data sessions
- **Dynamic Visual System:**
  - Color-coded arrows based on water temperature (Red >120°F, Orange 70-120°F, Blue <70°F)
  - Flow path visualization adapts to main/diversion/mix modes
  - Temperature displays styled with matching color scheme
- **Data Management:**
  - Session-based data logging (CSV) with 5-second sampling
  - Live graphing with selectable parameters
  - Historical session replay and analysis
  - Delete and download capabilities
- **Optimized Performance:**
  - Optimistic UI updates for instant control response (500ms ignore windows)
  - Split broadcast architecture (5s temps, instant controls)
  - WebSocket communication for real-time updates

---

## Web UI Quick Start

### 1. Start the Server

\`\`\`bash
cd ~/SHOPHEATER3000
source .venv/bin/activate
python shopheater3000.py
\`\`\`

> **🔄 DEFAULT STATE:** Server starts with **BOTH valves OPEN** (mix mode) as a safety measure.  
> This ensures water always has a circulation path. Adjust via Controls page as needed.

### 2. Access the Web UI

The server automatically binds to all network interfaces (`0.0.0.0`), making it accessible from any device on your local network.

**On the Raspberry Pi:**
- Dashboard: http://localhost:8000
- Controls: http://localhost:8000/controls
- Live Graph: http://localhost:8000/graph
- Data Explorer: http://localhost:8000/explorer
- Advanced Analysis: http://localhost:8000/advanced

**From other devices on your LAN:**
- Find your Pi's IP address (shown in server startup message, or run `hostname -I`)
- Access: http://[raspberry-pi-ip]:8000
- Example: http://192.168.1.168:8000
- All pages work the same: `/controls`, `/graph`, `/explorer`, `/advanced`

**Note:** The server startup message will display both localhost and LAN IP addresses for easy access.

---

## Web UI Features

### Dashboard (Main Page)
**Real-Time Monitoring (updates every 5 seconds):**
- 6 temperature sensors with calibration offsets, color-coded by temperature
- 3 calculated temperature deltas
- Flow rate (L/min)
- Current fan mode/voltage (`OFF`, `5V`, `12V`)
- Dynamic visual flow diagram with color-coded arrows
- Reservoir image changes color based on temperature (blue/orange/red)

**Visual Flow Modes:**
- **Main Mode:** Water flows through main loop (hot water path)
- **Diversion Mode:** Water bypasses heat exchanger (cooling path)
- **Mix Mode:** Water flows through both paths simultaneously
- Arrows automatically show/hide and rotate based on solenoid states
- Arrow colors match water temperature in each section

### Controls Page
**User Controls (instant response, 500ms latency):**
- Mode selector (Manual/Automatic)
- Main loop solenoid toggle
- Diversion solenoid toggle
- Fan mode buttons: `OFF`, `5V`, `12V`
- Data logging toggle (Save button)
- Live graphing toggle (Graph button)

**Automatic Mode Status Panel (visible in Automatic mode):**
- Predicted hot water temperature (30s lookahead)
- Current automatic fan target (`OFF`, `5V`, `12V`)
- Diversion latch state (`ENGAGED` / `CLEAR`)
- Return-to-main countdown timer
- Human-readable decision reason

**Optimistic UI Updates:**
- Controls respond instantly to user input
- Smart ignore windows (500ms) prevent flickering
- Server confirmations reconcile state automatically

### Live Graph Page
**Dynamic Charting:**
- Select parameters via checkboxes:
  - All 6 temperatures (Hot, Cool, Mix, Reservoir, Air In, Air Out)
  - All 3 temperature deltas
  - Flow rate
  - Fan speed
- X-axis: Time elapsed since graphing started
- Updates every 5 seconds
- Auto-scaling and legend
- Chart.js powered visualization

### Data Explorer Page
**Session Management:**
- Browse saved data logging sessions (CSV files)
- View historical graph sessions with interactive replay
- Download CSV logs for external analysis
- Delete old sessions with confirmation
- Metadata display (timestamp, duration, data points, file size)
- All files timestamped to session start time

**Data Organization:**
- CSV logs stored in `data_logs/` subdirectory
- Graph sessions stored in `graph_sessions/` subdirectory
- Independent Save and Graph functionality
- In-memory data collection, saved on server shutdown or manual save

### Advanced Analysis Page
**Correlation & Visualization Tool:**
- Load historical CSV sessions or stream live data
- Configurable X/Y axes - plot any parameter against any other
- Multi-series support - overlay multiple Y-axis parameters
- Scatter plots (X = parameter) or time series (X = time)

**Filters:**
- Fan voltage range (min/max)
- Flow mode selection (main, diversion, mix, none)

**Analysis Features:**
- Linear regression trendlines with R² correlation coefficient
- Toggle between all data points or averaged values
- Export filtered data as new CSV file

**Example Use Cases:**
- Fan Voltage vs Delta Radiator: "How does `0V/5V/12V` fan operation affect heat transfer?"
- Delta Heater vs Delta Radiator (filtered by fan voltage): "At 5V fan, how does heater input relate to output?"
- Time vs Multiple Temperatures: "How do all temps change over a session?"

See [UI_REORGANIZATION.md](UI_REORGANIZATION.md) for detailed architecture documentation.

---

## Automatic Control Mode

Toggle between **Manual** and **Automatic** on the Controls page. In Automatic mode, fan speed and valve state are managed by the server; manual WebSocket commands for those controls are ignored.

### Fan Logic (Comfort + Safety)

| Condition | Fan Mode | Notes |
|-----------|----------|-------|
| `air_heated < 60°F` **and** `delta_air <= 10°F` | **OFF** | Comfort gate: avoid blowing cold air |
| `target=OFF` and `water_hot > 100°F` | **5V probe pulse** | Run 5V for 15s every 60s to refresh `delta_air` |
| Comfort gate met | **5V** | Default low-speed once air is warm |
| `predicted_hot >= 183°F`, or `water_hot >= 175°F`, or `delta_heater >= 45°F`, or `rate(delta_heater) >= 10°F/min` | **12V** | Predictive safety escalation |
| Emergency flow collapse (`flow < 0.5 GPM` at `hot >= 170°F`) | **12V** | Immediate protective response |

**Downshift behavior:** When temperatures are rising, fan transitions happen immediately (chatter is acceptable). When cooling, downshifts are held for 25 seconds to avoid relay chatter.

**Anti-boil pulse:** If fan target is OFF but predicted hot is near 175°F, a brief 5V pulse fires every 20 seconds.

### Valve Logic (Overheat Protection)

| Condition | Valve State | Notes |
|-----------|-------------|-------|
| Normal operation | **Main-only** | Shop heating through radiator |
| `predicted_hot >= 193°F`, or `water_hot >= 193°F`, or emergency flow collapse | **Diversion-only** | Bypass radiator to cool water through reservoir |
| Diversion latched, `water_hot < 180°F` sustained, trends declining | Countdown starts (120s) | Return timer shown on Controls page |
| Return timer expires with stable cooldown | **Main-only** | Resume shop heating |

### Predictive Model

The controller computes `predicted_hot` using a 30-second lookahead from two signals:
1. **Rate of change of `water_hot`** over the last 60 seconds
2. **Projected hot from heater lift:** `water_cold + delta_heater + rate(delta_heater) * 0.5 min`

The higher of the two projections is used. This catches both steady temperature climbs and rapid fire-intensity ramps before they reach dangerous levels.

### Atmospheric Boundary Note

The system operates with atmospheric boundaries:
- The standpipe is open to atmosphere
- The reservoir diversion loop is also open to atmosphere when diversion is active

Because of this, there is no pressurized boiling margin in those paths. Local boiling can begin in the heater coil before bulk temperature sensors show extreme values. For this reason, the automatic controller prioritizes predictive triggers and flow-collapse detection instead of waiting for `water_hot` near 200°F.

### Configurable Thresholds

All thresholds are class constants in `ShopHeaterController`:

| Constant | Default | Purpose |
|----------|---------|---------|
| `AUTO_FAN_WARM_AIR_F` | 60°F | Comfort gate: minimum air temp to turn fans on |
| `AUTO_FAN_WARM_DELTA_AIR_F` | 10°F | Comfort gate: minimum delta-air to turn fans on |
| `AUTO_FAN_PREDICTIVE_12V_F` | 183°F | Predicted hot threshold for 12V escalation |
| `AUTO_VALVE_PREDICTIVE_DIVERSION_F` | 193°F | Predicted hot threshold to force diversion |
| `AUTO_VALVE_RETURN_HOT_F` | 180°F | Hot temp must drop below this to begin return timer |
| `AUTO_VALVE_RETURN_HOLD_S` | 120s | Sustained cooldown duration before returning to main |
| `AUTO_COOLDOWN_DOWNSTEP_HOLD_S` | 25s | Cooling-phase hysteresis before fan downshift |
| `AUTO_AIR_PROBE_MIN_HOT_F` | 100°F | Minimum hot temp to start air-delta probe pulses |
| `AUTO_AIR_PROBE_INTERVAL_S` | 60s | Time between OFF-state air probe pulses |
| `AUTO_AIR_PROBE_DURATION_S` | 15s | 5V duration for each air probe pulse |

---

## GPIO Pin Allocation

| GPIO | Pin | Module | Function |
|------|-----|--------|----------|
| 4    | 7   | DS18B20 | Temperature (1-Wire, required) |
| 18   | 12  | Relay | Fan ON/OFF relay (`LOW` NC = ON, `HIGH` NO = OFF) |
| 17   | 11  | Relay | Fan supply select (`LOW` NC = 12V, `HIGH` NO = 5V) |
| 23   | 16  | Relay | Normal flow solenoid |
| 24   | 18  | Relay | Diversion flow solenoid |
| 27   | 13  | Flowmeter | Pulse counter |

**No conflicts** - all modules use separate GPIO pins.

### Fan Relay Logic (Intentional Fail-Safe)

- **Default NC behavior is intentional:** if relays drop to NC, fans run at **12V**.
- `GPIO18` (fan ON/OFF relay):
  - `LOW` (NC): fans ON
  - `HIGH` (NO): fans OFF
- `GPIO17` (voltage select relay):
  - `LOW` (NC): 12V supply
  - `HIGH` (NO): 5V supply
- Fan modes:
  - `OFF` = `GPIO18 HIGH` (voltage relay unchanged)
  - `5V` = `GPIO17 HIGH` and `GPIO18 LOW`
  - `12V` = `GPIO17 LOW` and `GPIO18 LOW`

> **Legacy note:** BTS7960 PWM control is retained in this repo for history/reference.  
> In this heater application, the PWM driver did not interact well with the fans' internal BLDC driver, so control moved to relay-selected OFF/5V/12V.

---

## Dependencies

\`\`\`
lgpio==0.2.2.0           # GPIO library (kernel 6.6+ compatible)
w1thermsensor==2.3.0     # DS18B20 temperature sensors
fastapi==0.109.0         # Web framework
uvicorn==0.27.0          # ASGI server
websockets==12.0         # WebSocket support
pillow>=10.0.0           # Image processing (for dynamic UI assets)
\`\`\`

**Why lgpio?**
- RPi.GPIO is broken on kernel 6.6+
- lgpio uses modern \`/dev/gpiochip\` interface
- No sudo required (only \`gpio\` group membership)

---

## Setup Instructions

### 1. Verify GPIO Permissions

\`\`\`bash
groups | grep gpio
\`\`\`

If not in gpio group:
\`\`\`bash
sudo usermod -a -G gpio $USER
# Log out and back in
\`\`\`

### 2. Activate Virtual Environment

\`\`\`bash
cd ~/SHOPHEATER3000
source .venv/bin/activate
\`\`\`

### 3. Install Dependencies

\`\`\`bash
pip install -r requirements.txt
\`\`\`

---

## Integration Example

\`\`\`python
#!/usr/bin/env python3
from fan_relay_controller import FanRelayController
from ds18b20_reader import DS18B20Reader
from flowmeter import FlowMeter
from relay_control import RelayController

# Initialize all modules
fan = FanRelayController(fan_onoff_pin=18, voltage_select_pin=17)
temp_reader = DS18B20Reader()
flow_meter = FlowMeter(gpio_pin=27)
valve_control = RelayController()

try:
    # Set initial state
    valve_control.mainLoop()
    fan.set_mode("12v")
    
    # Your control logic here
    
finally:
    # Always cleanup
    fan.cleanup()
    flow_meter.cleanup()
    valve_control.cleanup()
\`\`\`

See \`example_integration.py\` for a complete working example.

---

## Troubleshooting

### Common Issues

**"Failed to open GPIO chip"**
- Solution: \`sudo usermod -a -G gpio $USER\` and log out/in

**"GPIO pin already in use"**
- Solution: \`ps aux | grep python\` to find process, then \`kill [PID]\`

**"bad PWM frequency"**
- lgpio max: 10 kHz (vs RPi.GPIO 24+ kHz)
- Try 5-8 kHz for quieter operation

**Temperature sensor permission warnings**
- These are harmless - readings work perfectly

**Web UI control flickering/latency**
- ✅ SOLVED (Jan 11, 2026, optimized Jan 15, 2026)
- See PROBLEMS_SOLVED.md Problem #15
- Optimized ignore windows (500ms) for fast response

**Port 8000 in use**
- Solution: \`lsof -i :8000\` then \`kill [PID]\`

**WebSocket won't connect**
- Check server is running
- Try: \`http://localhost:8000\`
- Check firewall: \`sudo ufw allow 8000/tcp\`

---

## File Structure

\`\`\`
~/SHOPHEATER3000/
├── .venv/                          # Virtual environment
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
│
├── README.md                       # This file
├── PROBLEMS_SOLVED.md              # Troubleshooting history
├── TODO.md                         # User task list
├── UI_REORGANIZATION.md            # UI structure documentation
├── ARROW_ROTATIONS.md              # Visual flow diagram logic
├── IMPLEMENTATION_SUMMARY.md       # UI improvements summary
│
├── fan_relay_controller.py         # Active fan relay controller (OFF/5V/12V)
├── bts7960_controller.py           # Legacy PWM fan controller (historical)
├── ds18b20_reader.py               # Temperature sensors
├── flowmeter.py                    # Flow meter
├── relay_control.py                # Relay control
│
├── shopheater3000.py               # Main web server (FastAPI + WebSocket + automatic control)
├── web_ui.html                     # Dashboard (monitoring only)
├── controls.html                   # Controls page (solenoids, fan, modes, auto status)
├── graph.html                      # Live graphing page
├── explorer.html                   # Data explorer page
│
├── images/                         # UI assets
│   ├── 256_*.png                   # Static icons (reservoir, solenoids, etc.)
│   ├── *_blue.png                  # Blue arrows (cold water)
│   ├── *_orange.png                # Orange arrows (warm water)
│   ├── *_red.png                   # Red arrows (hot water)
│   ├── *_90.png                    # 90-degree turn arrows
│   └── *_branch.png                # Branching arrows (mix mode)
│
├── data_logs/                      # Saved CSV data logs
│   ├── .gitkeep                    # Keep directory in Git
│   └── session_YYYY-MM-DD_HH-MM-SS.csv
│
├── graph_sessions/                 # Saved graph sessions (JSON)
│   ├── .gitkeep                    # Keep directory in Git
│   └── graph_YYYY-MM-DD_HH-MM-SS.json
│
├── create_reservoir_colors.py     # Script to generate colored reservoir images
├── example_integration.py          # Integration example
└── verify_setup.py                 # Setup checker
\`\`\`

---

## Technical Specifications

- **Platform:** Raspberry Pi 4
- **OS:** Raspberry Pi OS (kernel 6.12.47+)
- **Python:** 3.11+
- **GPIO Library:** lgpio 0.2.2.0
- **Web Framework:** FastAPI with WebSocket
- **Frontend:** Vanilla JavaScript with Chart.js for graphing
- **Update Rates:**
  - Temperature broadcasts: 5 seconds
  - Control confirmations: Immediate
  - UI ignore windows: 500ms (optimized for responsiveness)
  - Data collection: 5 seconds (when enabled)
  - Graph updates: 5 seconds (when enabled)
- **Data Storage:**
  - CSV logs: `data_logs/` subdirectory
  - Graph sessions: `graph_sessions/` subdirectory (JSON)
  - Timestamped filenames for session tracking
- **Safety Features:**
  - **Startup Default:** Both valves OPEN (mix mode) - ensures safe circulation path
  - **Automatic Override:** Prevents both valves from closing simultaneously
  - **Flow Monitoring:** Real-time flow mode calculation (main/diversion/mix/none)
  - **Automatic Mode:** Predictive fan/valve control prevents overheating and boiling
  - **Emergency Flow Collapse:** Immediate diversion + 12V fan on low-flow at high temp
  - **Anti-Boil Pulse:** Brief fan activation when near risk threshold

---

## Changelog

### 2026-03-02 (Automatic Control Mode)
- **Automatic Fan Control:**
  - Comfort gate: fans OFF until air >= 60°F or delta_air > 10°F, then 5V
  - OFF-state air probe: 5V for 15s every 60s when hot > 100°F
  - Predictive 12V escalation when predicted hot nears 183°F
  - Emergency 12V on flow collapse (< 0.5 GPM at >= 170°F)
  - Cooling-phase downshift hysteresis (25s hold); rising allows immediate chatter
  - Anti-boil pulse: brief 5V every 20s when OFF but near 175°F predicted
- **Automatic Valve Control:**
  - Force diversion-only when predicted/actual water_hot >= 193°F
  - Return to main-only after sustained cooldown below 180°F for 120s
  - Return timer resets if temperatures rise again or trends reverse
- **Controls Page:**
  - Automatic status panel shows predicted hot, fan target, diversion latch, return timer, and decision reason
  - Fan, solenoid, and valve controls disabled (read-only) in automatic mode
  - WebSocket commands for fan/valve ignored server-side in automatic mode
- **Backend:**
  - `run_automatic_control()` runs every 5s via dedicated async loop
  - 60-second rolling history for rate-of-change calculations
  - Dual predictive model: hot trend + heater-lift projection
  - All thresholds exposed as class constants for tuning

### 2026-01-22 (Critical Safety & Arrow Corrections)
- **⚠️ SAFETY REQUIREMENT IMPLEMENTED:**
  - Added critical safety requirement: At least ONE valve must ALWAYS be open
  - **Server startup defaults changed: Both valves now default to OPEN (mix mode)**
  - Automatic safety override: Prevents both valves from closing simultaneously
  - If attempting to close one valve while other is closed, system auto-opens the other
- **Visual Flow Corrections:**
  - Fixed 90° arrow base image orientations (blue and orange images rotated to match red)
  - Corrected arrow rotations for cells 0:0, 0:1, 0:5, 3:0, 3:1, 3:5 across all flow modes
  - All arrows now display correct flow direction in main, diversion, and mix modes
  - Verified arrow orientation matches physical plumbing configuration
- **Documentation:**
  - Added prominent safety warning section in README
  - Updated technical specifications with safety features
  - Added safety notes to Quick Navigation

### 2026-01-15 (Data Management & UI Reorganization)
- **UI Reorganization:**
  - Split interface into 4 dedicated pages (Dashboard, Controls, Graph, Explorer)
  - Main page now monitoring-only with navigation links
  - Controls moved to dedicated page with optimized responsiveness
  - Reduced ignore windows from 2000ms → 500ms for faster control response
- **Data Logging:**
  - Toggle-activated CSV logging with 5-second sampling
  - Saves all temperatures, deltas, flow rate, fan, and solenoid states
  - Timestamped filenames based on session start time
  - Organized into `data_logs/` subdirectory
- **Live Graphing:**
  - Toggle-activated graphing with Chart.js
  - Selectable parameters via checkboxes
  - Real-time updates every 5 seconds
  - Time-based X-axis from session start
- **Data Explorer:**
  - Browse saved CSV logs and graph sessions
  - View historical graph sessions with interactive replay
  - Download CSV files for external analysis
  - Delete old sessions with confirmation dialogs
  - Metadata display (timestamp, duration, data points, size)
- **Architecture:**
  - Independent Save and Graph functionality
  - In-memory data collection, persistent on shutdown
  - JSON storage for graph sessions
  - Session-based data management

### 2026-01-14 (Dynamic Visual System)
- **Temperature-Based Coloring:**
  - Dynamic arrow colors based on water temperature
  - Red >120°F, Orange 70-120°F, Blue <70°F
  - Temperature text displays match arrow colors
  - Font size doubled (56px) for better visibility
- **Flow Mode Visualization:**
  - Server-side flow_mode tracking (main/diversion/mix)
  - Arrows show/hide based on solenoid states
  - Automatic rotation for correct flow direction
  - Branching arrows for mix mode
  - 3 distinct flow patterns with proper arrow routing
- **Visual Enhancements:**
  - Dynamic reservoir image (blue/orange/red water)
  - Removed unit labels (F, L/min) for cleaner display
  - Relocated reservoir image and temperature display
  - CSS visibility instead of display:none to preserve grid layout
- **Documentation:**
  - Created ARROW_ROTATIONS.md for rotation logic
  - Created IMPLEMENTATION_SUMMARY.md for UI overview
  - Updated PROBLEMS_SOLVED.md with extensive debugging history

### 2026-01-11 (UI Optimization)
- Fixed control flickering with optimistic UI updates
- Split broadcast: 5s temps, immediate controls
- Smart ignore windows (2s) with selective blocking
- Applied to toggles and fan speed slider
- Result: Bulletproof, instant-response controls

### 2026-01-09 (Web UI)
- Real-time FastAPI + WebSocket interface
- 6 temperature sensors + 3 deltas
- User controls for valves and fan
- Visual flow diagram

### 2026-01-06 (Initial Integration)
- Consolidated 4 codebases
- Migrated to lgpio for kernel 6.6+ support
- Unified virtual environment
- All modules tested and working

---

**Last Updated:** March 2, 2026  
**System Status:** ✅ Production-ready with automatic control, full data logging, graphing, historical analysis, and critical safety features

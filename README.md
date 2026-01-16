# SHOPHEATER3000

Integrated shop heater control system combining multiple Raspberry Pi GPIO modules with real-time web interface.

**Created:** January 6, 2026  
**Last Updated:** January 15, 2026  
**Status:** ✅ Production-ready with dynamic UI, data logging, and historical analysis tools

---

## Quick Navigation

**Getting Started:**
- [Overview](#overview) - System overview
- [Web UI Quick Start](#web-ui-quick-start) - Get the interface running
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
1. **raspi-bts7960** - Fan speed control (PWM motor driver)
2. **raspi-ds18b20** - Temperature sensing (1-Wire sensors)
3. **raspi-flowmeter** - Water flow measurement (pulse counter)
4. **raspi-relay-shopheater** - Solenoid valve control (relay switching)

**Key Features:**
- **Multi-Page Web UI:**
  - Dashboard: Real-time monitoring with dynamic visual flow diagram
  - Controls: Dedicated control interface for solenoids, fan, and modes
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

### 2. Access the Web UI

- **On the Raspberry Pi:**
  - Dashboard: http://localhost:8000
  - Controls: http://localhost:8000/controls
  - Live Graph: http://localhost:8000/graph
  - Data Explorer: http://localhost:8000/explorer
- **From another device:** http://[raspberry-pi-ip]:8000 (and /controls, /graph, /explorer)

---

## Web UI Features

### Dashboard (Main Page)
**Real-Time Monitoring (updates every 5 seconds):**
- 6 temperature sensors with calibration offsets, color-coded by temperature
- 3 calculated temperature deltas
- Flow rate (L/min)
- Current fan speed
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
- Fan speed slider (0-100) and text input
- Data logging toggle (Save button)
- Live graphing toggle (Graph button)

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

See [UI_REORGANIZATION.md](UI_REORGANIZATION.md) for detailed architecture documentation.

---

## GPIO Pin Allocation

| GPIO | Pin | Module | Function |
|------|-----|--------|----------|
| 4    | 7   | DS18B20 | Temperature (1-Wire, required) |
| 18   | 12  | BTS7960 | Fan PWM control |
| 23   | 16  | Relay   | Normal flow solenoid |
| 24   | 18  | Relay   | Diversion flow solenoid |
| 27   | 13  | Flowmeter | Pulse counter |

**No conflicts** - all modules use separate GPIO pins.

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
from bts7960_controller import BTS7960Controller
from ds18b20_reader import DS18B20Reader
from flowmeter import FlowMeter
from relay_control import RelayController

# Initialize all modules
fan = BTS7960Controller()
temp_reader = DS18B20Reader()
flow_meter = FlowMeter(gpio_pin=27)
valve_control = RelayController()

try:
    # Set initial state
    valve_control.mainLoop()
    fan.set_speed(50)
    
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
├── bts7960_controller.py           # Fan controller
├── ds18b20_reader.py               # Temperature sensors
├── flowmeter.py                    # Flow meter
├── relay_control.py                # Relay control
│
├── shopheater3000.py               # Main web server (FastAPI + WebSocket)
├── web_ui.html                     # Dashboard (monitoring only)
├── controls.html                   # Controls page (solenoids, fan, modes)
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

---

## Changelog

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

**Last Updated:** January 15, 2026  
**System Status:** ✅ Production-ready with full data logging, graphing, and historical analysis capabilities

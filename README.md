# SHOPHEATER3000

Integrated shop heater control system combining multiple Raspberry Pi GPIO modules with real-time web interface.

**Created:** January 6, 2026  
**Last Updated:** January 11, 2026  
**Status:** ✅ All modules operational, Web UI optimized with bulletproof control system

---

## Quick Navigation

**Getting Started:**
- [Overview](#overview) - System overview
- [Web UI Quick Start](#web-ui-quick-start) - Get the interface running
- [Setup Instructions](#setup-instructions) - Hardware and software setup

**Documentation:**
- [PROBLEMS_SOLVED.md](PROBLEMS_SOLVED.md) - Complete troubleshooting history
- [TODO.md](TODO.md) - User-directed task list

---

## Overview

This project integrates four separate codebases into a unified shop heater control system with real-time web interface.

**Hardware Modules:**
1. **raspi-bts7960** - Fan speed control (PWM motor driver)
2. **raspi-ds18b20** - Temperature sensing (1-Wire sensors)
3. **raspi-flowmeter** - Water flow measurement (pulse counter)
4. **raspi-relay-shopheater** - Solenoid valve control (relay switching)

**Key Features:**
- Real-time web interface with WebSocket communication
- Optimistic UI updates for instant control response  
- Split broadcast architecture (5s temps, instant controls)
- Smart ignore windows prevent UI flickering
- Manual and automatic control modes

---

## Web UI Quick Start

### 1. Start the Server

\`\`\`bash
cd ~/SHOPHEATER3000
source .venv/bin/activate
python shopheater3000.py
\`\`\`

### 2. Access the Web UI

- **On the Raspberry Pi:** http://localhost:8000
- **From another device:** http://[raspberry-pi-ip]:8000

---

## Web UI Features

**Real-Time Monitoring (updates every 5 seconds):**
- 6 temperature sensors with calibration offsets
- 3 calculated temperature deltas  
- Flow rate (L/min)
- Current fan speed

**User Controls (instant response):**
- Main loop solenoid toggle
- Diversion solenoid toggle
- Fan speed slider (0-100)

**Control Modes:**
- **Manual:** User control via UI with optimistic updates
- **Automatic:** Server-driven control, UI reflects state

**UI Architecture:**
- Split broadcasts: 5s sensor data, immediate control confirmations
- 2-second ignore windows prevent stale data from causing flicker
- Smart blocking: Only rejects state CHANGES, allows confirmations

See [PROBLEMS_SOLVED.md](PROBLEMS_SOLVED.md) Problem #15 for details on the UI optimization.

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

**Web UI control flickering**
- ✅ SOLVED (Jan 11, 2026)
- See PROBLEMS_SOLVED.md Problem #15

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
├── .venv/                    # Virtual environment
├── requirements.txt          # Python dependencies
│
├── README.md                 # This file
├── PROBLEMS_SOLVED.md        # Troubleshooting history
├── TODO.md                   # User task list
│
├── bts7960_controller.py     # Fan controller
├── ds18b20_reader.py         # Temperature sensors
├── flowmeter.py              # Flow meter
├── relay_control.py          # Relay control
│
├── shopheater3000.py         # Web server
├── web_ui.html               # Web interface
├── images/                   # UI icons
│
├── example_integration.py    # Integration example
└── verify_setup.py           # Setup checker
\`\`\`

---

## Technical Specifications

- **Platform:** Raspberry Pi 4
- **OS:** Raspberry Pi OS (kernel 6.12.47+)
- **Python:** 3.11+
- **GPIO Library:** lgpio 0.2.2.0
- **Web Framework:** FastAPI with WebSocket
- **Update Rates:**
  - Temperature broadcasts: 5 seconds
  - Control confirmations: Immediate
  - UI ignore windows: 2 seconds

---

## Changelog

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

**Last Updated:** January 11, 2026  
**System Status:** ✅ Production-ready, all modules operational

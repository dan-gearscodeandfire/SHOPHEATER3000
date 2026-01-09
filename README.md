# SHOPHEATER3000

Integrated shop heater control system combining multiple Raspberry Pi GPIO modules.

**Created:** January 6, 2026  
**Last Updated:** January 9, 2026  
**Status:** Web UI complete, all modules tested and operational

---

## Quick Navigation

**Getting Started:**
- [Overview](#overview) - System overview
- [Web UI](#web-ui) - **NEW!** Real-time web interface
- [Setup Instructions](#setup-instructions) - How to get started
- [Integration Example](#integration-example) - Working code example

**Module Documentation:**
- All module details are in this README and source files

**Web Interface:**
- [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) - Quick start guide for web UI
- [WEB_UI_README.md](WEB_UI_README.md) - Complete web UI documentation

**Troubleshooting:**
- [SOLVED_PROBLEMS.md](SOLVED_PROBLEMS.md) - Complete history of all problems encountered and solved

**Project Info:**
- [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md) - RPi.GPIO → lgpio migration notes

---

## Overview

This project integrates four separate codebases into a unified shop heater control system:

1. **raspi-bts7960** - Fan speed control (PWM motor driver)
2. **raspi-ds18b20** - Temperature sensing (1-Wire sensors)
3. **raspi-flowmeter** - Water flow measurement (pulse counter)
4. **raspi-relay-shopheater** - Solenoid valve control (relay switching)

---

## Consolidated Virtual Environment

A single `.venv` has been created with all dependencies from the four source codebases.

### Installed Packages

```
lgpio==0.2.2.0           # GPIO library (unified across all GPIO modules)
click==8.3.1             # CLI framework (dependency of w1thermsensor)
w1thermsensor==2.3.0     # DS18B20 temperature sensor library
fastapi==0.109.0         # Web framework for real-time UI
uvicorn==0.27.0          # ASGI server for FastAPI
websockets==12.0         # WebSocket support for real-time updates
```

### Key Change: RPi.GPIO → lgpio Migration

**All GPIO modules now use `lgpio`** for compatibility with Raspberry Pi kernel 6.6+ (currently running 6.12.47).

- ✅ **raspi-flowmeter** - Already used lgpio
- ✅ **raspi-relay-shopheater** - Already used lgpio
- ✅ **raspi-bts7960** - Migrated from RPi.GPIO to lgpio (Jan 2026)
- ✅ **raspi-ds18b20** - Uses kernel 1-Wire interface (no GPIO library needed)

**Why lgpio?**
- RPi.GPIO is broken on kernel 6.6+
- lgpio uses modern `/dev/gpiochip` interface
- No sudo required (only `gpio` group membership)
- Better error messages and permissions model

---

## GPIO Pin Allocation

Complete GPIO map across all modules:

| GPIO Pin | Physical Pin | Module | Function |
|----------|--------------|--------|----------|
| GPIO 4   | Pin 7        | DS18B20 | Temperature sensor (1-Wire) |
| GPIO 18  | Pin 12       | BTS7960 | Fan PWM control |
| GPIO 23  | Pin 16       | Relay   | Normal flow solenoid |
| GPIO 24  | Pin 18       | Relay   | Diversion flow solenoid |
| GPIO 27  | Pin 13       | Flowmeter | Pulse counter (flow sensor) |

**No conflicts** - all modules use separate GPIO pins.

---

## Source Codebases

All controller classes are now copied to this directory for easy integration.

### 1. raspi-bts7960 (Fan Control)
- **File:** `bts7960_controller.py`
- **GPIO:** 18 (PWM)
- **Hardware:** BTS7960 motor driver controlling two 12V fans
- **Key Features:**
  - PWM speed control (0-99%)
  - Automatic kick-start feature
  - 10 kHz PWM frequency (lgpio maximum, may be audible)
- **Status:** ✅ Migrated to lgpio
- **Class:** `BTS7960Controller`
- **Note:** lgpio max PWM = 10 kHz (vs RPi.GPIO 24+ kHz). Use 5-8 kHz if noise is an issue.

### 2. raspi-ds18b20 (Temperature)
- **File:** `ds18b20_reader.py`
- **GPIO:** 4 (1-Wire bus, **required** - no alternatives)
- **Hardware:** DS18B20 temperature sensors
- **Key Features:**
  - Multiple sensor support
  - Auto-discovery on 1-Wire bus
  - Automatic 10-bit resolution (optional, may show permission warnings)
- **Status:** ✅ No migration needed (uses kernel interface)
- **Class:** `DS18B20Reader`
- **Note:** Permission warnings on sensor init are harmless - readings work perfectly

### 3. raspi-flowmeter (Flow Measurement)
- **File:** `flowmeter.py`
- **GPIO:** 27 (interrupt-based pulse counter)
- **Hardware:** Digiten FL-408 water flow sensor
- **Key Features:**
  - Non-blocking interrupt-based counting
  - Thread-safe pulse counting
  - Flow rate calculation (L/min)
  - Calibrated: 450 pulses/liter, 3119 pulses/19.9 lbs
- **Status:** ✅ Already used lgpio
- **Class:** `FlowMeter`

### 4. raspi-relay-shopheater (Valve Control)
- **File:** `relay_control.py`
- **GPIO:** 23 (normal), 24 (diversion)
- **Hardware:** Two relay-controlled solenoid valves (12V, NC configuration)
- **Key Features:**
  - Fail-safe NC relay design
  - Multiple operating modes (mainLoop, diversion, mix, all_closed)
  - Individual GPIO control
- **Status:** ✅ Already used lgpio
- **Class:** `RelayController`

---

## Web UI

**NEW!** A complete real-time web interface for monitoring and controlling the shop heater system.

### Quick Start

```bash
cd ~/SHOPHEATER3000
source .venv/bin/activate
python shopheater3000.py
```

Then open a browser to: **http://localhost:8000** (or http://[pi-ip]:8000 from another device)

### Features

**Real-Time Monitoring (updates every 0.5 seconds):**
- 6 temperature sensors (water_hot, water_reservoir, water_mix, water_cold, air_cool, air_heated)
- 3 calculated temperature deltas (heater, radiator, air)
- Flow rate (L/min)
- Current fan speed

**User Controls:**
- Main loop solenoid toggle
- Diversion solenoid toggle
- Fan speed control (0-100) with synchronized text input and slider

**Technology:**
- FastAPI backend with WebSocket for bidirectional communication
- ~1-5ms latency for control commands
- Automatic reconnection on disconnect
- Visual flow diagram with live data overlay

### Documentation

- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - Quick installation and startup
- **[WEB_UI_README.md](WEB_UI_README.md)** - Complete feature documentation, API reference, troubleshooting

---

## Integration Example

A complete example is provided in `example_integration.py`. Here's how to use it:

```bash
cd ~/SHOPHEATER3000
source .venv/bin/activate
python example_integration.py
```

**Basic usage snippet:**

```python
#!/usr/bin/env python3
from bts7960_controller import BTS7960Controller
from ds18b20_reader import DS18B20Reader
from flowmeter import FlowMeter
from relay_control import RelayController

# Initialize all modules (no sys.path needed - all files are local)
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
```

See `example_integration.py` for a complete working example with temperature-based fan control.

---

## Setup Instructions

### 1. Verify GPIO Permissions

Ensure your user is in the `gpio` group:
```bash
groups | grep gpio
```

If not:
```bash
sudo usermod -a -G gpio $USER
# Log out and back in for changes to take effect
```

### 2. Activate Virtual Environment

```bash
cd ~/SHOPHEATER3000
source .venv/bin/activate
```

### 3. Verify Installation

```bash
pip list
# Should show: lgpio, click, w1thermsensor
```

### 4. Test Individual Modules

Before integrating, test each module independently in its source directory:

```bash
# Test fan control
cd ~/raspi-bts7960
source .venv/bin/activate
python example_usage.py

# Test temperature
cd ~/raspi-ds18b20
source .venv/bin/activate
python ds18b20_reader.py

# Test flow meter
cd ~/raspi-flowmeter
source .venv/bin/activate
python flowmeter.py

# Test relay control
cd ~/raspi-relay-shopheater
source .venv/bin/activate
python relay_control.py
```

---

## Migration Summary

### What Was Done

1. ✅ **Created consolidated virtual environment** in `~/SHOPHEATER3000/.venv`
2. ✅ **Migrated raspi-bts7960** from RPi.GPIO to lgpio
3. ✅ **Unified all dependencies** in single requirements.txt
4. ✅ **Documented GPIO pin allocation** to avoid conflicts
5. ✅ **Created integration examples** for reference

### What Was Changed

**raspi-bts7960/bts7960_controller.py:**
- Replaced `RPi.GPIO` with `lgpio`
- Updated initialization to use `lgpio.gpiochip_open()`
- Changed PWM API from `GPIO.PWM()` to `lgpio.tx_pwm()`
- Improved error messages and cleanup logic
- Maintained all original functionality (kick-start, speed control, context manager)

**requirements.txt:**
- Removed `RPi.GPIO==0.7.1` (deprecated, broken on kernel 6.6+)
- Kept `lgpio==0.2.2.0` (modern, works on all kernels)
- Kept `click==8.3.1` and `w1thermsensor==2.3.0` (unchanged)

### Testing Status

⚠️ **Hardware testing pending** - Code migration complete but not yet tested with actual hardware.

**See** `~/raspi-bts7960/README.md` for detailed testing checklist.

---

## Troubleshooting

### "Failed to open GPIO chip"
- **Cause:** User not in `gpio` group
- **Solution:** `sudo usermod -a -G gpio $USER` and log out/in

### "GPIO pin already in use"
- **Cause:** Another process using the GPIO pin
- **Solution:** Find and kill conflicting process: `ps aux | grep python`

### "bad PWM frequency" error
- **Cause:** lgpio supports max 10 kHz PWM (tested: 100-10000 Hz work, 20000+ fail)
- **Solution:** Use frequencies ≤10 kHz. Default is 10 kHz. Try 8 kHz or 5 kHz for quieter operation.

### Temperature sensor permission warnings
- **Symptom:** `/bin/sh: 1: cannot create /sys/bus/w1/devices/*/w1_slave: Permission denied`
- **Cause:** Sensor resolution auto-config requires root permissions
- **Solution:** Ignore warnings - temperature readings work perfectly without resolution setting

### Import errors from source codebases
- **Cause:** Source directories not in Python path
- **Solution:** Files are now local in SHOPHEATER3000 - no path modifications needed

### Multiple modules conflict
- **Cause:** Modules may use same GPIO pin
- **Solution:** Verify GPIO pin allocation table above - all pins are unique

### Fan noise at 10 kHz PWM
- **Symptom:** Audible whine from fans (10 kHz is at edge of human hearing)
- **Solution:** Lower PWM frequency to 8 kHz or 5 kHz:
  ```python
  fan = BTS7960Controller(rpwm_pin=18, pwm_freq=8000)  # Quieter
  ```

---

## Next Steps

1. **Hardware test each module** independently
2. **Test raspi-bts7960** after lgpio migration (see testing checklist in its README)
3. **Create main integration script** based on example above
4. **Implement control logic** for your specific shop heater requirements
5. **Add safety features** (temperature limits, flow monitoring, etc.)
6. **Consider adding logging** for debugging and monitoring

---

## File Structure

```
~/SHOPHEATER3000/
├── .venv/                              # Consolidated virtual environment
├── requirements.txt                    # Unified dependencies
│
├── README.md                           # This file (integration guide)
├── MIGRATION_SUMMARY.md                # Migration notes
├── INSTALLATION_GUIDE.md               # Web UI quick start guide
├── WEB_UI_README.md                    # Complete web UI documentation
│
├── bts7960_controller.py               # Fan controller class
├── ds18b20_reader.py                   # Temperature sensor class
├── flowmeter.py                        # Flow meter class
├── relay_control.py                    # Relay controller class
│
├── shopheater3000.py                   # Web server with real-time UI
├── web_ui.html                         # Web interface frontend
├── images/                             # Icons for web UI flow diagram
│
├── example_integration.py              # Complete integration example
├── verify_setup.py                     # Setup verification script
└── SOLVED_PROBLEMS.md                  # Complete troubleshooting history
```

**All source codebases remain in their original locations** (`~/raspi-bts7960`, `~/raspi-ds18b20`, etc.) for reference and independent testing.

---

## Technical Specifications

- **Platform:** Raspberry Pi (tested: Pi 4)
- **OS:** Raspberry Pi OS (kernel 6.12.47+)
- **Python:** 3.11+
- **GPIO Library:** lgpio 0.2.2.0
- **Permissions:** User must be in `gpio` group (no sudo required)

---

## License

Each source codebase maintains its original license. Integration code is provided as-is for system integration purposes.

---

## Changelog

### 2026-01-09 (Web UI Added)
- **NEW:** Real-time web interface with FastAPI + WebSocket
- Added `shopheater3000.py` - Main web server with hardware integration
- Added `web_ui.html` - Real-time monitoring and control interface
- Added FastAPI, uvicorn, websockets to dependencies
- Created comprehensive web UI documentation (WEB_UI_README.md, INSTALLATION_GUIDE.md)
- Implemented bidirectional WebSocket communication (0.5s update rate)
- Temperature conversion to Fahrenheit with delta calculations
- User controls: fan speed (0-100), main loop toggle, diversion toggle
- Visual flow diagram with live sensor data overlay

### 2026-01-06 (Initial Integration)
- **02:00 UTC** - Completed integration testing with all 4 modules working
- Created consolidated virtual environment
- Migrated raspi-bts7960 from RPi.GPIO to lgpio
- Discovered lgpio PWM frequency limitation (max 10 kHz vs RPi.GPIO 24+ kHz)
- Changed default PWM frequency from 24 kHz → 10 kHz
- Unified all dependencies in single requirements.txt
- Documented GPIO pin allocation
- Created integration examples and documentation
- Updated all virtual environments to use lgpio exclusively
- Verified temperature sensors (4x DS18B20), flow meter, relays, and fan control all working

---

**Last Updated:** January 9, 2026  
**System Status:** ✅ All modules tested and working, Web UI operational  
**Integration Test:** Passed - Temperature sensors (6x), fan control, relays, flow meter, web interface all operational


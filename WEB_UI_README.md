# Shop Heater Web UI

Real-time web interface for monitoring and controlling the shop heater system.

## Quick Start

### 1. Install Dependencies

```bash
cd ~/SHOPHEATER3000
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the Server

```bash
cd ~/SHOPHEATER3000
source .venv/bin/activate
python shopheater3000.py
```

### 3. Access the Web UI

Open a browser and navigate to:
- **On the Raspberry Pi:** http://localhost:8000
- **From another device:** http://[raspberry-pi-ip]:8000

Example: `http://192.168.1.100:8000`

---

## Features

### Real-Time Monitoring

**Temperature Sensors (6 total):**
- `water_hot` - Hot water temperature (Cell 1:2)
- `water_reservoir` - Reservoir temperature (Cell 2:0, overlaid on icon)
- `water_mix` - Mixed water temperature (Cell 2:2)
- `water_cold` - Cold water temperature (Cell 1:4)
- `air_cool` - Cool air temperature (Cell 4:1)
- `air_heated` - Heated air temperature (Cell 4:5)

**Calculated Deltas:**
- `delta_water_heater` - Temperature difference across heater (Cell 1:3)
- `delta_water_radiator` - Temperature difference across radiator (Cell 2:3)
- `delta_air` - Temperature difference in air (Cell 4:3)

**Flow Measurement:**
- Flow rate in L/min (Cell 2:4)

**Fan Speed:**
- Current fan speed percentage (Cell 4:3, below delta_air)

### User Controls

**Main Loop Solenoid Toggle:**
- **ON (checked)** → GPIO 23 LOW → Relay closed → Solenoid open
- **OFF (unchecked)** → GPIO 23 HIGH → Relay open → Solenoid closed

**Diversion Solenoid Toggle:**
- **ON (checked)** → GPIO 24 LOW → Relay closed → Solenoid open
- **OFF (unchecked)** → GPIO 24 HIGH → Relay open → Solenoid closed

**Fan Speed Control:**
- Text input box (0-100)
- Slider (0-100)
- Both controls are synchronized
- Changes are applied immediately via WebSocket

### Status Indicator

Green dot next to title = WebSocket connected
Red dot = WebSocket disconnected (will auto-reconnect)

---

## Architecture

### Backend (FastAPI + WebSocket)

**File:** `shopheater3000.py`

**Key Components:**
- `ShopHeaterController` - Main hardware integration class
- WebSocket endpoint at `/ws` for bidirectional communication
- Background task reads sensors every 0.5 seconds
- Broadcasts data to all connected clients
- Receives and processes control commands

**Data Update Rate:** 500ms (2 updates per second)

### Frontend (HTML + JavaScript)

**File:** `web_ui.html`

**Key Features:**
- 6×5 grid layout with flow diagram
- Real-time data updates via WebSocket
- Automatic reconnection on disconnect
- Synchronized controls (updates reflect hardware state)

**WebSocket Protocol:**

**Server → Client (sensor data):**
```json
{
  "temperatures": {
    "water_hot": 140.5,
    "water_reservoir": 135.2,
    "water_mix": 138.0,
    "water_cold": 70.3,
    "air_cool": 65.1,
    "air_heated": 95.8
  },
  "deltas": {
    "delta_water_heater": 70.2,
    "delta_water_radiator": 67.7,
    "delta_air": 30.7
  },
  "flow_rate": 2.45,
  "fan_speed": 75,
  "main_loop_state": true,
  "diversion_state": false
}
```

**Client → Server (control commands):**
```json
{
  "fan_speed": 75
}
```
```json
{
  "main_loop": true
}
```
```json
{
  "diversion": false
}
```

---

## Temperature Sensor Mapping

The backend automatically discovers DS18B20 sensors and maps them to logical names. If you have 6 sensors connected, they are assigned in order:

1. First sensor → `water_hot`
2. Second sensor → `water_reservoir`
3. Third sensor → `water_mix`
4. Fourth sensor → `water_cold`
5. Fifth sensor → `air_cool`
6. Sixth sensor → `air_heated`

**To customize sensor mapping:**

Edit `shopheater3000.py` in the `_initialize_sensor_map()` method and manually assign sensor IDs:

```python
def _initialize_sensor_map(self) -> Dict[str, Optional[str]]:
    sensor_map = {
        'water_hot': '00000xxxxxxx',  # Replace with actual sensor ID
        'water_reservoir': '00000yyyyyyy',
        # ... etc
    }
    return sensor_map
```

To discover sensor IDs:
```bash
cd ~/raspi-ds18b20
source .venv/bin/activate
python ds18b20_reader.py
```

---

## Configuration

### Change Update Rate

Edit `shopheater3000.py`, line ~238:
```python
await asyncio.sleep(0.5)  # Change to desired interval (seconds)
```

### Change PWM Frequency

Edit `shopheater3000.py`, line ~44:
```python
self.fan = BTS7960Controller(rpwm_pin=18, pwm_freq=10000)  # Change frequency
```

Lower frequencies (5000-8000 Hz) may reduce fan noise.

### Change Server Port

Edit `shopheater3000.py`, line ~315:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # Change port number
```

---

## Troubleshooting

### Server won't start

**Error: "Failed to open GPIO chip"**
- Ensure user is in `gpio` group: `groups | grep gpio`
- If not: `sudo usermod -a -G gpio $USER` and log out/in

**Error: "Address already in use"**
- Port 8000 is already in use
- Find process: `lsof -i :8000`
- Kill it: `kill [PID]`
- Or change port in `web_server.py`

### WebSocket won't connect

**Red status indicator**
- Server may not be running
- Firewall blocking port 8000
- Try accessing from Pi itself: `http://localhost:8000`

**Auto-reconnect feature**
- UI attempts to reconnect every 2 seconds
- Should reconnect automatically when server restarts

### Sensors show "--"

**No sensors found**
- Check 1-Wire is enabled: `lsmod | grep w1`
- If not: `sudo modprobe w1-gpio w1-therm`
- Verify wiring and pull-up resistor (4.7kΩ)

**Some sensors missing**
- Check sensor mapping in console output when server starts
- May need to assign sensors manually (see "Temperature Sensor Mapping")

### Controls don't work

**Commands sent but hardware doesn't respond**
- Check console output in terminal running `web_server.py`
- Verify GPIO permissions
- Check relay/fan wiring

**Controls update but don't stay synchronized**
- This is expected - UI shows actual hardware state
- If state doesn't change, check hardware connections

### Fan doesn't start

**Speed set but no motion**
- Low speed may not overcome starting friction
- BTS7960Controller has automatic kick-start at 99% for 1 second
- Verify wiring and power supply to BTS7960

---

## Network Access

### Find Raspberry Pi IP Address

```bash
hostname -I
```

### Access from Other Devices

1. Start the server on the Raspberry Pi
2. Find the Pi's IP address (e.g., 192.168.1.100)
3. On another device, open: `http://192.168.1.100:8000`

### Firewall Configuration (if needed)

```bash
sudo ufw allow 8000/tcp
```

---

## Development Notes

### Adding New Sensors/Data

1. Modify `ShopHeaterController.read_sensor_data()` in `shopheater3000.py`
2. Update data structure returned
3. Modify `updateDisplay()` in `web_ui.html` to handle new data
4. Add display elements to HTML grid as needed

### Adding New Controls

1. Add HTML control element in `web_ui.html`
2. Add event listener to send command via WebSocket
3. Handle command in `websocket_endpoint()` in `shopheater3000.py`
4. Call appropriate controller method

---

## Files

- `shopheater3000.py` - FastAPI backend server
- `web_ui.html` - Frontend UI
- `requirements.txt` - Python dependencies (includes FastAPI, uvicorn, websockets)
- `images/` - Icon images for flow diagram

---

## TODO

- [ ] Display solenoid status on grid (currently only in controls)
- [ ] Add data logging/history
- [ ] Add safety limits and alarms
- [ ] Add authentication for remote access
- [ ] Add HTTPS support for secure remote access

---

## Technical Specifications

- **Backend:** FastAPI (async Python framework)
- **WebSocket:** Native WebSocket (bidirectional, persistent connection)
- **Update Rate:** 500ms (2 Hz)
- **Latency:** ~1-5ms per WebSocket message
- **Bandwidth:** ~200 bytes/sec at 2 Hz update rate
- **Protocol:** JSON over WebSocket

---

**Last Updated:** January 9, 2026


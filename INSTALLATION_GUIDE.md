# Shop Heater Web UI - Installation Guide

Quick guide to get the web interface up and running.

## Step 1: Install Web Dependencies

```bash
cd ~/SHOPHEATER3000
source .venv/bin/activate
pip install -r requirements.txt
```

This will install:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `websockets` - WebSocket support

## Step 2: Verify Installation

```bash
pip list | grep -E "fastapi|uvicorn|websockets"
```

You should see:
```
fastapi        0.109.0
uvicorn        0.27.0
websockets     12.0
```

## Step 3: Start the Server

```bash
cd ~/SHOPHEATER3000
source .venv/bin/activate
python shopheater3000.py
```

## Step 4: Access the Web UI

### From the Raspberry Pi:
Open a browser: **http://localhost:8000**

### From another device on the network:
1. Find your Pi's IP address:
   ```bash
   hostname -I
   ```
   
2. Open browser to: **http://[PI_IP_ADDRESS]:8000**
   
   Example: `http://192.168.1.100:8000`

## What You Should See

✅ **Green status indicator** next to "Shop Heater Control" title
✅ **Grid display** with temperature placeholders (will show "--" until sensors are mapped)
✅ **Control panel** below the grid with:
   - Main Loop Solenoid toggle
   - Diversion Solenoid toggle
   - Fan Speed control (text box + slider)

## Stopping the Server

Press **Ctrl+C** in the terminal running the server.

The server will automatically:
- Close all WebSocket connections
- Set fan speed to 0
- Close all solenoids (safe state)
- Clean up GPIO resources

## Next Steps

See **WEB_UI_README.md** for:
- Complete feature documentation
- Sensor mapping instructions
- Troubleshooting guide
- Configuration options

## Quick Test (Without Hardware)

The server will start even if hardware is not connected, but you'll see error messages. This is normal for testing the web interface without physical sensors.

To test with hardware:
1. Ensure all modules are connected and working
2. Verify GPIO permissions: `groups | grep gpio`
3. Start the server
4. Check console output for sensor discovery

---

**Need Help?**
- See WEB_UI_README.md for detailed documentation
- See README.md for hardware setup
- See SOLVED_PROBLEMS.md for troubleshooting


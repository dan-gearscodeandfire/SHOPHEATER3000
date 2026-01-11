#!/usr/bin/env python3
"""
Shop Heater Web Server with WebSocket Support
FastAPI backend for real-time monitoring and control
"""

import asyncio
import json
from typing import Dict, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Import hardware controllers
from bts7960_controller import BTS7960Controller
from ds18b20_reader import DS18B20Reader
from flowmeter import FlowMeter
from relay_control import RelayController


class ShopHeaterController:
    """Main controller integrating all hardware modules."""
    
    # Sensor calibration offsets from ice water test (Jan 9, 2026)
    # Subtract these values from raw Celsius readings to get calibrated temps
    SENSOR_OFFSETS = {
        '4460008751fe': -0.75,   # Reads 0.75°C high
        '3c52f648a463': 0.00,    # Perfect reference sensor
        '3cf7f6496d4f': 0.00,    # Perfect in latest test
        '031294970b3f': +1.00,   # Reads 1.00°C low
        '3ca4f649bbd0': -0.81,   # Reads 0.81°C high
        '158200872bfa': -0.38    # Reads 0.38°C high
    }
    
    def __init__(self):
        """Initialize all hardware modules."""
        print("Initializing Shop Heater Controller...")
        
        # Initialize hardware
        self.fan = BTS7960Controller(rpwm_pin=18, pwm_freq=10000)
        self.temp_reader = DS18B20Reader()
        self.flow_meter = FlowMeter(gpio_pin=27)
        self.valve_control = RelayController()
        
        # Sensor mapping (will be populated from discovered sensors)
        # User will need to identify which physical sensor corresponds to which location
        self.sensor_map = self._initialize_sensor_map()
        
        # Current state
        self.current_fan_speed = 0
        self.main_loop_state = False  # False=off (HIGH), True=on (LOW)
        self.diversion_state = False  # False=off (HIGH), True=on (LOW)
        self.control_mode = 'manual'  # 'manual' or 'automatic'
        
        # Set initial safe state
        self.valve_control.all_closed()
        self.fan.set_speed(0)
        
        print("Controller initialized successfully")
    
    def _initialize_sensor_map(self) -> Dict[str, Optional[str]]:
        """
        Initialize sensor mapping.
        Maps logical names to specific sensor IDs assigned by user.
        """
        sensor_ids = self.temp_reader.get_sensor_addresses()
        
        # Specific sensor assignments (identified Jan 9, 2026)
        sensor_map = {
            'water_hot': '3ca4f649bbd0',
            'water_mix': '3cf7f6496d4f',
            'water_cold': '158200872bfa',
            'water_reservoir': '3c52f648a463',
            'air_heated': '4460008751fe',
            'air_cool': '031294970b3f'
        }
        
        print(f"Found {len(sensor_ids)} temperature sensors")
        print("Sensor mapping:")
        for name, sensor_id in sensor_map.items():
            # Check if assigned sensor is actually present
            status = "✓" if sensor_id in sensor_ids else "✗ NOT FOUND"
            print(f"  {name}: {sensor_id} {status}")
        
        return sensor_map
    
    def celsius_to_fahrenheit(self, celsius: Optional[float], sensor_id: Optional[str] = None) -> Optional[float]:
        """Convert Celsius to Fahrenheit with calibration, rounded to 0.1 places."""
        if celsius is None:
            return None
        
        # Apply calibration offset if sensor_id provided
        if sensor_id and sensor_id in self.SENSOR_OFFSETS:
            celsius += self.SENSOR_OFFSETS[sensor_id]
        
        fahrenheit = (celsius * 9/5) + 32
        return round(fahrenheit, 1)
    
    def read_sensor_data(self) -> Dict:
        """
        Read all sensor data and return as a dictionary.
        Temperatures are converted to Fahrenheit.
        """
        # Read all temperatures
        all_temps = self.temp_reader.read_all_temperatures()
        
        # Map to logical names and convert to Fahrenheit with calibration
        temps = {}
        for name, sensor_id in self.sensor_map.items():
            if sensor_id and sensor_id in all_temps:
                # Pass sensor_id for calibration
                temps[name] = self.celsius_to_fahrenheit(all_temps[sensor_id], sensor_id)
            else:
                temps[name] = None
        
        # Calculate deltas (only if both temps are available)
        delta_water_heater = None
        if temps['water_hot'] is not None and temps['water_cold'] is not None:
            delta_water_heater = round(temps['water_hot'] - temps['water_cold'], 1)
        
        delta_water_radiator = None
        if temps['water_mix'] is not None and temps['water_cold'] is not None:
            delta_water_radiator = round(temps['water_mix'] - temps['water_cold'], 1)
        
        delta_air = None
        if temps['air_heated'] is not None and temps['air_cool'] is not None:
            delta_air = round(temps['air_heated'] - temps['air_cool'], 1)
        
        # Read flow rate
        flow_rate = round(self.flow_meter.getFlowRate(), 2)
        
        # Assemble data packet
        data = {
            'temperatures': temps,
            'deltas': {
                'delta_water_heater': delta_water_heater,
                'delta_water_radiator': delta_water_radiator,
                'delta_air': delta_air
            },
            'flow_rate': flow_rate,
            'fan_speed': self.current_fan_speed,
            'main_loop_state': self.main_loop_state,
            'diversion_state': self.diversion_state,
            'control_mode': self.control_mode
        }
        
        return data
    
    def set_fan_speed(self, speed: int):
        """Set fan speed (0-100)."""
        speed = max(0, min(100, speed))  # Clamp to 0-100
        self.fan.set_speed(speed)
        self.current_fan_speed = speed
        print(f"Fan speed set to {speed}%")
    
    def set_main_loop(self, state: bool):
        """
        Set main loop solenoid state.
        True = on (GPIO LOW, relay closed, solenoid open)
        False = off (GPIO HIGH, relay open, solenoid closed)
        """
        if state:
            self.valve_control.normal_low()  # Turn on
        else:
            self.valve_control.normal_high()  # Turn off
        self.main_loop_state = state
        print(f"Main loop: {'ON' if state else 'OFF'}")
    
    def set_diversion(self, state: bool):
        """
        Set diversion solenoid state.
        True = on (GPIO LOW, relay closed, solenoid open)
        False = off (GPIO HIGH, relay open, solenoid closed)
        """
        if state:
            self.valve_control.diversion_low()  # Turn on
        else:
            self.valve_control.diversion_high()  # Turn off
        self.diversion_state = state
        print(f"Diversion: {'ON' if state else 'OFF'}")
    
    def set_control_mode(self, mode: str):
        """
        Set control mode.
        'manual' = user control via web UI
        'automatic' = automated control logic
        """
        if mode in ['manual', 'automatic']:
            self.control_mode = mode
            print(f"Control mode set to: {mode.upper()}")
        else:
            print(f"Invalid control mode: {mode}. Must be 'manual' or 'automatic'.")
    
    def cleanup(self):
        """Clean up all hardware resources."""
        print("Cleaning up hardware...")
        self.fan.cleanup()
        self.flow_meter.cleanup()
        self.valve_control.cleanup()
        print("Cleanup complete")


# Global controller instance
controller: Optional[ShopHeaterController] = None

# FastAPI app
app = FastAPI(title="Shop Heater Control")

# Connected WebSocket clients
active_connections: list[WebSocket] = []


@app.on_event("startup")
async def startup_event():
    """Initialize hardware on startup."""
    global controller
    print("=" * 60)
    print("STARTUP EVENT TRIGGERED")
    print("=" * 60)
    try:
        controller = ShopHeaterController()
        print("Controller initialized successfully in startup event")
        
        # Start background task for sensor reading
        asyncio.create_task(sensor_broadcast_loop())
        print("Background task created")
    except Exception as e:
        print(f"ERROR IN STARTUP: {e}")
        import traceback
        traceback.print_exc()
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up hardware on shutdown."""
    global controller
    if controller:
        controller.cleanup()


async def sensor_broadcast_loop():
    """
    Background task that reads sensors and broadcasts to all connected clients.
    Updates every 0.5 seconds.
    """
    print("Sensor broadcast loop started")
    while True:
        await asyncio.sleep(0.5)  # Update every 500ms
        
        if controller and active_connections:
            try:
                data = controller.read_sensor_data()
                message = json.dumps(data)
                print(f"Broadcasting to {len(active_connections)} clients: {len(message)} bytes")
                
                # Broadcast to all connected clients
                disconnected = []
                for connection in active_connections:
                    try:
                        await connection.send_text(message)
                    except Exception as e:
                        print(f"Error sending to client: {e}")
                        disconnected.append(connection)
                
                # Remove disconnected clients
                for connection in disconnected:
                    if connection in active_connections:
                        active_connections.remove(connection)
                        print(f"Removed disconnected client. Remaining: {len(active_connections)}")
            except Exception as e:
                print(f"Error in sensor broadcast: {e}")
                import traceback
                traceback.print_exc()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data and control."""
    await websocket.accept()
    active_connections.append(websocket)
    print(f"Client connected. Total connections: {len(active_connections)}")
    
    # Send initial data immediately
    try:
        if controller:
            data = controller.read_sensor_data()
            message = json.dumps(data)
            print(f"Sending initial data to client: {len(message)} bytes")
            await websocket.send_text(message)
            print("Initial data sent successfully")
    except Exception as e:
        print(f"Error sending initial data: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        while True:
            # Receive control commands from client
            data = await websocket.receive_text()
            command = json.loads(data)
            
            # Process command
            if controller:
                if 'fan_speed' in command:
                    controller.set_fan_speed(int(command['fan_speed']))
                
                if 'main_loop' in command:
                    controller.set_main_loop(bool(command['main_loop']))
                
                if 'diversion' in command:
                    controller.set_diversion(bool(command['diversion']))
                
                if 'control_mode' in command:
                    controller.set_control_mode(str(command['control_mode']))
                
                # Immediately send updated state back to client after command
                updated_data = controller.read_sensor_data()
                await websocket.send_text(json.dumps(updated_data))
                print(f"Sent immediate state update after command: {command}")
    
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(active_connections)}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.get("/")
async def read_root():
    """Serve the main HTML page."""
    return FileResponse("web_ui.html")


@app.get("/images/{filename}")
async def get_image(filename: str):
    """Serve images from the images directory."""
    image_path = Path("images") / filename
    if image_path.exists():
        return FileResponse(image_path)
    return {"error": "Image not found"}


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Shop Heater Web Server")
    print("=" * 60)
    print("Starting server on http://0.0.0.0:8000")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\nShutting down...")


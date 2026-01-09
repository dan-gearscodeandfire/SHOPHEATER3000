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
        
        # Set initial safe state
        self.valve_control.all_closed()
        self.fan.set_speed(0)
        
        print("Controller initialized successfully")
    
    def _initialize_sensor_map(self) -> Dict[str, Optional[str]]:
        """
        Initialize sensor mapping.
        Maps logical names to sensor IDs.
        If sensors are not yet assigned, they will be None.
        """
        sensor_ids = self.temp_reader.get_sensor_addresses()
        
        # Create mapping structure
        # Initially, we'll assign sensors in order if 6 are found
        # User can modify this mapping later
        sensor_names = [
            'water_hot',
            'water_reservoir', 
            'water_mix',
            'water_cold',
            'air_cool',
            'air_heated'
        ]
        
        sensor_map = {}
        for i, name in enumerate(sensor_names):
            if i < len(sensor_ids):
                sensor_map[name] = sensor_ids[i]
            else:
                sensor_map[name] = None
        
        print(f"Found {len(sensor_ids)} temperature sensors")
        print("Sensor mapping:")
        for name, sensor_id in sensor_map.items():
            print(f"  {name}: {sensor_id if sensor_id else 'NOT ASSIGNED'}")
        
        return sensor_map
    
    def celsius_to_fahrenheit(self, celsius: Optional[float]) -> Optional[float]:
        """Convert Celsius to Fahrenheit, rounded to 0.1 places."""
        if celsius is None:
            return None
        fahrenheit = (celsius * 9/5) + 32
        return round(fahrenheit, 1)
    
    def read_sensor_data(self) -> Dict:
        """
        Read all sensor data and return as a dictionary.
        Temperatures are converted to Fahrenheit.
        """
        # Read all temperatures
        all_temps = self.temp_reader.read_all_temperatures()
        
        # Map to logical names and convert to Fahrenheit
        temps = {}
        for name, sensor_id in self.sensor_map.items():
            if sensor_id and sensor_id in all_temps:
                temps[name] = self.celsius_to_fahrenheit(all_temps[sensor_id])
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
            'diversion_state': self.diversion_state
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
    controller = ShopHeaterController()
    
    # Start background task for sensor reading
    asyncio.create_task(sensor_broadcast_loop())


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
    while True:
        await asyncio.sleep(0.5)  # Update every 500ms
        
        if controller and active_connections:
            try:
                data = controller.read_sensor_data()
                message = json.dumps(data)
                
                # Broadcast to all connected clients
                disconnected = []
                for connection in active_connections:
                    try:
                        await connection.send_text(message)
                    except:
                        disconnected.append(connection)
                
                # Remove disconnected clients
                for connection in disconnected:
                    active_connections.remove(connection)
            except Exception as e:
                print(f"Error in sensor broadcast: {e}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data and control."""
    await websocket.accept()
    active_connections.append(websocket)
    print(f"Client connected. Total connections: {len(active_connections)}")
    
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
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print(f"Client disconnected. Total connections: {len(active_connections)}")
    except Exception as e:
        print(f"WebSocket error: {e}")
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


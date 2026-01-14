#!/usr/bin/env python3
"""
Shop Heater Web Server with WebSocket Support
FastAPI backend for real-time monitoring and control
"""

import asyncio
import json
import csv
from datetime import datetime
from typing import Dict, Optional, List
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
        self.flow_mode = 'main'  # 'main', 'diversion', or 'mix'
        
        # Data logging and graphing state
        self.save_enabled = False
        self.graph_enabled = False
        self.saved_data = []  # Data collected when save_enabled is True
        self.graph_data = []  # Data collected when graph_enabled is True
        
        # Set initial safe state
        self.valve_control.all_closed()
        self.fan.set_speed(0)
        
        # Calculate initial flow mode based on valve states
        self.calculate_flow_mode()
        
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
            'control_mode': self.control_mode,
            'flow_mode': self.flow_mode,
            'save_enabled': self.save_enabled,
            'graph_enabled': self.graph_enabled
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
        self.calculate_flow_mode()
    
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
        self.calculate_flow_mode()
    
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
    
    def set_save_enabled(self, state: bool):
        """
        Enable or disable data logging.
        When enabled, collects data every 5 seconds to be saved to CSV on shutdown.
        """
        old_state = self.save_enabled
        self.save_enabled = state
        
        if state and not old_state:
            # Just enabled - clear old data and start fresh
            self.saved_data = []
            print("Data logging ENABLED - will save to CSV on shutdown")
        elif not state and old_state:
            print(f"Data logging DISABLED - {len(self.saved_data)} records collected")
    
    def set_graph_enabled(self, state: bool):
        """
        Enable or disable live graphing.
        When enabled, collects data every 5 seconds for real-time graphing.
        When disabled, clears collected data.
        """
        old_state = self.graph_enabled
        self.graph_enabled = state
        
        if state and not old_state:
            # Just enabled - clear old data and start fresh session
            self.graph_data = []
            print("Live graphing ENABLED - new graph session started")
        elif not state and old_state:
            print(f"Live graphing DISABLED - {len(self.graph_data)} records cleared")
            self.graph_data = []  # Clear data when disabled
    
    def calculate_flow_mode(self):
        """
        Calculate current flow mode based on valve states.
        Returns: 'main', 'diversion', or 'mix'
        """
        if self.main_loop_state and self.diversion_state:
            self.flow_mode = 'mix'
        elif self.main_loop_state and not self.diversion_state:
            self.flow_mode = 'main'
        elif not self.main_loop_state and self.diversion_state:
            self.flow_mode = 'diversion'
        else:
            # Both off - should not happen in normal operation
            self.flow_mode = 'none'
        
        print(f"Flow mode calculated: {self.flow_mode.upper()} (main={self.main_loop_state}, diversion={self.diversion_state})")
    
    def collect_data_point(self):
        """
        Collect a single data point for logging/graphing.
        Called every 5 seconds by the data collection task.
        """
        if not self.save_enabled and not self.graph_enabled:
            return  # Nothing to do
        
        # Get current sensor data
        data = self.read_sensor_data()
        
        # Create a flattened data point with timestamp
        data_point = {
            'timestamp': datetime.now().isoformat(),
            # Temperatures
            'water_hot': data['temperatures']['water_hot'],
            'water_reservoir': data['temperatures']['water_reservoir'],
            'water_mix': data['temperatures']['water_mix'],
            'water_cold': data['temperatures']['water_cold'],
            'air_cool': data['temperatures']['air_cool'],
            'air_heated': data['temperatures']['air_heated'],
            # Deltas
            'delta_water_heater': data['deltas']['delta_water_heater'],
            'delta_water_radiator': data['deltas']['delta_water_radiator'],
            'delta_air': data['deltas']['delta_air'],
            # Other data
            'flow_rate': data['flow_rate'],
            'fan_speed': data['fan_speed'],
            'main_loop_state': data['main_loop_state'],
            'diversion_state': data['diversion_state'],
            'control_mode': data['control_mode'],
            'flow_mode': data['flow_mode']
        }
        
        # Add to appropriate lists
        if self.save_enabled:
            self.saved_data.append(data_point)
        
        if self.graph_enabled:
            self.graph_data.append(data_point)
    
    def save_to_csv(self):
        """
        Save collected data to a CSV file.
        Called on shutdown if save_enabled was used during the session.
        """
        if not self.saved_data:
            print("No data to save")
            return
        
        # Generate filename with session timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"session_{timestamp}.csv"
        filepath = Path(__file__).parent / filename
        
        # Define CSV fieldnames
        fieldnames = [
            'timestamp', 
            'water_hot', 'water_reservoir', 'water_mix', 'water_cold', 'air_cool', 'air_heated',
            'delta_water_heater', 'delta_water_radiator', 'delta_air',
            'flow_rate', 'fan_speed', 'main_loop_state', 'diversion_state', 
            'control_mode', 'flow_mode'
        ]
        
        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.saved_data)
            
            print(f"✅ Saved {len(self.saved_data)} records to {filename}")
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")
    
    def cleanup(self):
        """Clean up all hardware resources and save data if needed."""
        print("Cleaning up hardware...")
        
        # Save data to CSV if we collected any
        if self.saved_data:
            self.save_to_csv()
        
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
        
        # Start background tasks
        asyncio.create_task(sensor_broadcast_loop())
        asyncio.create_task(data_collection_loop())
        print("Background tasks created (sensor broadcast + data collection)")
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
    Sends temperature/sensor data every 5 seconds.
    Control state changes are sent immediately via command handler.
    """
    print("Sensor broadcast loop started")
    while True:
        await asyncio.sleep(5.0)  # Update every 5 seconds (temperature updates only)
        
        if controller and active_connections:
            try:
                data = controller.read_sensor_data()
                message = json.dumps(data)
                print(f"Broadcasting temperatures to {len(active_connections)} clients: {len(message)} bytes")
                
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


async def data_collection_loop():
    """
    Background task that collects data points every 5 seconds for logging/graphing.
    Runs independently of sensor broadcast to ensure consistent data collection.
    """
    print("Data collection loop started")
    while True:
        await asyncio.sleep(5.0)  # Collect data every 5 seconds
        
        if controller:
            try:
                # Collect data if either save or graph is enabled
                if controller.save_enabled or controller.graph_enabled:
                    controller.collect_data_point()
                    
                    # Log collection status
                    status_parts = []
                    if controller.save_enabled:
                        status_parts.append(f"Save: {len(controller.saved_data)} records")
                    if controller.graph_enabled:
                        status_parts.append(f"Graph: {len(controller.graph_data)} records")
                    
                    if status_parts:
                        print(f"Data collected - {', '.join(status_parts)}")
            except Exception as e:
                print(f"Error in data collection: {e}")
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
                
                if 'save_enabled' in command:
                    controller.set_save_enabled(bool(command['save_enabled']))
                
                if 'graph_enabled' in command:
                    controller.set_graph_enabled(bool(command['graph_enabled']))
                
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


@app.get("/graph")
async def read_graph():
    """Serve the graph page."""
    return FileResponse("graph.html")


@app.get("/test_arrows.html")
async def test_arrows():
    """Serve the arrow test page."""
    return FileResponse("test_arrows.html")


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


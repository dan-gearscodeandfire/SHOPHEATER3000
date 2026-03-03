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
from collections import deque
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Import hardware controllers
from fan_relay_controller import FanRelayController
from ds18b20_reader import DS18B20Reader
from flowmeter import FlowMeter
from relay_control import RelayController


class ShopHeaterController:
    """Main controller integrating all hardware modules."""

    AUTO_FAN_WARM_AIR_F = 60.0
    AUTO_FAN_WARM_DELTA_AIR_F = 10.0
    AUTO_FAN_PREDICTIVE_12V_F = 185.0
    AUTO_VALVE_PREDICTIVE_DIVERSION_F = 195.0
    AUTO_VALVE_RETURN_HOT_F = 180.0
    AUTO_VALVE_RETURN_HOLD_S = 120.0
    AUTO_COOLDOWN_DOWNSTEP_HOLD_S = 25.0
    
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
        self.fan = FanRelayController(fan_onoff_pin=18, voltage_select_pin=17)
        self.temp_reader = DS18B20Reader()
        self.flow_meter = FlowMeter(gpio_pin=27)
        self.valve_control = RelayController()
        
        # Sensor mapping (will be populated from discovered sensors)
        # User will need to identify which physical sensor corresponds to which location
        self.sensor_map = self._initialize_sensor_map()
        
        # Current state
        self.current_fan_mode = "12v"
        self.current_fan_voltage = self._fan_mode_to_voltage(self.current_fan_mode)
        self.main_loop_state = True  # SAFETY: Default to OPEN - False=off (HIGH), True=on (LOW)
        self.diversion_state = True  # SAFETY: Default to OPEN - False=off (HIGH), True=on (LOW)
        self.control_mode = 'manual'  # 'manual' or 'automatic'
        self.flow_mode = 'mix'  # 'main', 'diversion', or 'mix' - starts as 'mix' (both open)
        
        # Data logging and graphing state
        self.save_enabled = False
        self.graph_enabled = False
        self.saved_data = []  # Data collected when save_enabled is True
        self.graph_data = []  # Data collected when graph_enabled is True
        self.save_start_time = None  # Timestamp when logging started
        self.graph_start_time = None  # Timestamp when graphing started

        # Automatic control state
        self._auto_delta_heater_history = deque(maxlen=12)  # ~60 seconds at 5s cadence
        self._auto_hot_history = deque(maxlen=12)  # ~60 seconds at 5s cadence
        self._auto_last_predicted_hot = None
        self._auto_force_diversion = False
        self._auto_below_return_since = None
        self._auto_pending_downstep = None
        self._auto_last_off_pulse = 0.0
        self._auto_fan_target = "off"
        self._auto_reason = "Automatic mode inactive"
        self._auto_return_hold_remaining_s = None
        
        # Set initial safe state - CRITICAL: Both valves must be open for circulation
        # Never close both valves - this creates dangerous error state with no flow path
        self.valve_control.mainLoop()  # Open main loop
        self.valve_control.diversion_low()  # Open diversion (LOW = on/open)
        self.fan.set_mode("12v")
        
        # Calculate initial flow mode based on valve states (should be 'mix')
        self.calculate_flow_mode()
        
        print(f"SAFETY: Both valves initialized to OPEN (flow_mode: {self.flow_mode})")
        
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
            'fan_voltage': self.current_fan_voltage,
            'fan_mode': self.current_fan_mode,
            'main_loop_state': self.main_loop_state,
            'diversion_state': self.diversion_state,
            'control_mode': self.control_mode,
            'flow_mode': self.flow_mode,
            'predicted_hot': self._auto_last_predicted_hot,
            'auto_force_diversion': self._auto_force_diversion,
            'auto_fan_target': self._auto_fan_target,
            'auto_reason': self._auto_reason,
            'auto_return_hold_remaining_s': self._auto_return_hold_remaining_s,
            'save_enabled': self.save_enabled,
            'graph_enabled': self.graph_enabled
        }
        
        return data
    
    def _fan_mode_to_voltage(self, mode: str) -> int:
        """Map fan relay mode to numeric voltage for graphing/logging."""
        if mode == "off":
            return 0
        if mode == "5v":
            return 5
        return 12

    def set_fan_mode(self, mode: str):
        """Set fan mode: 'off', '5v', or '12v'."""
        normalized = self.fan.set_mode(mode)
        self.current_fan_mode = normalized
        self.current_fan_voltage = self._fan_mode_to_voltage(normalized)
        print(f"Fan mode set to {normalized.upper()} ({self.current_fan_voltage}V)")

    def set_fan_speed(self, speed: int):
        """
        Legacy compatibility: map percentage commands to relay modes.
        <=0 => off, 1-71 => 5v, >71 => 12v
        """
        speed = max(0, min(100, speed))
        if speed <= 0:
            self.set_fan_mode("off")
        elif speed <= 71:
            self.set_fan_mode("5v")
        else:
            self.set_fan_mode("12v")
    
    def set_main_loop(self, state: bool):
        """
        Set main loop solenoid state.
        True = on (GPIO LOW, relay closed, solenoid open)
        False = off (GPIO HIGH, relay open, solenoid closed)
        
        SAFETY: If trying to close main loop while diversion is closed,
        automatically opens diversion to prevent both valves being closed.
        """
        # SAFETY CHECK: Prevent both valves from being closed
        if not state and not self.diversion_state:
            print("⚠️  SAFETY OVERRIDE: Cannot close main loop while diversion is closed!")
            print("    Automatically opening diversion valve to maintain flow path...")
            self.valve_control.diversion_low()  # Force diversion open
            self.diversion_state = True
        
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
        
        SAFETY: If trying to close diversion while main loop is closed,
        automatically opens main loop to prevent both valves being closed.
        """
        # SAFETY CHECK: Prevent both valves from being closed
        if not state and not self.main_loop_state:
            print("⚠️  SAFETY OVERRIDE: Cannot close diversion while main loop is closed!")
            print("    Automatically opening main loop valve to maintain flow path...")
            self.valve_control.normal_low()  # Force main loop open
            self.main_loop_state = True
        
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
            if mode == "automatic":
                self._auto_below_return_since = None
                self._auto_pending_downstep = None
                self._auto_force_diversion = False
        else:
            print(f"Invalid control mode: {mode}. Must be 'manual' or 'automatic'.")

    def _compute_rate_f_per_min(self, history: deque) -> float:
        """Compute slope from oldest/newest sample in F/min."""
        if len(history) < 2:
            return 0.0

        t0, v0 = history[0]
        t1, v1 = history[-1]
        dt = t1 - t0
        if dt <= 0:
            return 0.0

        return (v1 - v0) / dt * 60.0

    def _set_fan_mode_if_changed(self, mode: str):
        """Avoid redundant relay writes/noise."""
        if self.current_fan_mode != mode:
            self.set_fan_mode(mode)

    def _set_flow_main_only(self):
        """Main loop open, diversion closed."""
        self.set_main_loop(True)
        self.set_diversion(False)

    def _set_flow_diversion_only(self):
        """Main loop closed, diversion open."""
        self.set_main_loop(False)
        self.set_diversion(True)

    def run_automatic_control(self):
        """
        Automatic mode:
        - Keep fans OFF until air is warm enough (comfort gate)
        - Then default to 5V
        - Escalate to 12V early based on predicted hot-water rise
        - Force diversion-only when predicted hot risk exceeds threshold
        - Recover to main-only after sustained cooldown
        """
        if self.control_mode != "automatic":
            self._auto_fan_target = self.current_fan_mode
            self._auto_reason = "Automatic mode inactive"
            self._auto_return_hold_remaining_s = None
            return

        data = self.read_sensor_data()
        temps = data.get("temperatures", {})
        deltas = data.get("deltas", {})

        water_hot = temps.get("water_hot")
        water_cold = temps.get("water_cold")
        air_heated = temps.get("air_heated")
        delta_air = deltas.get("delta_air")
        delta_heater = deltas.get("delta_water_heater")
        flow_rate = data.get("flow_rate")

        now = time.monotonic()

        # Track recent trends for predictive logic
        if delta_heater is not None:
            self._auto_delta_heater_history.append((now, float(delta_heater)))
        if water_hot is not None:
            self._auto_hot_history.append((now, float(water_hot)))

        roc_delta_heater = self._compute_rate_f_per_min(self._auto_delta_heater_history)
        roc_hot = self._compute_rate_f_per_min(self._auto_hot_history)

        predicted_hot = None
        if water_hot is not None:
            predicted_hot = float(water_hot)
            # 30-second lookahead from hot trend
            predicted_hot += max(0.0, roc_hot) * 0.5

            # Additional predictor based on heater-lift acceleration and return temp.
            if water_cold is not None and delta_heater is not None:
                projected_from_heater = float(water_cold) + float(delta_heater) + max(0.0, roc_delta_heater) * 0.5
                predicted_hot = max(predicted_hot, projected_from_heater)

        self._auto_last_predicted_hot = round(predicted_hot, 1) if predicted_hot is not None else None

        # ---------- Valve automatic logic ----------
        emergency_flow_collapse = (
            flow_rate is not None and water_hot is not None and
            float(flow_rate) < 0.5 and float(water_hot) >= 170.0
        )
        diversion_trigger = (
            predicted_hot is not None and predicted_hot >= self.AUTO_VALVE_PREDICTIVE_DIVERSION_F
        ) or (
            water_hot is not None and float(water_hot) >= self.AUTO_VALVE_PREDICTIVE_DIVERSION_F
        ) or emergency_flow_collapse

        if diversion_trigger:
            self._auto_force_diversion = True
            self._auto_below_return_since = None
            self._auto_return_hold_remaining_s = None
            self._set_flow_diversion_only()
        elif self._auto_force_diversion:
            can_start_return_timer = (
                water_hot is not None and predicted_hot is not None and
                float(water_hot) < self.AUTO_VALVE_RETURN_HOT_F and
                float(predicted_hot) < self.AUTO_FAN_PREDICTIVE_12V_F and
                roc_delta_heater <= 0.0 and roc_hot <= 0.0
            )
            if can_start_return_timer:
                if self._auto_below_return_since is None:
                    self._auto_below_return_since = now
                    self._auto_return_hold_remaining_s = int(self.AUTO_VALVE_RETURN_HOLD_S)
                elif (now - self._auto_below_return_since) >= self.AUTO_VALVE_RETURN_HOLD_S:
                    self._auto_force_diversion = False
                    self._auto_below_return_since = None
                    self._auto_return_hold_remaining_s = None
                    self._set_flow_main_only()
                else:
                    remaining = self.AUTO_VALVE_RETURN_HOLD_S - (now - self._auto_below_return_since)
                    self._auto_return_hold_remaining_s = max(0, int(remaining))
            else:
                self._auto_below_return_since = None
                self._auto_return_hold_remaining_s = None
        else:
            # Normal automatic baseline is main-loop only for shop heating.
            self._auto_return_hold_remaining_s = None
            self._set_flow_main_only()

        # ---------- Fan automatic logic ----------
        warmed_gate = (
            (air_heated is not None and float(air_heated) >= self.AUTO_FAN_WARM_AIR_F) or
            (delta_air is not None and float(delta_air) > self.AUTO_FAN_WARM_DELTA_AIR_F)
        )

        should_force_12v = (
            (predicted_hot is not None and predicted_hot >= self.AUTO_FAN_PREDICTIVE_12V_F) or
            (water_hot is not None and float(water_hot) >= 175.0) or
            (delta_heater is not None and float(delta_heater) >= 45.0) or
            (roc_delta_heater >= 10.0) or
            emergency_flow_collapse
        )

        if should_force_12v:
            desired_fan = "12v"
        elif warmed_gate:
            desired_fan = "5v"
        else:
            desired_fan = "off"
        self._auto_fan_target = desired_fan

        # Brief pulse while mostly OFF to avoid latent boil when near risk.
        near_risk_while_off = (
            desired_fan == "off" and predicted_hot is not None and predicted_hot >= 175.0
        )
        if near_risk_while_off:
            if (now - self._auto_last_off_pulse) >= 20.0:
                self._set_fan_mode_if_changed("5v")
                self._auto_last_off_pulse = now
                self._auto_reason = "Near-risk anti-boil pulse: forcing brief 5V while OFF target"
                return

        # If temperatures are rising, allow immediate transitions (even chatter).
        # If cooling, hold downshifts for a short period to avoid relay chatter.
        cooling_trend = roc_hot <= 0.0 and roc_delta_heater <= 0.0
        current_fan = self.current_fan_mode
        fan_order = {"off": 0, "5v": 1, "12v": 2}
        is_downshift = fan_order.get(desired_fan, 0) < fan_order.get(current_fan, 0)

        if not is_downshift:
            self._auto_pending_downstep = None
            self._set_fan_mode_if_changed(desired_fan)
            if emergency_flow_collapse:
                self._auto_reason = "Emergency flow collapse: forcing diversion + 12V"
            elif self._auto_force_diversion:
                self._auto_reason = "Diversion latched: predicted/actual hot exceeded 195F"
            elif should_force_12v:
                self._auto_reason = "Predictive safety cap near 185F: forcing 12V"
            elif warmed_gate:
                self._auto_reason = "Comfort gate met (air >= 60F or delta_air > 10F): running 5V"
            else:
                self._auto_reason = "Comfort gate not met: fans OFF to avoid cold blow"
            return

        if not cooling_trend:
            self._auto_pending_downstep = None
            self._set_fan_mode_if_changed(desired_fan)
            self._auto_reason = "Rising trend: immediate fan transition allowed"
            return

        if self._auto_pending_downstep is None or self._auto_pending_downstep.get("target") != desired_fan:
            self._auto_pending_downstep = {"target": desired_fan, "started": now}
            self._auto_reason = (
                f"Cooling trend: waiting {int(self.AUTO_COOLDOWN_DOWNSTEP_HOLD_S)}s before downshifting to {desired_fan.upper()}"
            )
            return

        if (now - self._auto_pending_downstep["started"]) >= self.AUTO_COOLDOWN_DOWNSTEP_HOLD_S:
            self._set_fan_mode_if_changed(desired_fan)
            self._auto_pending_downstep = None
            self._auto_reason = f"Cooling hold complete: downshifted to {desired_fan.upper()}"
    
    def set_save_enabled(self, state: bool):
        """
        Enable or disable data logging.
        When enabled, collects data every 5 seconds to be saved to CSV on shutdown.
        """
        old_state = self.save_enabled
        self.save_enabled = state
        
        if state and not old_state:
            # Just enabled - clear old data and start fresh session
            self.saved_data = []
            self.save_start_time = datetime.now()
            print(f"Data logging ENABLED - session started at {self.save_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        elif not state and old_state:
            # Just disabled - save the session now
            if self.saved_data:
                self.save_to_csv()
            print(f"Data logging DISABLED - {len(self.saved_data)} records saved")
    
    def set_graph_enabled(self, state: bool):
        """
        Enable or disable live graphing.
        When enabled, collects data every 5 seconds for real-time graphing.
        When disabled, saves session and clears data.
        """
        old_state = self.graph_enabled
        self.graph_enabled = state
        
        if state and not old_state:
            # Just enabled - clear old data and start fresh session
            self.graph_data = []
            self.graph_start_time = datetime.now()
            print(f"Live graphing ENABLED - session started at {self.graph_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        elif not state and old_state:
            # Just disabled - save the session
            if self.graph_data:
                self.save_graph_session()
            print(f"Live graphing DISABLED - {len(self.graph_data)} records saved")
            self.graph_data = []  # Clear data after saving
    
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
            'fan_voltage': data['fan_voltage'],
            'fan_mode': data['fan_mode'],
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
        Save collected data to a CSV file in data_logs/ subdirectory.
        Uses timestamp from when logging started (not shutdown).
        """
        if not self.saved_data or not self.save_start_time:
            print("No data to save")
            return
        
        # Generate filename with session START timestamp
        timestamp = self.save_start_time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"session_{timestamp}.csv"
        
        # Save to data_logs subdirectory
        data_dir = Path(__file__).parent / "data_logs"
        data_dir.mkdir(exist_ok=True)
        filepath = data_dir / filename
        
        # Define CSV fieldnames
        fieldnames = [
            'timestamp', 
            'water_hot', 'water_reservoir', 'water_mix', 'water_cold', 'air_cool', 'air_heated',
            'delta_water_heater', 'delta_water_radiator', 'delta_air',
            'flow_rate', 'fan_voltage', 'fan_mode', 'main_loop_state', 'diversion_state',
            'control_mode', 'flow_mode'
        ]
        
        try:
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.saved_data)
            
            print(f"✅ Saved {len(self.saved_data)} records to data_logs/{filename}")
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")
    
    def save_graph_session(self):
        """
        Save graph session data to JSON file in graph_sessions/ subdirectory.
        Uses timestamp from when graphing started.
        """
        if not self.graph_data or not self.graph_start_time:
            print("No graph data to save")
            return
        
        # Generate filename with session START timestamp
        timestamp = self.graph_start_time.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"graph_{timestamp}.json"
        
        # Save to graph_sessions subdirectory
        graph_dir = Path(__file__).parent / "graph_sessions"
        graph_dir.mkdir(exist_ok=True)
        filepath = graph_dir / filename
        
        # Calculate session duration
        duration_seconds = (datetime.now() - self.graph_start_time).total_seconds()
        
        # Create session metadata
        session_data = {
            'metadata': {
                'start_time': self.graph_start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': duration_seconds,
                'data_points': len(self.graph_data)
            },
            'data': self.graph_data
        }
        
        try:
            with open(filepath, 'w') as jsonfile:
                json.dump(session_data, jsonfile, indent=2)
            
            print(f"✅ Saved graph session ({len(self.graph_data)} points, {duration_seconds:.1f}s) to graph_sessions/{filename}")
        except Exception as e:
            print(f"❌ Error saving graph session: {e}")
    
    def cleanup(self):
        """Clean up all hardware resources and save data if needed."""
        print("Cleaning up hardware...")
        
        # Save data to CSV if we collected any
        if self.saved_data:
            self.save_to_csv()
        
        # Save graph session if we collected any
        if self.graph_data:
            self.save_graph_session()
        
        self.fan.cleanup()
        self.flow_meter.cleanup()
        self.valve_control.cleanup()
        print("Cleanup complete")


# Global controller instance
controller: Optional[ShopHeaterController] = None

# FastAPI app
app = FastAPI(title="Shop Heater Control")

# Mount static directories
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/data_logs", StaticFiles(directory="data_logs"), name="data_logs")
app.mount("/graph_sessions", StaticFiles(directory="graph_sessions"), name="graph_sessions")

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
        asyncio.create_task(automatic_control_loop())
        print("Background tasks created (sensor broadcast + data collection + automatic control)")
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


async def automatic_control_loop():
    """Background task that runs automatic control logic every 5 seconds."""
    print("Automatic control loop started")
    while True:
        await asyncio.sleep(5.0)

        if controller:
            try:
                controller.run_automatic_control()
            except Exception as e:
                print(f"Error in automatic control: {e}")
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
                manual_override_allowed = controller.control_mode == "manual"

                if 'fan_speed' in command:
                    if manual_override_allowed:
                        controller.set_fan_speed(int(command['fan_speed']))
                    else:
                        print("Ignoring fan_speed command in AUTOMATIC mode")
                
                if 'fan_mode' in command:
                    if manual_override_allowed:
                        controller.set_fan_mode(str(command['fan_mode']))
                    else:
                        print("Ignoring fan_mode command in AUTOMATIC mode")
                
                if 'main_loop' in command:
                    if manual_override_allowed:
                        controller.set_main_loop(bool(command['main_loop']))
                    else:
                        print("Ignoring main_loop command in AUTOMATIC mode")
                
                if 'diversion' in command:
                    if manual_override_allowed:
                        controller.set_diversion(bool(command['diversion']))
                    else:
                        print("Ignoring diversion command in AUTOMATIC mode")
                
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


@app.get("/controls")
async def read_controls():
    """Serve the controls page."""
    return FileResponse("controls.html")


@app.get("/graph")
async def read_graph():
    """Serve the graph page."""
    return FileResponse("graph.html")


@app.get("/explorer")
async def read_explorer():
    """Serve the data explorer page."""
    return FileResponse("explorer.html")


@app.get("/advanced")
async def read_advanced():
    """Serve the advanced analysis page."""
    return FileResponse("advanced.html")


@app.get("/api/sessions")
async def list_sessions():
    """List all CSV log sessions."""
    data_dir = Path(__file__).parent / "data_logs"
    sessions = []
    
    if data_dir.exists():
        for csv_file in sorted(data_dir.glob("session_*.csv"), reverse=True):
            stats = csv_file.stat()
            sessions.append({
                'filename': csv_file.name,
                'size': stats.st_size,
                'modified': stats.st_mtime,
                'type': 'csv'
            })
    
    return {"sessions": sessions}


@app.get("/api/session_data/{filename}")
async def get_session_data(filename: str):
    """Get full data from a CSV session file as JSON."""
    data_dir = Path(__file__).parent / "data_logs"
    filepath = data_dir / filename
    
    # Security: ensure filename is safe
    if not filename.startswith("session_") or not filename.endswith(".csv"):
        return {"error": "Invalid filename format"}
    
    if not filepath.exists():
        return {"error": "Session not found"}
    
    try:
        data = []
        with open(filepath, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Convert numeric strings to floats where applicable
                converted = {}
                for key, value in row.items():
                    if key == 'timestamp':
                        converted[key] = value
                    elif value.lower() in ('true', 'false'):
                        converted[key] = value.lower() == 'true'
                    else:
                        try:
                            converted[key] = float(value)
                        except (ValueError, TypeError):
                            converted[key] = value
                data.append(converted)
        
        return {"data": data, "count": len(data)}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/graph_sessions")
async def list_graph_sessions():
    """List all saved graph sessions."""
    graph_dir = Path(__file__).parent / "graph_sessions"
    sessions = []
    
    if graph_dir.exists():
        for json_file in sorted(graph_dir.glob("graph_*.json"), reverse=True):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    metadata = data.get('metadata', {})
                    sessions.append({
                        'filename': json_file.name,
                        'start_time': metadata.get('start_time'),
                        'end_time': metadata.get('end_time'),
                        'duration': metadata.get('duration_seconds'),
                        'data_points': metadata.get('data_points'),
                        'type': 'graph'
                    })
            except Exception as e:
                print(f"Error reading {json_file}: {e}")
    
    return {"sessions": sessions}


@app.get("/api/load_session/{filename}")
async def load_session(filename: str):
    """Load a specific graph session."""
    graph_dir = Path(__file__).parent / "graph_sessions"
    filepath = graph_dir / filename
    
    # Security: ensure filename doesn't contain path traversal
    if ".." in filename or "/" in filename:
        return {"error": "Invalid filename"}
    
    if not filepath.exists():
        return {"error": "Session not found"}
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


@app.delete("/api/delete_graph_session/{filename}")
async def delete_graph_session(filename: str):
    """Delete a specific graph session file."""
    graph_dir = Path(__file__).parent / "graph_sessions"
    filepath = graph_dir / filename
    
    # Security: ensure filename doesn't contain path traversal
    if ".." in filename or "/" in filename:
        return {"success": False, "error": "Invalid filename"}
    
    # Ensure it's a graph file
    if not filename.startswith("graph_") or not filename.endswith(".json"):
        return {"success": False, "error": "Invalid file type"}
    
    if not filepath.exists():
        return {"success": False, "error": "Session not found"}
    
    try:
        filepath.unlink()  # Delete the file
        print(f"🗑️ Deleted graph session: {filename}")
        return {"success": True, "message": f"Deleted {filename}"}
    except Exception as e:
        print(f"❌ Error deleting graph session {filename}: {e}")
        return {"success": False, "error": str(e)}


@app.delete("/api/delete_csv_session/{filename}")
async def delete_csv_session(filename: str):
    """Delete a specific CSV data log file."""
    data_dir = Path(__file__).parent / "data_logs"
    filepath = data_dir / filename
    
    # Security: ensure filename doesn't contain path traversal
    if ".." in filename or "/" in filename:
        return {"success": False, "error": "Invalid filename"}
    
    # Ensure it's a CSV file
    if not filename.startswith("session_") or not filename.endswith(".csv"):
        return {"success": False, "error": "Invalid file type"}
    
    if not filepath.exists():
        return {"success": False, "error": "Session not found"}
    
    try:
        filepath.unlink()  # Delete the file
        print(f"🗑️ Deleted CSV session: {filename}")
        return {"success": True, "message": f"Deleted {filename}"}
    except Exception as e:
        print(f"❌ Error deleting CSV session {filename}: {e}")
        return {"success": False, "error": str(e)}


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
    import socket
    
    # Get local IP address for LAN access
    def get_local_ip():
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "localhost"
    
    local_ip = get_local_ip()
    
    print("=" * 60)
    print("Shop Heater Web Server")
    print("=" * 60)
    print("Starting server...")
    print("")
    print("Access from this device:")
    print(f"  http://localhost:8000")
    print("")
    print("Access from other devices on your network:")
    print(f"  http://{local_ip}:8000")
    print("")
    print("Available pages:")
    print("  - Dashboard:  /")
    print("  - Controls:   /controls")
    print("  - Live Graph: /graph")
    print("  - Explorer:   /explorer")
    print("  - Advanced:   /advanced")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\nShutting down...")


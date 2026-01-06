#!/usr/bin/env python3
"""
SHOPHEATER3000 - Basic Integration Example

Demonstrates how to use all four modules together in a single script.
This is a simple temperature-based fan control example.
"""

import time
import signal
import sys

# Import all the controller classes
from bts7960_controller import BTS7960Controller
from ds18b20_reader import DS18B20Reader
from flowmeter import FlowMeter
from relay_control import RelayController


class ShopHeater:
    """
    Integrated shop heater control system.clear
    
    
    Combines fan control, temperature sensing, flow measurement,
    and valve control into a unified system.
    """
    
    def __init__(self):
        """Initialize all modules."""
        print("Initializing SHOPHEATER3000...")
        
        # Initialize modules
        self.fan = BTS7960Controller(rpwm_pin=18, pwm_freq=10000)
        self.temp_reader = DS18B20Reader()
        self.flow_meter = FlowMeter(gpio_pin=27)
        self.valve_control = RelayController()
        
        # Set initial state
        self.valve_control.mainLoop()  # Normal flow path
        self.fan.set_speed(0)  # Fans off
        
        # Initialize flow rate tracking
        self.flow_meter.getFlowRate()
        
        print("All modules initialized.")
        print("GPIO pin allocation:")
        print("  GPIO 4  - DS18B20 Temperature Sensor")
        print("  GPIO 18 - BTS7960 Fan Control (PWM)")
        print("  GPIO 23 - Relay (Normal Solenoid)")
        print("  GPIO 24 - Relay (Diversion Solenoid)")
        print("  GPIO 27 - Flow Meter Pulse Counter")
        print()
    
    def read_sensors(self):
        """
        Read all sensors and return current state.
        
        Returns:
            dict: Current system state with sensor readings
        """
        temps = self.temp_reader.read_all_temperatures()
        temp_c = list(temps.values())[0] if temps else None
        temp_f = (temp_c * 9/5) + 32 if temp_c is not None else None
        
        flow_rate_lpm = self.flow_meter.getFlowRate()
        total_liters = self.flow_meter.get_flow_liters()
        total_pounds = self.flow_meter.get_flow_pounds()
        
        return {
            'temp_c': temp_c,
            'temp_f': temp_f,
            'flow_rate_lpm': flow_rate_lpm,
            'total_liters': total_liters,
            'total_pounds': total_pounds
        }
    
    def temperature_control(self, temp_f):
        """
        Adjust fan speed based on temperature.
        
        Args:
            temp_f: Temperature in Fahrenheit
        
        Returns:
            int: Fan speed percentage set
        """
        if temp_f is None:
            return 0
        
        # Simple temperature-based fan control
        if temp_f < 140:      # Below 140°F
            fan_speed = 30
        elif temp_f < 158:    # 140-158°F
            fan_speed = 50
        elif temp_f < 176:    # 158-176°F
            fan_speed = 70
        else:                 # Above 176°F
            fan_speed = 90
        
        self.fan.set_speed(fan_speed)
        return fan_speed
    
    def run(self, interval=2):
        """
        Main monitoring loop.
        
        Args:
            interval: Seconds between readings (default: 2)
        """
        print("Starting monitoring loop...")
        print("Press Ctrl+C to stop")
        print()
        print("-" * 80)
        
        try:
            while True:
                # Read all sensors
                state = self.read_sensors()
                
                # Control fan based on temperature
                if state['temp_f'] is not None:
                    fan_speed = self.temperature_control(state['temp_f'])
                    
                    # Display status
                    print(f"[{time.strftime('%H:%M:%S')}] "
                          f"Temp: {state['temp_f']:.1f}°F ({state['temp_c']:.1f}°C) | "
                          f"Fan: {fan_speed:2d}% | "
                          f"Flow: {state['flow_rate_lpm']:.2f} L/min | "
                          f"Total: {state['total_pounds']:.2f} lbs ({state['total_liters']:.2f} L)")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] ERROR: Cannot read temperature sensor")
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n\nShutdown requested...")
    
    def cleanup(self):
        """Clean up all GPIO resources."""
        print("Cleaning up GPIO resources...")
        
        try:
            self.fan.stop()
            self.fan.cleanup()
            print("  ✓ Fan controller cleaned up")
        except Exception as e:
            print(f"  ✗ Fan cleanup error: {e}")
        
        try:
            self.flow_meter.cleanup()
            print("  ✓ Flow meter cleaned up")
        except Exception as e:
            print(f"  ✗ Flow meter cleanup error: {e}")
        
        try:
            self.valve_control.cleanup()
            print("  ✓ Valve control cleaned up")
        except Exception as e:
            print(f"  ✗ Valve control cleanup error: {e}")
        
        print("Cleanup complete.")


def main():
    """Main entry point."""
    heater = None
    
    # Setup signal handler for clean shutdown
    def signal_handler(sig, frame):
        print("\n\nSignal received, shutting down...")
        if heater:
            heater.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize and run
        heater = ShopHeater()
        heater.run(interval=2)
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if heater:
            heater.cleanup()


if __name__ == "__main__":
    main()


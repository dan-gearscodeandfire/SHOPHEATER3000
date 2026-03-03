#!/usr/bin/env python3
"""
SHOPHEATER3000 - Basic Integration Example

Demonstrates how to use all four modules together in a single script.
This is a simple temperature-based fan mode control example.
"""

import time
import signal
import sys

# Import all the controller classes
from fan_relay_controller import FanRelayController
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
        self.fan = FanRelayController(fan_onoff_pin=18, voltage_select_pin=17)
        self.temp_reader = DS18B20Reader()
        self.flow_meter = FlowMeter(gpio_pin=27)
        self.valve_control = RelayController()
        
        # Set initial state
        self.valve_control.mainLoop()  # Normal flow path
        self.fan.set_mode("12v")  # Default relay fail-safe state
        
        # Initialize flow rate tracking
        self.flow_meter.getFlowRate()
        
        print("All modules initialized.")
        print("GPIO pin allocation:")
        print("  GPIO 4  - DS18B20 Temperature Sensor")
        print("  GPIO 18 - Fan ON/OFF relay (NC ON, NO OFF)")
        print("  GPIO 17 - Fan voltage relay (NC 12V, NO 5V)")
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
        Adjust fan mode based on temperature.
        
        Args:
            temp_f: Temperature in Fahrenheit
        
        Returns:
            str: Fan mode set
        """
        if temp_f is None:
            return "off"
        
        # Simple temperature-based fan control using relay modes
        if temp_f < 140:      # Below 140°F
            fan_mode = "5v"
        elif temp_f < 158:    # 140-158°F
            fan_mode = "5v"
        elif temp_f < 176:    # 158-176°F
            fan_mode = "12v"
        else:                 # Above 176°F
            fan_mode = "12v"
        
        self.fan.set_mode(fan_mode)
        return fan_mode
    
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
                    fan_mode = self.temperature_control(state['temp_f'])
                    
                    # Display status
                    print(f"[{time.strftime('%H:%M:%S')}] "
                          f"Temp: {state['temp_f']:.1f}°F ({state['temp_c']:.1f}°C) | "
                          f"Fan: {fan_mode.upper():>3} | "
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


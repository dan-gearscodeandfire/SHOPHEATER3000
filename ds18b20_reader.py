#!/usr/bin/env python3
"""
DS18B20 Temperature Sensor Reader
A basic class for reading temperatures from DS18B20 sensors on the 1-Wire bus.
"""

import time
from typing import List, Dict, Optional
from w1thermsensor import W1ThermSensor, Sensor


class DS18B20Reader:
    """
    A class to read temperatures from DS18B20 sensors on the 1-Wire bus.
    
    Automatically configures all discovered sensors to 10-bit resolution
    when sensors are detected or refreshed. This ensures consistent
    behavior for all sensors on the bus.
    """
    
    def __init__(self):
        """Initialize the DS18B20 reader and discover available sensors."""
        self.sensors: List[W1ThermSensor] = []
        self._discover_sensors()
    
    def _discover_sensors(self) -> None:
        """
        Discover all available DS18B20 sensors on the bus.
        Automatically sets all discovered sensors to 10-bit resolution.
        """
        try:
            self.sensors = W1ThermSensor.get_available_sensors([Sensor.DS18B20])
            # Automatically set all discovered sensors to 10-bit resolution
            self._auto_set_resolution()
        except Exception as e:
            print(f"Warning: Error discovering sensors: {e}")
            self.sensors = []
    
    def _auto_set_resolution(self) -> None:
        """
        Automatically set all discovered sensors to 10-bit resolution.
        This ensures future devices are always configured correctly.
        Fails silently if resolution cannot be set (e.g., permission issues).
        """
        for sensor in self.sensors:
            try:
                sensor.set_resolution(10)
            except Exception as e:
                # Fail silently - resolution setting may require root permissions
                # This is expected behavior and shouldn't break normal operation
                pass
    
    def get_sensor_addresses(self) -> List[str]:
        """
        Get a list of all sensor addresses (IDs) on the bus.
        
        Returns:
            List of sensor addresses as strings
        """
        return [sensor.id for sensor in self.sensors]
    
    def read_all_temperatures(self) -> Dict[str, Optional[float]]:
        """
        Read temperatures from all discovered sensors.
        
        Returns:
            Dictionary mapping sensor addresses to temperatures (Celsius).
            Returns None for sensors that fail to read.
        """
        results = {}
        for sensor in self.sensors:
            try:
                temperature = sensor.get_temperature()
                results[sensor.id] = temperature
            except Exception as e:
                print(f"Error reading sensor {sensor.id}: {e}")
                results[sensor.id] = None
        return results
    
    def read_temperature(self, sensor_id: str) -> Optional[float]:
        """
        Read temperature from a specific sensor by ID.
        
        Args:
            sensor_id: The address/ID of the sensor to read
            
        Returns:
            Temperature in Celsius, or None if read fails
        """
        for sensor in self.sensors:
            if sensor.id == sensor_id:
                try:
                    return sensor.get_temperature()
                except Exception as e:
                    print(f"Error reading sensor {sensor_id}: {e}")
                    return None
        print(f"Sensor {sensor_id} not found")
        return None
    
    def refresh_sensors(self) -> None:
        """
        Re-scan the bus for sensors (useful if sensors are added/removed).
        Automatically sets all newly discovered sensors to 10-bit resolution.
        """
        self._discover_sensors()
    
    def set_resolution(self, sensor_id: str, resolution: int) -> bool:
        """
        Set the resolution for a specific sensor.
        
        Args:
            sensor_id: The address/ID of the sensor
            resolution: Resolution in bits (9, 10, 11, or 12)
            
        Returns:
            True if successful, False otherwise
            
        Note:
            This operation requires root permissions. You may need to run
            your script with sudo or ensure the user has write access to
            the sensor device files.
        """
        if resolution not in [9, 10, 11, 12]:
            raise ValueError("Resolution must be 9, 10, 11, or 12 bits")
        
        for sensor in self.sensors:
            if sensor.id == sensor_id:
                try:
                    sensor.set_resolution(resolution)
                    return True
                except Exception as e:
                    print(f"Error setting resolution for sensor {sensor_id}: {e}")
                    print("Note: Setting resolution may require root permissions")
                    return False
        print(f"Sensor {sensor_id} not found")
        return False
    
    def set_all_resolution(self, resolution: int) -> Dict[str, bool]:
        """
        Set the resolution for all discovered sensors.
        
        Args:
            resolution: Resolution in bits (9, 10, 11, or 12)
            
        Returns:
            Dictionary mapping sensor IDs to success status
        """
        results = {}
        for sensor in self.sensors:
            results[sensor.id] = self.set_resolution(sensor.id, resolution)
        return results
    
    def get_resolution(self, sensor_id: str) -> Optional[int]:
        """
        Get the current resolution for a specific sensor.
        
        Args:
            sensor_id: The address/ID of the sensor
            
        Returns:
            Resolution in bits, or None if sensor not found
        """
        for sensor in self.sensors:
            if sensor.id == sensor_id:
                try:
                    return sensor.get_resolution()
                except Exception as e:
                    print(f"Error getting resolution for sensor {sensor_id}: {e}")
                    return None
        print(f"Sensor {sensor_id} not found")
        return None


def main():
    """
    Main demonstration loop that outputs sensor addresses and temperatures
    once every second.
    """
    print("Initializing DS18B20 sensor reader...")
    reader = DS18B20Reader()
    
    # Display discovered sensors
    addresses = reader.get_sensor_addresses()
    if not addresses:
        print("No DS18B20 sensors found on the bus.")
        print("Make sure:")
        print("  1. 1-Wire interface is enabled (modprobe w1-gpio w1-therm)")
        print("  2. Sensors are properly connected")
        print("  3. Pull-up resistor (4.7kΩ) is connected between data and 3.3V")
        return
    
    print(f"Found {len(addresses)} sensor(s) on the bus:")
    for addr in addresses:
        print(f"  - {addr}")
    print("\nStarting temperature readings (1 second intervals)...")
    print("-" * 60)
    
    try:
        while True:
            temperatures = reader.read_all_temperatures()
            
            print(f"\n[{time.strftime('%H:%M:%S')}] Temperature readings:")
            for sensor_id, temp in temperatures.items():
                if temp is not None:
                    print(f"  Sensor {sensor_id}: {temp:.2f}°C")
                else:
                    print(f"  Sensor {sensor_id}: [READ ERROR]")
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nStopped by user.")


if __name__ == "__main__":
    main()


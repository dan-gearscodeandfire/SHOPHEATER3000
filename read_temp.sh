#!/bin/bash
# Quick temperature reading script for SHOPHEATER3000

cd ~/SHOPHEATER3000
source .venv/bin/activate

python3 << 'EOF'
from ds18b20_reader import DS18B20Reader

# Initialize reader
reader = DS18B20Reader()

# Get sensor addresses
addresses = reader.get_sensor_addresses()

if not addresses:
    print("ERROR: No DS18B20 sensors found!")
    print("Make sure:")
    print("  1. Sensor is connected to GPIO 4 (Pin 7)")
    print("  2. 1-Wire interface is enabled in /boot/firmware/config.txt")
    print("     dtoverlay=w1-gpio,gpiopin=4")
    exit(1)

print(f"Found {len(addresses)} sensor(s)")
print()

# Read all temperatures
temps = reader.read_all_temperatures()

for sensor_id, temp_c in temps.items():
    if temp_c is not None:
        temp_f = (temp_c * 9/5) + 32
        print(f"Sensor: {sensor_id}")
        print(f"  Temperature: {temp_c:.2f}°C ({temp_f:.2f}°F)")
    else:
        print(f"Sensor: {sensor_id}")
        print(f"  Temperature: [READ ERROR]")

EOF


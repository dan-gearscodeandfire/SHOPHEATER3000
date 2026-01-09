#!/bin/bash
# Read temperature with 10-bit resolution (requires sudo for resolution setting)

cd ~/SHOPHEATER3000
sudo .venv/bin/python3 -c "
from ds18b20_reader import DS18B20Reader

# Initialize reader (will set 10-bit resolution with sudo)
reader = DS18B20Reader()

# Get sensor addresses
addresses = reader.get_sensor_addresses()

if not addresses:
    print('ERROR: No DS18B20 sensors found!')
    exit(1)

print(f'Found {len(addresses)} sensor(s) - 10-bit resolution set')
print()

# Read all temperatures
temps = reader.read_all_temperatures()

for sensor_id, temp_c in temps.items():
    if temp_c is not None:
        temp_f = (temp_c * 9/5) + 32
        print(f'Sensor: {sensor_id}')
        print(f'  Temperature: {temp_c:.1f}°C ({temp_f:.1f}°F)')
    else:
        print(f'Sensor: {sensor_id}')
        print(f'  Temperature: [READ ERROR]')
"


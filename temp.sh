#!/bin/bash
# Ultra-simple temperature one-liner
cd ~/SHOPHEATER3000 && source .venv/bin/activate && python3 -c "
from ds18b20_reader import DS18B20Reader
temps = DS18B20Reader().read_all_temperatures()
for t in temps.values():
    if t: print(f'{t:.1f}°C ({t*9/5+32:.1f}°F)')
"


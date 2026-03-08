# Automatic Mode Flowchart

Decision-tree view of the `automatic` control loop in `shopheater3000.py` (runs every 5 seconds).

```mermaid
flowchart TD
    A[Automatic loop tick every 5s] --> B{control_mode == automatic?}
    B -- No --> B1[Set status: automatic inactive\nReturn]
    B -- Yes --> C[Read sensors\nCompute delta_heater, delta_air,\nroc_hot, roc_delta_heater,\npredicted_hot]

    %% -------------------------
    %% Valve branch
    %% -------------------------
    C --> V0{Emergency flow collapse?\nflow < 0.5 AND water_hot >= 170}
    V0 -- Yes --> V1[Latch diversion\nmain=OFF diversion=ON]
    V0 -- No --> V2{predicted_hot >= 193\nOR water_hot >= 193}
    V2 -- Yes --> V1
    V2 -- No --> V3{Diversion currently latched?}

    V3 -- No --> V4[Set normal valves\nmain=ON diversion=OFF]
    V3 -- Yes --> V5{Cooldown release conditions met?\nwater_hot < 180\nAND predicted_hot < 183\nAND roc_hot <= 0\nAND roc_delta_heater <= 0}
    V5 -- No --> V6[Keep diversion latched\nReset return timer]
    V5 -- Yes --> V7{Return timer >= 120s?}
    V7 -- No --> V8[Keep diversion latched\nUpdate remaining timer]
    V7 -- Yes --> V9[Unlatch diversion\nSet main=ON diversion=OFF]

    %% -------------------------
    %% Fan branch
    %% -------------------------
    C --> F0{Force 12V condition?\npredicted_hot >= 183\nOR water_hot >= 175\nOR delta_heater >= 45\nOR roc_delta_heater >= 10\nOR emergency flow collapse}
    F0 -- Yes --> F1[desired_fan = 12V]
    F0 -- No --> F2{Comfort gate met?\nair_heated >= 60\nOR delta_air > 10}
    F2 -- Yes --> F3[desired_fan = 5V]
    F2 -- No --> F4[desired_fan = OFF]

    %% Probe pulse (only when desired OFF)
    F4 --> P0{Probe eligible?\nwater_hot > 100}
    P0 -- No --> P9[No probe]
    P0 -- Yes --> P1{Probe window active?}
    P1 -- Yes --> P2[Force fan = 5V\nProbe active]
    P1 -- No --> P3{Probe interval elapsed?\n>= 60s since last probe}
    P3 -- Yes --> P4[Start probe window 15s\nForce fan = 5V]
    P3 -- No --> P9

    %% Anti-boil pulse (only when desired OFF and no active probe override)
    P9 --> AB0{Near-risk OFF pulse?\npredicted_hot >= 175\nAND pulse interval elapsed}
    AB0 -- Yes --> AB1[Brief force fan = 5V\nReturn]
    AB0 -- No --> D0[Proceed with desired_fan]

    %% If probe active or started, loop returns early
    P2 --> Z[Return]
    P4 --> Z

    %% Downshift / upshift resolution
    F1 --> D0
    F3 --> D0

    D0 --> D1{Downshift?\ndesired < current}
    D1 -- No --> D2[Set fan immediately to desired\nClear downshift pending]
    D1 -- Yes --> D3{Cooling trend?\nroc_hot <= 0 AND roc_delta_heater <= 0}
    D3 -- No --> D4[Set fan immediately to desired\nClear downshift pending]
    D3 -- Yes --> D5{Pending downshift target matches?}
    D5 -- No --> D6[Start pending downshift timer\nReturn]
    D5 -- Yes --> D7{Hold >= 25s?}
    D7 -- No --> D8[Keep current fan\nReturn]
    D7 -- Yes --> D9[Apply downshift\nClear pending]

    D2 --> Z
    D4 --> Z
    D6 --> Z
    D8 --> Z
    D9 --> Z

    %% Final
    V1 --> Z
    V4 --> Z
    V6 --> Z
    V8 --> Z
    V9 --> Z
    AB1 --> Z
```

## Notes

- This diagram reflects threshold values currently in code (`183F`, `193F`, etc.).
- The fan probe pulse exists to keep `delta_air` measurable when comfort logic would otherwise keep fans OFF.
- In automatic mode, direct manual fan/valve commands are ignored server-side.

#!/usr/bin/env python3
"""
Fan relay control for SHOPHEATER3000.

Hardware wiring (intentional fail-safe defaults):
- GPIO18: Fan ON/OFF relay
  - NC (GPIO LOW / relay de-energized) = fans ON
  - NO (GPIO HIGH / relay energized)   = fans OFF
- GPIO17: Supply select relay
  - NC (GPIO LOW / relay de-energized) = 12V
  - NO (GPIO HIGH / relay energized)   = 5V

Modes:
- off  -> fans OFF, leave voltage relay unchanged
- 5v   -> select 5V and turn fans ON
- 12v  -> select 12V and turn fans ON
"""

import lgpio


class FanRelayController:
    """Controls fan power using two relays."""

    def __init__(self, fan_onoff_pin: int = 18, voltage_select_pin: int = 17):
        self.fan_onoff_pin = fan_onoff_pin
        self.voltage_select_pin = voltage_select_pin

        self._chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(self._chip, self.fan_onoff_pin)
        lgpio.gpio_claim_output(self._chip, self.voltage_select_pin)

        # Track the configured voltage source so OFF can preserve it.
        self.current_voltage_mode = "12v"

        # Default safe relay state: fans ON at 12V (both relays at NC).
        self.select_12v()
        self.turn_on()

    def turn_on(self) -> None:
        """Set ON/OFF relay to NC path (fans ON)."""
        lgpio.gpio_write(self._chip, self.fan_onoff_pin, 0)

    def turn_off(self) -> None:
        """Set ON/OFF relay to NO path (fans OFF)."""
        lgpio.gpio_write(self._chip, self.fan_onoff_pin, 1)

    def select_5v(self) -> None:
        """Set supply relay to NO path (5V)."""
        lgpio.gpio_write(self._chip, self.voltage_select_pin, 1)
        self.current_voltage_mode = "5v"

    def select_12v(self) -> None:
        """Set supply relay to NC path (12V)."""
        lgpio.gpio_write(self._chip, self.voltage_select_pin, 0)
        self.current_voltage_mode = "12v"

    def set_mode(self, mode: str) -> str:
        """
        Set fan mode and return normalized mode.

        Accepts: 'off', '5v', '12v' (case-insensitive).
        """
        normalized = mode.lower().strip()
        if normalized not in {"off", "5v", "12v"}:
            raise ValueError(f"Invalid fan mode: {mode}")

        if normalized == "off":
            self.turn_off()
        elif normalized == "5v":
            self.select_5v()
            self.turn_on()
        else:
            self.select_12v()
            self.turn_on()

        return normalized

    def cleanup(self) -> None:
        """Release GPIO resources."""
        try:
            lgpio.gpiochip_close(self._chip)
        except Exception:
            pass

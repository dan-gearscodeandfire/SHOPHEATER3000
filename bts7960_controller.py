"""
BTS7960 Motor Driver Controller for Raspberry Pi
Controls two 12V fans in parallel via BTS7960 motor driver

SIMPLIFIED VERSION - Based on working ESP32 configuration
Hardware requirements:
- R_EN and L_EN tied to VCC (both HIGH)
- LPWM tied to GND (reverse disabled)
- Only RPWM controlled via GPIO for speed

Migrated to lgpio for compatibility with Raspberry Pi kernel 6.6+
"""

import lgpio
import time


class BTS7960Controller:
    """
    Controls fan speed via BTS7960 motor driver using lgpio.
    
    SIMPLIFIED wiring for unidirectional control:
    - RPWM  -> GPIO18 (Pin 12) - PWM speed control
    - VCC   -> 5V
    - GND   -> GND
    
    On BTS7960 board (jumpers):
    - R_EN  -> VCC (tied HIGH)
    - L_EN  -> VCC (tied HIGH)
    - LPWM  -> GND (tied LOW)
    """
    
    def __init__(self, rpwm_pin=18, pwm_freq=10000):
        """
        Initialize BTS7960 controller with lgpio.
        
        Args:
            rpwm_pin: GPIO pin for RPWM (default: 18)
            pwm_freq: PWM frequency in Hz (default: 10000 - maximum lgpio supports, minimizes audible noise)
        """
        self.rpwm_pin = rpwm_pin
        self.pwm_freq = pwm_freq
        self.chip = None
        self.current_speed = 0  # Track current speed for kick-start logic
        
        # Open GPIO chip
        try:
            self.chip = lgpio.gpiochip_open(0)
        except Exception as e:
            raise RuntimeError(
                f"Failed to open GPIO chip. Make sure you have proper permissions.\n"
                f"You may need to be in the 'gpio' group.\n"
                f"Original error: {e}"
            )
        
        # Configure RPWM pin as output
        try:
            lgpio.gpio_claim_output(self.chip, self.rpwm_pin)
        except Exception as e:
            lgpio.gpiochip_close(self.chip)
            raise RuntimeError(
                f"Failed to setup GPIO {self.rpwm_pin}. Pin may be in use.\n"
                f"Original error: {e}"
            )
        
        # Initialize PWM on RPWM pin
        # lgpio uses frequency and duty cycle (0-100)
        # Start with 0% duty cycle (fans off)
        lgpio.tx_pwm(self.chip, self.rpwm_pin, self.pwm_freq, 0)
    
    def set_speed(self, speed):
        """
        Set fan speed with kick-start feature.
        
        When transitioning from 0 speed to any non-zero speed, briefly run
        at full speed (99%) for 1 second to help fans start smoothly.
        
        Args:
            speed: Integer value 0-99 representing speed percentage
                   (values >= 100 are capped to 99)
        """
        # Cap speed at 99 if 100 or greater is provided
        if speed >= 100:
            speed = 99
        
        # Clamp to valid range 0-99
        speed = max(0, min(99, speed))
        
        # Kick-start logic: if transitioning from 0 to non-zero speed
        if self.current_speed == 0 and speed > 0:
            # Run at full speed for 1 second
            lgpio.tx_pwm(self.chip, self.rpwm_pin, self.pwm_freq, 99)
            time.sleep(1)
        
        # Set PWM duty cycle on RPWM to desired speed
        lgpio.tx_pwm(self.chip, self.rpwm_pin, self.pwm_freq, speed)
        
        # Update current speed tracker
        self.current_speed = speed
    
    def stop(self):
        """Stop the fans (set speed to 0)."""
        lgpio.tx_pwm(self.chip, self.rpwm_pin, self.pwm_freq, 0)
        self.current_speed = 0
    
    def cleanup(self):
        """Clean up GPIO resources."""
        try:
            # Stop PWM
            lgpio.tx_pwm(self.chip, self.rpwm_pin, self.pwm_freq, 0)
            # Free the GPIO pin
            lgpio.gpio_free(self.chip, self.rpwm_pin)
            # Close the chip
            lgpio.gpiochip_close(self.chip)
        except:
            pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()

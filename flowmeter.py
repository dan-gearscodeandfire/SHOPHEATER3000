"""
Flow Meter Pulse Counter for Raspberry Pi

This module provides a non-blocking flow meter pulse counter class that
reads pulses from a Digiten FL-408 water flow sensor connected to GPIO 27.

The FL-408 uses a Hall effect sensor and outputs square wave pulses.
Frequency (Hz) = 7.5 × Flow Rate (L/min)
450 pulses = 1 liter of water

Future conversion: 3,119 pulses = 19.9 pounds of water
"""

import lgpio
import threading
import time


class FlowMeter:
    """
    Non-blocking flow meter pulse counter.
    
    Uses GPIO interrupts to count pulses without blocking the main thread.
    Designed for portability and easy integration with other codebases.
    
    Attributes:
        gpio_pin (int): GPIO pin number (default: 18)
        pulse_count (int): Total number of pulses counted since initialization
        pulses_per_pound (float): Conversion factor (pulses per pound of water)
        lock (threading.Lock): Thread lock for thread-safe pulse counting
    """
    
    # Conversion factor: 3,119 pulses = 19.9 pounds of water
    # Empirically measured with known weight of water on this specific FL-408 sensor
    PULSES_PER_POUND = 3119 / 19.9  # Approximately 156.73 pulses per pound
    
    # lgpio edge constants
    RISING = lgpio.RISING_EDGE
    FALLING = lgpio.FALLING_EDGE
    BOTH = lgpio.BOTH_EDGES
    
    def __init__(self, gpio_pin=27, pulses_per_pound=None, edge=None, pull_up_down=None):
        """
        Initialize the flow meter.
        
        Args:
            gpio_pin (int): GPIO pin number to monitor (default: 27)
            pulses_per_pound (float, optional): Custom conversion factor.
                If None, uses the default: 3119 pulses = 19.9 pounds
                (empirically measured with known weight of water)
            edge (int, optional): Edge to detect. FALLING (default), 
                RISING, or BOTH. For FL-408 sensor at 3.3V, FALLING edge works best.
            pull_up_down (int, optional): Pull resistor configuration.
                lgpio.SET_PULL_UP (default) or lgpio.SET_PULL_DOWN.
                FL-408 at 3.3V works best with SET_PULL_UP and FALLING edge.
        """
        self.gpio_pin = gpio_pin
        self.pulse_count = 0
        self.lock = threading.Lock()
        self.edge = edge if edge is not None else self.FALLING
        self.pull_up_down = pull_up_down if pull_up_down is not None else lgpio.SET_PULL_UP
        
        # Flow rate tracking
        self.last_flow_check_time = time.time()
        self.last_flow_check_pulses = 0
        
        # Set conversion factor
        if pulses_per_pound is None:
            self.pulses_per_pound = self.PULSES_PER_POUND
        else:
            self.pulses_per_pound = pulses_per_pound
        
        # Open GPIO chip
        try:
            self.chip = lgpio.gpiochip_open(0)
        except Exception as e:
            raise RuntimeError(
                f"Failed to open GPIO chip. Make sure you have proper permissions.\n"
                f"You may need to be in the 'gpio' group.\n"
                f"Original error: {e}"
            )
        
        # Setup pin as input with pull resistor
        try:
            lgpio.gpio_claim_input(self.chip, self.gpio_pin, self.pull_up_down)
        except Exception as e:
            # Pin might be busy - try to free it first and retry
            try:
                lgpio.gpio_free(self.chip, self.gpio_pin)
                time.sleep(0.1)
                lgpio.gpio_claim_input(self.chip, self.gpio_pin, self.pull_up_down)
            except Exception as e2:
                lgpio.gpiochip_close(self.chip)
                raise RuntimeError(
                    f"Failed to setup GPIO {self.gpio_pin}. Pin may be in use.\n"
                    f"Try: ps aux | grep python | grep -v grep\n"
                    f"And kill any conflicting processes.\n"
                    f"Original error: {e}"
                )
        
        # Setup alert (edge detection) with callback
        try:
            # Set up edge detection
            lgpio.gpio_claim_alert(self.chip, self.gpio_pin, self.edge)
            
            # Register callback
            self.callback_id = lgpio.callback(
                self.chip,
                self.gpio_pin,
                self.edge,
                self._pulse_callback
            )
        except Exception as e:
            lgpio.gpio_free(self.chip, self.gpio_pin)
            lgpio.gpiochip_close(self.chip)
            raise RuntimeError(
                f"Failed to add edge detection on GPIO {self.gpio_pin}.\n"
                f"Original error: {e}"
            )
    
    def _pulse_callback(self, chip, gpio, level, tick):
        """
        Internal callback function for GPIO interrupt.
        Increments pulse count in a thread-safe manner.
        
        Args:
            chip (int): GPIO chip handle
            gpio (int): GPIO pin number
            level (int): Pin level (0 or 1)
            tick (int): Timestamp in microseconds
        """
        with self.lock:
            self.pulse_count += 1
    
    def get_pulse_count(self):
        """
        Get the current pulse count.
        
        Returns:
            int: Total number of pulses counted since initialization
        """
        with self.lock:
            return self.pulse_count
    
    def reset(self):
        """
        Reset the pulse count to zero.
        Also resets flow rate tracking.
        """
        with self.lock:
            self.pulse_count = 0
            self.last_flow_check_time = time.time()
            self.last_flow_check_pulses = 0
    
    def get_flow_pounds(self):
        """
        Convert pulse count to pounds of water.
        Uses empirically measured calibration: 3,119 pulses = 19.9 pounds.
        
        Returns:
            float: Pounds of water based on pulse count and measured calibration
        """
        with self.lock:
            return self.pulse_count / self.pulses_per_pound
    
    def get_flow_liters(self):
        """
        Convert pulse count to liters of water (FL-408 specific).
        FL-408: 450 pulses = 1 liter
        
        Returns:
            float: Total liters of water based on pulse count
        """
        with self.lock:
            return self.pulse_count / 450.0
    
    def getFlowRate(self):
        """
        Calculate current flow rate in liters per minute.
        Measures pulses since last call to determine instantaneous flow rate.
        
        Returns:
            float: Current flow rate in liters per minute (L/min)
        
        Example:
            fm = FlowMeter()
            # First call establishes baseline
            rate1 = fm.getFlowRate()  # Returns 0.0 on first call
            time.sleep(2)
            rate2 = fm.getFlowRate()  # Returns actual flow rate
        """
        current_time = time.time()
        
        with self.lock:
            current_pulses = self.pulse_count
            time_elapsed = current_time - self.last_flow_check_time
            pulses_elapsed = current_pulses - self.last_flow_check_pulses
            
            # Update tracking variables for next call
            self.last_flow_check_time = current_time
            self.last_flow_check_pulses = current_pulses
        
        # Avoid division by zero on very first call
        if time_elapsed < 0.001:
            return 0.0
        
        # Calculate flow rate
        # pulses_elapsed pulses in time_elapsed seconds
        # Convert to liters: pulses / 450
        # Convert to per minute: * (60 / time_elapsed)
        liters = pulses_elapsed / 450.0
        flow_rate_lpm = (liters / time_elapsed) * 60.0
        
        return flow_rate_lpm
    
    def get_flow_rate_lpm(self, time_interval_seconds=60):
        """
        Calculate flow rate in liters per minute (FL-408 specific).
        This requires tracking pulses over time. For accurate measurement,
        call this method periodically and reset the counter.
        
        Args:
            time_interval_seconds (float): Time interval in seconds (default: 60)
        
        Returns:
            float: Flow rate in liters per minute
        """
        # FL-408: Frequency (Hz) = 7.5 × Flow Rate (L/min)
        # So Flow Rate = Frequency / 7.5
        # But we need to measure frequency, which requires time-based sampling
        # This is a simplified version - for accurate flow rate, you'd want
        # to track pulses over a known time interval
        with self.lock:
            # This is a placeholder - actual implementation would need
            # time-based pulse counting
            return 0.0
    
    def cleanup(self):
        """
        Clean up GPIO resources.
        Call this when done using the flow meter.
        """
        try:
            self.callback_id.cancel()
        except:
            pass
        
        try:
            lgpio.gpio_free(self.chip, self.gpio_pin)
        except:
            pass
        
        try:
            lgpio.gpiochip_close(self.chip)
        except:
            pass


def main():
    """
    Simple main function that outputs the number of pulses since execution began.
    """
    print("Initializing flow meter on GPIO 27...")
    flow_meter = FlowMeter(gpio_pin=27)
    
    try:
        print("Flow meter active. Counting pulses...")
        print("Press Ctrl+C to exit\n")
        
        while True:
            pulse_count = flow_meter.get_pulse_count()
            print(f"Pulses since start: {pulse_count}", end='\r')
            time.sleep(0.1)  # Update display every 100ms
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        final_count = flow_meter.get_pulse_count()
        print(f"Final pulse count: {final_count}")
        flow_meter.cleanup()
        print("Cleanup complete.")


if __name__ == "__main__":
    main()


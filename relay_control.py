"""
Relay Control Module for Shop Heater Solenoid Valves

This module controls two relay-controlled solenoid valves on GPIO 23 and 24.
The relays are Normally Closed (NC) configuration with 12V on COM.

Hardware Setup:
- GPIO 23 (NORMAL): Controls main flow path
- GPIO 24 (DIVERSION): Controls diversion path
- Relays are NC: solenoids are powered (open) when GPIO is LOW
- When GPIO is HIGH, relay opens and solenoid closes (no power)

Solenoid Behavior:
- Solenoids default to closed position (no power needed)
- To open solenoid: need 12V power (relay closed, GPIO LOW)
- To close solenoid: cut power (relay open, GPIO HIGH)
"""

import lgpio
import time
import atexit


class RelayController:
    """
    Controls two relays for shop heater solenoid valves.
    
    Attributes:
        NORMAL_PIN (int): GPIO pin for normal flow relay (GPIO 23)
        DIVERSION_PIN (int): GPIO pin for diversion relay (GPIO 24)
        chip: lgpio chip handle
    """
    
    NORMAL_PIN = 23
    DIVERSION_PIN = 24
    
    def __init__(self):
        """
        Initialize the relay controller and setup GPIO pins.
        Registers cleanup handler for safe shutdown.
        """
        try:
            self.chip = lgpio.gpiochip_open(0)
        except Exception as e:
            raise RuntimeError(
                f"Failed to open GPIO chip. Make sure you have proper permissions.\n"
                f"You may need to be in the 'gpio' group.\n"
                f"Original error: {e}"
            )
        
        # Setup both pins as outputs
        try:
            lgpio.gpio_claim_output(self.chip, self.NORMAL_PIN)
            lgpio.gpio_claim_output(self.chip, self.DIVERSION_PIN)
        except Exception as e:
            lgpio.gpiochip_close(self.chip)
            raise RuntimeError(
                f"Failed to setup GPIO pins. Pins may be in use.\n"
                f"Original error: {e}"
            )
        
        # Register cleanup handler
        atexit.register(self.cleanup)
        
        print(f"RelayController initialized:")
        print(f"  NORMAL relay on GPIO {self.NORMAL_PIN}")
        print(f"  DIVERSION relay on GPIO {self.DIVERSION_PIN}")
    
    # ========== Core GPIO Control Functions ==========
    
    def normal_high(self):
        """
        Set NORMAL relay GPIO (23) to HIGH.
        This opens the relay, cutting power to the solenoid (solenoid closes).
        """
        lgpio.gpio_write(self.chip, self.NORMAL_PIN, 1)
        print(f"GPIO {self.NORMAL_PIN} (NORMAL) set to HIGH - relay open, solenoid closed")
    
    def normal_low(self):
        """
        Set NORMAL relay GPIO (23) to LOW.
        This closes the relay, providing power to the solenoid (solenoid opens).
        """
        lgpio.gpio_write(self.chip, self.NORMAL_PIN, 0)
        print(f"GPIO {self.NORMAL_PIN} (NORMAL) set to LOW - relay closed, solenoid open")
    
    def diversion_high(self):
        """
        Set DIVERSION relay GPIO (24) to HIGH.
        This opens the relay, cutting power to the solenoid (solenoid closes).
        """
        lgpio.gpio_write(self.chip, self.DIVERSION_PIN, 1)
        print(f"GPIO {self.DIVERSION_PIN} (DIVERSION) set to HIGH - relay open, solenoid closed")
    
    def diversion_low(self):
        """
        Set DIVERSION relay GPIO (24) to LOW.
        This closes the relay, providing power to the solenoid (solenoid opens).
        """
        lgpio.gpio_write(self.chip, self.DIVERSION_PIN, 0)
        print(f"GPIO {self.DIVERSION_PIN} (DIVERSION) set to LOW - relay closed, solenoid open")
    
    # ========== Mode Control Functions ==========
    
    def mainLoop(self):
        """
        Set relays for main loop operation.
        - NORMAL solenoid: OPEN (GPIO 23 LOW - relay closed, power on)
        - DIVERSION solenoid: CLOSED (GPIO 24 HIGH - relay open, power off)
        
        This allows flow through the main/normal path.
        """
        self.normal_low()      # Open NORMAL solenoid
        self.diversion_high()  # Close DIVERSION solenoid
        print("Mode: MAIN LOOP - Normal path open, diversion closed")
    
    def diversion(self):
        """
        Set relays for diversion operation.
        - NORMAL solenoid: CLOSED (GPIO 23 HIGH - relay open, power off)
        - DIVERSION solenoid: OPEN (GPIO 24 LOW - relay closed, power on)
        
        This diverts flow through the diversion path.
        """
        self.normal_high()    # Close NORMAL solenoid
        self.diversion_low()  # Open DIVERSION solenoid
        print("Mode: DIVERSION - Normal path closed, diversion open")
    
    def mix(self):
        """
        Set relays for mix operation.
        - NORMAL solenoid: OPEN (GPIO 23 LOW - relay closed, power on)
        - DIVERSION solenoid: OPEN (GPIO 24 LOW - relay closed, power on)
        
        This opens both solenoids, allowing flow through both paths.
        """
        self.normal_low()      # Open NORMAL solenoid
        self.diversion_low()   # Open DIVERSION solenoid
        print("Mode: MIX - Both paths open")
    
    def all_closed(self):
        """
        Close both solenoids (cut power to both).
        - NORMAL solenoid: CLOSED (GPIO 23 HIGH - relay open, power off)
        - DIVERSION solenoid: CLOSED (GPIO 24 HIGH - relay open, power off)
        
        This stops flow through both paths.
        """
        self.normal_high()     # Close NORMAL solenoid
        self.diversion_high()  # Close DIVERSION solenoid
        print("Mode: ALL CLOSED - Both paths closed")
    
    # ========== Status and Utility Functions ==========
    
    def get_status(self):
        """
        Read and display current GPIO states.
        
        Returns:
            tuple: (normal_state, diversion_state) where 0=LOW, 1=HIGH
        """
        normal_state = lgpio.gpio_read(self.chip, self.NORMAL_PIN)
        diversion_state = lgpio.gpio_read(self.chip, self.DIVERSION_PIN)
        
        print(f"\nCurrent GPIO States:")
        print(f"  GPIO {self.NORMAL_PIN} (NORMAL): {'HIGH' if normal_state else 'LOW'} "
              f"(relay {'open' if normal_state else 'closed'}, solenoid {'closed' if normal_state else 'open'})")
        print(f"  GPIO {self.DIVERSION_PIN} (DIVERSION): {'HIGH' if diversion_state else 'LOW'} "
              f"(relay {'open' if diversion_state else 'closed'}, solenoid {'closed' if diversion_state else 'open'})")
        
        return (normal_state, diversion_state)
    
    def cleanup(self):
        """
        Clean up GPIO resources.
        Sets both relays to safe state (both HIGH - solenoids closed).
        """
        try:
            # Set both to HIGH (safe state - solenoids closed)
            lgpio.gpio_write(self.chip, self.NORMAL_PIN, 1)
            lgpio.gpio_write(self.chip, self.DIVERSION_PIN, 1)
            
            # Free GPIO pins
            lgpio.gpio_free(self.chip, self.NORMAL_PIN)
            lgpio.gpio_free(self.chip, self.DIVERSION_PIN)
            
            # Close chip
            lgpio.gpiochip_close(self.chip)
            
            print("\nGPIO cleanup complete - both solenoids closed (safe state)")
        except:
            pass


def main():
    """
    Interactive test menu for relay control.
    Provides text-based command interface for testing all relay functions.
    """
    print("=" * 60)
    print("Shop Heater Relay Control - Interactive Test Menu")
    print("=" * 60)
    
    try:
        controller = RelayController()
        print("\nRelay controller ready!\n")
        
        while True:
            print("\n" + "-" * 60)
            print("Available Commands:")
            print("-" * 60)
            print("  Mode Commands:")
            print("    mainloop  - Main loop mode (normal open, diversion closed)")
            print("    diversion - Diversion mode (normal closed, diversion open)")
            print("    mix       - Mix mode (both paths open)")
            print("    closed    - All closed (both paths closed)")
            print()
            print("  Individual GPIO Commands:")
            print("    nh        - Normal HIGH (close normal solenoid)")
            print("    nl        - Normal LOW (open normal solenoid)")
            print("    dh        - Diversion HIGH (close diversion solenoid)")
            print("    dl        - Diversion LOW (open diversion solenoid)")
            print()
            print("  Utility Commands:")
            print("    status    - Show current GPIO states")
            print("    help      - Show this menu")
            print("    quit      - Exit program")
            print("-" * 60)
            
            command = input("\nEnter command: ").strip().lower()
            
            if command == "mainloop":
                controller.mainLoop()
            
            elif command == "diversion":
                controller.diversion()
            
            elif command == "mix":
                controller.mix()
            
            elif command == "closed":
                controller.all_closed()
            
            elif command == "nh":
                controller.normal_high()
            
            elif command == "nl":
                controller.normal_low()
            
            elif command == "dh":
                controller.diversion_high()
            
            elif command == "dl":
                controller.diversion_low()
            
            elif command == "status":
                controller.get_status()
            
            elif command == "help":
                continue  # Will redisplay menu
            
            elif command in ["quit", "exit", "q"]:
                print("\nExiting...")
                break
            
            else:
                print(f"\nUnknown command: '{command}'")
                print("Type 'help' to see available commands")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nShutting down...")


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
BTS7960 Fan Controller - Interactive CLI
"""

import time
from bts7960_controller import BTS7960Controller


def main():
    # Use context manager for automatic cleanup
    with BTS7960Controller() as controller:
        print("BTS7960 Fan Controller - Interactive Control")
        print("=" * 50)
        print("Enter fan speed (0-100) or 'q' to quit")
        print("=" * 50)
        
        while True:
            try:
                # Get user input
                user_input = input("\nEnter fan speed (0-100) or 'q' to quit: ").strip()
                
                # Check for quit command
                if user_input.lower() == 'q':
                    print("\nStopping fans and exiting...")
                    controller.stop()
                    break
                
                # Validate and convert input
                try:
                    speed = int(user_input)
                except ValueError:
                    print(f"Error: '{user_input}' is not a valid integer. Please enter a number between 0 and 100.")
                    continue
                
                # Check range
                if speed < 0 or speed > 100:
                    print(f"Error: {speed} is out of range. Please enter a value between 0 and 100.")
                    continue
                
                # Set the speed
                controller.set_speed(speed)
                actual_speed = min(speed, 99)  # Controller caps at 99
                print(f"✓ Fan speed set to {actual_speed}%")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted! Stopping fans and exiting...")
                controller.stop()
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                continue
        
        print("Goodbye!")


if __name__ == "__main__":
    main()


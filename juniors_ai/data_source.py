# data_source.py
# This module simulates a source of dynamic, real-time data for the pixel system.

import time
import random
from datetime import datetime, timedelta

# --- Simulated Data Points ---

_current_temperature = 22.5 # Initial temperature in Celsius
_uptime_start_time = time.time() # Start time for uptime calculation
_event_counter = 0 # Simple event counter

def get_current_temperature() -> float:
    """Simulates a fluctuating temperature reading."""
    global _current_temperature
    # Simulate slight random change
    _current_temperature += random.uniform(-0.5, 0.5)
    _current_temperature = round(max(15.0, min(30.0, _current_temperature)), 1) # Keep within a reasonable range
    return _current_temperature

def get_system_uptime() -> str:
    """Calculates and returns a human-readable system uptime."""
    uptime_seconds = int(time.time() - _uptime_start_time)
    days = uptime_seconds // (24 * 3600)
    uptime_seconds %= (24 * 3600)
    hours = uptime_seconds // 3600
    uptime_seconds %= 3600
    minutes = uptime_seconds // 60
    seconds = uptime_seconds % 60

    if days > 0:
        return f"{days}d {hours:02}h"
    elif hours > 0:
        return f"{hours:02}h {minutes:02}m"
    else:
        return f"{minutes:02}m {seconds:02}s"

def get_event_count() -> int:
    """Returns a simple incrementing event counter."""
    global _event_counter
    _event_counter += 1
    return _event_counter

def get_current_time_str() -> str:
    """Returns the current formatted time."""
    return datetime.now().strftime("%H:%M:%S")

def get_random_value(min_val: int = 0, max_val: int = 100) -> int:
    """Returns a random integer within a specified range."""
    return random.randint(min_val, max_val)

# --- Test / Example Usage ---
if __name__ == "__main__":
    print("--- Testing data_source.py ---")
    for i in range(5):
        print(f"Temperature: {get_current_temperature()}°C")
        print(f"Uptime: {get_system_uptime()}")
        print(f"Events: {get_event_count()}")
        print(f"Current Time: {get_current_time_str()}")
        print(f"Random Value: {get_random_value(10, 20)}")
        time.sleep(1)
    print("--- Data simulation complete. ---")

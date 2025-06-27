import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import threading
import json
import os

@dataclass
class CounterState:
    """Represents the state of a single counter."""
    id: int
    value: int
    binary_value: str
    timestamp: float
    access_count: int = 0
    is_dirty: bool = False

    def update(self, new_value: int) -> None:
        """Update counter value and metadata."""
        self.value = new_value
        self.binary_value = bin(new_value)[2:]  # Strip '0b' prefix
        self.timestamp = time.time()
        self.access_count += 1
        self.is_dirty = True

class RAIDCounter:
    """RAID-like counter system with four counters and data reconstruction."""
    
    def __init__(self, save_path: str = "raid_counter_state.json"):
        self.counters: Dict[int, CounterState] = {}
        self.save_path = save_path
        self._lock = threading.RLock()
        self._write_counter = 0
        self._start_time = time.time()
        self._last_speedometer_check = time.time()
        self._writes_per_second = 0.0
        self._initialize_counters()
        self._load_state()

    def _initialize_counters(self) -> None:
        """Initialize counters with starting values 1, 11, 111, 1111."""
        with self._lock:
            initial_values = {1: 1, 2: 11, 3: 111, 4: 1111}
            for counter_id, value in initial_values.items():
                if counter_id not in self.counters:
                    self.counters[counter_id] = CounterState(
                        id=counter_id,
                        value=value,
                        binary_value=bin(value)[2:],
                        timestamp=time.time()
                    )

    def write_data(self, counter_id: int, data: Any) -> bool:
        """Write data to a counter, encoding it as an integer."""
        with self._lock:
            if counter_id not in self.counters:
                return False
            
            if isinstance(data, int):
                value = data
            elif isinstance(data, str):
                value = sum(ord(c) for c in data)
            else:
                value = hash(str(data))
            
            self.counters[counter_id].update(value)
            self._write_counter += 1
            self._update_speedometer()
            self._save_state()
            return True

    def read_data(self, counter_id: int) -> Optional[int]:
        """Read value from a counter."""
        with self._lock:
            if counter_id not in self.counters:
                return None
            counter = self.counters[counter_id]
            counter.access_count += 1
            return counter.value

    def reconstruct_counter(self, failed_counter_id: int) -> Optional[int]:
        """Reconstruct a failed counter by summing the other counters."""
        with self._lock:
            if failed_counter_id not in self.counters:
                return None
            
            other_counters = [cid for cid in self.counters if cid != failed_counter_id]
            if not other_counters:
                return None
            
            reconstructed_value = sum(self.counters[cid].value for cid in other_counters)
            self.counters[failed_counter_id].update(reconstructed_value)
            self._save_state()
            return reconstructed_value

    def _update_speedometer(self) -> None:
        """Update the speedometer for write operations."""
        current_time = time.time()
        if current_time - self._last_speedometer_check >= 1.0:
            self._writes_per_second = self._write_counter / (current_time - self._last_speedometer_check)
            self._last_speedometer_check = current_time
            self._write_counter = 0

    def get_speedometer_reading(self) -> Dict[str, float]:
        """Get speedometer metrics."""
        current_time = time.time()
        return {
            'writes_per_second': self._writes_per_second,
            'total_runtime': current_time - self._start_time,
            'total_counters': len(self.counters),
            'active_writes': self._write_counter
        }

    def get_status_report(self) -> str:
        """Generate a status report for the counters."""
        speedometer = self.get_speedometer_reading()
        report = f"""
RAID Counter System Status Report
================================
Counters Active: {len(self.counters)}
Writes Per Second: {speedometer['writes_per_second']:.2f}
Total Runtime: {speedometer['total_runtime']:.2f} seconds

Counter States:
"""
        for counter_id in sorted(self.counters.keys()):
            counter = self.counters[counter_id]
            status = "DIRTY" if counter.is_dirty else "CLEAN"
            report += f"  Counter [{counter_id}]: Value={counter.value} (Binary={counter.binary_value}) | Access: {counter.access_count} | {status}\n"
        return report

    def _save_state(self) -> bool:
        """Save counter states to disk."""
        try:
            with self._lock:
                state = {
                    'counters': {
                        str(cid): {
                            'id': c.id,
                            'value': c.value,
                            'binary_value': c.binary_value,
                            'timestamp': c.timestamp,
                            'access_count': c.access_count,
                            'is_dirty': c.is_dirty
                        } for cid, c in self.counters.items()
                    },
                    'metadata': {
                        'save_timestamp': time.time(),
                        'total_writes': self._write_counter
                    }
                }
                with open(self.save_path, 'w') as f:
                    json.dump(state, f, indent=2)
                return True
        except Exception:
            return False

    def _load_state(self) -> bool:
        """Load counter states from disk."""
        if not os.path.exists(self.save_path):
            return False
        try:
            with open(self.save_path, 'r') as f:
                state = json.load(f)
            with self._lock:
                self.counters.clear()
                for cid, data in state['counters'].items():
                    cid = int(cid)
                    self.counters[cid] = CounterState(
                        id=data['id'],
                        value=data['value'],
                        binary_value=data['binary_value'],
                        timestamp=data['timestamp'],
                        access_count=data['access_count'],
                        is_dirty=data['is_dirty']
                    )
                return True
        except Exception:
            return False

class PXOSLauncher:
    """Main PXOS Launcher with integrated RAID counter system."""
    
    def __init__(self, save_path: str = "raid_counter_state.json"):
        self.raid = RAIDCounter(save_path=save_path)
        self.running = False
        # Placeholder for future components (e.g., VisualFilesystem, map)
        self.vfs = None  # Can be initialized later if needed
        self.map = None  # Placeholder for map integration

    def start(self) -> None:
        """Start the PXOS Launcher."""
        self.running = True
        print("PXOS Launcher started.")
        self._main_loop()

    def stop(self) -> None:
        """Stop the PXOS Launcher."""
        self.running = False
        print("PXOS Launcher stopped.")

    def _main_loop(self) -> None:
        """Main loop for periodic tasks (e.g., status updates)."""
        while self.running:
            # Periodic status check (e.g., every 5 seconds)
            print(self.get_raid_status())
            time.sleep(5)

    def write_raid_data(self, counter_id: int, data: Any) -> bool:
        """Write data to a RAID counter."""
        return self.raid.write_data(counter_id, data)

    def read_raid_data(self, counter_id: int) -> Optional[int]:
        """Read data from a RAID counter."""
        return self.raid.read_data(counter_id)

    def reconstruct_raid_counter(self, counter_id: int) -> Optional[int]:
        """Reconstruct a failed RAID counter."""
        return self.raid.reconstruct_counter(counter_id)

    def get_raid_speedometer(self) -> Dict[str, float]:
        """Get speedometer metrics for RAID counters."""
        return self.raid.get_speedometer_reading()

    def get_raid_status(self) -> str:
        """Get status report for RAID counters."""
        return self.raid.get_status_report()

    def initialize_map(self, map_data: Dict) -> None:
        """Placeholder for map initialization."""
        # Store map data in RAID counters or separate structure
        self.map = map_data
        print("Map initialized with data:", map_data)
        # Example: Store map metadata in counter 1
        self.write_raid_data(1, f"Map: {str(map_data)}")

# Example usage
if __name__ == "__main__":
    launcher = PXOSLauncher()
    
    # Start the launcher in a separate thread
    import threading
    threading.Thread(target=launcher.start, daemon=True).start()
    
    # Test RAID counter operations
    launcher.write_raid_data(1, "System Boot")
    launcher.write_raid_data(2, 1024)
    launcher.write_raid_data(3, "Map Metadata")
    launcher.write_raid_data(4, {"key": "value"})
    
    # Read data
    print(f"Counter 1: {launcher.read_raid_data(1)}")
    print(f"Counter 2: {launcher.read_raid_data(2)}")
    
    # Simulate counter failure and reconstruct
    print("\nSimulating failure of Counter 3...")
    reconstructed = launcher.reconstruct_raid_counter(3)
    print(f"Reconstructed Counter 3: {reconstructed}")
    
    # Display speedometer
    print("\nSpeedometer:", launcher.get_raid_speedometer())
    
    # Initialize a sample map
    sample_map = {"nodes": [1, 2, 3], "edges": [(1, 2), (2, 3)]}
    launcher.initialize_map(sample_map)
    
    # Keep the main thread alive for testing
    try:
        time.sleep(10)
    finally:
        launcher.stop()
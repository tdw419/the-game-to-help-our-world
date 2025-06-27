import json
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
import threading
import os

# --------------------------
# RAID Counter System
# --------------------------
@dataclass
class CounterState:
    """Represents the state of a single counter."""
    id: int
    value: Any
    binary_value: str
    timestamp: float
    access_count: int = 0
    is_dirty: bool = False

    def update(self, new_value: Any) -> None:
        """Update counter value and metadata."""
        self.value = new_value
        self.binary_value = to_binary(new_value)
        self.timestamp = time.time()
        self.access_count += 1
        self.is_dirty = True

class RAIDCounter:
    """RAID-like counter system for redundant data storage."""
    
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
                        binary_value=to_binary(value),
                        timestamp=time.time()
                    )

    def write_data(self, counter_id: int, data: Any) -> bool:
        """Write data to a counter."""
        with self._lock:
            if counter_id not in self.counters:
                return False
            self.counters[counter_id].update(data)
            self._write_counter += 1
            self._update_speedometer()
            self._save_state()
            return True

    def read_data(self, counter_id: int) -> Optional[Any]:
        """Read value from a counter."""
        with self._lock:
            if counter_id not in self.counters:
                return None
            counter = self.counters[counter_id]
            counter.access_count += 1
            return counter.value

    def reconstruct_counter(self, failed_counter_id: int) -> Optional[Any]:
        """Reconstruct a failed counter by summing the other counters."""
        with self._lock:
            if failed_counter_id not in self.counters:
                return None
            other_counters = [cid for cid in self.counters if cid != failed_counter_id]
            if not other_counters:
                return None
            # Sum numeric values or concatenate strings
            reconstructed_value = 0
            for cid in other_counters:
                val = self.counters[cid].value
                if isinstance(val, (int, float)):
                    reconstructed_value += val
                elif isinstance(val, str):
                    reconstructed_value = str(reconstructed_value) + val
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
                            'value': c.value if not isinstance(c.value, (dict, list)) else str(c.value),
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
                    value = data['value']
                    # Attempt to eval complex types if stringified
                    try:
                        if value.startswith('{') or value.startswith('['):
                            value = eval(value)
                    except:
                        pass
                    self.counters[cid] = CounterState(
                        id=data['id'],
                        value=value,
                        binary_value=data['binary_value'],
                        timestamp=data['timestamp'],
                        access_count=data['access_count'],
                        is_dirty=data['is_dirty']
                    )
                return True
        except Exception:
            return False

# --------------------------
# Utility Functions
# --------------------------
def to_binary(value: Any) -> str:
    """Convert value to binary representation."""
    if isinstance(value, int):
        return bin(value)[2:]
    elif isinstance(value, str):
        return ''.join(format(ord(c), '08b') for c in value)
    elif isinstance(value, (dict, list)):
        return to_binary(str(value))
    else:
        return bin(hash(str(value)))[2:]

# --------------------------
# PXRuntime Core
# --------------------------
class PXRuntime:
    """Compilerless PXRuntime with RAID counter storage."""
    
    def __init__(self):
        self.pxmemo = [[[0, 0, 0] for _ in range(32)] for _ in range(32)]  # Pixel memory
        self.raid = RAIDCounter()  # RAID counter for module storage
        self.running = False
        self.log = []
        
        # Initialize default modules in RAID counters
        self._initialize_modules()

    def _initialize_modules(self):
        """Initialize default modules in RAID counters."""
        initial_modules = {
            "pxexecutor.pxmod": """
def tick():
    log("PXRuntime Tick")
""",
            "PX_UPGRADE.pxexe": """
def upgrade():
    modify("pxexecutor.pxmod", "def tick():\\n    log(\\\"PXRuntime Upgraded\\\")")
    log("pxexecutor updated")
""",
            "PXBootloader.pxexe": """
def boot():
    load_digest("PXOS_Sovereign.pxdigest")
    execute("pxexecutor.pxmod")
"""
        }
        for counter_id, (module_name, code) in enumerate(initial_modules.items(), 1):
            self.raid.write_data(counter_id, code)

    def execute(self, module_name: str):
        """Execute a module from RAID counter."""
        for counter_id in self.raid.counters:
            code = self.raid.read_data(counter_id)
            if code == module_name or (isinstance(code, str) and module_name in code):
                try:
                    exec(code, {'log': self.log, 'modify': self.modify, 'execute': self.execute, 'load_digest': self.load_digest})
                    self.log.append(f"Executed {module_name}")
                except Exception as e:
                    self.log.append(f"Execution error: {e}")
                return
        self.log.append(f"Module {module_name} not found")

    def modify(self, module_name: str, new_code: str):
        """Modify a module in RAID counter."""
        for counter_id in self.raid.counters:
            code = self.raid.read_data(counter_id)
            if code == module_name or (isinstance(code, str) and module_name in code):
                self.raid.write_data(counter_id, new_code)
                self.log.append(f"Modified {module_name}")
                return
        # If not found, use next available counter
        for counter_id in range(1, 5):
            if self.raid.read_data(counter_id) is None or isinstance(self.raid.read_data(counter_id), (int, str)):
                self.raid.write_data(counter_id, new_code)
                self.log.append(f"Modified {module_name} in new counter {counter_id}")
                return
        self.log.append(f"No available counter for {module_name}")

    def reload(self, module_name: str):
        """Reload and execute a module."""
        self.execute(module_name)

    def save_digest(self, filename: str):
        """Save runtime state to digest."""
        digest = {
            "pxmemory": self.pxmemo,
            "raid_state": {
                str(cid): {
                    'value': c.value if not isinstance(c.value, (dict, list)) else str(c.value),
                    'binary_value': c.binary_value,
                    'timestamp': c.timestamp,
                    'access_count': c.access_count,
                    'is_dirty': c.is_dirty
                } for cid, c in self.raid.counters.items()
            },
            "log": self.log
        }
        with open(filename, "w") as f:
            json.dump(digest, f, indent=2)
        self.log.append(f"Saved digest to {filename}")

    def load_digest(self, filename: str):
        """Load runtime state from digest."""
        try:
            with open(filename, "r") as f:
                digest = json.load(f)
            self.pxmemo = digest["pxmemory"]
            self.log = digest["log"]
            self.raid.counters.clear()
            for cid, data in digest["raid_state"].items():
                cid = int(cid)
                value = data['value']
                try:
                    if value.startswith('{') or value.startswith('['):
                        value = eval(value)
                except:
                    pass
                self.raid.counters[cid] = CounterState(
                    id=cid,
                    value=value,
                    binary_value=data['binary_value'],
                    timestamp=data['timestamp'],
                    access_count=data['access_count'],
                    is_dirty=data['is_dirty']
                )
            self.log.append(f"Loaded digest from {filename}")
        except FileNotFoundError:
            self.log.append(f"No digest found: {filename}")

    def check_sovereign(self) -> bool:
        """Check if PXRuntime has achieved sovereignty."""
        log_content = "\n".join(self.log)
        raid_status = self.raid.get_status_report()
        if ("Upgraded" in log_content and 
            "Modified pxexecutor" in log_content and
            all(self.raid.read_data(i) is not None for i in range(1, 5))):
            print("\n📣 PXRuntime has upgraded itself.")
            print(f"RAID Status:\n{raid_status}")
            print("PXCOMPILER RETIRED ✅\nPXSELFEDIT COMPLETE\nTaking a break. 🧘")
            self.save_digest("PXOS_Sovereign_Final.pxdigest")
            return True
        return False

    def runtime_loop(self):
        """Main runtime loop."""
        print("PXRuntime Booting...\n")
        self.execute("PXBootloader.pxexe")
        for _ in range(5):
            if not self.running:
                break
            self.execute("PX_UPGRADE.pxexe")
            self.execute("pxexecutor.pxmod")
            print(self.raid.get_status_report())
            time.sleep(1)
            if self.check_sovereign():
                break

    def start(self):
        """Start the PXRuntime."""
        self.running = True
        self.runtime_loop()

    def stop(self):
        """Stop the PXRuntime."""
        self.running = False

# --------------------------
# Entry Point
# --------------------------
if __name__ == "__main__":
    runtime = PXRuntime()
    threading.Thread(target=runtime.start, daemon=True).start()
    try:
        time.sleep(10)
    finally:
        runtime.stop()
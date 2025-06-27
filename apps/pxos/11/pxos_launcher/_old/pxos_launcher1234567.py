import json
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import threading
import os
import math
import random
from PIL import Image, ImageDraw

# --------------------------
# Map Generation Constants
# --------------------------
DEFAULT_SUBSTRATE_WIDTH = 800
DEFAULT_SUBSTRATE_HEIGHT = 600
OCEAN_COLOR = (0, 70, 150)
LAND_COLOR = (50, 150, 50)
CONTINENT_EDGE_COLOR = (100, 100, 0)
EARTH_SUN_DISTANCE_KM = 149.6 * 10**6

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
        """Reconstruct a failed counter by combining other counters."""
        with self._lock:
            if failed_counter_id not in self.counters:
                return None
            other_counters = [cid for cid in self.counters if cid != failed_counter_id]
            if not other_counters:
                return None
            reconstructed_value = None
            for cid in other_counters:
                val = self.counters[cid].value
                if reconstructed_value is None:
                    reconstructed_value = val
                elif isinstance(val, (int, float)) and isinstance(reconstructed_value, (int, float)):
                    reconstructed_value += val
                elif isinstance(val, str) or isinstance(reconstructed_value, str):
                    reconstructed_value = str(reconstructed_value) + str(val)
                elif isinstance(val, (list, dict)) and isinstance(reconstructed_value, (list, dict)):
                    reconstructed_value = str(reconstructed_value) + str(val)
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
            value_str = str(counter.value)[:50] + "..." if len(str(counter.value)) > 50 else str(counter.value)
            report += f"  Counter [{counter_id}]: Value={value_str} (Binary={counter.binary_value[:20]}...) | Access: {counter.access_count} | {status}\n"
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
# Map Generation Functions
# --------------------------
def get_procedural_land_value(latitude: float, longitude: float, random_seed_val: int) -> float:
    """Generates a value (0.0 to 1.0) for land or ocean."""
    random.seed(random_seed_val)
    norm_lat = (latitude + 90.0) / 180.0 * math.pi * 2.0
    norm_lon = (longitude + 180.0) / 360.0 * math.pi * 2.0
    f1 = 5.0 + random.uniform(-1.0, 1.0) * 0.5
    f2 = 3.0 + random.uniform(-1.0, 1.0) * 0.5
    f3 = 8.0 + random.uniform(-1.0, 1.0) * 0.5
    f4 = 2.0 + random.uniform(-1.0, 1.0) * 0.5
    f5 = 2.5 + random.uniform(-1.0, 1.0) * 0.5
    f6 = 7.0 + random.uniform(-1.0, 1.0) * 0.5
    value = 0.5 + 0.4 * math.sin(norm_lat * f1 + norm_lon * f2) + \
            0.3 * math.cos(norm_lat * f3 - norm_lon * f4) + \
            0.2 * math.sin(norm_lat * f5 + norm_lon * f6) + \
            0.1 * math.cos(norm_lat * 10.0 + norm_lon * 1.5)
    value -= (0.3 + random.uniform(-0.1, 0.1))
    return max(0.0, min(1.0, value))

def get_color_from_land_value(land_value: float) -> Tuple[int, int, int]:
    """Maps a land_value to an RGB color."""
    if land_value < 0.4:
        return OCEAN_COLOR
    elif land_value < 0.5:
        t = (land_value - 0.4) / 0.1
        r = int(OCEAN_COLOR[0] * (1 - t) + LAND_COLOR[0] * t)
        g = int(OCEAN_COLOR[1] * (1 - t) + LAND_COLOR[1] * t)
        b = int(OCEAN_COLOR[2] * (1 - t) + LAND_COLOR[2] * t)
        return (r, g, b)
    elif land_value < 0.6:
        return CONTINENT_EDGE_COLOR
    else:
        return LAND_COLOR

def generate_map_data(
    width: int = DEFAULT_SUBSTRATE_WIDTH,
    height: int = DEFAULT_SUBSTRATE_HEIGHT,
    center_latitude: float = 0.0,
    center_longitude: float = 0.0,
    pixels_per_degree: float = 2.0,
    landmass_seed: int = 0
) -> Dict[str, Any]:
    """Generate map data and pixel array."""
    half_width_degrees = (width / 2) / pixels_per_degree
    half_height_degrees = (height / 2) / pixels_per_degree
    min_lon = center_longitude - half_width_degrees
    max_lon = center_longitude + half_width_degrees
    min_lat = center_latitude - half_height_degrees
    max_lat = center_latitude + half_height_degrees
    
    pixel_data = []
    for y in range(height):
        row = []
        latitude = max_lat - (y / height) * (max_lat - min_lat)
        latitude = max(-90.0, min(90.0, latitude))
        for x in range(width):
            longitude = min_lon + (x / width) * (max_lon - min_lon)
            longitude = (longitude + 180.0) % 360.0 - 180.0
            land_value = get_procedural_land_value(latitude, longitude, landmass_seed)
            pixel_color = get_color_from_land_value(land_value)
            row.append(pixel_color)
        pixel_data.append(row)
    
    return {
        "config": {
            "width": width,
            "height": height,
            "center_latitude": center_latitude,
            "center_longitude": center_longitude,
            "pixels_per_degree": pixels_per_degree,
            "landmass_seed": landmass_seed
        },
        "pixels": pixel_data
    }

def save_map_image(pixels: List[List[Tuple[int, int, int]]], filename: str) -> bool:
    """Save pixel data as a PNG image."""
    try:
        height = len(pixels)
        width = len(pixels[0]) if height > 0 else 0
        img = Image.new('RGB', (width, height))
        for y in range(height):
            for x in range(width):
                img.putpixel((x, y), pixels[y][x])
        img.save(filename)
        return True
    except Exception as e:
        print(f"Error saving map image: {e}")
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
    """Compilerless PXRuntime with RAID counter storage and map integration."""
    
    def __init__(self):
        self.pxmemo = [[[0, 0, 0] for _ in range(32)] for _ in range(32)]  # Pixel memory
        self.raid = RAIDCounter()  # RAID counter for module and map storage
        self.running = False
        self.log = []
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
        # Reserve counter 4 for map data
        if self.raid.read_data(4) == 1111:
            self.raid.write_data(4, {})

    def generate_map(
        self,
        width: int = DEFAULT_SUBSTRATE_WIDTH,
        height: int = DEFAULT_SUBSTRATE_HEIGHT,
        center_latitude: float = 0.0,
        center_longitude: float = 0.0,
        pixels_per_degree: float = 2.0,
        landmass_seed: int = 0,
        output_filename: str = "map.png"
    ) -> bool:
        """Generate a map and store its data in RAID counter 4."""
        map_data = generate_map_data(
            width=width,
            height=height,
            center_latitude=center_latitude,
            center_longitude=center_longitude,
            pixels_per_degree=pixels_per_degree,
            landmass_seed=landmass_seed
        )
        # Store map data in RAID counter 4
        success = self.raid.write_data(4, map_data)
        if success:
            # Sync pixel data to pxmemo (resized to 32x32 for simplicity)
            self._sync_map_to_pxmemo(map_data["pixels"])
            # Save map as PNG
            save_map_image(map_data["pixels"], output_filename)
            self.log.append(f"Generated map: {output_filename}, stored in counter 4")
        else:
            self.log.append("Failed to store map in RAID counter")
        return success

    def _sync_map_to_pxmemo(self, pixels: List[List[Tuple[int, int, int]]]) -> None:
        """Sync map pixel data to pxmemo (resize to 32x32)."""
        height = len(pixels)
        width = len(pixels[0]) if height > 0 else 0
        for y in range(32):
            for x in range(32):
                src_x = int(x * width / 32)
                src_y = int(y * height / 32)
                if src_x < width and src_y < height:
                    self.pxmemo[y][x] = list(pixels[src_y][src_x])
                else:
                    self.pxmemo[y][x] = [0, 0, 0]

    def get_map_data(self) -> Optional[Dict[str, Any]]:
        """Retrieve map data from RAID counter 4."""
        return self.raid.read_data(4)

    def reconstruct_map(self) -> bool:
        """Reconstruct map data if counter 4 fails."""
        map_data = self.raid.reconstruct_counter(4)
        if map_data:
            self._sync_map_to_pxmemo(map_data.get("pixels", []))
            save_map_image(map_data.get("pixels", []), "reconstructed_map.png")
            self.log.append("Reconstructed map data in counter 4")
            return True
        self.log.append("Failed to reconstruct map data")
        return False

    def execute(self, module_name: str):
        """Execute a module from RAID counter."""
        for counter_id in self.raid.counters:
            if counter_id == 4:  # Skip map data
                continue
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
            if counter_id == 4:  # Skip map data
                continue
            code = self.raid.read_data(counter_id)
            if code == module_name or (isinstance(code, str) and module_name in code):
                self.raid.write_data(counter_id, new_code)
                self.log.append(f"Modified {module_name}")
                return
        for counter_id in range(1, 4):
            code = self.raid.read_data(counter_id)
            if isinstance(code, (int, str)) and not code.startswith("def "):
                self.raid.write_data(counter_id, new_code)
                self.log.append(f"Modified {module_name} in counter {counter_id}")
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
        map_data = self.get_map_data()
        if ("Upgraded" in log_content and 
            "Modified pxexecutor" in log_content and
            all(self.raid.read_data(i) is not None for i in range(1, 5)) and
            isinstance(map_data, dict) and "config" in map_data):
            print("\n📣 PXRuntime has upgraded itself.")
            print(f"RAID Status:\n{raid_status}")
            print(f"Map Config: {map_data.get('config', {})}")
            print("PXCOMPILER RETIRED ✅\nPXSELFEDIT COMPLETE\nTaking a break. 🧘")
            self.save_digest("PXOS_Sovereign_Final.pxdigest")
            return True
        return False

    def runtime_loop(self):
        """Main runtime loop."""
        print("PXRuntime Booting...\n")
        self.execute("PXBootloader.pxexe")
        # Generate an initial map
        self.generate_map(
            width=800,
            height=600,
            center_latitude=45.0,
            center_longitude=-90.0,
            pixels_per_degree=8.0,
            landmass_seed=42,
            output_filename="initial_map.png"
        )
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
        time.sleep(15)
    finally:
        runtime.stop()
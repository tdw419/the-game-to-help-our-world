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
                # Auto-create new counter if it doesn't exist
                self.counters[counter_id] = CounterState(
                    id=counter_id,
                    value=data,
                    binary_value=to_binary(data),
                    timestamp=time.time()
                )
            else:
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

    def get_all_counters(self) -> Dict[int, Any]:
        """Get all counter values."""
        with self._lock:
            return {cid: counter.value for cid, counter in self.counters.items()}

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
            value_preview = str(counter.value)[:50] + "..." if len(str(counter.value)) > 50 else str(counter.value)
            report += f"  Counter [{counter_id}]: Value={value_preview} | Access: {counter.access_count} | {status}\n"
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
                        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
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
# Map Generation Constants (Now stored in RAID)
# --------------------------
MAP_CONSTANTS = {
    'DEFAULT_WIDTH': 800,
    'DEFAULT_HEIGHT': 600,
    'OCEAN_COLOR': (0, 70, 150),
    'LAND_COLOR': (50, 150, 50),
    'CONTINENT_EDGE_COLOR': (100, 100, 0),
    'SUN_CORE_AREA_COLOR': (255, 150, 0),
    'SUN_CORE_DATA_ACTIVE_COLOR': (255, 255, 0),
    'SUN_CORE_DATA_INACTIVE_COLOR': (100, 50, 0),
    'SUN_CORE_GRID_COLOR': (255, 200, 100),
    'CORE_PIXEL_COLOR': (255, 0, 0),
    'EARTH_SUN_DISTANCE_KM': 149.6 * 10**6,
    'CORE_OFFSETS': [(-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
}

# --------------------------
# Utility Functions
# --------------------------
def to_binary(value: Any) -> str:
    """Convert value to binary representation."""
    if isinstance(value, int):
        return bin(value)[2:]
    elif isinstance(value, str):
        return ''.join(format(ord(c), '08b') for c in value[:10])  # Limit string length
    elif isinstance(value, (dict, list)):
        return to_binary(str(value)[:50])  # Limit complex type length
    else:
        return bin(hash(str(value)) & 0xFFFFFFFF)[2:]  # Ensure positive hash

def get_procedural_land_value(latitude: float, longitude: float, random_seed_val: int) -> float:
    """Generate procedural land value from coordinates and seed."""
    random.seed(random_seed_val)
    
    norm_lat = (latitude + 90.0) / 180.0 * math.pi * 2.0
    norm_lon = (longitude + 180.0) / 360.0 * math.pi * 2.0
    
    f1 = 5.0 + random.uniform(-1.0, 1.0) * 0.5
    f2 = 3.0 + random.uniform(-1.0, 1.0) * 0.5
    f3 = 8.0 + random.uniform(-1.0, 1.0) * 0.5
    f4 = 2.0 + random.uniform(-1.0, 1.0) * 0.5
    f5 = 2.5 + random.uniform(-1.0, 1.0) * 0.5
    f6 = 7.0 + random.uniform(-1.0, 1.0) * 0.5

    value = 0.5 \
        + 0.4 * math.sin(norm_lat * f1 + norm_lon * f2) \
        + 0.3 * math.cos(norm_lat * f3 - norm_lon * f4) \
        + 0.2 * math.sin(norm_lat * f5 + norm_lon * f6) \
        + 0.1 * math.cos(norm_lat * 10.0 + norm_lon * 1.5)

    value -= (0.3 + random.uniform(-0.1, 0.1))
    return max(0.0, min(1.0, value))

def get_color_from_land_value(land_value: float, constants: dict) -> tuple:
    """Maps a land_value to RGB color using stored constants."""
    if land_value < 0.4:
        return constants['OCEAN_COLOR']
    elif land_value < 0.5:
        t = (land_value - 0.4) / 0.1
        ocean = constants['OCEAN_COLOR']
        land = constants['LAND_COLOR']
        r = int(ocean[0] * (1 - t) + land[0] * t)
        g = int(ocean[1] * (1 - t) + land[1] * t)
        b = int(ocean[2] * (1 - t) + land[2] * t)
        return (r, g, b)
    elif land_value < 0.6:
        return constants['CONTINENT_EDGE_COLOR']
    else:
        return constants['LAND_COLOR']

# --------------------------
# PXRuntime Core with Map Integration
# --------------------------
class PXRuntime:
    """Compilerless PXRuntime with RAID counter storage and integrated map generation."""
    
    def __init__(self):
        self.pxmemo = [[[0, 0, 0] for _ in range(32)] for _ in range(32)]  # Pixel memory
        self.raid = RAIDCounter()  # RAID counter for module storage
        self.running = False
        self.log = []
        
        # Map-specific RAID counter assignments
        self.MAP_COUNTER_IDS = {
            'CONSTANTS': 10,      # Map generation constants
            'BOOT_PIXEL': 11,     # Boot pixel RGB data
            'MAP_PARAMS': 12,     # Current map parameters
            'MAP_DATA': 13,       # Generated map pixel data
            'MAP_METADATA': 14,   # Map generation metadata
        }
        
        self._initialize_modules()
        self._initialize_map_system()

    def _initialize_modules(self):
        """Initialize default modules in RAID counters."""
        initial_modules = {
            5: """
def tick():
    log("PXRuntime Tick with Map Integration")
    generate_map_from_raid()
""",
            6: """
def map_upgrade():
    boot_pixel = get_boot_pixel_from_raid()
    if boot_pixel:
        r, g, b = boot_pixel
        new_r = (r + 10) % 256
        store_boot_pixel_in_raid((new_r, g, b))
        log(f"Map boot pixel upgraded to ({new_r}, {g}, {b})")
""",
            7: """
def map_bootloader():
    log("Map system bootloader starting...")
    initialize_default_boot_pixel()
    generate_map_from_raid()
    log("Map system ready")
"""
        }
        for counter_id, code in initial_modules.items():
            self.raid.write_data(counter_id, code)

    def _initialize_map_system(self):
        """Initialize map generation system in RAID memory."""
        # Store map constants
        self.raid.write_data(self.MAP_COUNTER_IDS['CONSTANTS'], MAP_CONSTANTS)
        
        # Store default boot pixel
        default_boot_pixel = (128, 128, 128)  # Neutral gray
        self.raid.write_data(self.MAP_COUNTER_IDS['BOOT_PIXEL'], default_boot_pixel)
        
        # Store default map parameters
        default_params = {
            'width': 800,
            'height': 600,
            'center_latitude': 0.0,
            'center_longitude': 0.0,
            'pixels_per_degree': 2.0,
            'include_boot_patterns': False,
            'include_sun_core_filesystem': True,
            'solar_system_pixel_scale': 0.0000005,
            'sun_core_fs_size': 200,
            'sun_core_activity_seed': 0
        }
        self.raid.write_data(self.MAP_COUNTER_IDS['MAP_PARAMS'], default_params)
        
        self.log.append("Map system initialized in RAID memory")

    def store_boot_pixel_in_raid(self, rgb_tuple: Tuple[int, int, int]) -> bool:
        """Store boot pixel RGB in RAID memory."""
        success = self.raid.write_data(self.MAP_COUNTER_IDS['BOOT_PIXEL'], rgb_tuple)
        if success:
            self.log.append(f"Boot pixel stored in RAID: {rgb_tuple}")
            # Auto-update map parameters based on new boot pixel
            self._update_map_params_from_boot_pixel(rgb_tuple)
        return success

    def get_boot_pixel_from_raid(self) -> Optional[Tuple[int, int, int]]:
        """Retrieve boot pixel RGB from RAID memory."""
        return self.raid.read_data(self.MAP_COUNTER_IDS['BOOT_PIXEL'])

    def _update_map_params_from_boot_pixel(self, rgb_tuple: Tuple[int, int, int]):
        """Update map generation parameters based on boot pixel."""
        R, G, B = rgb_tuple
        
        # Derive parameters from RGB values (same logic as original)
        center_longitude = (R / 255.0 * 360.0) - 180.0
        
        min_pixels_per_degree = 0.5
        max_pixels_per_degree = 20.0
        pixels_per_degree = min_pixels_per_degree + (G / 255.0) * (max_pixels_per_degree - min_pixels_per_degree)
        center_latitude = (G / 255.0 * 180.0) - 90.0
        
        include_boot_patterns = bool(B & 0b00000001)
        include_sun_core_filesystem = bool((B >> 1) & 0b00000001)
        sun_core_activity_seed = (B >> 2) * 10
        
        # Update stored parameters
        current_params = self.raid.read_data(self.MAP_COUNTER_IDS['MAP_PARAMS']) or {}
        current_params.update({
            'center_latitude': center_latitude,
            'center_longitude': center_longitude,
            'pixels_per_degree': pixels_per_degree,
            'include_boot_patterns': include_boot_patterns,
            'include_sun_core_filesystem': include_sun_core_filesystem,
            'sun_core_activity_seed': sun_core_activity_seed,
            'landmass_seed': R  # Use R channel as landmass seed
        })
        
        self.raid.write_data(self.MAP_COUNTER_IDS['MAP_PARAMS'], current_params)
        self.log.append(f"Map parameters updated from boot pixel: Lat={center_latitude:.2f}, Lon={center_longitude:.2f}")

    def generate_map_from_raid(self, output_filename: str = "raid_generated_map.png") -> bool:
        """Generate map using parameters stored in RAID memory."""
        try:
            # Retrieve all necessary data from RAID
            constants = self.raid.read_data(self.MAP_COUNTER_IDS['CONSTANTS'])
            boot_pixel = self.raid.read_data(self.MAP_COUNTER_IDS['BOOT_PIXEL'])
            params = self.raid.read_data(self.MAP_COUNTER_IDS['MAP_PARAMS'])
            
            if not all([constants, boot_pixel, params]):
                self.log.append("Error: Missing map data in RAID memory")
                return False
            
            # Extract parameters
            width = params.get('width', 800)
            height = params.get('height', 600)
            center_lat = params.get('center_latitude', 0.0)
            center_lon = params.get('center_longitude', 0.0)
            pixels_per_degree = params.get('pixels_per_degree', 2.0)
            landmass_seed = params.get('landmass_seed', boot_pixel[0])
            
            # Create image
            img = Image.new('RGB', (width, height), color=(0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Generate procedural map
            half_width_degrees = (width / 2) / pixels_per_degree
            half_height_degrees = (height / 2) / pixels_per_degree
            
            min_lon = center_lon - half_width_degrees
            max_lon = center_lon + half_width_degrees
            min_lat = center_lat - half_height_degrees
            max_lat = center_lat + half_height_degrees
            
            # Store pixel data for RAID
            map_pixel_data = []
            
            for y in range(height):
                latitude = max_lat - (y / height) * (max_lat - min_lat)
                latitude = max(-90.0, min(90.0, latitude))
                
                row_data = []
                for x in range(width):
                    longitude = min_lon + (x / width) * (max_lon - min_lon)
                    longitude = (longitude + 180.0) % 360.0 - 180.0
                    
                    land_value = get_procedural_land_value(latitude, longitude, landmass_seed)
                    pixel_color = get_color_from_land_value(land_value, constants)
                    
                    draw.point((x, y), fill=pixel_color)
                    row_data.append(pixel_color)
                
                # Store every 10th row to avoid memory overflow
                if y % 10 == 0:
                    map_pixel_data.append(row_data[::10])  # Every 10th pixel
            
            # Save image
            img.save(output_filename)
            
            # Store map data and metadata in RAID
            self.raid.write_data(self.MAP_COUNTER_IDS['MAP_DATA'], map_pixel_data)
            
            metadata = {
                'filename': output_filename,
                'generation_time': time.time(),
                'boot_pixel': boot_pixel,
                'dimensions': (width, height),
                'center_coordinates': (center_lat, center_lon),
                'landmass_seed': landmass_seed
            }
            self.raid.write_data(self.MAP_COUNTER_IDS['MAP_METADATA'], metadata)
            
            self.log.append(f"Map generated from RAID data: {output_filename}")
            self.log.append(f"Map stored in RAID counter {self.MAP_COUNTER_IDS['MAP_DATA']}")
            return True
            
        except Exception as e:
            self.log.append(f"Map generation error: {e}")
            return False

    def initialize_default_boot_pixel(self):
        """Initialize with a default boot pixel if none exists."""
        if not self.get_boot_pixel_from_raid():
            default_pixel = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            self.store_boot_pixel_in_raid(default_pixel)
            self.log.append(f"Initialized default boot pixel: {default_pixel}")

    def set_boot_pixel_and_generate(self, r: int, g: int, b: int, filename: str = None) -> bool:
        """Set new boot pixel and generate map in one operation."""
        self.store_boot_pixel_in_raid((r, g, b))
        output_file = filename or f"boot_pixel_{r}_{g}_{b}.png"
        return self.generate_map_from_raid(output_file)

    def get_map_status_report(self) -> str:
        """Get detailed status report of map system in RAID."""
        report = "\nMap System RAID Status\n" + "="*30 + "\n"
        
        boot_pixel = self.get_boot_pixel_from_raid()
        params = self.raid.read_data(self.MAP_COUNTER_IDS['MAP_PARAMS'])
        metadata = self.raid.read_data(self.MAP_COUNTER_IDS['MAP_METADATA'])
        
        report += f"Boot Pixel (Counter {self.MAP_COUNTER_IDS['BOOT_PIXEL']}): {boot_pixel}\n"
        
        if params:
            report += f"Map Parameters (Counter {self.MAP_COUNTER_IDS['MAP_PARAMS']}):\n"
            report += f"  Center: ({params.get('center_latitude', 0):.2f}°, {params.get('center_longitude', 0):.2f}°)\n"
            report += f"  Zoom: {params.get('pixels_per_degree', 0):.2f} px/degree\n"
            report += f"  Size: {params.get('width', 0)}x{params.get('height', 0)}\n"
        
        if metadata:
            report += f"Last Generated (Counter {self.MAP_COUNTER_IDS['MAP_METADATA']}):\n"
            report += f"  File: {metadata.get('filename', 'Unknown')}\n"
            report += f"  Time: {time.ctime(metadata.get('generation_time', 0))}\n"
        
        map_data = self.raid.read_data(self.MAP_COUNTER_IDS['MAP_DATA'])
        if map_data:
            report += f"Map Data (Counter {self.MAP_COUNTER_IDS['MAP_DATA']}): {len(map_data)} rows stored\n"
        
        return report

    # Original methods continue...
    def execute(self, module_name: str):
        """Execute a module from RAID counter."""
        for counter_id in self.raid.counters:
            code = self.raid.read_data(counter_id)
            if isinstance(code, str) and (module_name in code or f"def {module_name}" in code):
                try:
                    # Provide additional functions for map operations
                    exec_globals = {
                        'log': lambda msg: self.log.append(str(msg)),
                        'modify': self.modify,
                        'execute': self.execute,
                        'load_digest': self.load_digest,
                        'generate_map_from_raid': self.generate_map_from_raid,
                        'get_boot_pixel_from_raid': self.get_boot_pixel_from_raid,
                        'store_boot_pixel_in_raid': self.store_boot_pixel_in_raid,
                        'initialize_default_boot_pixel': self.initialize_default_boot_pixel,
                        'set_boot_pixel_and_generate': self.set_boot_pixel_and_generate
                    }
                    exec(code, exec_globals)
                    self.log.append(f"Executed module containing {module_name}")
                except Exception as e:
                    self.log.append(f"Execution error in {module_name}: {e}")
                return
        self.log.append(f"Module {module_name} not found")

    def modify(self, module_name: str, new_code: str):
        """Modify a module in RAID counter."""
        for counter_id in self.raid.counters:
            code = self.raid.read_data(counter_id)
            if isinstance(code, str) and module_name in code:
                self.raid.write_data(counter_id, new_code)
                self.log.append(f"Modified {module_name}")
                return
        # If not found, use next available counter
        for counter_id in range(1, 100):  # Expanded range
            existing = self.raid.read_data(counter_id)
            if existing is None:
                self.raid.write_data(counter_id, new_code)
                self.log.append(f"Created {module_name} in new counter {counter_id}")
                return
        self.log.append(f"No available counter for {module_name}")

    def reload(self, module_name: str):
        """Reload and execute a module."""
        self.execute(module_name)

    def save_digest(self, filename: str):
        """Save runtime state to digest including map data."""
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
            "log": self.log,
            "map_counter_ids": self.MAP_COUNTER_IDS
        }
        with open(filename, "w") as f:
            json.dump(digest, f, indent=2)
        self.log.append(f"Saved digest with map data to {filename}")

    def load_digest(self, filename: str):
        """Load runtime state from digest including map data."""
        try:
            with open(filename, "r") as f:
                digest = json.load(f)
            self.pxmemo = digest["pxmemory"]
            self.log = digest["log"]
            
            # Restore map counter IDs if available
            if "map_counter_ids" in digest:
                self.MAP_COUNTER_IDS = digest["map_counter_ids"]
            
            self.raid.counters.clear()
            for cid, data in digest["raid_state"].items():
                cid = int(cid)
                value = data['value']
                try:
                    if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
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
            self.log.append(f"Loaded digest with map data from {filename}")
        except FileNotFoundError:
            self.log.append(f"No digest found: {filename}")

    def check_sovereign(self) -> bool:
        """Check if PXRuntime has achieved sovereignty."""
        log_content = "\n".join(self.log)
        raid_status = self.raid.get_status_report()
        map_status = self.get_map_status_report()
        
        if ("Map system ready" in log_content and 
            len(self.raid.counters) >= 10):
            print("\n🌍 PXRuntime with Map Integration achieved sovereignty!")
            print(f"RAID Status:\n{raid_status}")
            print(f"Map Status:\n{map_status}")
            print("MAP INTEGRATION COMPLETE ✅\nTaking a break. 🧘")
            self.save_digest("PXOS_Map_Sovereign_Final.pxdigest")
            return True
        return False

    def runtime_loop(self):
        """Main runtime loop with map integration."""
        print("PXRuntime with Map Integration Booting...\n")
        self.execute("map_bootloader")
        
        # Generate maps with different boot pixels
        test_pixels = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (128, 128, 128)]
        
        for i, pixel in enumerate(test_pixels):
            if not self.running:
                break
            self.set_boot_pixel_and_generate(*pixel, f"test_map_{i+1}.png")
            print(self.get_map_status_report())
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
    
    # Demonstrate map integration
    print("=== PXRuntime Map Integration Demo ===")
    
    # Set a specific boot pixel and generate map
    runtime.set_boot_pixel_and_generate(200, 100, 15, "demo_map.png")
    print(runtime.get_map_status_report())
    
    # Show RAID status
    print(runtime.raid.get_status_report())
    
    # Start full runtime
    threading.Thread(target=runtime.start, daemon=True).start()
    try:
        time.sleep(10)
    finally:
        runtime.stop()
        print("\nFinal RAID Status:")
        print(runtime.raid.get_status_report())
        print("\nFinal Map Status:")
        print(runtime.get_map_status_report())
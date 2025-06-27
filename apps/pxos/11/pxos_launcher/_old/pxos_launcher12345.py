import json
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
import threading
import os
from PIL import Image, ImageDraw, ImageOps
import math
import random

# --------------------------
# Utility Functions (retained and moved for clarity)
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
# RAID Counter System (Unchanged, provided for context)
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
                # Dynamically create new counter if it doesn't exist
                self.counters[counter_id] = CounterState(
                    id=counter_id,
                    value=None, # Will be updated by .update()
                    binary_value='',
                    timestamp=time.time()
                )
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
                            # Handle dict/list values by stringifying them
                            'value': c.value if not isinstance(c.value, (dict, list)) else repr(c.value),
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
        except Exception as e:
            print(f"Error saving RAID state: {e}")
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
                        # Safely evaluate for dicts/lists
                        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                            value = eval(value)
                    except Exception:
                        pass # Keep as string if eval fails
                    self.counters[cid] = CounterState(
                        id=data['id'],
                        value=value,
                        binary_value=data['binary_value'],
                        timestamp=data['timestamp'],
                        access_count=data['access_count'],
                        is_dirty=data['is_dirty']
                    )
                return True
        except Exception as e:
            print(f"Error loading RAID state: {e}")
            return False

# --------------------------
# PXMapGenerator Module
# --------------------------

# Constants for PixelOS Patterns
CORE_PIXEL_COUNT = 9
CORE_OFFSETS = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (0, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1)
]
CORE_PIXEL_COLOR = (255, 0, 0) # Red (RGB)

# Earth-like Map Generation Constants
OCEAN_COLOR = (0, 70, 150)    # Darker blue
LAND_COLOR = (50, 150, 50)    # Greenish
CONTINENT_EDGE_COLOR = (100, 100, 0) # Yellowish for shorelines/transitions

# Sun's Core Filesystem Constants
SUN_CORE_AREA_COLOR = (255, 150, 0) # Fiery Orange
SUN_CORE_DATA_ACTIVE_COLOR = (255, 255, 0) # Bright Yellow
SUN_CORE_DATA_INACTIVE_COLOR = (100, 50, 0) # Darker Orange (for "empty" or "cold" storage)
SUN_CORE_GRID_COLOR = (255, 200, 100) # Lighter for grid lines

# Solar System Constants (for conceptual scaling)
EARTH_SUN_DISTANCE_KM = 149.6 * 10**6

@dataclass
class MapState:
    """Represents the state/parameters for generating a map."""
    boot_pixel_rgb: Optional[tuple] = None
    width: int = 800
    height: int = 600
    output_filename: str = "pxboot.png"
    hex_counter_initial: int = 0
    frame_count_initial: int = 0
    include_boot_patterns: bool = False
    center_latitude: float = 0.0
    center_longitude: float = 0.0
    pixels_per_degree: float = 2.0
    include_sun_core_filesystem: bool = True
    solar_system_pixel_scale: float = 0.0000005
    sun_core_fs_size: int = 200
    sun_core_fs_offset_x_pixels: Optional[float] = None
    sun_core_fs_offset_y_pixels: Optional[float] = None
    sun_core_activity_seed: int = 0

class PXMapGenerator:
    """Encapsulates map generation logic."""

    def __init__(self):
        pass # No state to initialize here, as state is passed via MapState object

    def _is_core_pixel(self, x: int, y: int, width: int, height: int) -> bool:
        """Checks if a given pixel coordinate is part of the immutable core."""
        center_x = width // 2
        center_y = height // 2
        for ox, oy in CORE_OFFSETS:
            if x == center_x + ox and y == center_y + oy:
                return True
        return False

    def _get_procedural_land_value(self, latitude: float, longitude: float, random_seed_val: int) -> float:
        """
        Generates a value (0.0 to 1.0) representing land (higher) or ocean (lower)
        based on geographic coordinates using a simple mathematical function.
        This is NOT real Earth geography, but a procedural, Earth-like pattern.
        The pattern is influenced by random_seed_val.
        """
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

    def _get_color_from_land_value(self, land_value: float) -> tuple:
        """Maps a land_value (0.0-1.0) to an RGB color."""
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

    def _draw_initial_boot_pattern(self, draw: ImageDraw.ImageDraw, width: int, height: int):
        """
        Draws the initial boot pattern, including the core and a blue ring.
        This simulates the 'initial_boot_flag == 1' state in the compute shader.
        """
        center_x, center_y = width // 2, height // 2

        for ox, oy in CORE_OFFSETS:
            pixel_x = center_x + ox
            pixel_y = center_y + oy
            if 0 <= pixel_x < width and 0 <= pixel_y < height:
                draw.point((pixel_x, pixel_y), fill=CORE_PIXEL_COLOR)

        ring_radius = 5.0
        for x in range(width):
            for y in range(height):
                if self._is_core_pixel(x, y, width, height):
                    continue

                dist_from_center = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                if abs(dist_from_center - ring_radius) < 1.0:
                    draw.point((x, y), fill=(0, 0, 255))

        for x in range(0, width, 10):
            draw.line([(x, 0), (x, height)], fill=(50, 50, 50))
        for y in range(0, height, 10):
            draw.line([(0, y), (width, y)], fill=(50, 50, 50))


    def _draw_binary_addition_pattern(self, draw: ImageDraw.ImageDraw, width: int, height: int, hex_counter: int, frame_count: int):
        """
        Simulates the binary addition pattern as seen in the compute shader.
        This is for visualization in the static image.
        """
        center_x, center_y = width // 2, height // 2

        offset_x_a = -20
        offset_x_b = -10
        offset_x_result = 0

        y_range = 8

        pixel_x_base_a = center_x + offset_x_a
        pixel_x_base_b = center_x + offset_x_b
        pixel_x_base_result = center_x + offset_x_result

        for bit_pos in range(y_range):
            pixel_y = center_y + bit_pos
            input_a_val = (frame_count >> bit_pos) & 1
            color = (0, 255, 0) if input_a_val == 1 else (0, 70, 0)
            draw.point((pixel_x_base_a, pixel_y), fill=color)

        for bit_pos in range(y_range):
            pixel_y = center_y + bit_pos
            input_b_val = (hex_counter >> bit_pos) & 1
            color = (255, 255, 0) if input_b_val == 1 else (70, 70, 0)
            draw.point((pixel_x_base_b, pixel_y), fill=color)

        result = (frame_count + hex_counter)
        for bit_pos in range(y_range + 1):
            pixel_y = center_y + bit_pos
            result_val = (result >> bit_pos) & 1
            color = (0, 255, 255) if result_val == 1 else (0, 70, 70)
            draw.point((pixel_x_base_result, pixel_y), fill=color)

    def _draw_sun_core_filesystem(
        self,
        draw: ImageDraw.ImageDraw,
        start_x: int, start_y: int,
        width: int, height: int,
        activity_seed: int = 0
    ):
        """
        Draws a conceptual 'Sun's Core Filesystem' area.
        This area will feature a fiery background with a data grid.
        """
        for y_offset in range(height):
            for x_offset in range(width):
                current_x = start_x + x_offset
                current_y = start_y + y_offset

                dist_to_center_x = (x_offset - width / 2) / width
                dist_to_center_y = (y_offset - height / 2) / height
                radial_dist = math.sqrt(dist_to_center_x**2 + dist_to_center_y**2)

                random.seed(activity_seed + x_offset * 7 + y_offset * 13)
                noise_val = (random.random() * 2 - 1) * 0.1

                brightness = 1.0 - radial_dist * 0.8 + noise_val

                r = int(SUN_CORE_AREA_COLOR[0] * brightness)
                g = int(SUN_CORE_AREA_COLOR[1] * brightness)
                b = int(SUN_CORE_AREA_COLOR[2] * brightness)
                if 0 <= current_x < draw.im.size[0] and 0 <= current_y < draw.im.size[1]:
                    draw.point((current_x, current_y), fill=(r, g, b))

        block_size = 10
        for y_offset in range(0, height, block_size):
            for x_offset in range(0, width, block_size):
                current_x = start_x + x_offset
                current_y = start_y + y_offset

                if (0 <= current_x < draw.im.size[0] and 0 <= current_y < draw.im.size[1] and
                    current_x + block_size <= draw.im.size[0] and current_y + block_size <= draw.im.size[1]):

                    draw.rectangle([current_x, current_y, current_x + block_size, current_y + block_size],
                                   outline=SUN_CORE_GRID_COLOR)

                    random.seed(activity_seed + x_offset * 100 + y_offset)
                    if random.random() < 0.3 + (activity_seed % 100 / 500.0):
                        fill_color = SUN_CORE_DATA_ACTIVE_COLOR
                    else:
                        fill_color = SUN_CORE_DATA_INACTIVE_COLOR

                    draw.rectangle([current_x + 1, current_y + 1, current_x + block_size - 1, current_y + block_size - 1],
                                   fill=fill_color)

    def generate_map(self, map_state: MapState):
        """
        Generates a pixel map (Image) for the PixelOS based on a MapState object.
        """
        print(f"Generating pixel substrate map: {map_state.width}x{map_state.height}...")

        # --- Decode boot_pixel_rgb if provided ---
        if map_state.boot_pixel_rgb is not None:
            R, G, B = map_state.boot_pixel_rgb
            print(f"Booting from pixel RGB: ({R}, {G}, {B})")

            landmass_seed = R
            map_state.center_longitude = (R / 255.0 * 360.0) - 180.0

            min_pixels_per_degree = 0.5
            max_pixels_per_degree = 20.0
            map_state.pixels_per_degree = min_pixels_per_degree + (G / 255.0) * (max_pixels_per_degree - min_pixels_per_degree)
            map_state.center_latitude = (G / 255.0 * 180.0) - 90.0

            map_state.include_boot_patterns = bool(B & 0b00000001)
            map_state.include_sun_core_filesystem = bool((B >> 1) & 0b00000001)
            map_state.sun_core_activity_seed = (B >> 2) * 10

            map_state.hex_counter_initial = R * 256 + G
            map_state.frame_count_initial = G * 256 + B

            map_state.sun_core_fs_offset_x_pixels = None
            map_state.sun_core_fs_offset_y_pixels = None
        else:
            landmass_seed = random.randint(0, 255) # Use a random seed if not specified by pixel

        print(f"  Derived Parameters:")
        print(f"    Center: Lat {map_state.center_latitude:.2f}, Lon {map_state.center_longitude:.2f}")
        print(f"    Zoom: {map_state.pixels_per_degree:.2f} pixels per degree")
        print(f"    Boot Patterns: {map_state.include_boot_patterns}, Sun's Core FS: {map_state.include_sun_core_filesystem}")
        print(f"    Sun's Core Activity Seed: {map_state.sun_core_activity_seed}")
        print(f"    Landmass Seed: {landmass_seed}")

        img = Image.new('RGB', (map_state.width, map_state.height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)

        # --- Draw the procedural Earth map background ---
        half_width_degrees = (map_state.width / 2) / map_state.pixels_per_degree
        half_height_degrees = (map_state.height / 2) / map_state.pixels_per_degree

        min_lon = map_state.center_longitude - half_width_degrees
        max_lon = map_state.center_longitude + half_width_degrees
        min_lat = map_state.center_latitude - half_height_degrees
        max_lat = map_state.center_latitude + half_height_degrees

        for y in range(map_state.height):
            latitude = max_lat - (y / map_state.height) * (max_lat - min_lat)
            latitude = max(-90.0, min(90.0, latitude))

            for x in range(map_state.width):
                longitude = min_lon + (x / map_state.width) * (max_lon - min_lon)
                longitude = (longitude + 180.0) % 360.0 - 180.0

                land_value = self._get_procedural_land_value(latitude, longitude, landmass_seed)
                pixel_color = self._get_color_from_land_value(land_value)

                draw.point((x, y), fill=pixel_color)

        # --- Calculate Earth's center pixel on the map ---
        earth_center_pixel_x = map_state.width // 2
        earth_center_pixel_y = map_state.height // 2

        # --- Draw Sun's Core Filesystem if requested ---
        if map_state.include_sun_core_filesystem:
            sun_core_fs_x_pos = 0
            sun_core_fs_y_pos = 0

            if map_state.sun_core_fs_offset_x_pixels is not None and map_state.sun_core_fs_offset_y_pixels is not None:
                sun_core_fs_x_pos = earth_center_pixel_x + int(map_state.sun_core_fs_offset_x_pixels)
                sun_core_fs_y_pos = earth_center_pixel_y + int(map_state.sun_core_fs_offset_y_pixels)
                print(f"  Sun's Core Filesystem: Manually offset by ({map_state.sun_core_fs_offset_x_pixels}, {map_state.sun_core_fs_offset_y_pixels}) pixels from Earth's center.")
            else:
                distance_pixels = EARTH_SUN_DISTANCE_KM * map_state.solar_system_pixel_scale
                sun_core_fs_x_pos = earth_center_pixel_x + int(distance_pixels)
                sun_core_fs_y_pos = earth_center_pixel_y
                print(f"  Sun's Core Filesystem: Calculated at {distance_pixels:.2f} pixels from Earth's center (based on {map_state.solar_system_pixel_scale} px/km).")
                sun_core_fs_x_pos -= map_state.sun_core_fs_size // 2
                sun_core_fs_y_pos -= map_state.sun_core_fs_size // 2

            self._draw_sun_core_filesystem(
                draw,
                sun_core_fs_x_pos, sun_core_fs_y_pos,
                map_state.sun_core_fs_size, map_state.sun_core_fs_size,
                activity_seed=map_state.sun_core_activity_seed
            )

        # --- Draw additional PixelOS boot patterns if requested ---
        if map_state.include_boot_patterns:
            self._draw_initial_boot_pattern(draw, map_state.width, map_state.height)
            self._draw_binary_addition_pattern(draw, map_state.width, map_state.height, map_state.hex_counter_initial, map_state.frame_count_initial)

        try:
            img.save(map_state.output_filename)
            print(f"Successfully generated '{map_state.output_filename}'")
        except Exception as e:
            print(f"Error saving image: {e}")

# --------------------------
# PXRuntime Core (Modified)
# --------------------------
class PXRuntime:
    """Compilerless PXRuntime with RAID counter storage and map integration."""

    MAP_STATE_COUNTER_ID = 5 # Assign a dedicated counter ID for map state

    def __init__(self):
        self.pxmemo = [[[0, 0, 0] for _ in range(32)] for _ in range(32)]  # Pixel memory
        self.raid = RAIDCounter()  # RAID counter for module storage
        self.map_generator = PXMapGenerator() # Instance of map generator
        self.running = False
        self.log = []

        self._initialize_modules()
        self._initialize_map_state() # Initialize or load map state

    def _initialize_modules(self):
        """Initialize default modules in RAID counters."""
        initial_modules = {
            1: """
def tick():
    log("PXRuntime Tick")
""",
            2: """
def upgrade():
    modify("pxexecutor.pxmod", "def tick():\\n    log(\\\"PXRuntime Upgraded\\\")")
    log("pxexecutor updated")
""",
            3: """
def boot():
    load_digest("PXOS_Sovereign.pxdigest")
    execute("pxexecutor.pxmod")
"""
        }
        for counter_id, code in initial_modules.items():
            # Check if module already exists to avoid overwriting on load
            if self.raid.read_data(counter_id) is None:
                self.raid.write_data(counter_id, code)

    def _initialize_map_state(self):
        """Initialize or load the map state."""
        # Attempt to load existing map state from RAID
        loaded_state_data = self.raid.read_data(self.MAP_STATE_COUNTER_ID)
        if loaded_state_data:
            try:
                # Convert dictionary back to MapState object
                # Handle tuple conversion for boot_pixel_rgb if it was stringified
                if 'boot_pixel_rgb' in loaded_state_data and isinstance(loaded_state_data['boot_pixel_rgb'], list):
                    loaded_state_data['boot_pixel_rgb'] = tuple(loaded_state_data['boot_pixel_rgb'])

                self.current_map_state = MapState(**loaded_state_data)
                self.log.append("Loaded map state from RAID.")
            except Exception as e:
                self.log.append(f"Error loading map state from RAID: {e}. Using default.")
                self.current_map_state = MapState() # Fallback to default if load fails
        else:
            # If no map state found, create a default one
            self.current_map_state = MapState(
                boot_pixel_rgb=(100, 150, 255), # Example initial boot pixel
                width=1024,
                height=768,
                output_filename="pxos_boot_map.png"
            )
            self.save_map_state(self.current_map_state) # Save initial state
            self.log.append("Initialized default map state and saved to RAID.")

        # Generate the map image based on the current state
        self.map_generator.generate_map(self.current_map_state)


    def execute(self, module_name: str):
        """Execute a module from RAID counter."""
        found = False
        for counter_id in self.raid.counters:
            code = self.raid.read_data(counter_id)
            if isinstance(code, str) and module_name in code: # Check if module_name is a substring of the code
                try:
                    # Provide access to PXRuntime methods within the executed code
                    exec_globals = {
                        'log': self.log.append,
                        'modify': self.modify,
                        'execute': self.execute,
                        'load_digest': self.load_digest,
                        'save_map_state': self.save_map_state, # Make map interaction available
                        'load_map_state': self.load_map_state,
                        'current_map_state': self.current_map_state # Provide current state
                    }
                    exec(code, exec_globals)
                    self.log.append(f"Executed {module_name}")
                    found = True
                except Exception as e:
                    self.log.append(f"Execution error in {module_name}: {e}")
                break # Exit after finding and attempting to execute
        if not found:
            self.log.append(f"Module {module_name} not found")

    def modify(self, module_name: str, new_code: str):
        """Modify a module in RAID counter or add if not found."""
        modified = False
        for counter_id in self.raid.counters:
            code = self.raid.read_data(counter_id)
            if isinstance(code, str) and module_name in code:
                self.raid.write_data(counter_id, new_code)
                self.log.append(f"Modified {module_name}")
                modified = True
                break
        if not modified:
            # Find an available counter for new module
            for counter_id in range(1, len(self.raid.counters) + 2): # Check existing and one more
                if self.raid.read_data(counter_id) is None or isinstance(self.raid.read_data(counter_id), (int, float)):
                    self.raid.write_data(counter_id, new_code)
                    self.log.append(f"Added {module_name} to new counter {counter_id}")
                    modified = True
                    break
        if not modified:
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
                    'value': c.value if not isinstance(c.value, (dict, list, tuple)) else repr(c.value), # Handle tuple
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
                    if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                        value = eval(value) # Safe for dicts/lists
                    elif isinstance(value, str) and value.startswith('(') and value.endswith(')'): # Handle tuples
                        value = eval(value)
                except Exception:
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
            # After loading RAID state, re-initialize map state from the loaded data
            self._initialize_map_state()
        except FileNotFoundError:
            self.log.append(f"No digest found: {filename}")
        except Exception as e:
            self.log.append(f"Error loading digest: {e}")

    def save_map_state(self, map_state: MapState) -> bool:
        """
        Saves the current map generation parameters to a dedicated RAID counter.
        The map image is also re-generated.
        """
        map_data = map_state.__dict__.copy()
        # Convert tuple to list for JSON serialization if it exists
        if 'boot_pixel_rgb' in map_data and isinstance(map_data['boot_pixel_rgb'], tuple):
            map_data['boot_pixel_rgb'] = list(map_data['boot_pixel_rgb'])

        success = self.raid.write_data(self.MAP_STATE_COUNTER_ID, map_data)
        if success:
            self.log.append(f"Map state saved to RAID counter {self.MAP_STATE_COUNTER_ID}.")
            self.current_map_state = map_state # Update current state
            self.map_generator.generate_map(self.current_map_state) # Regenerate map with new state
        else:
            self.log.append(f"Failed to save map state to RAID counter {self.MAP_STATE_COUNTER_ID}.")
        return success

    def load_map_state(self) -> Optional[MapState]:
        """
        Loads the map generation parameters from the dedicated RAID counter.
        The map image is also re-generated.
        """
        loaded_data = self.raid.read_data(self.MAP_STATE_COUNTER_ID)
        if loaded_data:
            try:
                # Convert list back to tuple for boot_pixel_rgb
                if 'boot_pixel_rgb' in loaded_data and isinstance(loaded_data['boot_pixel_rgb'], list):
                    loaded_data['boot_pixel_rgb'] = tuple(loaded_data['boot_pixel_rgb'])
                self.current_map_state = MapState(**loaded_data)
                self.log.append(f"Map state loaded from RAID counter {self.MAP_STATE_COUNTER_ID}.")
                self.map_generator.generate_map(self.current_map_state) # Regenerate map
                return self.current_map_state
            except Exception as e:
                self.log.append(f"Error converting loaded map data to MapState: {e}")
                return None
        self.log.append(f"No map state found in RAID counter {self.MAP_STATE_COUNTER_ID}.")
        return None

    def check_sovereign(self) -> bool:
        """Check if PXRuntime has achieved sovereignty."""
        log_content = "\n".join(self.log)
        raid_status = self.raid.get_status_report()
        # Check for map state persistence as part of sovereignty
        if ("Upgraded" in log_content and
            "Modified pxexecutor" in log_content and
            all(self.raid.read_data(i) is not None for i in range(1, 5)) and
            self.raid.read_data(self.MAP_STATE_COUNTER_ID) is not None): # Check for map state
            print("\n📣 PXRuntime has upgraded itself and persisted map state.")
            print(f"RAID Status:\n{raid_status}")
            print("PXCOMPILER RETIRED ✅\nPXSELFEDIT COMPLETE\nTaking a break. 🧘")
            self.save_digest("PXOS_Sovereign_Final.pxdigest")
            return True
        return False

    def runtime_loop(self):
        """Main runtime loop."""
        print("PXRuntime Booting...\n")
        self.execute("PXBootloader.pxexe")
        for i in range(5): # Run for a few iterations to demonstrate
            if not self.running:
                break
            self.execute("PX_UPGRADE.pxexe")
            self.execute("pxexecutor.pxmod")
            print(self.raid.get_status_report())
            # Example of modifying map state programmatically
            if i == 2:
                self.log.append("Attempting to modify map state programmatically.")
                new_map_state = MapState(
                    boot_pixel_rgb=(50, 200, 129), # Change the boot pixel
                    width=600,
                    height=800,
                    output_filename="pxos_reboot_map.png"
                )
                self.save_map_state(new_map_state)
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
    # Clean up previous state for a fresh run
    if os.path.exists("raid_counter_state.json"):
        os.remove("raid_counter_state.json")
    if os.path.exists("PXOS_Sovereign_Final.pxdigest"):
        os.remove("PXOS_Sovereign_Final.pxdigest")
    if os.path.exists("pxos_boot_map.png"):
        os.remove("pxos_boot_map.png")
    if os.path.exists("pxos_reboot_map.png"):
        os.remove("pxos_reboot_map.png")

    runtime = PXRuntime()
    threading.Thread(target=runtime.start, daemon=True).start()
    try:
        time.sleep(10) # Let the runtime execute for a bit
    finally:
        runtime.stop()
        print("\nFinal PXRuntime Log:")
        for entry in runtime.log:
            print(entry)

        # Verify map state was saved and can be reloaded
        print("\nAttempting to load map state directly from file for verification:")
        temp_raid = RAIDCounter()
        temp_raid._load_state() # Load directly from the file
        loaded_map_data = temp_raid.read_data(PXRuntime.MAP_STATE_COUNTER_ID)
        if loaded_map_data:
            print(f"Verified map state loaded from raid_counter_state.json: {loaded_map_data}")
        else:
            print("Failed to verify map state from raid_counter_state.json.")
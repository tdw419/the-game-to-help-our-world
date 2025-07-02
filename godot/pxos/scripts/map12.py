import os
from PIL import Image, ImageDraw, ImageOps
import math
import random
import sys
import json
import base64
import time
from datetime import datetime

# --- RRE Metadata for this map.py version ---
MAP_PY_VERSION = "2.0.0" # Updated version for RRE Dev Env
MAP_PY_BUILD_DATE = "2025-06-30"
# --- End RRE Metadata ---

# --- Configuration ---
DEFAULT_SUBSTRATE_WIDTH = 800
DEFAULT_SUBSTRATE_HEIGHT = 600
OUTPUT_FILENAME = "pxboot.png"
PXMEMORY_EXPORT_FILENAME = "pxmemory_export.json" # File to export Godot RRE state
GODOT_SCRIPTS_PATH = "res://scripts/" # Conceptual path for Godot scripts

# --- Constants for PixelOS Patterns (from previous map.py) ---
CORE_PIXEL_COUNT = 9
CORE_OFFSETS = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (0, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1)
]
CORE_PIXEL_COLOR = (255, 0, 0)

OCEAN_COLOR = (0, 70, 150)
LAND_COLOR = (50, 150, 50)
CONTINENT_EDGE_COLOR = (100, 100, 0)

SUN_CORE_AREA_COLOR = (255, 150, 0)
SUN_CORE_DATA_ACTIVE_COLOR = (255, 255, 0)
SUN_CORE_DATA_INACTIVE_COLOR = (100, 50, 0)
SUN_CORE_GRID_COLOR = (255, 200, 100)

EARTH_SUN_DISTANCE_KM = 149.6 * 10**6

# --- PXMemory: The Canonical In-Memory Godot RRE State ---
# This dictionary holds the entire state of the Godot RRE project,
# including module source code, roadmaps, logs, and snapshots.
PXMemory = {
    'godot_rre': {
        'modules': {},  # Stores GDScript module source code
        'roadmaps': {}, # Stores named roadmaps (e.g., "rre_upgrade_v4")
        'logs': [],     # Stores historical logs from map.py's perspective
        'active_scroll': None, # The current active roadmap/scroll name
        'snapshots': [], # Historical snapshots of PXMemory['godot_rre']
        'metadata': {
            'version': MAP_PY_VERSION,
            'last_modified': str(datetime.now()),
            'description': "Canonical in-memory state for Godot RRE development."
        }
    }
}

# --- RRE Development Environment Functions ---

def import_godot_gdscript_modules(script_dir: str = "scripts/"):
    """
    Reads GDScript files from a specified directory and imports their content
    into PXMemory['godot_rre']['modules']. This is typically a one-time import.
    """
    print(f"\n--- Importing GDScript modules from '{script_dir}' ---")
    if not os.path.exists(script_dir):
        print(f"  WARNING: Script directory '{script_dir}' not found. Skipping import.")
        return

    imported_count = 0
    for filename in os.listdir(script_dir):
        if filename.endswith(".gd"):
            module_name = filename[:-3] # Remove .gd extension
            filepath = os.path.join(script_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                    PXMemory['godot_rre']['modules'][module_name] = {
                        'source': source_code,
                        'status': 'imported',
                        'metadata': {'imported_at': str(datetime.now())}
                    }
                    print(f"  Imported: {module_name}.gd")
                    imported_count += 1
            except Exception as e:
                print(f"  ERROR importing {filename}: {e}")
    print(f"--- Finished importing {imported_count} GDScript modules. ---")

def mutate_module_in_memory(module_name: str, patch_code: str, status: str = 'patched'):
    """
    Conceptually mutates a module's source code directly in PXMemory.
    This simulates AI-driven or programmatic code changes.
    """
    if module_name in PXMemory['godot_rre']['modules']:
        PXMemory['godot_rre']['modules'][module_name]['source'] += f"\n# PATCHED: {patch_code}\n"
        PXMemory['godot_rre']['modules'][module_name]['status'] = status
        PXMemory['godot_rre']['modules'][module_name]['metadata']['last_mutated'] = str(datetime.now())
        print(f"\n--- Mutated module '{module_name}' in memory. ---")
    else:
        print(f"\n--- WARNING: Module '{module_name}' not found for mutation. ---")

def generate_new_module_in_memory(module_name: str, source_code: str, status: str = 'new'):
    """
    Conceptually generates a new module's source code directly in PXMemory.
    This simulates AI-driven module creation.
    """
    if module_name in PXMemory['godot_rre']['modules']:
        print(f"\n--- WARNING: Module '{module_name}' already exists. Overwriting. ---")
    PXMemory['godot_rre']['modules'][module_name] = {
        'source': source_code,
        'status': status,
        'metadata': {'generated_at': str(datetime.now())}
    }
    print(f"\n--- Generated new module '{module_name}' in memory. ---")

def flush_gdscript_modules_to_disk(output_dir: str = "scripts/"):
    """
    Writes the current state of GDScript modules from PXMemory back to .gd files on disk.
    This allows Godot to load the updated code on next scene reload or editor restart.
    """
    print(f"\n--- Flushing GDScript modules to disk in '{output_dir}' ---")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"  Created directory: {output_dir}")

    flushed_count = 0
    for module_name, data in PXMemory['godot_rre']['modules'].items():
        filepath = os.path.join(output_dir, f"{module_name}.gd")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(data['source'])
            print(f"  Flushed: {module_name}.gd")
            flushed_count += 1
        except Exception as e:
            print(f"  ERROR flushing {module_name}.gd: {e}")
    print(f"--- Finished flushing {flushed_count} GDScript modules. ---")

def export_px_memory_to_json(filename: str = PXMEMORY_EXPORT_FILENAME):
    """
    Exports the entire PXMemory['godot_rre'] state to a JSON file.
    Godot can read this file on startup to reflect the Python-managed state.
    """
    print(f"\n--- Exporting PXMemory state to '{filename}' ---")
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(PXMemory['godot_rre'], f, indent=2)
        print(f"--- Successfully exported PXMemory state. ---")
    except Exception as e:
        print(f"--- ERROR exporting PXMemory state: {e} ---")

def load_px_memory_from_json(filename: str = PXMEMORY_EXPORT_FILENAME):
    """
    Loads PXMemory['godot_rre'] state from a JSON file.
    Useful for restoring a previous state or for Godot to conceptually write back changes.
    """
    global PXMemory
    print(f"\n--- Loading PXMemory state from '{filename}' ---")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            PXMemory['godot_rre'] = loaded_data
        print(f"--- Successfully loaded PXMemory state. ---")
    except FileNotFoundError:
        print(f"--- WARNING: '{filename}' not found. Starting with empty PXMemory. ---")
    except Exception as e:
        print(f"--- ERROR loading PXMemory state: {e} ---")

def take_px_memory_snapshot(snapshot_name: str = None):
    """
    Takes a snapshot of the current PXMemory['godot_rre'] state and stores it
    within the 'snapshots' list in PXMemory.
    """
    if snapshot_name is None:
        snapshot_name = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    snapshot_data = {
        "name": snapshot_name,
        "timestamp": str(datetime.now()),
        "state": PXMemory['godot_rre'].copy() # Deep copy if nested mutable objects
    }
    # Remove large 'modules' source code from snapshot if not needed for historical diffs
    # snapshot_data['state']['modules'] = {k: {s:v for s,v in d.items() if s!='source'} for k,d in snapshot_data['state']['modules'].items()}
    
    PXMemory['godot_rre']['snapshots'].append(snapshot_data)
    print(f"\n--- Took PXMemory snapshot: '{snapshot_name}'. Total snapshots: {len(PXMemory['godot_rre']['snapshots'])}. ---")


# --- Helper Functions (from previous map.py, kept for completeness) ---

def is_core_pixel(x: int, y: int, width: int, height: int) -> bool:
    center_x = width // 2
    center_y = height // 2
    for ox, oy in CORE_OFFSETS:
        if x == center_x + ox and y == center_y + oy:
            return True
    return False

def get_procedural_land_value(latitude: float, longitude: float, random_seed_val: int) -> tuple:
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
    land_value = max(0.0, min(1.0, value))
    elevation_value = 0.0
    if land_value < 0.4: elevation_value = 0.0
    elif land_value < 0.5: t = (land_value - 0.4) / 0.1; elevation_value = 0.1 * t
    elif land_value < 0.6: t = (land_value - 0.5) / 0.1; elevation_value = 0.1 + 0.2 * t
    else: t = (land_value - 0.6) / 0.4; elevation_value = 0.3 + 0.7 * t
    return land_value, elevation_value

def get_color_from_land_value(land_value: float) -> tuple:
    if land_value < 0.4: return OCEAN_COLOR
    elif land_value < 0.5:
        t = (land_value - 0.4) / 0.1
        r = int(OCEAN_COLOR[0] * (1 - t) + LAND_COLOR[0] * t)
        g = int(OCEAN_COLOR[1] * (1 - t) + LAND_COLOR[1] * t)
        b = int(OCEAN_COLOR[2] * (1 - t) + LAND_COLOR[2] * t)
        return (r, g, b)
    elif land_value < 0.6: return CONTINENT_EDGE_COLOR
    else: return LAND_COLOR

def draw_initial_boot_pattern(draw: ImageDraw.ImageDraw, width: int, height: int):
    center_x, center_y = width // 2, height // 2
    for ox, oy in CORE_OFFSETS:
        pixel_x = center_x + ox
        pixel_y = center_y + oy
        if 0 <= pixel_x < width and 0 <= pixel_y < height:
            draw.point((pixel_x, pixel_y), fill=CORE_PIXEL_COLOR)
    ring_radius = 5.0
    for x in range(width):
        for y in range(height):
            if is_core_pixel(x, y, width, height): continue
            dist_from_center = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            if abs(dist_from_center - ring_radius) < 1.0: draw.point((x, y), fill=(0, 0, 255))
    for x in range(0, width, 10): draw.line([(x, 0), (x, height)], fill=(50, 50, 50))
    for y in range(0, height, 10): draw.line([(0, y), (width, y)], fill=(50, 50, 50))

def draw_binary_addition_pattern(draw: ImageDraw.ImageDraw, width: int, height: int, hex_counter: int, frame_count: int):
    center_x, center_y = width // 2, height // 2
    offset_x_a = -20; offset_x_b = -10; offset_x_result = 0
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

def draw_sun_core_filesystem(
    draw: ImageDraw.ImageDraw, 
    start_x: int, start_y: int, 
    width: int, height: int,
    activity_seed: int = 0
):
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
                if random.random() < 0.3 + (activity_seed % 100 / 500.0): fill_color = SUN_CORE_DATA_ACTIVE_COLOR
                else: fill_color = SUN_CORE_DATA_INACTIVE_COLOR
                draw.rectangle([current_x + 1, current_y + 1, current_x + block_size - 1, current_y + block_size - 1], 
                                fill=fill_color)

def draw_territory_claims(draw: ImageDraw.ImageDraw, manifest: list):
    for territory in manifest:
        name = territory.get("name", "Unnamed")
        map_coords = territory.get("map_coords")
        signature_color = tuple(territory.get("signature_color", (255, 255, 255)))
        claim_icon_char = territory.get("claim_icon_char", "X")
        if map_coords and len(map_coords) == 4:
            x_s, y_s, x_e, y_e = map_coords
            print(f"  Drawing territory for {name} at ({x_s},{y_s}) to ({x_e},{y_e}) with color {signature_color}.")
            draw.rectangle([x_s, y_s, x_e, y_e], outline=signature_color, width=1)
            text_x = x_s + (x_e - x_s) // 2 - 2
            text_y = y_s + (y_e - y_s) // 2 - 4
            draw.rectangle([text_x, text_y, text_x + 4, text_y + 4], fill=signature_color)
            
def generate_pixel_substrate_map(
    boot_pixel_rgb: tuple = None,
    width: int = DEFAULT_SUBSTRATE_WIDTH,
    height: int = DEFAULT_SUBSTRATE_HEIGHT,
    output_filename: str = OUTPUT_FILENAME,
    external_elevation_path: str = None,
    territory_manifest_b64: str = None,
    hex_counter_initial: int = 0,
    frame_count_initial: int = 0,
    include_boot_patterns: bool = False,
    center_latitude: float = 0.0,
    center_longitude: float = 0.0,
    pixels_per_degree: float = 2.0,
    include_sun_core_filesystem: bool = True,
    solar_system_pixel_scale: float = 0.0000005,
    sun_core_fs_size: int = 200,
    sun_core_fs_offset_x_pixels: float = None,
    sun_core_fs_offset_y_pixels: float = None,
    sun_core_activity_seed: int = 0
):
    start_time = time.time()
    print(f"Generating pixel substrate map: {width}x{height} (map.py v{MAP_PY_VERSION})...")

    if boot_pixel_rgb is not None:
        R, G, B = boot_pixel_rgb
        print(f"Booting from pixel RGB: ({R}, {G}, {B})")
        landmass_seed = R
        center_longitude = (R / 255.0 * 360.0) - 180.0
        min_pixels_per_degree = 0.5
        max_pixels_per_degree = 20.0
        pixels_per_degree = min_pixels_per_degree + (G / 255.0) * (max_pixels_per_degree - min_pixels_per_degree)
        center_latitude = (G / 255.0 * 180.0) - 90.0
        include_boot_patterns = bool(B & 0b00000001)
        include_sun_core_filesystem = bool((B >> 1) & 0b00000001)
        sun_core_activity_seed = (B >> 2) * 10 
        hex_counter_initial = R * 256 + G
        frame_count_initial = G * 256 + B
        sun_core_fs_offset_x_pixels = None 
        sun_core_fs_offset_y_pixels = None
    else:
        landmass_seed = random.randint(0, 255)

    print(f"  Derived Parameters:")
    print(f"    Center: Lat {center_latitude:.2f}, Lon {center_longitude:.2f}")
    print(f"    Zoom: {pixels_per_degree:.2f} pixels per degree")
    print(f"    Boot Patterns: {include_boot_patterns}, Sun's Core FS: {include_sun_core_filesystem}")
    print(f"    Sun's Core Activity Seed: {sun_core_activity_seed}")
    print(f"    Landmass Seed: {landmass_seed}")

    img = Image.new('RGBA', (width, height), color=(0, 0, 0, 0)) 
    pixels = img.load()

    external_elev_img = None
    if external_elevation_path:
        try:
            external_elev_img = Image.open(external_elevation_path).convert('L')
            if external_elev_img.size != (width, height):
                print(f"  WARNING: External elevation image size {external_elev_img.size} does not match map size {width}x{height}. Resizing.")
                external_elev_img = external_elev_img.resize((width, height))
            external_elev_pixels = external_elev_img.load()
            print(f"  Loaded external elevation from '{external_elevation_path}'.")
        except FileNotFoundError:
            print(f"  ERROR: External elevation file '{external_elevation_path}' not found. Using procedural elevation.")
            external_elev_img = None
        except Exception as e:
            print(f"  ERROR: Could not load external elevation image: {e}. Using procedural elevation.")
            external_elev_img = None

    half_width_degrees = (width / 2) / pixels_per_degree
    half_height_degrees = (height / 2) / pixels_per_degree
    min_lon = center_longitude - half_width_degrees
    max_lon = center_longitude + half_width_degrees
    min_lat = center_latitude - half_height_degrees
    max_lat = center_latitude + half_height_degrees

    for y in range(height):
        latitude = max_lat - (y / height) * (max_lat - min_lat)
        latitude = max(-90.0, min(90.0, latitude))
        for x in range(width):
            longitude = min_lon + (x / width) * (max_lon - min_lon)
            longitude = (longitude + 180.0) % 360.0 - 180.0
            land_value, procedural_elevation_value = get_procedural_land_value(latitude, longitude, landmass_seed)
            pixel_color_rgb = get_color_from_land_value(land_value)
            final_elevation_value = procedural_elevation_value
            if external_elev_img: final_elevation_value = external_elev_pixels[x, y] / 255.0
            alpha_elevation = int(final_elevation_value * 255)
            pixels[x, y] = (pixel_color_rgb[0], pixel_color_rgb[1], pixel_color_rgb[2], alpha_elevation)

    draw = ImageDraw.Draw(img)

    earth_center_pixel_x = width // 2
    earth_center_pixel_y = height // 2

    if include_sun_core_filesystem:
        sun_core_fs_x_pos = 0
        sun_core_fs_y_pos = 0
        if sun_core_fs_offset_x_pixels is not None and sun_core_fs_offset_y_pixels is not None:
            sun_core_fs_x_pos = earth_center_pixel_x + int(sun_core_fs_offset_x_pixels)
            sun_core_fs_y_pos = earth_center_pixel_y + int(sun_core_fs_offset_y_pixels)
            print(f"  Sun's Core Filesystem: Manually offset by ({sun_core_fs_offset_x_pixels}, {sun_core_fs_offset_y_pixels}) pixels from Earth's center.")
        else:
            distance_pixels = EARTH_SUN_DISTANCE_KM * solar_system_pixel_scale
            sun_core_fs_x_pos = earth_center_pixel_x + int(distance_pixels)
            sun_core_fs_y_pos = earth_center_pixel_y
            print(f"  Sun's Core Filesystem: Calculated at {distance_pixels:.2f} pixels from Earth's center (based on {solar_system_pixel_scale} px/km).")
            sun_core_fs_x_pos -= sun_core_fs_size // 2
            sun_core_fs_y_pos -= sun_core_fs_size // 2

        draw_sun_core_filesystem(
            draw, 
            sun_core_fs_x_pos, sun_core_fs_y_pos, 
            sun_core_fs_size, sun_core_fs_size,
            activity_seed=sun_core_activity_seed
        )

    if include_boot_patterns:
        draw_initial_boot_pattern(draw, width, height)
        draw_binary_addition_pattern(draw, width, height, hex_counter_initial, frame_count_initial)

    if territory_manifest_b64:
        try:
            manifest_json = base64.b64decode(territory_manifest_b64).decode('utf-8')
            manifest = json.loads(manifest_json)
            print(f"  Drawing {len(manifest)} AI territory claims.")
            draw_territory_claims(draw, manifest)
        except Exception as e:
            print(f"  ERROR: Could not decode/draw territory manifest: {e}")

    try:
        img.save(output_filename)
        print(f"Successfully generated '{output_filename}' (RGBA with Elevation in Alpha)")
    except Exception as e:
        print(f"Error saving image: {e}")

    end_time = time.time()
    generation_time = end_time - start_time
    print(f"Map generation completed in {generation_time:.4f} seconds (ANALYZE/GENERATE phase metric).")

# --- Main execution ---
if __name__ == "__main__":
    # Ensure Pillow is installed: pip install Pillow
    
    # Load PXMemory state if it exists
    load_px_memory_from_json()

    # If no arguments, run a default scenario or RRE development cycle
    if len(sys.argv) == 1:
        print("\nRunning map.py in RRE Development Mode.")
        
        # --- RRE Development Cycle Example ---
        # 1. Import existing Godot scripts into PXMemory
        import_godot_gdscript_modules()

        # 2. Mutate a module in memory (conceptual)
        mutate_module_in_memory("PXReflexDaemon", "Added RRE heartbeat ping.")

        # 3. Generate a new conceptual module in memory
        generate_new_module_in_memory("PXMetaReflector", """
# PXMetaReflector.gd
# This is a conceptual module generated by map.py for RRE.
extends Node
func reflect(): print("Self-reflection initiated.")
""")

        # 4. Define a sample roadmap in PXMemory
        PXMemory['godot_rre']['roadmaps']['rre_upgrade_v4'] = {
            'steps': [
                ":: EXECUTE LOG:Starting RRE Upgrade v4",
                ":: EXECUTE INSTALL PXMetaReflector.gd",
                ":: EXECUTE ACTIVATE PXMetaReflector",
                ":: EXECUTE LOG:RRE Upgrade v4 Complete",
                ":: EXECUTE DONE"
            ],
            'status': 'ready',
            'metadata': {'created_at': str(datetime.now())}
        }
        print("\n--- Defined 'rre_upgrade_v4' roadmap in PXMemory. ---")

        # 5. Take a snapshot of the current PXMemory state
        take_px_memory_snapshot("After_RRE_Dev_Cycle_1")

        # 6. Flush GDScript modules to disk (for Godot to pick up)
        flush_gdscript_modules_to_disk()

        # 7. Export the entire PXMemory state to JSON (for Godot to read)
        export_px_memory_to_json()

        # Generate a default pxboot.png based on some derived parameters
        print("\n--- Generating default pxboot.png based on PXMemory state ---")
        generate_pixel_substrate_map(
            boot_pixel_rgb=(120, 100, 10), # Example RGB, could be derived from PXMemory state
            output_filename="pxboot_rre_dev.png",
            width=64, height=64,
            include_boot_patterns=True,
            include_sun_core_filesystem=True,
            sun_core_activity_seed=random.randint(0, 255)
        )
        
        print("\n--- RRE Development Cycle Complete. Check 'scripts/' and 'pxmemory_export.json'. ---")

    elif len(sys.argv) >= 7:
        boot_r = int(sys.argv[1])
        boot_g = int(sys.argv[2])
        boot_b = int(sys.argv[3])
        map_width = int(sys.argv[4])
        map_height = int(sys.argv[5])
        output_file = sys.argv[6]
        external_elev_path = sys.argv[7] if len(sys.argv) > 7 else None
        territory_manifest_b64_arg = sys.argv[8] if len(sys.argv) > 8 else None
        
        generate_pixel_substrate_map(
            boot_pixel_rgb=(boot_r, boot_g, boot_b),
            width=map_width,
            height=map_height,
            output_filename=output_file,
            external_elevation_path=external_elev_path,
            territory_manifest_b64=territory_manifest_b64_arg
        )
    else:
        print("Running map.py examples. To integrate with Godot, call with: python map.py R G B WIDTH HEIGHT OUTPUT_PATH [EXTERNAL_ELEVATION_PATH] [TERRITORY_MANIFEST_B64]")
        
        example_manifest = [
            {"name": "Local_Test_AI1", "map_coords": (10, 10, 20, 20), "signature_color": (255, 0, 0)},
            {"name": "Local_Test_AI2", "map_coords": (30, 30, 40, 40), "signature_color": (0, 255, 0)}
        ]
        import json
        local_manifest_b64 = base64.b64encode(json.dumps(example_manifest).encode('utf-8')).decode('utf-8')

        print("\n--- Booting procedural map with local claims ---")
        generate_pixel_substrate_map(
            boot_pixel_rgb=(120, 100, 10),
            output_filename="local_claims_map.png",
            width=64, height=64,
            territory_manifest_b64=local_manifest_b64
        )
        print("\nEnsure 'Pillow' is installed (pip install Pillow).")

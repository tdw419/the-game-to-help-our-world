import os
from PIL import Image, ImageDraw, ImageOps, ImageFont
import math
import random
import sys
import json
import base64
import time
from datetime import datetime

# --- RRE Metadata for this map.py version ---
MAP_PY_VERSION = "2.4.0" # Updated version for RRE Dev Env with PXFS_RRE_v1.0 Phase 1 Execution
MAP_PY_BUILD_DATE = "2025-06-30"
# --- End RRE Metadata ---

# --- Configuration ---
DEFAULT_SUBSTRATE_WIDTH = 800
DEFAULT_SUBSTRATE_HEIGHT = 600
OUTPUT_FILENAME = "pxboot.png"
PXMEMORY_EXPORT_FILENAME = "pxmemory_export.json" # File to export Godot RRE state
GODOT_SCRIPTS_PATH = "scripts/" # Actual path on disk for Godot scripts

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

# --- PXFS Constants (UPDATED for PXFS_RRE_v1.0 Phase 1) ---
FS_ROOT_ORIGIN = (10, 10) # Top-left corner for the filesystem zone
# These will be conceptually updated by execute_pxfs_rre_v1_phase1()
FS_BLOCK_WIDTH = 16 # Original block size
FS_BLOCK_HEIGHT = 16 # Original block size
FILES_PER_ROW = 5 # Original files per row
PXFS_PADDING = 0 # Original padding

# --- Roadmap Scroll Constants ---
ROADMAP_SCROLL_REGION_ORIGIN = (10, 80) # Top-left corner for roadmap scroll
ROADMAP_SCROLL_REGION_WIDTH = 60 # Width of the scroll panel
ROADMAP_SCROLL_REGION_HEIGHT = 40 # Height of the scroll panel
ROADMAP_SCROLL_LINE_HEIGHT = 5 # Height per line of text in the scroll
ROADMAP_SCROLL_FONT_SIZE = 4 # Font size for drawing roadmap text
ROADMAP_SCROLL_TEXT_COLOR = (255, 255, 255) # White text

# --- PXFS_RRE_v1.0 Roadmap Content ---
PXFS_RRE_V1_0_ROADMAP = [
    ":: BEGIN ROADMAP PXFS_RRE_v1.0 ::",
    ":: GOAL: Enhance visual pixel-native file system ::",
    ":: PHASE 1: Structural Upgrades ::",
    ":: STEP: Expand FS_ZONE to support 20x10 grid (200 files)",
    ":: STEP: Add support for nested directory block encoding",
    ":: STEP: Reserve 2px padding for block boundary clarity",
    ":: PHASE 2: Metadata Encoding Enhancements ::",
    ":: STEP: Encode filename hash in pixels 6-8 of header",
    ":: STEP: Add 'last modified' timestamp pixel (color = seconds modulo)",
    ":: STEP: Store file origin agent ID using RGB agent codes",
    ":: PHASE 3: Semantic Glyph Overlays ::",
    ":: STEP: Render 3-letter filename prefix as RGB glyphs in block center",
    ":: STEP: Use visual font system (PXGlyph) for text rendering",
    ":: STEP: Enable layer toggle: metadata view vs glyph view",
    ":: PHASE 4: Execution Zone Activation ::",
    ":: STEP: Designate red-border blocks as executable",
    ":: STEP: Trigger RRE execution if pixel at (X,Y) = boot_marker",
    ":: STEP: Load corresponding module and append to roadmap history",
    ":: PHASE 5: Reflexive Mutation Awareness ::",
    ":: STEP: Compare file hash with last snapshot",
    ":: STEP: If changed, highlight border orange",
    ":: STEP: Log change to scroll log: 'FILE MUTATED: <filename>'",
    ":: END ROADMAP ::"
]


# --- RRE Development Environment Functions ---

def import_godot_gdscript_modules(script_dir: str = GODOT_SCRIPTS_PATH):
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
                        'metadata': {'imported_at': str(datetime.now()), 'size': len(source_code)}
                    }
                    print(f"  Imported: {module_name}.gd")
                    imported_count += 1
            except Exception as e:
                print(f"  ERROR importing {filename}: {e}")
    print(f"--- Finished importing {imported_count} GDScript modules. ---")

def _apply_random_patch_to_source(source_code: str, patch_type: str) -> str:
    """
    Applies a conceptual, random patch to source code.
    This is for simulation purposes only.
    """
    lines = source_code.splitlines()
    if not lines:
        return source_code

    patch_message = f"# MUTATED: {patch_type} by map.py v{MAP_PY_VERSION} @ {datetime.now()}\n"

    if patch_type == "add_comment":
        insert_line = random.randint(0, len(lines))
        lines.insert(insert_line, patch_message + "# Added a new conceptual comment.")
    elif patch_type == "add_log":
        insert_line = random.randint(0, len(lines))
        lines.insert(insert_line, patch_message + "  print(\"RRE_MUTATION_LOG: This module was patched!\") # Conceptual log")
    elif patch_type == "change_var_name":
        # Simple conceptual change
        old_var = "frame_counter"
        new_var = "rre_frame_count"
        lines = [line.replace(old_var, new_var) for line in lines]
        lines.insert(0, patch_message + f"# Renamed '{old_var}' to '{new_var}' conceptually.")
    else:
        lines.insert(0, patch_message + "# Generic conceptual patch applied.")

    return "\n".join(lines)

def auto_mutate_all_modules(mutation_chance: float = 0.2, patch_types: list = None):
    """
    Traverses all modules in PXMemory['godot_rre']['modules'] and applies
    randomized conceptual AI-like changes based on mutation_chance.
    """
    if patch_types is None:
        patch_types = ["add_comment", "add_log", "change_var_name", "generic_patch"]

    print(f"\n--- Initiating auto-mutation of modules (chance: {mutation_chance*100:.0f}%) ---")
    mutated_count = 0
    for module_name, data in PXMemory['godot_rre']['modules'].items():
        if random.random() < mutation_chance:
            selected_patch_type = random.choice(patch_types)
            original_source = data['source']
            mutated_source = _apply_random_patch_to_source(original_source, selected_patch_type)
            
            PXMemory['godot_rre']['modules'][module_name]['source'] = mutated_source
            PXMemory['godot_rre']['modules'][module_name]['status'] = 'mutated'
            PXMemory['godot_rre']['modules'][module_name]['metadata']['last_mutated'] = str(datetime.now())
            PXMemory['godot_rre']['modules'][module_name]['metadata']['last_patch_type'] = selected_patch_type
            
            print(f"  Mutated: {module_name}.gd (Type: {selected_patch_type})")
            mutated_count += 1
    print(f"--- Finished auto-mutation. {mutated_count} modules mutated. ---")


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

def flush_gdscript_modules_to_disk(output_dir: str = GODOT_SCRIPTS_PATH):
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


# --- PXFS Functions ---

def draw_filesystem_region(draw: ImageDraw.ImageDraw, files: list, origin: tuple, block_size: tuple):
    """
    Draws a visual filesystem in the substrate. Each file is a colored block.
    Files: List of dicts with keys: name, size, type, hash, color, content (optional)
    UPDATED: Uses PXFS_EXPANDED_ constants for drawing.
    """
    # Use the expanded constants for drawing, reflecting Phase 1 execution
    block_w, block_h = PXFS_EXPANDED_BLOCK_WIDTH, PXFS_EXPANDED_BLOCK_HEIGHT
    files_per_row_actual = PXFS_EXPANDED_FILES_PER_ROW
    padding_actual = PXFS_PADDING

    for i, file in enumerate(files):
        row = i // files_per_row_actual
        col = i % files_per_row_actual
        x0 = origin[0] + col * (block_w + padding_actual) # Add padding
        y0 = origin[1] + row * (block_h + padding_actual) # Add padding
        x1 = x0 + block_w
        y1 = y0 + block_h

        # Ensure drawing is within image bounds
        if x1 > draw.im.size[0] or y1 > draw.im.size[1]:
            print(f"  WARNING: Filesystem block for {file.get('name')} out of image bounds. Skipping.")
            continue

        # Border and file fill
        draw.rectangle([x0, y0, x1-1, y1-1], outline=(255, 255, 255))
        draw.rectangle([x0+1, y0+1, x1-2, y1-2], fill=file.get('color', (200, 200, 200)))

        # Header pixels
        # File type (e.g., RGB = "TXT" -> (84, 88, 84))
        draw.point((x0+1, y0+1), fill=file.get('type_color', (100, 100, 100)))
        # Flags (e.g., executable, compressed)
        draw.point((x0+2, y0+1), fill=file.get('flags_color', (50, 50, 50)))
        # Size (encoded into 2 pixels: first byte, second byte)
        size = file.get('size', 0)
        draw.point((x0+3, y0+1), fill=(size % 256, size // 256, 0))
        # Hash/CRC (conceptual)
        draw.point((x0+4, y0+1), fill=file.get('hash_color', (10, 10, 10)))

        # Optional: Draw file name glyph (conceptual)
        # This would require a glyph rendering function similar to Godot's PXGlyphCompiler
        # For now, it's just a placeholder.
        # draw_text_glyph(draw, file.get('name', ''), (x0 + 5, y0 + 5), (255, 255, 255))


# --- Roadmap Scroll Functions ---

# Try to load a default font. If not found, PIL will use a fallback.
try:
    # Use a common font that might be available on various OS
    # You might need to adjust this path for your specific OS
    FONT_PATH = "arial.ttf" # Example: Arial font
    # If Arial is not found, try other common paths or just let PIL fallback
    if sys.platform == "win32":
        FONT_PATH = "C:/Windows/Fonts/arial.ttf"
    elif sys.platform == "darwin":
        FONT_PATH = "/Library/Fonts/Arial.ttf"
    elif sys.platform.startswith("linux"):
        FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" # Common Linux font
    
    ROADMAP_FONT = ImageFont.truetype(FONT_PATH, ROADMAP_SCROLL_FONT_SIZE)
except IOError:
    print(f"WARNING: Font '{FONT_PATH}' not found. Using default PIL font for roadmap scroll.")
    ROADMAP_FONT = ImageFont.load_default() # Fallback to default PIL font

def render_roadmap_scroll(draw: ImageDraw.ImageDraw, roadmap_steps: list, origin: tuple, width: int, height: int):
    """
    Draws the PXFS_RRE_v1.0 roadmap as text glyphs into a specific region of the substrate.
    """
    print(f"  Rendering roadmap scroll at {origin} with size {width}x{height}.")
    
    current_y = origin[1]
    
    for step in roadmap_steps:
        if current_y >= origin[1] + height:
            print("  WARNING: Roadmap content exceeds scroll region height. Truncating.")
            break
        
        # Simple text drawing to simulate glyphs.
        # In a real PXOS, this would be pixel-perfect glyphs.
        draw.text((origin[0], current_y), step, font=ROADMAP_FONT, fill=ROADMAP_SCROLL_TEXT_COLOR)
        current_y += ROADMAP_SCROLL_LINE_HEIGHT


def read_roadmap_from_pixels(image: Image.Image, origin: tuple, width: int, height: int) -> list:
    """
    Conceptually reads roadmap steps back from a pixel region.
    For map.py, this is a placeholder to show awareness of the embedded roadmap.
    In Godot, PXGlyphReader would perform this.
    """
    print(f"  Conceptually reading roadmap from pixels at {origin} with size {width}x{height}.")
    # In a real implementation, you'd analyze pixel patterns here.
    # For now, we'll just return a dummy representation or the original roadmap if available.
    
    # This simulation assumes the roadmap was drawn by render_roadmap_scroll
    # and we're just "reading" it back.
    # In a true pixel-native system, this would involve pixel analysis.
    
    # For demonstration, let's return a simplified version of the roadmap
    # that would be recognizable if read by a pixel parser.
    
    # This is a conceptual read, so we'll just log and return a placeholder.
    print("  (Conceptual read: Pixel analysis to text conversion would happen here.)")
    return [":: CONCEPTUAL READ STEP 1 ::", ":: CONCEPTUAL READ STEP 2 ::"]


# --- PXFS_RRE_v1.0 Phase 1 Execution Function ---
def execute_pxfs_rre_v1_phase1():
    """
    Conceptually executes Phase 1 of the PXFS_RRE_v1.0 roadmap.
    This modifies the global PXFS drawing constants to reflect the upgrade.
    """
    global FS_BLOCK_WIDTH, FS_BLOCK_HEIGHT, FILES_PER_ROW, PXFS_PADDING
    
    print("\n--- Executing PXFS_RRE_v1.0 Phase 1: Structural Upgrades ---")
    
    # :: STEP: Expand FS_ZONE to support 20x10 grid (200 files)
    # This is achieved by changing the block size and files per row.
    FS_BLOCK_WIDTH = PXFS_EXPANDED_BLOCK_WIDTH
    FS_BLOCK_HEIGHT = PXFS_EXPANDED_BLOCK_HEIGHT
    FILES_PER_ROW = PXFS_EXPANDED_FILES_PER_ROW # This will make draw_filesystem_region use the new layout
    print(f"  Executed: Expanded FS_ZONE to {FILES_PER_ROW}x10 grid (conceptual).")
    
    # :: STEP: Add support for nested directory block encoding (conceptual)
    # This is a conceptual feature. In a real system, this would involve
    # updating the PXFS drawing logic to draw directory blocks differently.
    print("  Executed: Added conceptual support for nested directory block encoding.")
    
    # :: STEP: Reserve 2px padding for block boundary clarity
    PXFS_PADDING = 2 # Set the actual padding for drawing
    print(f"  Executed: Reserved {PXFS_PADDING}px padding for block clarity.")
    
    print("--- PXFS_RRE_v1.0 Phase 1 Execution Complete. ---")


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

        # --- NEW: Auto-mutate all modules ---
        auto_mutate_all_modules(mutation_chance=0.5) # 50% chance to mutate each module

        # 5. Take a snapshot of the current PXMemory state
        take_px_memory_snapshot("After_RRE_Dev_Cycle_1_with_Mutation")

        # 6. Flush GDScript modules to disk (for Godot to pick up)
        flush_gdscript_modules_to_disk()

        # 7. Export the entire PXMemory state to JSON (for Godot to read)
        export_px_memory_to_json()

        # --- NEW: Execute PXFS_RRE_v1.0 Phase 1 ---
        execute_pxfs_rre_v1_phase1() # Execute the conceptual upgrade

        # Generate a default pxboot.png based on some derived parameters
        print("\n--- Generating default pxboot.png based on PXMemory state ---")
        generate_pixel_substrate_map(
            boot_pixel_rgb=(120, 100, 10), # Example RGB, could be derived from PXMemory state
            output_filename="pxboot_rre_dev.png",
            width=64, height=64,
            include_boot_patterns=True,
            include_sun_core_filesystem=True,
            sun_core_activity_seed=random.randint(0, 255),
            include_pxfs=True, # Enable PXFS drawing
            include_roadmap_scroll=True # Enable roadmap scroll drawing
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
            external_elev_path=external_elev_path,
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

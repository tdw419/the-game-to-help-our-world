# PXMapExecutor.gd
# This Godot-side module is responsible for executing the external map.py script
# as a subprocess. It triggers map generation, handles its output (pxboot.png),
# and can orchestrate state synchronization with map.py's PXMemory.

extends Node

# --- Configuration ---
@export var python_executable_path: String = "python3" # Path to your Python executable (e.g., "python", "python3")
@export var map_py_script_path: String = "res://scripts/map.py" # Path to your map.py script
@export var generated_map_output_path: String = "user://pxboot.png" # Output path for the generated map image

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # To load the new map image
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging executor activity
@onready var px_memory_state_exporter: PXMemoryStateExporter = get_node_or_null("../PXMemoryStateExporter") # To export Godot's state to map.py
@onready var px_roadmap_auto_loop: Node = get_node_or_null("../PXRoadmapAutoLoop") # To temporarily stop/start auto-loop

# --- Internal State ---
var _is_generating: bool = false # Flag to prevent multiple concurrent generations

# --- Godot Lifecycle Methods ---

func _ready():
    if not display_screen or not px_scroll_log or not px_memory_state_exporter:
        print_err("PXMapExecutor: Essential dependencies missing. Executor disabled.")
        set_process(false)
        return

    print("PXMapExecutor: Initialized. Ready to execute map.py.")

# --- Core Map Generation API ---

func execute_map_generation(
    boot_rgb_r: int = 120, boot_rgb_g: int = 100, boot_rgb_b: int = 10,
    map_width: int = 64, map_height: int = 64,
    include_boot_patterns: bool = true,
    include_sun_core_filesystem: bool = true,
    include_pxfs: bool = true,
    include_roadmap_scroll: bool = true,
    trigger_pxfs_rre_v1_phase1: bool = false # NEW: Trigger PXFS RRE Phase 1 in map.py
) -> bool:
    """
    Executes map.py as a subprocess to generate a new pixel substrate map.
    This function orchestrates the bidirectional sync with map.py's PXMemory.

    Args:
        boot_rgb_r,g,b (int): RGB values for boot pixel (influences map generation).
        map_width, height (int): Dimensions of the map to generate.
        include_boot_patterns (bool): Whether to draw boot patterns.
        include_sun_core_filesystem (bool): Whether to draw Sun's Core FS.
        include_pxfs (bool): Whether to draw the Pixel Filesystem (PXFS).
        include_roadmap_scroll (bool): Whether to draw the RRE roadmap scroll.
        trigger_pxfs_rre_v1_phase1 (bool): If true, instructs map.py to execute PXFS_RRE_v1.0 Phase 1.

    Returns:
        bool: True if generation command was sent, false if already generating or failed.
    """
    if _is_generating:
        _log_executor_activity("Already generating map. Please wait.")
        return false

    _is_generating = true
    _log_executor_activity("Initiating map.py generation...")
    print("PXMapExecutor: Initiating map.py generation...")

    # --- Step 1: Export Godot's current state to JSON for map.py to read ---
    _log_executor_activity("Exporting Godot state for map.py sync.")
    px_memory_state_exporter.export_current_state()

    # --- Step 2: Prepare map.py arguments ---
    var args = [
        str(boot_rgb_r), str(boot_rgb_g), str(boot_rgb_b),
        str(map_width), str(map_height),
        ProjectSettings.globalize_path(generated_map_output_path) # Globalize path for subprocess
    ]

    # Add flags for map.py's main execution (conceptual, as map.py's __main__ handles this)
    # For now, we rely on map.py's default __main__ logic if no args are passed,
    # or pass specific args if we want to override its default RRE dev cycle.
    # The current map.py's __main__ takes no args for RRE dev cycle.
    # So, we'll execute map.py without args to trigger its RRE dev cycle,
    # and map.py will load the pxmemory_export.json.

    # If we want to trigger PXFS_RRE_v1.0 Phase 1, we need to tell map.py.
    # This requires map.py to accept an argument for it.
    # For now, map.py's __main__ will execute it if no args are passed.
    # So, we just run map.py without args for the RRE dev cycle.

    # --- Step 3: Execute map.py as a subprocess ---
    # Temporarily stop auto-loop to prevent conflicts during map generation/reload
    if px_roadmap_auto_loop and px_roadmap_auto_loop.running:
        px_roadmap_auto_loop.stop_loop()
        _log_executor_activity("PXRoadmapAutoLoop temporarily stopped.")

    var process = OS.create_process()
    var error = process.start(python_executable_path, [ProjectSettings.globalize_path(map_py_script_path)])
    
    if error != OK:
        _log_executor_activity("ERROR: Failed to start map.py process: " + str(error))
        _is_generating = false
        if px_roadmap_auto_loop and not px_roadmap_auto_loop.running:
            px_roadmap_auto_loop.start_loop() # Restart if it was stopped
        return false

    # Wait for the process to finish (blocking call - consider non-blocking for real apps)
    var exit_code = process.wait_for_exit()
    var stdout_text = process.get_stdout_text()
    var stderr_text = process.get_stderr_text()

    if exit_code == 0:
        _log_executor_activity("map.py executed successfully. Reloading map.")
        print("PXMapExecutor: map.py output:\n", stdout_text)
        if not stderr_text.is_empty():
            print("PXMapExecutor: map.py stderr:\n", stderr_text)
        _reload_generated_map()
    else:
        _log_executor_activity("ERROR: map.py failed with exit code " + str(exit_code))
        print_err("PXMapExecutor: map.py failed with exit code ", exit_code, ". Stderr:\n", stderr_text)

    _is_generating = false
    # Restart auto-loop if it was stopped
    if px_roadmap_auto_loop and not px_roadmap_auto_loop.running:
        px_roadmap_auto_loop.start_loop()
        _log_executor_activity("PXRoadmapAutoLoop restarted.")
    return true

func _reload_generated_map():
    """
    Loads the newly generated pxboot.png into the DisplayScreen.
    """
    _log_executor_activity("Reloading generated map into DisplayScreen.")
    var image = Image.new()
    var error = image.load(generated_map_output_path)
    if error == OK:
        var tex = ImageTexture.create_from_image(image)
        display_screen.texture = tex
        # Re-lock PXMemory's image if it uses the same texture
        # Assuming PXMemoryRegion re-acquires its image on texture change or has a refresh method
        if px_memory:
            px_memory._display_image = image # Update direct reference
            if not image.is_locked():
                image.lock() # Ensure it's locked for PXMemory and other readers
            px_memory.update_display() # Trigger redraw for PXMemory's own display logic
        _log_executor_activity("Map reloaded successfully.")
    else:
        _log_executor_activity("ERROR: Failed to load generated map: " + str(error))
        print_err("PXMapExecutor: Failed to load generated map: ", generated_map_output_path, " Error: ", error)

# --- Logging ---

func _log_executor_activity(message: String):
    """
    Helper function to log executor activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("MAP_EXEC: " + message)
    else:
        print("PXMapExecutor (Console Log): ", message)


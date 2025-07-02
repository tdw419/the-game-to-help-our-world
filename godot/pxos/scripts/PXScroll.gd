# PXScroll.gd
# This script enables PXOS to interpret symbolic commands (as glyphs)
# from a designated memory region and trigger corresponding actions.
# It acts as a pixel-based program interpreter.

extends Node

# --- Configuration ---
# The Rect2 defining the area on the canvas where PXScroll will look for commands.
# This should be a region where other modules (e.g., PXMemoryGlyphEditor, PXAgentNode)
# can write glyph-based commands.
@export var scroll_command_region: Rect2 = Rect2(0, 50, 40, 5) # Example: A small strip at the bottom-left

# The frequency at which PXScroll will scan its region for new commands (in seconds).
const SCAN_FREQUENCY = 0.5 # Scan twice per second

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Adjust path as needed
@onready var px_glyph_reader: PXGlyphReader = null # Will be initialized in _ready
@onready var px_glyph_compiler: PXGlyphCompiler = null # Will be initialized in _ready
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # For commands that interact with memory
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging PXScroll's actions

# Internal reference to the image data of the display for reading/writing
var display_image: Image = null

# --- Internal State ---
var time_since_last_scan: float = 0.0
var last_read_command: String = "" # To avoid re-executing the same command repeatedly

# --- Command Map ---
# A dictionary mapping recognized string commands to Callable actions.
# Each callable will receive the full command string and its arguments (if any).
var command_map: Dictionary = {}

# --- Godot Lifecycle Methods ---

func _ready():
    # Initialize dependencies
    px_glyph_reader = PXGlyphReader.new()
    px_glyph_compiler = PXGlyphCompiler.new()

    if not px_glyph_reader or not px_glyph_compiler:
        print_err("PXScroll: Failed to initialize glyph utilities. Disabling.")
        set_process(false)
        return

    if not px_memory:
        print_warn("PXScroll: PXMemoryRegion not found. Memory-related commands will not function.")
    if not px_scroll_log:
        print_warn("PXScroll: PXScrollLog not found. Logging will go to console.")

    # Get the display image reference and lock it for access
    if display_screen and display_screen.texture:
        display_image = display_screen.texture.get_data()
        if display_image:
            display_image.lock() # Lock the image for pixel access
            print("PXScroll: Initialized. Scanning region: ", scroll_command_region)
            # Clear the initial command region
            clear_region(scroll_command_region)
            update_display() # Apply initial clear
        else:
            print_err("PXScroll: Could not get image data from display_screen texture.")
    else:
        print_err("PXScroll: 'DisplayScreen' TextureRect or its texture not found. Cannot operate.")
        set_process(false)
        return

    # Populate the command map
    _setup_commands()

func _process(delta):
    # Only run if initialized and image is locked
    if display_image and display_image.is_locked():
        time_since_last_scan += delta
        if time_since_last_scan >= SCAN_FREQUENCY:
            time_since_last_scan = 0.0
            scan_and_execute_commands()

func _exit_tree():
    # Unlock the image when the node is removed from the scene tree
    if display_image and display_image.is_locked():
        display_image.unlock()
    print("PXScroll: Cleaned up image lock.")

# --- Command Setup ---

func _setup_commands():
    # Define the symbolic commands and their corresponding execution functions.
    command_map["HELLO"] = Callable(self, "_cmd_hello")
    command_map["ADD"] = Callable(self, "_cmd_add")
    command_map["MOVE"] = Callable(self, "_cmd_move")
    command_map["LOOP"] = Callable(self, "_cmd_loop") # Example of a more complex command
    command_map["CLEAR"] = Callable(self, "_cmd_clear_region") # Example: clear a region

    print("PXScroll: Commands loaded: ", command_map.keys())

# --- Scan and Execute Logic ---

func scan_and_execute_commands():
    """
    Scans the scroll_command_region for new glyph-based commands and executes them.
    """
    if not display_image or not display_image.is_locked(): return
    if not px_glyph_reader: return

    var current_command_text = px_glyph_reader.read_glyphs_from_image(display_image, scroll_command_region)

    if current_command_text and current_command_text != last_read_command:
        print("PXScroll: Detected new command: '", current_command_text, "'")
        _log_to_scroll("SCROLL: " + current_command_text.left(10)) # Log truncated command
        execute_command(current_command_text)
        last_read_command = current_command_text # Update last read command
        clear_region(scroll_command_region) # Clear region after execution to signal consumption
        update_display() # Update display after clearing
    elif current_command_text == last_read_command and not current_command_text.is_empty():
        # Command is still present but already executed, do nothing
        pass
    else:
        # No command or empty region
        last_read_command = "" # Reset if region is now empty
        pass # print("PXScroll: No new commands.")


func execute_command(full_command_string: String):
    """
    Parses the full command string and executes the corresponding action.
    """
    var parts = full_command_string.split(" ", false) # Split by space, don't include empty strings
    var command_name = parts[0].to_upper() # Command name is the first part, uppercase
    var args = []
    if parts.size() > 1:
        args = parts.slice(1) # Remaining parts are arguments

    var command_callable = command_map.get(command_name)

    if command_callable and command_callable.is_valid():
        print("PXScroll: Executing command '", command_name, "' with args: ", args)
        # Call the function with arguments
        match args.size():
            0: command_callable.call()
            1: command_callable.call(args[0])
            2: command_callable.call(args[0], args[1])
            _: command_callable.callv(args) # For more than 2 args
    else:
        print_warn("PXScroll: Unknown or invalid command: '", full_command_string, "'")
        _log_to_scroll("ERR: " + full_command_string.left(10))

# --- Command Execution Functions ---
# These functions define what each symbolic command does.

func _cmd_hello():
    print("  [CMD:HELLO] PXOS says HELLO from scroll!")
    _log_to_scroll("HELLO!")
    # Example: Write a specific byte to memory
    if px_memory:
        px_memory.write_byte(px_memory.memory_region_rect.position.x, px_memory.memory_region_rect.position.y + 1, 100)
        print("  [CMD:HELLO] Wrote 100 to memory.")

func _cmd_add(value_str: String):
    var value = value_str.to_int()
    if value_str.is_valid_int():
        print("  [CMD:ADD] Adding ", value, " (conceptually).")
        _log_to_scroll("ADD " + str(value))
        # Example: Modify a byte in memory by adding value
        if px_memory:
            var current_val = px_memory.read_byte(px_memory.memory_region_rect.position.x, px_memory.memory_region_rect.position.y + 2)
            if current_val != -1:
                px_memory.write_byte(px_memory.memory_region_rect.position.x, px_memory.memory_region_rect.position.y + 2, (current_val + value) % 256)
                print("  [CMD:ADD] Memory byte updated.")
    else:
        print_warn("  [CMD:ADD] Invalid argument: ", value_str)

func _cmd_move(x_str: String, y_str: String):
    var x = x_str.to_int()
    var y = y_str.to_int()
    if x_str.is_valid_int() and y_str.is_valid_int():
        print("  [CMD:MOVE] Moving pixel to (", x, ",", y, ") (conceptually).")
        _log_to_scroll("MOVE " + str(x) + "," + str(y))
        # Example: Change a pixel color on the main display
        if display_image and display_image.is_locked():
            if x >= 0 and x < display_image.get_width() and y >= 0 and y < display_image.get_height():
                display_image.set_pixel(x, y, Color(randf(), randf(), randf(), 1.0)) # Random color
                update_display()
            else:
                print_warn("  [CMD:MOVE] Coordinates out of display bounds.")
    else:
        print_warn("  [CMD:MOVE] Invalid arguments for MOVE: ", x_str, ",", y_str)

func _cmd_loop(count_str: String):
    var count = count_str.to_int()
    if count_str.is_valid_int() and count > 0:
        print("  [CMD:LOOP] Initiating loop for ", count, " cycles (conceptually).")
        _log_to_scroll("LOOP " + str(count))
        # This could trigger a series of actions or set a state for the kernel
        # For a true loop, you'd need more complex state management or a dedicated loop interpreter.
        # For now, it's just a log.
    else:
        print_warn("  [CMD:LOOP] Invalid argument for LOOP: ", count_str)

func _cmd_clear_region(region_name: String):
    print("  [CMD:CLEAR] Clearing region: ", region_name)
    _log_to_scroll("CLR " + region_name)
    # Example: Clear a specific region by name (you'd need to define these regions)
    # For simplicity, let's clear the scroll command region itself.
    if region_name.to_upper() == "COMMAND":
        clear_region(scroll_command_region)
        update_display()
    else:
        print_warn("  [CMD:CLEAR] Unknown region name: ", region_name)


# --- Helper Functions ---

func _log_to_scroll(message: String):
    if px_scroll_log:
        px_scroll_log.add_line(message)
    else:
        print("PXScroll (Console Log): ", message)

func clear_region(region: Rect2):
    """
    Helper function to clear a specified region on the display image.
    Sets all pixels in the region to transparent black.
    """
    if not display_image or not display_image.is_locked(): return
    if not px_glyph_compiler: return # Need compiler for GLYPH_INACTIVE_COLOR

    for y in range(int(region.position.y), int(region.position.y + region.size.y)):
        for x in range(int(region.position.x), int(region.position.x + region.size.x)):
            if x >= 0 and x < display_image.get_width() and y >= 0 and y < display_image.get_height():
                display_image.set_pixel(x, y, px_glyph_compiler.GLYPH_INACTIVE_COLOR)


func update_display():
    """
    Updates the TextureRect with the modified display_image.
    """
    if display_screen:
        var new_texture = ImageTexture.new()
        new_texture.create_from_image(display_image, 0)
        display_screen.texture = new_texture
    else:
        print_err("PXScroll: 'DisplayScreen' TextureRect not found for display update.")


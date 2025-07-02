# PXAgentMemoryCoder.gd
# This script provides an interface for PXAgents to "write" symbolic commands
# (scrolls) as glyphs directly into a designated memory region on the display.
# These written commands can then be interpreted and executed by PXScroll.gd.

extends RefCounted # Extends RefCounted for easy instantiation by agents

# --- Configuration ---
# The Rect2 defining the target region where this coder will write commands.
# This should typically be the same as PXScroll.gd's 'scroll_command_region'.
@export var target_scroll_region: Rect2 = Rect2(0, 50, 40, 5)

# --- Dependencies ---
# These will be passed to the coder when it's initialized by an agent.
var display_image: Image = null
var px_glyph_compiler: PXGlyphCompiler = null
var display_screen: TextureRect = null # Needed to update the display after writing

# --- Initialization ---
func _init(_display_image: Image, _px_glyph_compiler: PXGlyphCompiler, _display_screen: TextureRect):
    display_image = _display_image
    px_glyph_compiler = _px_glyph_compiler
    display_screen = _display_screen

    if not display_image or not px_glyph_compiler or not display_screen:
        print_err("PXAgentMemoryCoder: Failed to initialize. Missing dependencies.")
    else:
        print("PXAgentMemoryCoder: Initialized. Target region: ", target_scroll_region)

# --- Core Functionality ---

func write_command(command_text: String) -> bool:
    """
    Writes a symbolic command (as glyphs) into the target scroll region.
    This command can then be read and executed by PXScroll.gd.

    Args:
        command_text (String): The command string to write (e.g., "HELLO", "ADD 5").

    Returns:
        bool: True if the command was successfully written, false otherwise.
    """
    if not display_image or not display_image.is_locked():
        print_err("PXAgentMemoryCoder: Display image not available or not locked. Cannot write command.")
        return false
    if not px_glyph_compiler:
        print_err("PXAgentMemoryCoder: Glyph compiler not available. Cannot write command.")
        return false
    if not display_screen:
        print_err("PXAgentMemoryCoder: Display screen not available. Cannot update display.")
        return false

    print("PXAgentMemoryCoder: Attempting to write command: '", command_text, "' to ", target_scroll_region)

    # Clear the target region before writing the new command
    _clear_region(target_scroll_region)

    # Compile and draw the command text into the display image
    var write_pos = target_scroll_region.position
    var success = px_glyph_compiler.compile_text_to_image(display_image, command_text, write_pos, false)

    if success:
        print("PXAgentMemoryCoder: Successfully wrote command: '", command_text, "'")
        _update_display() # Update the display to show the newly written command
        return true
    else:
        print_err("PXAgentMemoryCoder: Failed to write command '", command_text, "'.")
        return false

# --- Helper Functions ---

func _clear_region(region: Rect2):
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

func _update_display():
    """
    Updates the TextureRect with the modified display_image.
    """
    if display_screen:
        var new_texture = ImageTexture.new()
        new_texture.create_from_image(display_image, 0)
        display_screen.texture = new_texture
    else:
        print_err("PXAgentMemoryCoder: 'DisplayScreen' TextureRect not found for display update.")


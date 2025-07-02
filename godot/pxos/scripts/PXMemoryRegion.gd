# PXMemoryRegion.gd
# This script simulates a dedicated region of visual RAM on the PXOS display.
# It allows other modules (like PXReflexKernel or PXAgentNode) to read and
# write 8-bit byte values directly to pixels within its defined region.

extends Node

# --- Configuration ---
# The Rect2 defining the area on the canvas this memory region occupies.
# Example: Rect2(45, 0, 15, 64) for a vertical memory bank.
@export var memory_region_rect: Rect2 = Rect2(45, 0, 15, 64) # Example: A vertical strip for memory

# The color channel used to store the 8-bit value (0-255).
# 0: Red, 1: Green, 2: Blue, 3: Alpha
# Using Red channel by default for simplicity.
@export_range(0, 3, 1) var pixel_value_channel: int = 0 # 0=R, 1=G, 2=B, 3=A

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Adjust path as needed

# Internal reference to the image data of the display for reading/writing
var display_image: Image = null

# --- Godot Lifecycle Methods ---

func _ready():
    # Get the display image reference and lock it for access
    if display_screen and display_screen.texture:
        display_image = display_screen.texture.get_data()
        if display_image:
            display_image.lock() # Lock the image for pixel access
            print("PXMemoryRegion: Initialized. Operating in region: ", memory_region_rect)
            # Clear the initial memory region on the display
            clear_region(memory_region_rect)
            update_display() # Apply initial clear to screen
        else:
            print_err("PXMemoryRegion: Could not get image data from display_screen texture.")
    else:
        print_err("PXMemoryRegion: 'DisplayScreen' TextureRect or its texture not found. Cannot operate.")

func _exit_tree():
    # Unlock the image when the node is removed from the scene tree
    if display_image and display_image.is_locked():
        display_image.unlock()
    print("PXMemoryRegion: Cleaned up image lock.")

# --- Core Memory Region Logic ---

func read_byte(x: int, y: int) -> int:
    """
    Reads an 8-bit byte value (0-255) from a specific pixel within the memory region.
    The value is extracted from the configured pixel_value_channel.

    Args:
        x (int): The X coordinate within the overall display.
        y (int): The Y coordinate within the overall display.

    Returns:
        int: The 8-bit byte value (0-255), or -1 if coordinates are out of bounds
             or the image is not available.
    """
    if not display_image or not display_image.is_locked():
        print_err("PXMemoryRegion: Display image not available or locked for reading.")
        return -1

    # Ensure coordinates are within the memory region and image bounds
    if not memory_region_rect.has_point(Vector2(x, y)) or \
       x < 0 or x >= display_image.get_width() or \
       y < 0 or y >= display_image.get_height():
        print_warn("PXMemoryRegion: Read coordinates (", x, ",", y, ") are outside memory region or image bounds.")
        return -1

    var pixel_color = display_image.get_pixel(x, y)
    var byte_value = 0

    match pixel_value_channel:
        0: byte_value = int(pixel_color.r * 255.0) # Red channel
        1: byte_value = int(pixel_color.g * 255.0) # Green channel
        2: byte_value = int(pixel_color.b * 255.0) # Blue channel
        3: byte_value = int(pixel_color.a * 255.0) # Alpha channel
        _:
            print_err("PXMemoryRegion: Invalid pixel_value_channel configured.")
            return -1

    return byte_value

func write_byte(x: int, y: int, value: int) -> bool:
    """
    Writes an 8-bit byte value (0-255) to a specific pixel within the memory region.
    The value is encoded into the configured pixel_value_channel.

    Args:
        x (int): The X coordinate within the overall display.
        y (int): The Y coordinate within the overall display.
        value (int): The 8-bit byte value to write (0-255).

    Returns:
        bool: True if the write was successful, false otherwise.
    """
    if not display_image or not display_image.is_locked():
        print_err("PXMemoryRegion: Display image not available or locked for writing.")
        return false

    # Ensure coordinates are within the memory region and image bounds
    if not memory_region_rect.has_point(Vector2(x, y)) or \
       x < 0 or x >= display_image.get_width() or \
       y < 0 or y >= display_image.get_height():
        print_warn("PXMemoryRegion: Write coordinates (", x, ",", y, ") are outside memory region or image bounds. Skipping write.")
        return false

    # Clamp value to 0-255 range
    value = clamp(value, 0, 255)
    var normalized_value = float(value) / 255.0

    var current_color = display_image.get_pixel(x, y)
    var new_color = current_color

    match pixel_value_channel:
        0: new_color.r = normalized_value # Red channel
        1: new_color.g = normalized_value # Green channel
        2: new_color.b = normalized_value # Blue channel
        3: new_color.a = normalized_value # Alpha channel
        _:
            print_err("PXMemoryRegion: Invalid pixel_value_channel configured.")
            return false

    display_image.set_pixel(x, y, new_color)
    update_display() # Immediately update the display after writing
    return true

func clear_region(region: Rect2):
    """
    Helper function to clear a specified region on the display image.
    Sets all pixels in the region to black (0 value in all channels).
    """
    if not display_image or not display_image.is_locked(): return

    for y in range(int(region.position.y), int(region.position.y + region.size.y)):
        for x in range(int(region.position.x), int(region.position.x + region.size.x)):
            if x >= 0 and x < display_image.get_width() and y >= 0 and y < display_image.get_height():
                display_image.set_pixel(x, y, Color(0, 0, 0, 0)) # Set to transparent black

func update_display():
    """
    Updates the TextureRect with the modified display_image.
    """
    if display_screen:
        var new_texture = ImageTexture.new()
        new_texture.create_from_image(display_image, 0)
        display_screen.texture = new_texture
    else:
        print_err("PXMemoryRegion: 'DisplayScreen' TextureRect not found for display update.")


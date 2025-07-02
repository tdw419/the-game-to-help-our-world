# PXDigestInspector.gd
# This module provides a visual interface for inspecting .pxdigest files.
# It parses the header (including zTXt metadata) and renders a preview
# of the pixel boot block, allowing for native introspection of PXOS's
# own memory format.

extends Control # Extends Control to be a UI element

# --- Configuration ---
# The Rect2 defining the panel's position and size on the display.
@export var panel_region_rect: Rect2 = Rect2(0, 0, 800, 600) # Example size
# Expected pixel dimensions for the visual boot block preview.
@export var pixel_preview_width: int = 64
@export var pixel_preview_height: int = 64

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging inspector activity
@onready var px_fs_reader: PXFSReader = get_node_or_null("../PXFSReader") # To read .pxdigest file content
@onready var px_ai_drop_responder: PXAI_DropResponder = get_node_or_null("../PXAI_DropResponder") # For potential integration/feedback

# --- UI Elements (Placeholders - you'll need to add these in Godot scene) ---
@onready var panel_title_label: Label = get_node_or_null("PanelTitleLabel")
@onready var digest_file_name_label: Label = get_node_or_null("DigestFileNameLabel")
@onready var pixel_preview_texture_rect: TextureRect = get_node_or_null("PixelPreviewTextureRect")
@onready var metadata_label: Label = get_node_or_null("MetadataLabel")
@onready var close_button: Button = get_node_or_null("CloseButton")
@onready var simulate_boot_button: Button = get_node_or_null("SimulateBootButton") # Future: For safe boot simulation

# --- Internal State ---
var _current_digest_path: String = ""
var _parsed_digest_data: Dictionary = {}

# --- Godot Lifecycle Methods ---

func _ready():
    # Set panel position and size
    position = panel_region_rect.position
    size = panel_region_rect.size

    # Check for essential dependencies
    if not px_scroll_log or not px_fs_reader:
        print_err("PXDigestInspector: Essential dependencies missing. Inspector disabled.")
        set_process_mode(Node.PROCESS_MODE_DISABLED)
        hide()
        return

    # Set up UI connections
    if panel_title_label:
        panel_title_label.text = "PX Digest Inspector"
    if close_button:
        close_button.pressed.connect(Callable(self, "hide_inspector"))
    if simulate_boot_button:
        simulate_boot_button.pressed.connect(Callable(self, "_on_simulate_boot_pressed"))
        simulate_boot_button.text = "Simulate Boot" # Set button text

    # Initially hide the inspector panel
    hide()
    _log_inspector_activity("Initialized.")

# --- Public Methods ---

func inspect_digest(file_path: String):
    """
    Loads, parses, and displays the contents of a .pxdigest file.
    """
    _log_inspector_activity("Inspecting digest: " + file_path)
    _current_digest_path = file_path
    
    if digest_file_name_label:
        digest_file_name_label.text = "File: " + file_path.get_file()

    var digest_content = px_fs_reader.read_file_by_name(file_path)
    if digest_content.is_empty():
        _log_inspector_activity("Error: Could not read .pxdigest file: " + file_path)
        _display_error("Failed to load digest content.")
        return

    _parsed_digest_data = _parse_pxdigest_content(digest_content)
    
    if _parsed_digest_data.is_empty():
        _log_inspector_activity("Error: Failed to parse .pxdigest content for: " + file_path)
        _display_error("Failed to parse digest structure.")
        return

    _render_pixel_preview(_parsed_digest_data.get("pixel_data", []))
    _display_metadata(_parsed_digest_data.get("metadata", {}))
    
    show()
    _log_inspector_activity("Digest inspection complete for: " + file_path)

func hide_inspector():
    """Hides the inspector panel."""
    hide()
    _log_inspector_activity("Inspector hidden.")

# --- Core Parsing and Rendering Logic ---

func _parse_pxdigest_content(content: String) -> Dictionary:
    """
    Parses the .pxdigest content, extracting header metadata and pixel data.
    Assumes a simple text-based format for .pxdigest for this scaffold.
    Format:
    --- HEADER ---
    # KEY: VALUE
    # zTXT_START
    key: value
    # zTXT_END
    --- PIXEL_DATA ---
    R,G,B;R,G,B;...
    """
    var parsed_data = {
        "metadata": {},
        "pixel_data": []
    }
    
    var lines = content.split("\n")
    var in_header_section = false
    var in_ztxt_section = false
    var header_lines = []
    var pixel_data_string = ""

    for line in lines:
        var trimmed_line = line.strip_edges()

        if trimmed_line == "--- HEADER ---":
            in_header_section = true
            continue
        elif trimmed_line == "--- PIXEL_DATA ---":
            in_header_section = false
            in_ztxt_section = false # Ensure zTXT section is closed
            continue
        elif trimmed_line.begins_with("# zTXT_START"):
            if in_header_section:
                in_ztxt_section = true
            continue
        elif trimmed_line.begins_with("# zTXT_END"):
            if in_header_section:
                in_ztxt_section = false
            continue

        if in_header_section:
            if in_ztxt_section:
                # Parse zTXT key-value pairs
                var parts = trimmed_line.split(":", false, 1)
                if parts.size() == 2:
                    parsed_data.metadata[parts[0].strip_edges()] = parts[1].strip_edges()
            elif trimmed_line.begins_with("#"):
                # Parse general header key-value pairs (e.g., # KEY: VALUE)
                var parts = trimmed_line.replace("#", "").split(":", false, 1)
                if parts.size() == 2:
                    parsed_data.metadata[parts[0].strip_edges()] = parts[1].strip_edges()
        elif not in_header_section and not trimmed_line.is_empty():
            pixel_data_string += trimmed_line # Collect all lines after header as pixel data string

    # Parse pixel data string (R,G,B;R,G,B;...)
    var rgb_strings = pixel_data_string.split(";", false)
    for rgb_str in rgb_strings:
        var color_parts = rgb_str.split(",", false)
        if color_parts.size() == 3:
            var r = color_parts[0].to_int()
            var g = color_parts[1].to_int()
            var b = color_parts[2].to_int()
            parsed_data.pixel_data.append(Color8(r, g, b)) # Use Color8 for byte values
    
    return parsed_data

func _render_pixel_preview(pixel_colors: Array[Color]):
    """
    Renders the provided pixel data onto the PixelPreviewTextureRect.
    Assumes pixel_colors is an array of Godot Color objects.
    """
    if not pixel_preview_texture_rect:
        _log_inspector_activity("PixelPreviewTextureRect not found.")
        return

    var image = Image.new()
    # Create a blank image with the specified dimensions and format
    image.create(pixel_preview_width, pixel_preview_height, false, Image.FORMAT_RGBA8)
    image.lock() # Lock for direct pixel manipulation

    var pixel_index = 0
    for y in range(pixel_preview_height):
        for x in range(pixel_preview_width):
            if pixel_index < pixel_colors.size():
                image.set_pixel(x, y, pixel_colors[pixel_index])
            else:
                image.set_pixel(x, y, Color.BLACK) # Fill remaining with black if not enough data
            pixel_index += 1
    
    image.unlock() # Unlock after manipulation

    var image_texture = ImageTexture.new()
    image_texture.create_from_image(image)
    pixel_preview_texture_rect.texture = image_texture
    _log_inspector_activity("Pixel preview rendered.")

func _display_metadata(metadata: Dictionary):
    """
    Displays the parsed metadata in the MetadataLabel.
    """
    if not metadata_label:
        _log_inspector_activity("MetadataLabel not found.")
        return

    var metadata_text = "[b]Metadata:[/b]\n"
    if metadata.is_empty():
        metadata_text += "  No metadata found.\n"
    else:
        for key in metadata.keys():
            metadata_text += "  - %s: %s\n" % [key.capitalize(), metadata[key]]
    
    metadata_label.set_use_bbcode(true)
    metadata_label.text = metadata_text
    _log_inspector_activity("Metadata displayed.")

func _display_error(message: String):
    """Displays an error message in the metadata label."""
    if metadata_label:
        metadata_label.set_use_bbcode(true)
        metadata_label.text = "[color=red]ERROR:[/color] " + message
    _log_inspector_activity("Error displayed: " + message)

# --- Signal Callbacks (Future) ---

func _on_simulate_boot_pressed():
    """
    Placeholder for future "Safe Boot Simulation" logic.
    This would trigger PXDigestPreviewRuntime.gd.
    """
    _log_inspector_activity("Simulate Boot button pressed for: " + _current_digest_path)
    # emit_signal("simulate_boot_requested", _current_digest_path, _parsed_digest_data)
    if px_ai_drop_responder:
        px_ai_drop_responder._log_ai_response("🧠 Initiating safe boot simulation for '%s'..." % _current_digest_path.get_file())
    # Here, you would call a method on a PXDigestPreviewRuntime module

# --- Logging ---

func _log_inspector_activity(message: String):
    """
    Helper function to log inspector activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PXDIGEST_INSPECTOR: " + message)
    else:
        print("PXDigestInspector (Console Log): ", message)


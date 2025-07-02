# PXSandbox.gd
# This module provides a safe, temporary environment for editing .pxdigest files
# (metadata and pixel data) and re-running simulations without affecting the original file.
# It's a crucial tool for debugging, testing, and refining digest logic.

extends Control # Extends Control to be a UI element for the sandbox editor

# --- Configuration ---
@export var panel_region_rect: Rect2 = Rect2(0, 0, 1200, 800) # Default size for the sandbox panel
@export var title_text: String = "PX Digest Sandbox Editor"
@export var temp_sandbox_dir: String = "user://pxsandbox/" # Directory for temporary sandbox files

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging sandbox activity
@onready var px_fs_reader: PXFSReader = get_node_or_null("../PXFsReader") # For reading/writing files
@onready var px_digest_inspector: PXDigestInspector = get_node_or_null("../PXDigestInspector") # For parsing/rendering digest data
@onready var px_digest_preview_runtime: PXDigestPreviewRuntime = get_node_or_null("../PXDigestPreviewRuntime") # For running simulations
@onready var px_sim_panel: PXSimPanel = get_node_or_null("../PXSimPanel") # To display simulation results

# --- UI Elements (Placeholders - you'll need to add these in Godot scene) ---
@onready var panel_title_label: Label = get_node_or_null("PanelTitleLabel")
@onready var original_digest_label: Label = get_node_or_null("OriginalDigestLabel")
@onready var metadata_text_edit: TextEdit = get_node_or_null("MetadataTextEdit") # For editing zTXT metadata
@onready var pixel_data_text_edit: TextEdit = get_node_or_null("PixelDataTextEdit") # For editing pixel data (raw RGB values)
@onready var save_sandbox_button: Button = get_node_or_null("SaveSandboxButton")
@onready var run_simulation_button: Button = get_node_or_null("RunSimulationButton")
@onready var close_button: Button = get_node_or_null("CloseButton")
@onready var pixel_preview_texture_rect: TextureRect = get_node_or_null("PixelPreviewTextureRect") # To show live pixel changes

# --- Internal State ---
var _original_digest_path: String = ""
var _sandbox_digest_path: String = ""
var _current_sandbox_metadata: Dictionary = {}
var _current_sandbox_pixel_data: Array[Color] = [] # Array of Godot Color objects for live editing
var _framebuffer_image: Image = null
var _framebuffer_texture: ImageTexture = null

# --- Godot Lifecycle Methods ---

func _ready():
    # Set panel position and size
    position = panel_region_rect.position
    size = panel_region_rect.size

    # Check for essential dependencies
    if not px_scroll_log or not px_fs_reader or not px_digest_inspector or not px_digest_preview_runtime or not px_sim_panel:
        print_err("PXSandbox: Essential dependencies missing. Sandbox disabled.")
        set_process_mode(Node.PROCESS_MODE_DISABLED)
        hide()
        return

    # Initialize UI elements
    if panel_title_label:
        panel_title_label.text = title_text
    if metadata_text_edit:
        metadata_text_edit.syntax_highlighter = null # Simple text editing
        metadata_text_edit.wrap_mode = TextEdit.WRAP_WORD
    if pixel_data_text_edit:
        pixel_data_text_edit.syntax_highlighter = null
        pixel_data_text_edit.wrap_mode = TextEdit.WRAP_NONE # Pixels might be long lines

    if pixel_preview_texture_rect:
        _framebuffer_image = Image.new()
        _framebuffer_image.create(pixel_preview_texture_rect.size.x, pixel_preview_texture_rect.size.y, false, Image.FORMAT_RGBA8)
        _framebuffer_texture = ImageTexture.new()
        pixel_preview_texture_rect.texture = _framebuffer_texture
        _render_pixel_preview([]) # Clear initial preview

    # Connect UI button signals
    if save_sandbox_button:
        save_sandbox_button.pressed.connect(Callable(self, "_on_save_sandbox_pressed"))
    if run_simulation_button:
        run_simulation_button.pressed.connect(Callable(self, "_on_run_simulation_pressed"))
    if close_button:
        close_button.pressed.connect(Callable(self, "hide_sandbox"))
    
    # Connect TextEdit signals for live preview
    if metadata_text_edit:
        metadata_text_edit.text_changed.connect(Callable(self, "_on_metadata_text_changed"))
    if pixel_data_text_edit:
        pixel_data_text_edit.text_changed.connect(Callable(self, "_on_pixel_data_text_changed"))

    _ensure_temp_sandbox_directory()
    hide()
    _log_sandbox_activity("Initialized.")

# --- Public Methods ---

func open_digest_in_sandbox(digest_path: String):
    """
    Loads a .pxdigest file into the sandbox for editing and simulation.
    """
    _log_sandbox_activity("Opening digest in sandbox: " + digest_path)
    _original_digest_path = digest_path
    
    if original_digest_label:
        original_digest_label.text = "Original: " + digest_path.get_file()

    var digest_content = px_fs_reader.read_file_by_name(digest_path)
    if digest_content.is_empty():
        _log_sandbox_activity("Error: Could not read original digest file: " + digest_path)
        return

    var parsed_data = px_digest_inspector._parse_pxdigest_content(digest_content)
    _current_sandbox_metadata = parsed_data.get("metadata", {})
    _current_sandbox_pixel_data = parsed_data.get("pixel_data", [])

    _update_ui_from_sandbox_data()
    _generate_sandbox_file() # Create the temporary sandbox file
    show()
    _log_sandbox_activity("Digest loaded into sandbox.")

func hide_sandbox():
    """Hides the sandbox panel and cleans up temporary files."""
    hide()
    _log_sandbox_activity("Sandbox hidden.")
    _cleanup_sandbox_files()
    _clear_display()

# --- Internal UI Update & Data Management ---

func _update_ui_from_sandbox_data():
    """Updates TextEdit fields and pixel preview from current sandbox data."""
    if metadata_text_edit:
        var metadata_str = ""
        for key in _current_sandbox_metadata.keys():
            metadata_str += "%s: %s\n" % [key, _current_sandbox_metadata[key]]
        metadata_text_edit.text = metadata_str
    
    if pixel_data_text_edit:
        var pixel_str_array = []
        for color in _current_sandbox_pixel_data:
            pixel_str_array.append("%d,%d,%d" % [color.r8, color.g8, color.b8])
        pixel_data_text_edit.text = ";".join(pixel_str_array)
    
    _render_pixel_preview(_current_sandbox_pixel_data)

func _parse_metadata_from_text_edit() -> Dictionary:
    """Parses metadata from the TextEdit field."""
    var new_metadata = {}
    if metadata_text_edit:
        var lines = metadata_text_edit.text.split("\n")
        for line in lines:
            var parts = line.split(":", false, 1)
            if parts.size() == 2:
                new_metadata[parts[0].strip_edges()] = parts[1].strip_edges()
    return new_metadata

func _parse_pixel_data_from_text_edit() -> Array[Color]:
    """Parses pixel data from the TextEdit field."""
    var new_pixel_data: Array[Color] = []
    if pixel_data_text_edit:
        var rgb_strings = pixel_data_text_edit.text.split(";", false)
        for rgb_str in rgb_strings:
            var color_parts = rgb_str.split(",", false)
            if color_parts.size() == 3:
                var r = color_parts[0].to_int()
                var g = color_parts[1].to_int()
                var b = color_parts[2].to_int()
                new_pixel_data.append(Color8(r, g, b))
    return new_pixel_data

func _render_pixel_preview(pixel_colors: Array[Color]):
    """Renders the provided pixel data onto the PixelPreviewTextureRect."""
    if not pixel_preview_texture_rect or not _framebuffer_image:
        return

    _framebuffer_image.lock()
    _framebuffer_image.fill(Color.BLACK) # Clear previous
    var img_width = _framebuffer_image.get_width()
    var img_height = _framebuffer_image.get_height()

    var pixel_index = 0
    for y in range(img_height):
        for x in range(img_width):
            if pixel_index < pixel_colors.size():
                _framebuffer_image.set_pixel(x, y, pixel_colors[pixel_index])
            else:
                _framebuffer_image.set_pixel(x, y, Color.BLACK) # Fill remaining with black
            pixel_index += 1
    
    _framebuffer_image.unlock()
    _framebuffer_texture.create_from_image(_framebuffer_image)
    pixel_preview_texture_rect.texture = _framebuffer_texture

# --- File Management for Sandbox ---

func _generate_sandbox_file():
    """Generates a temporary .pxdigest file in the sandbox directory."""
    _ensure_temp_sandbox_directory()

    var original_file_name = _original_digest_path.get_file().replace(".pxdigest", "")
    _sandbox_digest_path = "%s%s_sandbox_%s.pxdigest" % [temp_sandbox_dir, original_file_name, str(Time.get_unix_time_from_system())]

    var file_content = _build_digest_content_from_sandbox_data()
    
    var file = FileAccess.open(_sandbox_digest_path, FileAccess.WRITE)
    if file:
        file.store_string(file_content)
        file.close()
        _log_sandbox_activity("Sandbox digest created: " + _sandbox_digest_path)
    else:
        _log_sandbox_activity("Error: Could not create sandbox digest file: " + _sandbox_digest_path)

func _build_digest_content_from_sandbox_data() -> String:
    """Builds the .pxdigest content string from current sandbox data."""
    var content = "--- HEADER ---\n"
    for key in _current_sandbox_metadata.keys():
        content += "%s: %s\n" % [key, _current_sandbox_metadata[key]]
    content += "# zTXT_START\n"
    # Assuming zTXT is just the key-value pairs for now.
    # For more complex zTXT, you'd need a more sophisticated parser/builder.
    for key in _current_sandbox_metadata.keys():
        content += "%s: %s\n" % [key, _current_sandbox_metadata[key]]
    content += "# zTXT_END\n"
    content += "--- PIXEL_DATA ---\n"
    var pixel_str_array = []
    for color in _current_sandbox_pixel_data:
        pixel_str_array.append("%d,%d,%d" % [color.r8, color.g8, color.b8])
    content += ";".join(pixel_str_array) + "\n"
    
    # If the original digest had an ISO payload, we should try to preserve it
    # This would require reading the original raw content and re-embedding.
    # For this scaffold, we omit re-embedding ISO payload from sandbox edits.
    # A full implementation would need to handle binary data within the text format.

    return content

func _ensure_temp_sandbox_directory():
    """Ensures the temporary sandbox directory exists."""
    var dir = DirAccess.open("user://")
    if dir and not dir.dir_exists(temp_sandbox_dir.replace("user://", "")):
        dir.make_dir(temp_sandbox_dir.replace("user://", ""))
        _log_sandbox_activity("Created temporary sandbox directory: " + temp_sandbox_dir)

func _cleanup_sandbox_files():
    """Removes temporary files created in the sandbox directory."""
    var dir = DirAccess.open(temp_sandbox_dir)
    if dir:
        dir.list_dir_begin()
        var file_name = dir.get_next()
        while file_name != "":
            if not dir.current_is_dir():
                var file_path = temp_sandbox_dir + file_name
                dir.remove(file_path)
                _log_sandbox_activity("Cleaned up sandbox file: " + file_path)
            file_name = dir.get_next()
        dir.list_dir_end()
    _log_sandbox_activity("Sandbox files cleanup complete.")

# --- UI Button Callbacks ---

func _on_save_sandbox_pressed():
    """Saves the current edits to the temporary sandbox file."""
    _current_sandbox_metadata = _parse_metadata_from_text_edit()
    _current_sandbox_pixel_data = _parse_pixel_data_from_text_edit()
    _generate_sandbox_file() # Overwrite the existing sandbox file
    _log_sandbox_activity("Sandbox changes saved to temporary file.")

func _on_run_simulation_pressed():
    """Runs a simulation using the current sandbox digest."""
    if _sandbox_digest_path.is_empty() or not FileAccess.file_exists(_sandbox_digest_path):
        _log_sandbox_activity("Error: No sandbox digest to simulate. Save changes first.")
        return
    
    _log_sandbox_activity("Running simulation from sandbox digest: " + _sandbox_digest_path.get_file())
    if px_sim_panel:
        px_sim_panel.show_panel(_sandbox_digest_path) # Show sim panel and trigger simulation
    else:
        _log_sandbox_activity("Error: PXSimPanel not available to display simulation.")

# --- TextEdit Change Callbacks for Live Preview ---

func _on_metadata_text_changed():
    """Updates internal metadata state and regenerates sandbox file on text change."""
    _current_sandbox_metadata = _parse_metadata_from_text_edit()
    _generate_sandbox_file() # Regenerate sandbox file with new metadata

func _on_pixel_data_text_changed():
    """Updates internal pixel data state and regenerates preview on text change."""
    _current_sandbox_pixel_data = _parse_pixel_data_from_text_edit()
    _render_pixel_preview(_current_sandbox_pixel_data)
    _generate_sandbox_file() # Regenerate sandbox file with new pixel data

# --- Utility Functions ---

func _clear_display():
    """Clears all display elements."""
    if original_digest_label: original_digest_label.text = "Original: N/A"
    if metadata_text_edit: metadata_text_edit.text = ""
    if pixel_data_text_edit: pixel_data_text_edit.text = ""
    _render_pixel_preview([]) # Clear pixel preview

# --- Logging ---

func _log_sandbox_activity(message: String):
    """
    Helper function to log sandbox activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PXSANDBOX: " + message)
    else:
        print("PXSandbox (Console Log): ", message)


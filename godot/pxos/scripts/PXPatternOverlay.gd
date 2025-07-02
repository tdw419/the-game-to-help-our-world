# PXPatternOverlay.gd
# This script provides a visual overlay on the PXOS display to highlight
# detected memory patterns. It supports per-byte highlighting, bounding boxes,
# and text labels, with configurable colors and toggles.

extends Node2D # Extends Node2D to use its _draw() function for custom rendering

# --- Configuration ---
@export var overlay_update_frequency: float = 0.1 # How often to redraw (in seconds)
@export var match_display_duration: float = 1.0 # How long a match remains highlighted (in seconds)

# --- Visual Mode Toggles ---
@export var enable_byte_highlight: bool = true
@export var enable_bounding_box: bool = true
@export var enable_label_annotation: bool = true

# --- Colors ---
@export var highlight_color: Color = Color(0.0, 1.0, 0.0, 0.5) # Green, semi-transparent
@export var bounding_box_color: Color = Color(1.0, 1.0, 0.0, 0.8) # Yellow, opaque
@export var label_color: Color = Color(1.0, 1.0, 1.0, 1.0) # White, opaque

# --- Label Offset ---
@export var label_offset: Vector2 = Vector2(0, -5) # Offset for label relative to pattern start

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Adjust path as needed
@onready var px_memory_pattern_detector: PXMemoryPatternDetector = get_node_or_null("../PXMemoryPattern")
var glyph_compiler: PXGlyphCompiler = null

# --- Internal State ---
# Stores active matches: [{"name": "PatternName", "start_coord": Vector2, "pattern_length": int, "time_remaining": float}]
var active_match_visuals: Array = []
var time_since_last_update: float = 0.0

# --- Godot Lifecycle Methods ---

func _ready():
    # Initialize dependencies
    glyph_compiler = PXGlyphCompiler.new()
    if not glyph_compiler:
        print_err("PXPatternOverlay: Failed to initialize PXGlyphCompiler.")
        set_process(false) # Disable if essential dependency is missing
        return

    if not px_memory_pattern_detector:
        print_err("PXPatternOverlay: PXMemoryPatternDetector node not found. Cannot visualize patterns.")
        set_process(false)
        return

    # Register this overlay's callback with the pattern detector
    # The callback will be called whenever a pattern is detected.
    px_memory_pattern_detector.add_pattern_callback(Callable(self, "_on_pattern_detected"))
    print("PXPatternOverlay: Initialized and registered with PXMemoryPatternDetector.")

    # Ensure this node is set to redraw
    set_process_mode(Node.PROCESS_MODE_ALWAYS)
    set_process(true)
    queue_redraw() # Request initial draw

func _process(delta):
    time_since_last_update += delta

    # Update TTL for active matches and remove expired ones
    for i in range(active_match_visuals.size() - 1, -1, -1):
        var match = active_match_visuals[i]
        match.time_remaining -= delta
        if match.time_remaining <= 0:
            active_match_visuals.remove_at(i)

    # Request redraw at configured frequency
    if time_since_last_update >= overlay_update_frequency:
        queue_redraw() # Request a redraw of the custom drawing
        time_since_last_update = 0.0

func _draw():
    # This function is called automatically by Godot when queue_redraw() is called.
    # All custom drawing logic goes here.

    if not display_screen or not display_screen.texture:
        # print_warn("PXPatternOverlay: DisplayScreen or its texture not available for drawing.")
        return

    # Get the global position and scale of the DisplayScreen to draw correctly over it
    var display_global_pos = display_screen.global_position
    var display_scale = display_screen.get_global_transform().get_scale()

    # Iterate through all currently active matches and draw their overlays
    for match in active_match_visuals:
        var start_coord = match.start_coord
        var pattern_length = match.pattern_length
        var pattern_name = match.name

        # Calculate the bounding box for the entire pattern
        # Assuming 1 pixel per byte for simplicity in PXMemoryRegion
        var end_coord_x = start_coord.x + pattern_length - 1
        var bounding_rect = Rect2(start_coord.x, start_coord.y, pattern_length, 1) # Assumes horizontal pattern

        # Adjust drawing to match the DisplayScreen's position and scale
        var draw_start_pos = (start_coord * display_scale) + display_global_pos
        var draw_bounding_rect = Rect2(draw_start_pos, bounding_rect.size * display_scale)

        # --- 1. Highlight Every Matched Byte ---
        if enable_byte_highlight:
            for i in range(pattern_length):
                var byte_pixel_pos = (Vector2(start_coord.x + i, start_coord.y) * display_scale) + display_global_pos
                draw_rect(Rect2(byte_pixel_pos, Vector2(1, 1) * display_scale), highlight_color)

        # --- 2. Draw a Bounding Box Around Matched Region ---
        if enable_bounding_box:
            # Draw a simple rectangle outline
            draw_rect(draw_bounding_rect, bounding_box_color, false, 1.0 * display_scale.x) # Last arg is line width

        # --- 3. Annotate the Region with a Label ---
        if enable_label_annotation and pattern_name:
            # Calculate label position
            var label_draw_pos = (start_coord + label_offset) * display_scale + display_global_pos
            # Draw the text using Godot's built-in drawing (or PXGlyphCompiler if needed)
            # For simplicity, we'll use draw_string for now. If you want pixel glyphs,
            # PXGlyphCompiler needs to draw directly onto the Image, then update the TextureRect.
            # For an overlay, draw_string is more direct.
            # If you want pixel glyphs for labels, PXGlyphCompiler would need to compile
            # to a separate ImageTexture that is then drawn as a sprite.
            # For this scaffold, let's use draw_string for simplicity.
            var font = ThemeDB.fallback_font # Use a default font
            var font_size = 8 * display_scale.x # Adjust font size based on scale
            draw_string(font, label_draw_pos, pattern_name, H_ALIGNMENT_LEFT, -1, font_size, label_color)


# --- Callback from PXMemoryPatternDetector ---
func _on_pattern_detected(pattern_array: Array[int], match_start_coord: Vector2, pattern_name: String):
    """
    Callback function invoked by PXMemoryPatternDetector when a pattern is detected.
    """
    print("PXPatternOverlay: Received detected pattern '", pattern_name, "' at ", match_start_coord)
    # Add the detected match to our list for drawing
    active_match_visuals.append({
        "name": pattern_name,
        "start_coord": match_start_coord,
        "pattern_length": pattern_array.size(),
        "time_remaining": match_display_duration
    })
    queue_redraw() # Request a redraw immediately after a new match is detected


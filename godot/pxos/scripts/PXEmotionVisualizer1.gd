# PXEmotionVisualizer.gd
# This script provides a visual overlay on the PXOS display to render
# the current levels of various emotions simulated by PXEmotionEngine.gd.
# It uses graphical elements (e.g., bars, meters, color changes) to
# make PXOS's affective state immediately observable.

extends Node2D # Extends Node2D for custom drawing

# --- Configuration ---
# The Rect2 defining the area on the canvas where this visualizer will draw.
@export var visualizer_region_rect: Rect2 = Rect2(85, 65, 40, 60) # Example: Below Goal Overlay

# How often the visualizer redraws itself (in seconds).
@export var redraw_frequency: float = 0.1 # Update frequently for smooth visual feedback

# --- Visuals ---
@export var bar_height_per_emotion: float = 8.0 # Height of each emotion bar
@export var bar_spacing: float = 2.0 # Spacing between bars
@export var bar_background_color: Color = Color(0.15, 0.15, 0.15, 0.8) # Dark grey for empty bar
@export var bar_fill_color_base: Color = Color(0.0, 0.5, 1.0, 0.8) # Base blue for fill

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Main display
@onready var px_emotion_engine: PXEmotionEngine = get_node_or_null("../PXEmotionEngine") # To read emotional states
var glyph_compiler: PXGlyphCompiler = null # For rendering text labels (emotion names)

# --- Internal State ---
var time_since_last_redraw: float = 0.0

# --- Godot Lifecycle Methods ---

func _ready():
    # Initialize dependencies
    glyph_compiler = PXGlyphCompiler.new()
    if not glyph_compiler:
        print_err("PXEmotionVisualizer: Failed to initialize PXGlyphCompiler. Disabling.")
        set_process(false)
        return

    if not px_emotion_engine:
        print_err("PXEmotionVisualizer: PXEmotionEngine node not found. Visualizer disabled.")
        set_process(false)
        return

    print("PXEmotionVisualizer: Initialized. Ready to visualize emotions.")
    set_process(true) # Ensure _process is running
    queue_redraw() # Request initial draw

func _process(delta):
    time_since_last_redraw += delta
    if time_since_last_redraw >= redraw_frequency:
        time_since_last_redraw = 0.0
        queue_redraw() # Request a redraw of the custom drawing

func _draw():
    # This function is called automatically by Godot when queue_redraw() is called.
    # All custom drawing logic goes here.

    if not display_screen or not display_screen.texture:
        return

    # Get the global position and scale of the DisplayScreen to draw correctly over it
    var display_global_pos = display_screen.global_position
    var display_scale = display_screen.get_global_transform().get_scale()

    # Clear the visualizer region background
    draw_rect(Rect2(visualizer_region_rect.position * display_scale + display_global_pos, visualizer_region_rect.size * display_scale), bar_background_color)

    var current_y_draw_offset = 0
    var emotions_to_display = px_emotion_engine.get_all_emotions()
    var emotion_names = emotions_to_display.keys()
    emotion_names.sort() # Sort alphabetically for consistent order

    for emotion_name in emotion_names:
        var emotion_level = emotions_to_display[emotion_name] # Value from 0.0 to 1.0

        # Calculate bar dimensions
        var bar_width_max = visualizer_region_rect.size.x - 5 # Max width, leaving some padding
        var bar_fill_width = bar_width_max * emotion_level

        var bar_pos_x = visualizer_region_rect.position.x + 2
        var bar_pos_y = visualizer_region_rect.position.y + current_y_draw_offset + 2

        # Draw emotion name label
        var label_draw_pos = (Vector2(bar_pos_x, bar_pos_y) * display_scale) + display_global_pos
        var font = ThemeDB.fallback_font
        var font_size = 6 * display_scale.x # Smaller font for labels
        draw_string(font, label_draw_pos, emotion_name.to_upper().left(7), H_ALIGNMENT_LEFT, -1, font_size, text_color)

        # Draw the bar background (full width)
        var bar_bg_rect_pos = (Vector2(bar_pos_x, bar_pos_y + font_size + 1) * display_scale) + display_global_pos
        var bar_bg_rect_size = Vector2(bar_width_max, bar_height_per_emotion) * display_scale
        draw_rect(Rect2(bar_bg_rect_pos, bar_bg_rect_size), bar_background_color)

        # Draw the bar fill (dynamic width based on emotion level)
        var bar_fill_rect_pos = bar_bg_rect_pos
        var bar_fill_rect_size = Vector2(bar_fill_width, bar_height_per_emotion) * display_scale

        # Interpolate color based on emotion level (e.g., from blue to red for frustration)
        var fill_color = bar_fill_color_base
        match emotion_name:
            "frustration":
                fill_color = bar_fill_color_base.lerp(Color(1.0, 0.0, 0.0, 0.8), emotion_level) # Blue to Red
            "satisfaction":
                fill_color = bar_fill_color_base.lerp(Color(0.0, 1.0, 0.0, 0.8), emotion_level) # Blue to Green
            "fear":
                fill_color = bar_fill_color_base.lerp(Color(1.0, 0.5, 0.0, 0.8), emotion_level) # Blue to Orange
            "curiosity_joy":
                fill_color = bar_fill_color_base.lerp(Color(0.0, 1.0, 1.0, 0.8), emotion_level) # Blue to Cyan
            "boredom_level":
                fill_color = bar_fill_color_base.lerp(Color(0.5, 0.5, 0.5, 0.8), emotion_level) # Blue to Grey
            _:
                fill_color = bar_fill_color_base.lerp(Color(1.0, 1.0, 0.0, 0.8), emotion_level) # Default Blue to Yellow

        draw_rect(Rect2(bar_fill_rect_pos, bar_fill_rect_size), fill_color)

        current_y_draw_offset += font_size + bar_height_per_emotion + bar_spacing + 5 # Advance Y for next bar
        if current_y_draw_offset + bar_height_per_emotion > visualizer_region_rect.size.y:
            break # Stop if we run out of space in the visualizer region


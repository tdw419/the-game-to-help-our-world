# PXThoughtTimeline.gd
# This script provides a visual timeline or "Thought Trail" of PXOS's
# introspective entries stored in PXIntrospectionMemory.gd. It renders
# these entries as a scrollable list on the display, allowing for
# visual replay and debugging of the system's cognitive history.

extends Node2D # Extends Node2D for custom drawing

# --- Configuration ---
# The Rect2 defining the area on the canvas where this timeline will draw.
@export var timeline_region_rect: Rect2 = Rect2(0, 80, 128, 48) # Example: A large area at the bottom

# How often the timeline redraws itself (in seconds).
@export var redraw_frequency: float = 0.5

# Maximum number of introspection entries to display at once in the scrollable view.
@export var max_display_entries: int = 10

# --- Visuals ---
@export var entry_background_color: Color = Color(0.1, 0.1, 0.1, 0.7) # Dark semi-transparent
@export var text_color: Color = Color(1.0, 1.0, 1.0, 1.0) # White text
@export var highlight_color: Color = Color(0.2, 0.5, 1.0, 0.5) # Blue for current view

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Main display
@onready var px_introspection_memory: PXIntrospectionMemory = get_node_or_null("../PXIntrospectionMemory") # To read introspection history
var glyph_compiler: PXGlyphCompiler = null # For rendering text labels (if using glyphs)

# --- Internal State ---
var time_since_last_redraw: float = 0.0
var scroll_offset_y: int = 0 # Vertical scroll offset in lines
var current_history: Array[Dictionary] = [] # Cached history for drawing

# --- Godot Lifecycle Methods ---

func _ready():
    # Initialize dependencies
    glyph_compiler = PXGlyphCompiler.new()
    if not glyph_compiler:
        print_err("PXThoughtTimeline: Failed to initialize PXGlyphCompiler. Disabling.")
        set_process(false)
        return

    if not px_introspection_memory:
        print_err("PXThoughtTimeline: PXIntrospectionMemory node not found. Timeline disabled.")
        set_process(false)
        return

    print("PXThoughtTimeline: Initialized. Ready to visualize thoughts.")
    set_process(true) # Ensure _process is running
    queue_redraw() # Request initial draw

func _process(delta):
    time_since_last_redraw += delta
    if time_since_last_redraw >= redraw_frequency:
        time_since_last_redraw = 0.0
        # Refresh the history cache
        current_history = px_introspection_memory.get_introspection_history()
        queue_redraw() # Request a redraw of the custom drawing

func _draw():
    # This function is called automatically by Godot when queue_redraw() is called.
    # All custom drawing logic goes here.

    if not display_screen or not display_screen.texture:
        return

    # Get the global position and scale of the DisplayScreen to draw correctly over it
    var display_global_pos = display_screen.global_position
    var display_scale = display_screen.get_global_transform().get_scale()

    # Clear the overlay region background
    draw_rect(Rect2(timeline_region_rect.position * display_scale + display_global_pos, timeline_region_rect.size * display_scale), entry_background_color)

    var current_y_draw_offset = 0
    var line_height = glyph_compiler.GLYPH_HEIGHT + glyph_compiler.GLYPH_SPACING_Y + 1 # Add a little extra space

    # Calculate the starting index for drawing based on scroll_offset_y
    # We want to display the most recent entries first, so history is reversed for drawing
    var history_to_display = current_history.slice(0, current_history.size()) # Create a copy
    history_to_display.reverse() # Display most recent at top of scroll area

    var start_display_index = scroll_offset_y
    var end_display_index = min(start_display_index + max_display_entries, history_to_display.size())

    for i in range(start_display_index, end_display_index):
        var entry = history_to_display[i]
        var explanation_text = entry.explanation
        var timestamp = entry.timestamp
        var decision_type = entry.context.get("decision_type", "UNKNOWN")

        # Truncate long explanations to fit in the line
        var max_chars_per_line = floor(timeline_region_rect.size.x / (glyph_compiler.GLYPH_WIDTH + glyph_compiler.GLYPH_SPACING_X)) - 5 # -5 for padding
        var display_text = explanation_text.left(max_chars_per_line) + ("..." if explanation_text.length() > max_chars_per_line else "")

        # Draw the entry background (optional, for highlighting individual lines)
        var line_rect_pos = (timeline_region_rect.position + Vector2(0, current_y_draw_offset)) * display_scale + display_global_pos
        var line_rect_size = Vector2(timeline_region_rect.size.x, line_height) * display_scale
        # draw_rect(Rect2(line_rect_pos, line_rect_size), Color(0.3, 0.3, 0.3, 0.5)) # Example individual line background

        # Draw the text
        var text_draw_pos = (timeline_region_rect.position + Vector2(2, current_y_draw_offset + 1)) * display_scale + display_global_pos
        var font = ThemeDB.fallback_font
        var font_size = 8 * display_scale.x # Adjust font size based on scale
        draw_string(font, text_draw_pos, display_text, H_ALIGNMENT_LEFT, -1, font_size, text_color)

        # Optional: Draw a small colored dot based on decision_type
        var dot_color = Color(0.5, 0.5, 0.5, 1.0) # Default grey
        match decision_type:
            "ISSUED": dot_color = Color(0.0, 0.8, 0.0, 1.0) # Green
            "SKIPPED": dot_color = Color(0.8, 0.8, 0.0, 1.0) # Yellow
            "MUTATED": dot_color = Color(0.2, 0.5, 1.0, 1.0) # Blue
            "FALLBACK": dot_color = Color(1.0, 0.5, 0.0, 1.0) # Orange
            "OUTCOME":
                match entry.context.get("outcome", ""):
                    "SUCCESS": dot_color = Color(0.0, 1.0, 0.0, 1.0)
                    "FAILURE": dot_color = Color(1.0, 0.0, 0.0, 1.0)
                    "ABORTED": dot_color = Color(0.5, 0.5, 0.5, 1.0)
        draw_circle((timeline_region_rect.position + Vector2(timeline_region_rect.size.x - 5, current_y_draw_offset + line_height / 2)) * display_scale + display_global_pos, 2 * display_scale.x, dot_color)


        current_y_draw_offset += line_height
        if current_y_draw_offset + line_height > timeline_region_rect.size.y:
            break # Stop if we run out of space in the overlay region

    # --- Scroll Bar (Conceptual) ---
    # You could draw a simple scroll bar here if needed.
    # For now, scrolling will be handled by input.


# --- Input for Scrolling ---
func _input(event):
    if event is InputEventMouseButton and event.pressed:
        if event.button_index == MOUSE_BUTTON_WHEEL_UP:
            scroll_up()
            get_viewport().set_input_as_handled() # Consume event
        elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
            scroll_down()
            get_viewport().set_input_as_handled() # Consume event


func scroll_up():
    scroll_offset_y = max(0, scroll_offset_y - 1)
    queue_redraw()
    print("PXThoughtTimeline: Scrolled up to offset ", scroll_offset_y)

func scroll_down():
    var total_entries = px_introspection_memory.introspection_history.size()
    var max_scroll_offset = max(0, total_entries - max_display_entries)
    scroll_offset_y = min(max_scroll_offset, scroll_offset_y + 1)
    queue_redraw()
    print("PXThoughtTimeline: Scrolled down to offset ", scroll_offset_y)


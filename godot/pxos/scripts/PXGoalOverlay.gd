# PXGoalOverlay.gd
# This script provides a visual overlay on the PXOS display to show
# a real-time timeline or list of recent goals (directives), their status,
# and potentially their mutation lineage. It acts as a "cognitive HUD."

extends Node2D # Extends Node2D to use its _draw() function for custom rendering

# --- Configuration ---
# The Rect2 defining the area on the canvas where this overlay will draw.
@export var overlay_region_rect: Rect2 = Rect2(85, 0, 40, 64) # Example: A vertical strip on the right

# How often the overlay redraws itself (in seconds).
@export var redraw_frequency: float = 0.5

# Maximum number of goal entries to display in the overlay.
@export var max_display_goals: int = 10

# --- Colors for Goal Outcomes ---
@export var pending_color: Color = Color(0.8, 0.8, 0.0, 0.8)  # Yellow
@export var success_color: Color = Color(0.0, 0.8, 0.0, 0.8)  # Green
@export var failure_color: Color = Color(0.8, 0.0, 0.0, 0.8)  # Red
@export var aborted_color: Color = Color(0.5, 0.5, 0.5, 0.8)  # Grey

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Main display
@onready var px_goal_memory: PXGoalMemory = get_node_or_null("../PXGoalMemory") # To read goal history
var glyph_compiler: PXGlyphCompiler = null # For rendering text labels

# --- Internal State ---
var time_since_last_redraw: float = 0.0

# --- Godot Lifecycle Methods ---

func _ready():
    # Initialize dependencies
    glyph_compiler = PXGlyphCompiler.new()
    if not glyph_compiler:
        print_err("PXGoalOverlay: Failed to initialize PXGlyphCompiler. Disabling.")
        set_process(false)
        return

    if not px_goal_memory:
        print_err("PXGoalOverlay: PXGoalMemory node not found. Overlay disabled.")
        set_process(false)
        return

    print("PXGoalOverlay: Initialized. Ready to visualize goals.")
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

    # Clear the overlay region before redrawing
    # Note: For _draw, we use draw_rect with a transparent color.
    draw_rect(Rect2(overlay_region_rect.position * display_scale + display_global_pos, overlay_region_rect.size * display_scale), Color(0, 0, 0, 0.5)) # Semi-transparent black background

    # Get recent goals from PXGoalMemory
    var recent_goals = px_goal_memory.get_goal_history()
    # Sort by timestamp (most recent last)
    recent_goals.sort_custom(Callable(self, "_sort_goals_by_timestamp"))

    var current_y_offset = 0
    var line_height = glyph_compiler.GLYPH_HEIGHT + glyph_compiler.GLYPH_SPACING_Y + 1 # Add a little extra space

    # Display only the most recent goals up to max_display_goals
    var display_count = min(recent_goals.size(), max_display_goals)
    for i in range(recent_goals.size() - display_count, recent_goals.size()):
        var goal_entry = recent_goals[i]

        var goal_text = goal_entry.goal_type
        var outcome_color = pending_color

        match goal_entry.outcome:
            "SUCCESS": outcome_color = success_color
            "FAILURE": outcome_color = failure_color
            "ABORTED": outcome_color = aborted_color
            "PENDING": outcome_color = pending_color

        # Draw a small colored square indicating outcome
        var outcome_square_pos = (overlay_region_rect.position + Vector2(1, current_y_offset + 1)) * display_scale + display_global_pos
        draw_rect(Rect2(outcome_square_pos, Vector2(glyph_compiler.GLYPH_HEIGHT, glyph_compiler.GLYPH_HEIGHT) * display_scale), outcome_color)

        # Draw the goal text label
        var label_draw_pos = (overlay_region_rect.position + Vector2(1 + glyph_compiler.GLYPH_WIDTH + glyph_compiler.GLYPH_SPACING_X, current_y_offset)) * display_scale + display_global_pos
        var font = ThemeDB.fallback_font
        var font_size = 8 * display_scale.x # Adjust font size based on scale
        draw_string(font, label_draw_pos, goal_text, H_ALIGNMENT_LEFT, -1, font_size, label_color)

        current_y_offset += line_height
        if current_y_offset + line_height > overlay_region_rect.size.y:
            break # Stop if we run out of space in the overlay region

# --- Helper for Sorting Goals ---
func _sort_goals_by_timestamp(goal_a: GoalEntry, goal_b: GoalEntry) -> bool:
    return goal_a.timestamp < goal_b.timestamp # Sort oldest first


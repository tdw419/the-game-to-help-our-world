# PXTerminalDisplayManager.gd
extends Node

class_name PXTerminalDisplayManager

# References to core PXOS components
var display_manager: PXDisplayManager = null # The underlying pixel drawing canvas
var shell_output_target: RichTextLabel = null # The original shell output RichTextLabel

# Terminal dimensions (in characters)
var terminal_width_chars := 30 # For 5px wide chars, 160px / 5px = 32 chars. Let's use 30 for margin.
var terminal_height_lines := 15 # For 7px high chars, 120px / 7px approx 17 lines. Let's use 15.

# Terminal buffer
var terminal_buffer := [] # Array of strings, each string is a line
var max_buffer_lines := 50 # How many lines to keep in history
var scroll_offset := 0 # How many lines scrolled up from bottom

# Cursor properties
var cursor_x := 0 # Current character column
var cursor_y := 0 # Current line in visible terminal area (0 to terminal_height_lines-1)
var cursor_blink_state := true
var cursor_blink_timer: Timer

# Input line buffer
var input_line_buffer := ""
var input_mode := false # True when waiting for read_line input

# Colors (RGB 0-255)
var default_text_color := Color(255, 255, 255) # White
var background_color := Color(0, 0, 0) # Black
var cursor_color := Color(0, 255, 255) # Cyan

func _ready():
	# Setup cursor blinking
	cursor_blink_timer = Timer.new()
	add_child(cursor_blink_timer)
	cursor_blink_timer.wait_time = 0.5
	cursor_blink_timer.autostart = true
	cursor_blink_timer.connect("timeout", self, "_on_cursor_blink_timeout")
	
	# Initial clear
	_clear_terminal_buffer()

func _on_cursor_blink_timeout():
	cursor_blink_state = not cursor_blink_state
	_render_terminal() # Re-render to show/hide cursor

func set_display_manager(dm: PXDisplayManager):
	display_manager = dm
	# Adjust terminal dimensions based on display manager's pixel dimensions
	terminal_width_chars = int(display_manager.width / display_manager.char_width) - 2 # -2 for some margin
	terminal_height_lines = int(display_manager.height / display_manager.char_height) - 2 # -2 for some margin

func set_shell_output_target(target: RichTextLabel):
	shell_output_target = target

# --- Core Terminal Logic ---

func _clear_terminal_buffer():
	terminal_buffer.clear()
	for i in range(terminal_height_lines): # Fill with empty lines
		terminal_buffer.append("")
	cursor_x = 0
	cursor_y = terminal_height_lines - 1 # Start at the bottom line for input

func _add_line_to_buffer(line_text: String):
	# Handle line wrapping
	var remaining_text = line_text
	while remaining_text.length() > terminal_width_chars:
		var wrapped_line = remaining_text.substr(0, terminal_width_chars)
		terminal_buffer.append(wrapped_line)
		remaining_text = remaining_text.substr(terminal_width_chars)
	terminal_buffer.append(remaining_text)

	# Trim buffer if it exceeds max_buffer_lines
	while terminal_buffer.size() > max_buffer_lines:
		terminal_buffer.remove(0) # Remove oldest line

	# Adjust scroll offset if new lines are added while scrolled up
	if scroll_offset > 0:
		scroll_offset = min(scroll_offset + 1, terminal_buffer.size() - terminal_height_lines)
		scroll_offset = max(0, scroll_offset) # Ensure it doesn't go below 0

	# Move cursor to new line
	cursor_x = 0
	cursor_y = terminal_height_lines - 1 # Always at the bottom for new output

	_render_terminal() # Re-render after adding text

func _render_terminal():
	if not display_manager: return

	display_manager.clear_display(background_color.r * 255, background_color.g * 255, background_color.b * 255)

	var start_line_index = max(0, terminal_buffer.size() - terminal_height_lines - scroll_offset)
	var end_line_index = min(terminal_buffer.size(), start_line_index + terminal_height_lines)

	var current_render_y = 0
	for i in range(start_line_index, end_line_index):
		var line_text = terminal_buffer[i]
		display_manager.draw_text(line_text, 1 * display_manager.char_width, current_render_y * display_manager.char_height + 1,
								  int(default_text_color.r * 255), int(default_text_color.g * 255), int(default_text_color.b * 255))
		current_render_y += 1

	# Render input line
	var input_display_text = "> " + input_line_buffer
	display_manager.draw_text(input_display_text, 1 * display_manager.char_width, (terminal_height_lines - 1) * display_manager.char_height + 1,
							  int(default_text_color.r * 255), int(default_text_color.g * 255), int(default_text_color.b * 255))

	# Render cursor
	if cursor_blink_state and input_mode: # Only show cursor when in input mode
		var cursor_draw_x = (1 + input_display_text.length()) * display_manager.char_width
		var cursor_draw_y = (terminal_height_lines - 1) * display_manager.char_height + 1
		display_manager.draw_rect(cursor_draw_x, cursor_draw_y, display_manager.char_width, display_manager.char_height,
								  int(cursor_color.r * 255), int(cursor_color.g * 255), int(cursor_color.b * 255))

	display_manager.refresh_display()

# --- Public API for PXOSUIScreen / PXVM ---

func print_to_terminal(text: String):
	# Split text by newlines and add each as a separate line
	var lines = text.split("\n", false)
	for line in lines:
		_add_line_to_buffer(line)
	_render_terminal() # Ensure immediate refresh

func set_input_mode(enabled: bool):
	input_mode = enabled
	cursor_blink_state = true # Reset cursor state when entering input mode
	cursor_blink_timer.start() # Ensure timer is running
	_render_terminal()

func append_input_char(char_code: int):
	if input_mode:
		input_line_buffer += char(char_code)
		_render_terminal()

func backspace_input():
	if input_mode and input_line_buffer.length() > 0:
		input_line_buffer = input_line_buffer.left(input_line_buffer.length() - 1)
		_render_terminal()

func get_current_input_line() -> String:
	return input_line_buffer

func clear_input_line():
	input_line_buffer = ""
	_render_terminal()

func scroll_up():
	scroll_offset = min(scroll_offset + 1, terminal_buffer.size() - terminal_height_lines)
	scroll_offset = max(0, scroll_offset) # Cap at 0
	_render_terminal()

func scroll_down():
	scroll_offset = max(0, scroll_offset - 1)
	_render_terminal()
# PXBootSim.gd
# This module provides a visual simulation of a system boot process,
# displaying simulated kernel messages and simple framebuffer draws.
# It's intended for introspective analysis and preview, not actual execution.

extends Control # Extends Control to be a UI element for the simulation display

# --- Configuration ---
@export var panel_region_rect: Rect2 = Rect2(0, 0, 800, 600) # Default size for the simulation panel
@export var simulation_speed_multiplier: float = 1.0 # Adjusts how fast messages/drawings appear
@export var fade_out_duration: float = 1.0 # Duration for the "press Enter" fade-out

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging simulation activity
# @onready var px_digest_preview_runtime: PXDigestPreviewRuntime = get_node_or_null("../PXDigestPreviewRuntime") # Future: To receive actual simulation data

# --- UI Elements (Placeholders - you'll need to add these in Godot scene) ---
@onready var boot_log_display: RichTextLabel = get_node_or_null("BootLogDisplay")
@onready var framebuffer_texture_rect: TextureRect = get_node_or_null("FramebufferTextureRect") # For visual framebuffer draw
@onready var press_enter_label: Label = get_node_or_null("PressEnterLabel") # For optional fade-out prompt
@onready var close_button: Button = get_node_or_null("CloseButton")

# --- Internal State ---
var _simulated_messages: Array[String] = []
var _current_message_index: int = 0
var _message_display_timer: Timer = null
var _framebuffer_image: Image = null
var _framebuffer_texture: ImageTexture = null
var _simulation_active: bool = false
var _fade_out_active: bool = false

# --- Godot Lifecycle Methods ---

func _ready():
    # Set panel position and size
    position = panel_region_rect.position
    size = panel_region_rect.size

    # Check for essential dependencies
    if not px_scroll_log:
        print_err("PXBootSim: PXScrollLog dependency missing. Simulation logging disabled.")
        # Do not disable the node entirely, as it can still run the simulation.

    # Initialize UI elements
    if boot_log_display:
        boot_log_display.clear()
        boot_log_display.set_use_bbcode(true)
    if framebuffer_texture_rect:
        _framebuffer_image = Image.new()
        _framebuffer_image.create(framebuffer_texture_rect.size.x, framebuffer_texture_rect.size.y, false, Image.FORMAT_RGBA8)
        _framebuffer_texture = ImageTexture.new()
        _framebuffer_texture_rect.texture = _framebuffer_texture
    if press_enter_label:
        press_enter_label.text = "PRESS ENTER TO CONTINUE..."
        press_enter_label.hide()
    if close_button:
        close_button.pressed.connect(Callable(self, "hide_simulation"))

    # Set up message display timer
    _message_display_timer = Timer.new()
    add_child(_message_display_timer)
    _message_display_timer.one_shot = false # Repeat for messages
    _message_display_timer.timeout.connect(Callable(self, "_display_next_message"))

    # Initially hide the simulation panel
    hide()
    _simulation_active = false
    _log_simulation_activity("Initialized.")

# --- Public Methods ---

func start_simulation(simulated_log_data: Array[String], initial_framebuffer_data: Array[Color] = []):
    """
    Starts the visual boot simulation with provided log messages and optional initial framebuffer data.
    """
    if _simulation_active:
        _log_simulation_activity("Error: Simulation already active. Stop current one first.")
        return

    _log_simulation_activity("Starting boot simulation.")
    _simulated_messages = simulated_log_data
    _current_message_index = 0
    _simulation_active = true
    _fade_out_active = false
    
    _clear_display()
    show()

    # Initialize framebuffer if data provided
    if framebuffer_texture_rect and _framebuffer_image:
        _framebuffer_image.lock()
        _framebuffer_image.fill(Color.BLACK) # Start with black screen
        if not initial_framebuffer_data.is_empty():
            _draw_pixels_to_framebuffer(initial_framebuffer_data)
        _framebuffer_image.unlock()
        _framebuffer_texture.create_from_image(_framebuffer_image)

    # Start displaying messages
    _message_display_timer.wait_time = 0.1 / simulation_speed_multiplier # Fast initial message
    _message_display_timer.start()
    _display_next_message() # Display first message immediately

func hide_simulation():
    """Hides the simulation panel and stops all related processes."""
    if _simulation_active:
        _log_simulation_activity("Hiding boot simulation.")
        _simulation_active = false
        _message_display_timer.stop()
        if press_enter_label:
            press_enter_label.hide()
        hide()
        _clear_display()

# --- Internal Simulation Logic ---

func _display_next_message():
    """Displays the next simulated kernel message and updates framebuffer."""
    if not _simulation_active:
        return

    if _current_message_index < _simulated_messages.size():
        var message = _simulated_messages[_current_message_index]
        if boot_log_display:
            boot_log_display.append_text(message + "\n")
            boot_log_display.scroll_to_line(boot_log_display.get_line_count() - 1)
        _log_simulation_activity("SIM_MSG: " + message)

        # Simulate framebuffer draw based on message content (simple heuristic)
        _simulate_framebuffer_draw(message)

        _current_message_index += 1
        _message_display_timer.wait_time = 0.5 / simulation_speed_multiplier # Regular message speed
    else:
        _log_simulation_activity("Simulation log complete.")
        _message_display_timer.stop()
        _trigger_fade_out() # Start fade-out effect

func _simulate_framebuffer_draw(message: String):
    """
    Simulates simple framebuffer drawing based on keywords in the message.
    (M6: Show file system prep / framebuffer draw)
    """
    if not framebuffer_texture_rect or not _framebuffer_image:
        return

    _framebuffer_image.lock()
    var img_width = _framebuffer_image.get_width()
    var img_height = _framebuffer_image.get_height()

    var color_change = Color.BLACK
    if message.to_lower().find("loading") != -1:
        color_change = Color.BLUE
    elif message.to_lower().find("initializing") != -1:
        color_change = Color.GREEN
    elif message.to_lower().find("filesystem") != -1:
        color_change = Color.ORANGE
    elif message.to_lower().find("kernel") != -1:
        color_change = Color.PURPLE
    elif message.to_lower().find("display") != -1:
        color_change = Color.AQUA
    elif message.to_lower().find("boot complete") != -1:
        color_change = Color.WHITE # Full screen white on boot complete

    # Simple fill or random pixel draw
    if color_change != Color.BLACK:
        for i in range(50): # Draw 50 random pixels
            var x = randi() % img_width
            var y = randi() % img_height
            _framebuffer_image.set_pixel(x, y, color_change)
        # Or a simple gradient/fill for more dramatic effect
        # _framebuffer_image.fill(color_change.lightened(0.5))

    _framebuffer_image.unlock()
    _framebuffer_texture.create_from_image(_framebuffer_image) # Update texture

func _draw_pixels_to_framebuffer(pixel_colors: Array[Color]):
    """Draws a given array of colors to the framebuffer image."""
    if not framebuffer_texture_rect or not _framebuffer_image:
        return

    _framebuffer_image.lock()
    var img_width = _framebuffer_image.get_width()
    var img_height = _framebuffer_image.get_height()
    var pixel_index = 0
    for y in range(img_height):
        for x in range(img_width):
            if pixel_index < pixel_colors.size():
                _framebuffer_image.set_pixel(x, y, pixel_colors[pixel_index])
            pixel_index += 1
    _framebuffer_image.unlock()
    _framebuffer_texture.create_from_image(_framebuffer_image)

func _trigger_fade_out():
    """
    Starts the optional "press Enter to continue" fade-out.
    (M6: Optional “press Enter to continue” fadeout)
    """
    if press_enter_label and not _fade_out_active:
        press_enter_label.show()
        _fade_out_active = true
        var tween = create_tween()
        tween.set_loops() # Loop the fade in/out
        tween.tween_property(press_enter_label, "modulate:a", 0.0, fade_out_duration / 2.0).set_ease(Tween.EASE_IN_OUT)
        tween.tween_property(press_enter_label, "modulate:a", 1.0, fade_out_duration / 2.0).set_ease(Tween.EASE_IN_OUT)
        _log_simulation_activity("Fade-out prompt triggered.")

func _input(event: InputEvent):
    """Handles input events for the fade-out prompt."""
    if _fade_out_active and event.is_action_pressed("ui_accept"): # "ui_accept" is usually Enter key
        _log_simulation_activity("Enter pressed, ending fade-out.")
        if press_enter_label:
            press_enter_label.hide()
        _fade_out_active = false
        # You might want to emit a signal here to tell the parent to close the panel
        # or transition to another state.
        hide_simulation() # Auto-hide after input

# --- Utility Functions ---

func _clear_display():
    """Clears all display elements."""
    if boot_log_display: boot_log_display.clear()
    if framebuffer_texture_rect and _framebuffer_image:
        _framebuffer_image.lock()
        _framebuffer_image.fill(Color.BLACK)
        _framebuffer_image.unlock()
        _framebuffer_texture.create_from_image(_framebuffer_image)
    if press_enter_label: press_enter_label.hide()

# --- Logging ---

func _log_simulation_activity(message: String):
    """
    Helper function to log simulation activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PXBOOTSIM: " + message)
    else:
        print("PXBootSim (Console Log): ", message)


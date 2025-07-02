# PXFramebuffer.gd
# Simulated framebuffer display panel for visual output inside PXRuntime.
# This module now supports drawing individual pixels and rendering text strings
# onto its internal image, simulating a pixel-native display.

extends Control

# --- Configuration ---
@export var framebuffer_width: int = 640
@export var framebuffer_height: int = 480
@export var pixel_size: int = 2  # For zoom/scaling pixels in the TextureRect display
@export var default_font_path: String = "res://px_assets/fonts/PxPlus_IBM_VGA8.ttf" # Path to a fixed-width pixel font
@export var default_font_size: int = 8
@export var default_line_height: int = 10

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog")

# --- Internal State ---
var framebuffer_image: Image
var framebuffer_texture: ImageTexture
var is_initialized := false
var _loaded_font: Font # Store the loaded font resource

# --- Lifecycle ---
func _ready():
    _init_framebuffer()
    _load_font()
    _log("PXFramebuffer initialized (%dx%d). Font loaded: %s" % [framebuffer_width, framebuffer_height, default_font_path])

func _init_framebuffer():
    """Initializes the internal Image and ImageTexture for the framebuffer."""
    framebuffer_image = Image.create(framebuffer_width, framebuffer_height, false, Image.FORMAT_RGBA8) # Use RGBA8 for alpha
    framebuffer_image.fill(Color.BLACK)
    framebuffer_texture = ImageTexture.create_from_image(framebuffer_image)
    is_initialized = true
    # Request a redraw of the Control node
    update()

func _load_font():
    """Loads the specified font resource."""
    if not default_font_path.is_empty() and FileAccess.file_exists(default_font_path):
        _loaded_font = load(default_font_path)
        if _loaded_font:
            _log("Font loaded successfully from: " + default_font_path)
            # Set font size for the loaded font
            _loaded_font.set_height(default_font_size)
        else:
            _log("Error: Failed to load font from: " + default_font_path)
    else:
        _log("Warning: Default font path is empty or font file not found: " + default_font_path)
    
    if _loaded_font == null:
        _log("Using default engine font as fallback.")
        _loaded_font = ThemeDB.get_default_theme().get_default_font() # Fallback to default engine font
        _loaded_font.set_height(default_font_size)


# --- Public API ---

func update_framebuffer(pixels: Image):
    """
    Accepts a new Image object and updates the texture shown.
    This is for direct image blitting, e.g., from a .pxdigest pixel block.
    """
    if not is_initialized:
        _init_framebuffer()

    # Ensure the incoming image matches dimensions or scale it
    if pixels.get_width() != framebuffer_width or pixels.get_height() != framebuffer_height:
        _log("Warning: Incoming image dimensions (%dx%d) do not match framebuffer (%dx%d). Scaling." % [
            pixels.get_width(), pixels.get_height(), framebuffer_width, framebuffer_height
        ])
        pixels = pixels.get_resized_image(framebuffer_width, framebuffer_height, Image.INTERPOLATE_NEAREST)
    
    framebuffer_image = pixels.duplicate()
    framebuffer_texture.create_from_image(framebuffer_image)
    update() # Request a redraw
    _log("Framebuffer updated with new image (%dx%d)" % [framebuffer_image.get_width(), framebuffer_image.get_height()])

func update_from_raw_data(width: int, height: int, raw_data: PackedByteArray):
    """
    For simulated memory input: accepts raw RGB bytes and updates framebuffer.
    """
    var img = Image.create_from_data(width, height, false, Image.FORMAT_RGB8, raw_data)
    update_framebuffer(img)

func set_pixel(x: int, y: int, color: Color):
    """
    Draws a single pixel at (x, y) on the framebuffer.
    (Supports PIXEL DRAW mode)
    """
    if not is_initialized or not framebuffer_image:
        _log("Framebuffer not initialized for set_pixel.")
        return
    
    if x >= 0 and x < framebuffer_width and y >= 0 and y < framebuffer_height:
        framebuffer_image.lock()
        framebuffer_image.set_pixel(x, y, color)
        framebuffer_image.unlock()
        framebuffer_texture.create_from_image(framebuffer_image) # Update texture
        update() # Request redraw
    else:
        _log("Warning: set_pixel coordinates (%d, %d) out of bounds." % [x, y])

func draw_string_on_image(text: String, position: Vector2, font: Font, color: Color):
    """
    Draws a string onto the internal framebuffer_image at a specific pixel position.
    Manages internal image drawing.
    (Supports TEXT GRID and PIXEL DRAW modes)
    """
    if not is_initialized or not framebuffer_image:
        _log("Framebuffer not initialized for draw_string_on_image.")
        return
    if font == null:
        font = _loaded_font # Use default loaded font if not provided
        if font == null:
            _log("Error: No font available for drawing string: " + text)
            return

    # Use a temporary Viewport to render text onto a texture, then blit to framebuffer_image
    # This is the most reliable way to draw text with fonts onto an Image in Godot.
    var viewport = Viewport.new()
    add_child(viewport)
    viewport.set_size(Vector2(framebuffer_width, framebuffer_height))
    viewport.set_transparent_background(true)
    
    var label = Label.new()
    viewport.add_child(label)
    label.add_theme_font_size_override("font_size", font.get_height())
    label.add_theme_font_override("font", font)
    label.add_theme_color_override("font_color", color)
    label.set_position(position)
    label.text = text
    
    # Force update and wait for rendering
    get_tree().process_frame.connect(Callable(self, "_capture_viewport_texture").bind(viewport, label), CONNECT_ONE_SHOT)

func _capture_viewport_texture(viewport: Viewport, label: Label):
    """Helper to capture the viewport's texture after rendering."""
    # This method is called after the frame has processed, ensuring label is rendered.
    var viewport_texture = viewport.get_texture()
    if viewport_texture:
        var img_from_viewport = viewport_texture.get_image()
        if img_from_viewport:
            framebuffer_image.lock()
            # Blit the rendered text from the viewport's image onto our framebuffer_image
            framebuffer_image.blit_rect(img_from_viewport, Rect2(Vector2.ZERO, img_from_viewport.get_size()), Vector2.ZERO)
            framebuffer_image.unlock()
            framebuffer_texture.create_from_image(framebuffer_image)
            update() # Request redraw
            _log("Framebuffer updated with text from viewport.")
        else:
            _log("Error: Could not get image from viewport texture.")
    else:
        _log("Error: Viewport texture is null.")
    
    # Clean up temporary nodes
    label.queue_free()
    viewport.queue_free()


func export_framebuffer_as_png(path: String = "user://framebuffer_export.png"):
    """Exports the current framebuffer content as a PNG image."""
    if framebuffer_image:
        framebuffer_image.save_png(path)
        _log("Framebuffer exported to: " + path)
    else:
        _log("Error: Framebuffer not initialized for export.")

func get_font(size: int) -> Font:
    """Returns the loaded font, or a fallback, at the specified size."""
    if _loaded_font:
        _loaded_font.set_height(size) # Adjust height dynamically if needed
        return _loaded_font
    _log("Warning: No custom font loaded, returning default engine font.")
    var default_engine_font = ThemeDB.get_default_theme().get_default_font()
    default_engine_font.set_height(size)
    return default_engine_font

# --- Drawing ---
func _draw():
    """Godot's drawing callback for the Control node."""
    if framebuffer_texture:
        # Draw the framebuffer_texture scaled by pixel_size
        draw_texture_rect(framebuffer_texture, Rect2(Vector2.ZERO, Vector2(framebuffer_width, framebuffer_height) * pixel_size))

# --- Logging ---
func _log(msg: String):
    """Helper function for internal logging."""
    if px_scroll_log:
        px_scroll_log.add_line("PXFRAMEBUFFER: " + msg)
    else:
        print("PXFramebuffer (Log): ", msg)


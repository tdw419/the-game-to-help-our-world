# PXFramebuffer.gd
# Simulated framebuffer display panel for visual output inside PXRuntime

extends Control

# --- Configuration ---
@export var framebuffer_width: int = 640
@export var framebuffer_height: int = 480
@export var pixel_size: int = 2  # For zoom/scaling pixels

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog")

# --- Internal State ---
var framebuffer_image: Image
var framebuffer_texture: ImageTexture
var is_initialized := false

# --- Lifecycle ---
func _ready():
    _init_framebuffer()
    _log("PXFramebuffer initialized (%dx%d)" % [framebuffer_width, framebuffer_height])

func _init_framebuffer():
    framebuffer_image = Image.create(framebuffer_width, framebuffer_height, false, Image.FORMAT_RGB8)
    framebuffer_image.fill(Color.BLACK)
    framebuffer_texture = ImageTexture.create_from_image(framebuffer_image)
    is_initialized = true
    update()

# --- Public API ---

func update_framebuffer(pixels: Image):
    """
    Accepts a new Image object and updates the texture shown.
    """
    if not is_initialized:
        _init_framebuffer()

    framebuffer_image = pixels.duplicate()
    framebuffer_texture = ImageTexture.create_from_image(framebuffer_image)
    update()
    _log("Framebuffer updated with new image (%dx%d)" % [framebuffer_image.get_width(), framebuffer_image.get_height()])

func update_from_raw_data(width: int, height: int, raw_data: PackedByteArray):
    """
    For simulated memory input: accepts raw RGB bytes.
    """
    var img = Image.create_from_data(width, height, false, Image.FORMAT_RGB8, raw_data)
    update_framebuffer(img)

func export_framebuffer_as_png(path: String = "user://framebuffer_export.png"):
    framebuffer_image.save_png(path)
    _log("Framebuffer exported to: " + path)

# --- Drawing ---
func _draw():
    if framebuffer_texture:
        draw_texture_rect(framebuffer_texture, Rect2(Vector2.ZERO, Vector2(framebuffer_width, framebuffer_height) * pixel_size))

# --- Logging ---
func _log(msg: String):
    if px_scroll_log:
        px_scroll_log.add_line("PXFRAMEBUFFER: " + msg)
    else:
        print("PXFramebuffer (Log): ", msg)

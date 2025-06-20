# PXOSHost.gd
# PXOS GPU Host Runtime - Godot 4.x

extends Node2D

@onready var pxboot_texture := preload("res://assets/pxboot.png")
var px_image : Image
var px_texture : ImageTexture
var px_vm_state = {}  # Internal PXTalk VM state (e.g., R0–R5, PC, Flags)

func _ready():
	generate_pxboot_image(64)  # ✅ Run once to generate pxboot.png (disable after first run)
	load_pxboot()
	setup_display()
	print("PXOS Host Initialized")

# ✅ Generate a 64×64 red-diagonal test image
func generate_pxboot_image(size: int = 64):
	var img = Image.create(size, size, false, Image.FORMAT_RGB8)
	for y in range(size):
		for x in range(size):
			img.set_pixel(x, y, Color(0, 0, 0))  # Black background
		img.set_pixel(y, y, Color(1, 0, 0))      # Red pixel on diagonal
	img.save_png("res://assets/pxboot.png")
	print("Generated pxboot.png with red diagonal pattern.")

# ✅ Load pxboot image and prepare it as a texture
func load_pxboot():
	px_image = pxboot_texture.get_image()
	px_texture = ImageTexture.create_from_image(px_image)

# ✅ Create and display a scaled-up framebuffer
func setup_display():
	var sprite = Sprite2D.new()
	sprite.texture = px_texture
	sprite.scale = Vector2(2, 2)  # Scale up for visibility
	add_child(sprite)

# ✅ Main frame loop (now using _delta to avoid warning)
func _process(_delta):
	px_talk_tick()
	px_texture.update(px_image)

# ✅ Scan each pixel and run basic PXTalk logic
func px_talk_tick():
	var width = px_image.get_width()
	var height = px_image.get_height()
	for y in range(height):
		for x in range(width):
			var color = px_image.get_pixel(x, y)
			run_px_instruction(x, y, color)

# ✅ Simple prototype logic: toggle red pixels
func run_px_instruction(x: int, y: int, color: Color):
	if color.r > 0.5:
		px_image.set_pixel(x, y, Color(0, 0, 0))  # Turn off red pixel
	elif color.r == 0:
		px_image.set_pixel(x, y, Color(1, 0, 0))  # Turn it back on

# ✅ Optional: Reload original boot image
func reset_px_image():
	load_pxboot()
	px_texture.update(px_image)

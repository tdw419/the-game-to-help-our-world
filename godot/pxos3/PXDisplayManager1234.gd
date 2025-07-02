# PXDisplayManager.gd - UPDATED

extends Node

class_name PXDisplayManager

var width := 160
var height := 120
var image : Image
var texture : ImageTexture
var display_rect : TextureRect

# Font properties (already added from previous step)
var font_image: Image
var char_width := 5
var char_height := 7
var ascii_offset := 32

func _ready():
	# Create and initialize the framebuffer (existing code)
	image = Image.create(width, height, false, Image.FORMAT_RGB8)
	image.fill(Color(0, 0, 0))
	texture = ImageTexture.create_from_image(image)

	# Create a TextureRect to display the framebuffer (existing code)
	display_rect = TextureRect.new()
	display_rect.texture = texture
	display_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	display_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	display_rect.rect_size = Vector2(width * 4, height * 4) # scale up for visibility
	display_rect.anchor_right = 1.0
	display_rect.anchor_bottom = 1.0
	# IMPORTANT: You will need to add this 'display_rect' to your main scene's UI tree
	# For example, in PXOSUIScreen.gd's _ready():
	# get_node("YourMainUINode").add_child($PXDisplayManager.display_rect)
	# And set its position/size there.
	# For this script to work as a standalone node, we add it here:
	add_child(display_rect)


	# Load the font image (ASCII chars from 32 to 126) (existing code)
	var font_tex = load("res://assets/font_ascii.png") as Texture2D
	if font_tex:
		font_image = font_tex.get_image()
	else:
		print("Error: font_ascii.png not found at res://assets/font_ascii.png")


func draw_pixel(x: int, y: int, r: int, g: int, b: int):
	if x >= 0 and x < width and y >= 0 and y < height:
		image.set_pixel(x, y, Color(r / 255.0, g / 255.0, b / 255.0))

func draw_rect(x: int, y: int, w: int, h: int, r: int, g: int, b: int):
	# Ensure coordinates are within bounds
	var x_start = max(0, x)
	var y_start = max(0, y)
	var x_end = min(width, x + w)
	var y_end = min(height, y + h)

	for i in range(x_start, x_end):
		for j in range(y_start, y_end):
			image.set_pixel(i, j, Color(r / 255.0, g / 255.0, b / 255.0))

func clear_display(r: int, g: int, b: int):
	image.lock() # Lock before filling for performance
	image.fill(Color(r / 255.0, g / 255.0, b / 255.0))
	image.unlock() # Unlock after filling

func refresh_display():
	# Locking and unlocking is not strictly necessary for update() in Godot 4,
	# but it's good practice if other pixel manipulations were done without explicit lock/unlock.
	# For set_pixel, it's implicitly locked/unlocked per call.
	# For fill(), it's explicitly locked/unlocked.
	texture.update(image)

# --- Existing draw_char and draw_text methods (from previous step) ---
func draw_char(char_code: int, x: int, y: int, r: int, g: int, b: int):
	if not font_image: return
	if char_code < ascii_offset or char_code > 126: return

	var char_index = char_code - ascii_offset
	var src_x = char_index * char_width
	for dx in range(char_width):
		for dy in range(char_height):
			# Check bounds for destination pixel
			if (x + dx) >= 0 and (x + dx) < width and (y + dy) >= 0 and (y + dy) < height:
				var font_pixel_color = font_image.get_pixel(src_x + dx, dy)
				if font_pixel_color.a > 0.5: # Only draw if font pixel is not transparent
					image.set_pixel(x + dx, y + dy, Color(r/255.0, g/255.0, b/255.0))

func draw_text(text: String, x: int, y: int, r: int, g: int, b: int):
	for i in range(text.length()):
		draw_char(text[i].ord(), x + i * char_width, y, r, g, b)

# --- NEW: draw_line ---
func draw_line(x1: int, y1: int, x2: int, y2: int, r: int, g: int, b: int):
	var dx = abs(x2 - x1)
	var dy = abs(y2 - y1)
	var sx = 1 if x1 < x2 else -1
	var sy = 1 if y1 < y2 else -1
	var err = dx - dy

	var current_x = x1
	var current_y = y1

	while true:
		draw_pixel(current_x, current_y, r, g, b)
		if current_x == x2 and current_y == y2:
			break
		var e2 = 2 * err
		if e2 > -dy:
			err -= dy
			current_x += sx
		if e2 < dx:
			err += dx
			current_y += sy

# --- NEW: draw_circle ---
func draw_circle(cx: int, cy: int, radius: int, r: int, g: int, b: int):
	var x = radius
	var y = 0
	var err = 0

	while x >= y:
		# Draw 8 octants
		draw_pixel(cx + x, cy + y, r, g, b)
		draw_pixel(cx + y, cy + x, r, g, b)
		draw_pixel(cx - y, cy + x, r, g, b)
		draw_pixel(cx - x, cy + y, r, g, b)
		draw_pixel(cx - x, cy - y, r, g, b)
		draw_pixel(cx - y, cy - x, r, g, b)
		draw_pixel(cx + y, cy - x, r, g, b)
		draw_pixel(cx + x, cy - y, r, g, b)

		y += 1
		if err <= 0:
			err += 2 * y + 1
		if err > 0:
			x -= 1
			err -= 2 * x + 1

# --- NEW: draw_image_from_file (called by PXVM with an Image object) ---
func draw_image_from_file(img_to_draw: Image, x: int, y: int):
	if not img_to_draw:
		print("Error: Image to draw is null.")
		return

	# Ensure the image is ready for reading (not strictly needed for blit_rect if it's already loaded)
	# img_to_draw.lock() # Not needed for blit_rect

	# Define source and destination rectangles
	var src_rect = Rect2(0, 0, img_to_draw.get_width(), img_to_draw.get_height())
	var dst_pos = Vector2(x, y)

	# Blit the image onto the main framebuffer
	# blit_rect handles clipping automatically
	image.blit_rect(img_to_draw, src_rect, dst_pos)

	# img_to_draw.unlock() # Not needed for blit_rect
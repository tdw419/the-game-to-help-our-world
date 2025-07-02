extends Node

class_name PXDisplayManager

var width := 160
var height := 120
var image : Image
var texture : ImageTexture
var display_rect : TextureRect

func _ready():
	# Create and initialize the framebuffer
	image = Image.create(width, height, false, Image.FORMAT_RGB8)
	image.fill(Color(0, 0, 0))
	texture = ImageTexture.create_from_image(image)

	# Create a TextureRect to display the framebuffer
	display_rect = TextureRect.new()
	display_rect.texture = texture
	display_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	display_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	display_rect.rect_size = Vector2(width * 4, height * 4) # scale up for visibility
	display_rect.anchor_right = 1.0
	display_rect.anchor_bottom = 1.0
	add_child(display_rect)

func draw_pixel(x: int, y: int, r: int, g: int, b: int):
	if x >= 0 and x < width and y >= 0 and y < height:
		image.set_pixel(x, y, Color(r / 255.0, g / 255.0, b / 255.0))

func draw_rect(x: int, y: int, w: int, h: int, r: int, g: int, b: int):
	for i in x:(x + w):
		for j in y:(y + h):
			draw_pixel(i, j, r, g, b)

func clear_display(r: int, g: int, b: int):
	image.lock()
	image.fill(Color(r / 255.0, g / 255.0, b / 255.0))
	image.unlock()

func refresh_display():
	image.lock()
	image.unlock()
	texture.update(image)

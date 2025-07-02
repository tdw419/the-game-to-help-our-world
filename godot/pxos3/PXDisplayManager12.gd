# Add at the top
var font_image: Image
var char_width := 5
var char_height := 7
var ascii_offset := 32 # ASCII start of printable characters

func _ready():
	# Existing image/texture setup...
	# Load the font image (ASCII chars from 32 to 126)
	var font_tex = load("res://assets/font_ascii.png") as Texture2D
	font_image = font_tex.get_image()

func draw_char(char_code: int, x: int, y: int, r: int, g: int, b: int):
	if not font_image: return
	if char_code < ascii_offset or char_code > 126: return

	var char_index = char_code - ascii_offset
	var src_x = char_index * char_width
	for dx in range(char_width):
		for dy in range(char_height):
			var color = font_image.get_pixel(src_x + dx, dy)
			if color.a > 0.5:
				img.set_pixel(x + dx, y + dy, Color(r / 255.0, g / 255.0, b / 255.0))

func draw_text(text: String, x: int, y: int, r: int, g: int, b: int):
	for i in range(text.length()):
		var char_code = text[i].ord()
		draw_char(char_code, x + i * char_width, y, r, g, b)

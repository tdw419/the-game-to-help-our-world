var font_image: Image
var char_width := 5
var char_height := 7
var ascii_offset := 32 # Start at ASCII space

func _ready():
	# Existing display buffer setup
	var font_tex = load("res://assets/font_ascii.png") as Texture2D
	font_image = font_tex.get_image()

func draw_char(char_code: int, x: int, y: int, r: int, g: int, b: int):
	if not font_image: return
	if char_code < ascii_offset or char_code > 126: return
	var index = char_code - ascii_offset
	var src_x = index * char_width
	for dx in range(char_width):
		for dy in range(char_height):
			var px = font_image.get_pixel(src_x + dx, dy)
			if px.a > 0.5:
				img.set_pixel(x + dx, y + dy, Color(r/255.0, g/255.0, b/255.0))

func draw_text(text: String, x: int, y: int, r: int, g: int, b: int):
	for i in range(text.length()):
		draw_char(text[i].ord(), x + i * char_width, y, r, g, b)

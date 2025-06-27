from PIL import Image, ImageDraw
img = Image.new("RGB", (64, 64), (20, 20, 50))
draw = ImageDraw.Draw(img)
draw.text((10, 20), "PXOS", fill=(0, 255, 0), font=None)
img.save("assets/pxos_logo.png")
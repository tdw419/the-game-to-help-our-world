from PIL import Image
import zlib
import math

def encode_file_to_image(input_path, output_image_path, compress=True):
    with open(input_path, 'rb') as f:
        data = f.read()

    if compress:
        data = zlib.compress(data)

    # Pad to ensure 3-byte alignment
    padding = (3 - len(data) % 3) % 3
    data += b'\x00' * padding

    # Convert bytes to pixels
    pixels = [tuple(data[i:i+3]) for i in range(0, len(data), 3)]

    # Determine image size (square or near-square)
    size = math.ceil(len(pixels) ** 0.5)
    image = Image.new('RGB', (size, size), color=(0, 0, 0))

    for i, pixel in enumerate(pixels):
        x = i % size
        y = i // size
        if y < size:
            image.putpixel((x, y), pixel)

    image.save(output_image_path)
    print(f"Saved image backup to {output_image_path}")

from PIL import Image
import zlib

def decode_image_to_file(input_image_path, output_file_path, decompress=True):
    image = Image.open(input_image_path)
    pixels = list(image.getdata())

    # Flatten pixel tuples into a byte array
    raw_data = bytearray()
    for r, g, b in pixels:
        raw_data.extend([r, g, b])

    if decompress:
        try:
            raw_data = zlib.decompress(raw_data)
        except zlib.error as e:
            print("Error decompressing data:", e)
            return

    with open(output_file_path, 'wb') as f:
        f.write(raw_data)

    print(f"Restored file to {output_file_path}")

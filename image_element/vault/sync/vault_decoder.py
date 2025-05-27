from PIL import Image

def decode_vault_image(image_path):
    image = Image.open(image_path)
    pixels = image.load()
    width, height = image.size

    # Extract binary from red channel
    binary_data = ""
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            binary_data += "1" if r > 128 else "0"

    # Convert binary to characters
    chars = []
    for i in range(0, len(binary_data), 8):
        byte = binary_data[i:i+8]
        if len(byte) < 8:
            break
        chars.append(chr(int(byte, 2)))

    return ''.join(chars)

# Example usage
if __name__ == "__main__":
    message = decode_vault_image("vault_latest.png")
    print("Decoded message:")
    print(message)

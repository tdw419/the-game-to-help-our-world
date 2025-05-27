
from PIL import Image

def decode_vault_image(path):
    image = Image.open(path)
    pixels = image.load()
    width, height = image.size

    # Extract binary from red channel
    binary_data = ''
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            binary_data += '1' if r > 127 else '0'

    # Convert binary to text
    chars = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
    message = ''
    for byte in chars:
        try:
            message += chr(int(byte, 2))
        except ValueError:
            continue
    return message.strip()

# Example usage:
if __name__ == "__main__":
    path = "vault_latest.png"
    decoded = decode_vault_image(path)
    print("Decoded Vault Contents:\n")
    print(decoded)

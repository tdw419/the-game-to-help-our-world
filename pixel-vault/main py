pixel-vault/main.py

from encoder import encode_file_to_image from decoder import decode_image_to_file import sys import os

def main(): if len(sys.argv) < 3: print("Usage:") print("  Encode: python main.py encode <input_file> <output_image>") print("  Decode: python main.py decode <input_image> <output_file>") return

command = sys.argv[1]

if command == "encode":
    input_file = sys.argv[2]
    output_image = sys.argv[3]
    encode_file_to_image(input_file, output_image)

elif command == "decode":
    input_image = sys.argv[2]
    output_file = sys.argv[3]
    decode_image_to_file(input_image, output_file)

else:
    print("Invalid command. Use 'encode' or 'decode'.")

if name == "main": main()


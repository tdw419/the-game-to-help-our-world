# File: /ColorOS/CommandEncoder.py
# Utility to create .pxl command scripts as pixel-based text images

from PIL import Image, ImageDraw, ImageFont

class CommandEncoder:
    def __init__(self, width=256, height=256, bg_color=(0, 0, 0), text_color=(255, 255, 255)):
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.text_color = text_color
        self.image = Image.new("RGB", (width, height), bg_color)
        self.draw = ImageDraw.Draw(self.image)

    def encode_commands(self, commands, line_height=12):
        """
        Write command strings as lines of text into the image.
        Each line becomes a command the shell can later read.
        """
        y = 0
        for line in commands:
            self.draw.text((2, y), line, fill=self.text_color)
            y += line_height
        return self.image

    def save(self, out_path="boot_script.pxl.png"):
        self.image.save(out_path)
        print(f"[Encoder] Saved .pxl command script to {out_path}")

# Example usage:
if __name__ == "__main__":
    commands = [
        "LOG booting...",
        "RUN 0",
        "LOG boot complete"
    ]
    encoder = CommandEncoder()
    img = encoder.encode_commands(commands)
    encoder.save("boot_script.pxl.png")

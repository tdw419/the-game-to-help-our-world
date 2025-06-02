#!/usr/bin/env python3
from pathlib import Path
from PIL import Image

# Import the glyph array you copied:
from vga8x8_from_cpp import glyphs_8x8  # make sure this path is correct

# ── CONFIG ────────────────────────────────────────────────────────────────────
SAMPLE_LINES = ["The quick brown", "fox jumps over 12"]  # 2 lines of text
OUTPUT = Path("pixel-vault/fonts/previews/vga8x8-cpp-preview.png")
# ───────────────────────────────────────────────────────────────────────────────

def render_lines_to_image(lines):
    """Given a list of text lines (ASCII), return a PIL Image of their 8×8 bitmaps."""
    # Each glyph is 8×8 pixels:
    glyph_w, glyph_h = 8, 8
    # Compute canvas size:
    max_chars = max(len(line) for line in lines)
    width = glyph_w * max_chars
    height = glyph_h * len(lines)
    canvas = Image.new("1", (width, height), color=0)  # mode '1' = 1-bit B/W

    for row_idx, text in enumerate(lines):
        for col_idx, ch in enumerate(text):
            code = ord(ch)
            if code < 0 or code >= len(glyphs_8x8):
                # If outside range (e.g. non-ASCII), skip:
                continue
            bitmap = glyphs_8x8[code]  # list of 8 bytes
            # Draw each of the 8 rows:
            for y in range(8):
                row_byte = bitmap[y]
                for x in range(8):
                    # Test if bit (7-x) is set:
                    if row_byte & (1 << (7 - x)):
                        canvas.putpixel((col_idx * glyph_w + x, row_idx * glyph_h + y), 1)

    # Convert 1-bit to full RGB so “on”=black, “off”=white:
    rgb = canvas.convert("RGB")
    for x in range(rgb.width):
        for y in range(rgb.height):
            if rgb.getpixel((x, y)) == (255, 255, 255):
                # In 1-bit mode, “on” was 255→ white, so turn it black
                rgb.putpixel((x, y), (0, 0, 0))
            else:
                # “Off” was 0→ black; turn it white
                rgb.putpixel((x, y), (255, 255, 255))
    return rgb

def main():
    img = render_lines_to_image(SAMPLE_LINES)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(OUTPUT))
    print(f"✔ Preview saved to {OUTPUT}")

if __name__ == "__main__":
    main()

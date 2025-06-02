#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from PIL import Image

# ───────────────────────── CONFIGURATION ────────────────────────────────────────
# Path to your C++ source that contains the 8×8 array
CPP_PATH = Path("C:/zion/wwwroot/projects/the-game-to-help-our-world/fonts/VGA8x8-master/VGA8x8.cpp")

# Text to render in the preview (two 8×8 lines = 16px tall)
SAMPLE_LINES = ["The quick brown", "fox jumps over 12"]

# Where to save the output PNG
OUTPUT_PNG = Path("C:/zion/wwwroot/projects/the-game-to-help-our-world/pixel-vault/fonts/previews/vga8x8-cpp-preview.png")
# ────────────────────────────────────────────────────────────────────────────────


def parse_font8x8_from_cpp(cpp_path: Path):
    """
    Reads the VGA8x8.cpp file, locates the 'font8x8_basic' array,
    and returns a list of lists, where each sub-list is 8 integers (0–255).
    """
    text = cpp_path.read_text(encoding="utf-8", errors="ignore")

    # Find the start of 'font8x8_basic'
    array_start = text.find("font8x8_basic")
    if array_start == -1:
        print("[!] Could not find 'font8x8_basic' in VGA8x8.cpp", file=sys.stderr)
        sys.exit(1)

    # Extract the portion inside the outermost braces { ... };
    # We assume the pattern: static const unsigned char font8x8_basic[...] = {
    brace_open = text.find("{", array_start)
    if brace_open == -1:
        print("[!] Could not find opening brace for font8x8_basic", file=sys.stderr)
        sys.exit(1)

    # Now find the matching closing brace for that first '{'
    depth = 0
    for i in range(brace_open, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                brace_close = i
                break
    else:
        print("[!] Could not find closing brace for font8x8_basic", file=sys.stderr)
        sys.exit(1)

    array_text = text[brace_open + 1 : brace_close]  # contents between { ... }

    # Each glyph is defined as { 0x__,0x__, ... },  // comment
    # Use regex to find all instances of { byte,byte,...,byte }
    # We’ll match groups of 8 hex numbers inside braces.
    pattern = re.compile(r"\{\s*([0-9A-Fa-fx, ]+)\s*\}")
    matches = pattern.findall(array_text)

    glyphs = []
    for m in matches:
        # m is a string like '0x00,0x5F,0x00,0x00,0x00,0x00,0x00,0x00'
        # Split by comma, convert each to int
        bytes_str = [b.strip() for b in m.split(",") if b.strip()]
        if len(bytes_str) != 8:
            # Skip any entries that don’t have exactly 8 bytes
            continue
        row = []
        for b in bytes_str:
            try:
                val = int(b, 16)
            except ValueError:
                val = 0
            row.append(val)
        glyphs.append(row)
        if len(glyphs) >= 128:
            break  # stop once we have 128 entries (0x00–0x7F)

    if len(glyphs) < 95:
        print(f"[!] Parsed only {len(glyphs)} glyphs; expected ~95+ (for ASCII).", file=sys.stderr)

    return glyphs  # list of N lists, each 8 integers


def render_lines_to_image(glyphs, lines):
    """
    Given the glyph list (index = ASCII code), render the specified lines
    into a PIL Image (black text on white background).
    """
    glyph_w, glyph_h = 8, 8
    max_chars = max(len(line) for line in lines)
    width = glyph_w * max_chars
    height = glyph_h * len(lines)
    canvas = Image.new("1", (width, height), color=0)

    for row_idx, text in enumerate(lines):
        for col_idx, ch in enumerate(text):
            code = ord(ch)
            if 0 <= code < len(glyphs):
                bitmap = glyphs[code]
                for y in range(8):
                    row_byte = bitmap[y]
                    for x in range(8):
                        if row_byte & (1 << (7 - x)):
                            canvas.putpixel((col_idx * glyph_w + x, row_idx * glyph_h + y), 1)

    # Convert 1-bit to RGB so “on”=black and “off”=white
    rgb = canvas.convert("RGB")
    for x in range(rgb.width):
        for y in range(rgb.height):
            if rgb.getpixel((x, y)) == (255, 255, 255):
                rgb.putpixel((x, y), (0, 0, 0))
            else:
                rgb.putpixel((x, y), (255, 255, 255))
    return rgb


def main():
    # 1. Parse glyphs
    if not CPP_PATH.exists():
        print(f"[!] C++ source not found at {CPP_PATH}", file=sys.stderr)
        sys.exit(1)

    glyphs = parse_font8x8_from_cpp(CPP_PATH)

    # 2. Render sample text
    img = render_lines_to_image(glyphs, SAMPLE_LINES)

    # 3. Save output
    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(OUTPUT_PNG))
    print(f"✔ Preview saved to {OUTPUT_PNG}")


if __name__ == "__main__":
    main()

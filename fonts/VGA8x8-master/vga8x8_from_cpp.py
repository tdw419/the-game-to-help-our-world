# vga8x8_from_cpp.py
# ────────────────────────────────────────────────────────────────────────────────
# This file contains only the 8×8 glyph bitmaps from VGA8x8.cpp in Python form.
# Each entry is a list of 8 bytes (0–255). Index = ASCII code (0–127).
#        bit7 → leftmost pixel, bit0 → rightmost pixel.
# ────────────────────────────────────────────────────────────────────────────────

glyphs_8x8 = [
    # 0x00 (NUL) … 0x1F (unit controls) can remain if you wish, but they’ll never be rendered.
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+0000
    [0x00,0x00,0x00,0x5F,0x00,0x00,0x00,0x00],  # U+0001
    [0x00,0x00,0x07,0x00,0x07,0x00,0x00,0x00],  # U+0002
    [0x14,0x7F,0x14,0x7F,0x14,0x00,0x00,0x00],  # U+0003
    [0x24,0x2A,0x7F,0x2A,0x12,0x00,0x00,0x00],  # U+0004
    [0x23,0x13,0x08,0x64,0x62,0x00,0x00,0x00],  # U+0005
    [0x36,0x49,0x56,0x20,0x50,0x00,0x00,0x00],  # U+0006
    [0x00,0x08,0x07,0x03,0x00,0x00,0x00,0x00],  # U+0007
    [0x00,0x1C,0x22,0x41,0x00,0x00,0x00,0x00],  # U+0008
    [0x00,0x41,0x22,0x1C,0x00,0x00,0x00,0x00],  # U+0009
    [0x14,0x08,0x3E,0x08,0x14,0x00,0x00,0x00],  # U+000A
    [0x08,0x08,0x3E,0x08,0x08,0x00,0x00,0x00],  # U+000B
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+000C
    [0x00,0x80,0x60,0x20,0x18,0x00,0x00,0x00],  # U+000D
    [0x08,0x08,0x2A,0x1C,0x08,0x00,0x00,0x00],  # U+000E
    [0x08,0x1C,0x2A,0x08,0x08,0x00,0x00,0x00],  # U+000F
    [0x08,0x08,0x3E,0x08,0x08,0x00,0x00,0x00],  # U+0010 (duplicate of 0x000B)
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+0011
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+0012
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+0013
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+0014
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+0015
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+0016
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+0017
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+0018
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+0019
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+001A
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+001B
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+001C
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+001D
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+001E
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # U+001F

    # 0x20 ' ' (space) through 0x7E '~'
    [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00],  # 0x20 ' '
    [0x00,0x00,0x5F,0x00,0x00,0x00,0x00,0x00],  # 0x21 '!'
    [0x00,0x07,0x00,0x07,0x00,0x00,0x00,0x00],  # 0x22 '"'
    [0x14,0x7F,0x14,0x7F,0x14,0x00,0x00,0x00],  # 0x23 '#'
    [0x24,0x2A,0x7F,0x2A,0x12,0x00,0x00,0x00],  # 0x24 '$'
    [0x23,0x13,0x08,0x64,0x62,0x00,0x00,0x00],  # 0x25 '%'
    [0x36,0x49,0x55,0x22,0x50,0x00,0x00,0x00],  # 0x26 '&'
    [0x00,0x05,0x03,0x00,0x00,0x00,0x00,0x00],  # 0x27 '''
    [0x00,0x1C,0x22,0x41,0x00,0x00,0x00,0x00],  # 0x28 '('
    [0x00,0x41,0x22,0x1C,0x00,0x00,0x00,0x00],  # 0x29 ')'
    [0x14,0x08,0x3E,0x08,0x14,0x00,0x00,0x00],  # 0x2A '*'
    [0x08,0x08,0x3E,0x08,0x08,0x00,0x00,0x00],  # 0x2B '+'
    [0x00,0x50,0x30,0x00,0x00,0x00,0x00,0x00],  # 0x2C ','
    [0x08,0x08,0x08,0x08,0x08,0x00,0x00,0x00],  # 0x2D '-'
    [0x00,0x60,0x60,0x00,0x00,0x00,0x00,0x00],  # 0x2E '.'
    [0x20,0x10,0x08,0x04,0x02,0x00,0x00,0x00],  # 0x2F '/'
    [0x3E,0x51,0x49,0x45,0x3E,0x00,0x00,0x00],  # 0x30 '0'
    [0x00,0x42,0x7F,0x40,0x00,0x00,0x00,0x00],  # 0x31 '1'
    [0x62,0x51,0x49,0x49,0x46,0x00,0x00,0x00],  # 0x32 '2'
    [0x22,0x49,0x49,0x49,0x36,0x00,0x00,0x00],  # 0x33 '3'
    [0x18,0x14,0x12,0x7F,0x10,0x00,0x00,0x00],  # 0x34 '4'
    [0x27,0x45,0x45,0x45,0x39,0x00,0x00,0x00],  # 0x35 '5'
    [0x3C,0x4A,0x49,0x49,0x30,0x00,0x00,0x00],  # 0x36 '6'
    [0x01,0x71,0x09,0x05,0x03,0x00,0x00,0x00],  # 0x37 '7'
    [0x36,0x49,0x49,0x49,0x36,0x00,0x00,0x00],  # 0x38 '8'
    [0x06,0x49,0x49,0x29,0x1E,0x00,0x00,0x00],  # 0x39 '9'
    [0x00,0x36,0x36,0x00,0x00,0x00,0x00,0x00],  # 0x3A ':'
    [0x00,0x56,0x36,0x00,0x00,0x00,0x00,0x00],  # 0x3B ';'
    [0x08,0x14,0x22,0x41,0x00,0x00,0x00,0x00],  # 0x3C '<'
    [0x14,0x14,0x14,0x14,0x14,0x00,0x00,0x00],  # 0x3D '='
    [0x41,0x22,0x14,0x08,0x00,0x00,0x00,0x00],  # 0x3E '>'
    [0x02,0x01,0x59,0x09,0x06,0x00,0x00,0x00],  # 0x3F '?'
    [0x3E,0x41,0x5D,0x59,0x4E,0x00,0x00,0x00],  # 0x40 '@'
    [0x7C,0x12,0x11,0x12,0x7C,0x00,0x00,0x00],  # 0x41 'A'
    [0x7F,0x49,0x49,0x49,0x36,0x00,0x00,0x00],  # 0x42 'B'
    [0x3E,0x41,0x41,0x41,0x22,0x00,0x00,0x00],  # 0x43 'C'
    [0x7F,0x41,0x41,0x41,0x3E,0x00,0x00,0x00],  # 0x44 'D'
    [0x7F,0x49,0x49,0x49,0x41,0x00,0x00,0x00],  # 0x45 'E'
    [0x7F,0x09,0x09,0x09,0x01,0x00,0x00,0x00],  # 0x46 'F'
    [0x3E,0x41,0x49,0x49,0x7A,0x00,0x00,0x00],  # 0x47 'G'
    [0x7F,0x08,0x08,0x08,0x7F,0x00,0x00,]()

# File: /ColorOS/PixelSysCall.py
# Part of Color OS – Expanded syscall system for I/O and logging

from PIL import Image, ImageDraw
import os

class PixelSysCall:
    def __init__(self, memory_canvas):
        self.memory_canvas = memory_canvas
        self.syscall_table = {
            0x01: self.sys_write_to_disk,
            0x02: self.sys_read_from_disk,
            0x03: self.sys_log_message
        }

    def handle_syscall(self, syscall_id, *args):
        if syscall_id in self.syscall_table:
            return self.syscall_table[syscall_id](*args)
        else:
            print(f"[SysCall] Unknown syscall: {syscall_id}")
            return None

    def sys_write_to_disk(self, region_coords, out_path):
        x0, y0, x1, y1 = region_coords
        region = self.memory_canvas.crop((x0, y0, x1, y1))
        region.save(out_path)
        print(f"[SysCall] Saved region {region_coords} to {out_path}")
        return True

    def sys_read_from_disk(self, in_path, target_coords):
        if not os.path.exists(in_path):
            print(f"[SysCall] File not found: {in_path}")
            return False
        src_img = Image.open(in_path)
        x, y = target_coords
        self.memory_canvas.paste(src_img, (x, y))
        print(f"[SysCall] Loaded {in_path} to canvas at {target_coords}")
        return True

    def sys_log_message(self, message, log_path="log.img.png"):
        if os.path.exists(log_path):
            log_img = Image.open(log_path)
        else:
            log_img = Image.new("RGB", (512, 1024), (0, 0, 0))

        draw = ImageDraw.Draw(log_img)
        y_cursor = 0
        while y_cursor < log_img.height:
            pixel = log_img.getpixel((0, y_cursor))
            if pixel == (0, 0, 0):
                break
            y_cursor += 10

        draw.text((2, y_cursor), message, fill=(0, 255, 0))
        log_img.save(log_path)
        print(f"[SysCall] Logged message to {log_path}: {message}")
        return True

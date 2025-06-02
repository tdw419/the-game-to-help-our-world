# File: /ColorOS/PixelShell.py
# Part of Color OS – Image-native command interpreter shell

from PIL import Image
from PixelRunner import PixelRunner
from PixelSysCall import PixelSysCall
import pytesseract

class PixelShell:
    def __init__(self, canvas):
        self.canvas = canvas
        self.syscall = PixelSysCall(canvas)
        self.commands = {
            "RUN": self.cmd_run,
            "LOG": self.cmd_log,
            "DRAW": self.cmd_draw
        }

    def parse_command(self, text_line):
        parts = text_line.strip().split(" ", 1)
        if not parts:
            return None, None
        cmd = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ""
        return cmd, args

    def execute_script(self, lines):
        for line in lines:
            cmd, args = self.parse_command(line)
            if cmd in self.commands:
                self.commands[cmd](args)
            else:
                print(f"[Shell] Unknown command: {cmd}")

    def load_script_from_image(self, image_path):
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        lines = text.strip().splitlines()
        print(f"[Shell] Loaded commands from {image_path}: {lines}")
        self.execute_script(lines)

    def cmd_run(self, args):
        try:
            idx = int(args)
            filename = f"loaded_program_{idx}.pxl.png"
            img = Image.open(filename)
            runner = PixelRunner(img)
            runner.execute()
            print(f"[Shell] Ran program #{idx}")
        except Exception as e:
            print(f"[Shell] Error running program: {e}")

    def cmd_log(self, message):
        self.syscall.sys_log_message(message)

    def cmd_draw(self, arg):
        print(f"[Shell] DRAW not implemented yet: {arg}")

# Example usage
if __name__ == "__main__":
    canvas = Image.new("RGB", (256, 256), (0, 0, 0))
    shell = PixelShell(canvas)
    shell.load_script_from_image("boot_script.pxl.png")

```python
import os
import platform
from PIL import Image
import ast
from collections import Counter
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from RestrictedPython import compile_restricted, safe_globals

IS_PYODIDE = platform.system() == "Emscripten"
in_memory_storage = {}

# Define RGB-encoded blobs
blobs = {
    "pxboot_init": bytes.fromhex("B8 01 00 00 00 50 48 31 C0 48 FF C0 C3"),
    "pxos_pxasm": bytes.fromhex("4D4F5620307830303030203078310A505845454343203078313030300A484C54"),
    "PXDetectPCI": bytes.fromhex("5345545F505820307831303030203078303030300A5345545F505820307831303034203078383038360A484C54"),
    "PXMatchDriver": bytes.fromhex("5345545F505820307846303030203078313030340A434D5020307846303030203078383038360A484C54"),
    "PXDriverTemplates": bytes.fromhex("5345545F50582030783330303020307830300A5345545F50582030783330303420275058446973706C617954656D706C6174652E7A744674270A484C54"),
    "PXReflexMutator": bytes.fromhex("5345545F50582030783430303020307830300A434D502030784630303820307836340A484C54"),
    "PXAutoDriverController": bytes.fromhex("43414C4C203078313030300A43414C4C203078463030300A484C54"),
    "VisualFilesystem": bytes.fromhex("5345545F50582030783031303020307830350A5345545F505820307830313034203030320A484C54")
}

# Initialize pixel memory
canvas_size = 128
pixel_memory = [0] * (640 * 480)
blob_data = b"".join(blobs.values())
pixel_data = [0] * (canvas_size * canvas_size)
for i in range(0, len(blob_data), 3):
    r = blob_data[i] if i < len(blob_data) else 0
    g = blob_data[i + 1] if i + 1 < len(blob_data) else 0
    b = blob_data[i + 2] if i + 2 < len(blob_data) else 0
    pixel_data[i // 3] = (r << 16) | (g << 8) | b
for i in range(min(len(pixel_data), len(pixel_memory))):
    pixel_memory[i] = pixel_data[i]

class MiniVFS:
    def __init__(self):
        self.paths = set()
    
    def add_file(self, path):
        self.paths.add(path)

class MiniRT:
    def __init__(self):
        self.code_mapping = {}
        self.pxbot = None
    
    def set_pxbot(self, pxbot):
        self.pxbot = pxbot
    
    def save_code(self, name, image_path):
        self.code_mapping[name] = image_path
    
    def load_code(self, name):
        if name in self.code_mapping and self.pxbot:
            return self.pxbot._decode_from_image(self.code_mapping[name])
        return None
    
    def exec_code(self, name):
        code = self.load_code(name)
        if code:
            try:
                byte_code = compile_restricted(code, '<string>', 'exec')
                exec(byte_code, safe_globals)
                return f"Executed: {name}"
            except Exception as e:
                return f"Execution error: {e}"
        return f"Code '{name}' not found"
    
    def list_codes(self):
        return list(self.code_mapping.keys())

class PXBot:
    def __init__(self, vfs, rt):
        self.v, self.r, self.h = vfs, rt, []
        
    def run(self, command):
        self.h.append(command)
        parts = command.split(":")
        try:
            if parts[0] == "create":
                if parts[1] == "function":
                    return self._create_function(parts[2], parts[3], parts[4] if len(parts) > 4 else "None")
                if parts[1] == "class":
                    return self._create_class(parts[2], parts[3], parts[4] if len(parts) > 4 else "")
                if parts[1] == "pixel_art":
                    return self._create_pixel_art(parts[2])
                if parts[1] == "pattern":
                    return self._create_pattern(parts[2], int(parts[3]) if len(parts) > 3 else 32)
                if parts[1] == "template":
                    return self._create_template(parts[2], parts[3] if len(parts) > 3 else f"my_{parts[2]}")
            if parts[0] == "merge":
                return self._merge_codes(parts[1], parts[2], parts[3])
            if parts[0] == "analyze":
                return self._analyze_pixels(parts[1])
            if parts[0] == "optimize":
                return self._optimize_storage(parts[1])
            if parts[0] == "edit":
                return self._edit_code(parts[1], parts[2] if len(parts) > 2 else "")
            if parts[0] == "exec":
                return self.r.exec_code(parts[1])
            if parts[0] == "save":
                return self._save_custom_code(parts[1], parts[2])
            if parts[0] == "query":
                return self._query_system(parts[1] if len(parts) > 1 else "")
        except Exception as e:
            return f"Error: {e}"
    
    def _create_function(self, name, params, return_val):
        if "factorial" in name.lower():
            body = "if n <= 1: return 1\n return n * factorial(n-1)"
        else:
            body = "pass"
        code = f"def {name}({params}):\n {body}\n return {return_val}"
        return self._save_code(code, name)
    
    def _create_class(self, name, attrs, methods):
        attrs_init = "\n ".join([f"self.{x.strip()} = {x.strip()}" for x in attrs.split(",") if x.strip()])
        methods_def = "\n ".join([f"def {x.strip()}(self): pass" for x in methods.split(",") if x.strip()])
        code = f"""class {name}:
 def __init__(self, {attrs}):
 {attrs_init if attrs_init else "pass"}
 
 {methods_def if methods_def else "pass"}"""
        return self._save_code(code, name)
    
    def _create_pixel_art(self, code_name):
        code = self.r.load_code(code_name)
        if not code:
            return f"Code '{code_name}' not found"
        img = Image.new("RGB", (32, 32), (0, 0, 0))
        pixels = img.load()
        for i, char in enumerate(code[:32*32]):
            x, y = i % 32, i // 32
            pixels[x, y] = (ord(char) % 255, (ord(char) * 2) % 255, (ord(char) * 3) % 255)
        output_path = os.path.join("pxbot_code", f"{code_name}_art.png")
        if IS_PYODIDE:
            in_memory_storage[output_path] = img
        else:
            os.makedirs("pxbot_code", exist_ok=True)
            img.save(output_path)
        self.v.add_file(output_path)
        return f"Pixel art created: {output_path}"
    
    def _create_pattern(self, pattern_type, size):
        img = Image.new("RGB", (size, size), (0, 0, 0))
        pixels = img.load()
        if pattern_type == "gradient":
            for x in range(size):
                for y in range(size):
                    pixels[x, y] = (x * 255 // size, y * 255 // size, 128)
        elif pattern_type == "checkerboard":
            for x in range(size):
                for y in range(size):
                    pixels[x, y] = (255, 255, 255) if (x + y) % 2 == 0 else (0, 0, 0)
        elif pattern_type == "spiral":
            for x in range(size):
                for y in range(size):
                    angle = (x - size/2)**2 + (y - size/2)**2
                    pixels[x, y] = (int(255 * (angle % size) / size), 128, 128)
        elif pattern_type == "diamond":
            for x in range(size):
                for y in range(size):
                    dist = abs(x - size/2) + abs(y - size/2)
                    pixels[x, y] = (255 if dist < size/4 else 0, 128, 128)
        output_path = os.path.join("pxbot_code", f"{pattern_type}_{size}x{size}.png")
        if IS_PYODIDE:
            in_memory_storage[output_path] = img
        else:
            os.makedirs("pxbot_code", exist_ok=True)
            img.save(output_path)
        self.v.add_file(output_path)
        return f"Pattern created: {output_path}"
    
    def _create_template(self, template_type, name):
        templates = {
            "calculator": f"""def {name}():
    history = []
    def add(x, y):
        result = x + y
        history.append(f'{{x}} + {{y}} = {{result}}')
        return result
    return add""",
            "data_processor": f"""def {name}(data):
    return [x for x in data if x > 0]""",
            "web_scraper": f"""def {name}(url):
    import urllib.request
    with urllib.request.urlopen(url) as response:
        return response.read().decode('utf-8')""",
            "file_manager": f"""def {name}(filename):
    with open(filename, 'r') as f:
        return f.read()"""
        }
        code = templates.get(template_type, "pass")
        return self._save_code(code, name)
    
    def _merge_codes(self, code1, code2, new_name):
        c1 = self.r.load_code(code1)
        c2 = self.r.load_code(code2)
        if not c1 or not c2:
            return f"One or both codes not found: {code1}, {code2}"
        merged_code = f"# Merged from {code1} and {code2}\n{c1}\n\n{c2}"
        return self._save_code(merged_code, new_name)
    
    def _analyze_pixels(self, code_name):
        code = self.r.load_code(code_name)
        if not code:
            return f"Code '{code_name}' not found"
        pixel_count = len(code.encode('utf-8'))
        ascii_dist = sorted({chr(c): code.count(chr(c)) for c in range(32, 127) if chr(c) in code}.items())
        return f"Pixel analysis for {code_name}: {pixel_count} bytes, {len(code)} characters\nASCII distribution: {ascii_dist}"
    
    def _optimize_storage(self, code_name):
        code = self.r.load_code(code_name)
        if not code:
            return f"Code '{code_name}' not found"
        optimized_code = "".join(line.strip() for line in code.splitlines() if line.strip() and not line.strip().startswith("#"))
        return self._save_code(optimized_code, f"{code_name}_opt")
    
    def _save_custom_code(self, name, code):
        return self._save_code(code, name)
    
    def _edit_code(self, name, modification):
        existing_code = self.r.load_code(name)
        if not existing_code:
            return f"Code '{name}' not found"
        modified_code = existing_code + f"\n# {modification}"
        return self._save_code(modified_code, name)
    
    def _save_code(self, code, name):
        try:
            compile_restricted(code, '<string>', 'exec')
        except SyntaxError:
            return "Invalid Python syntax"
        code_dir = "pxbot_code"
        image_path = os.path.join(code_dir, f"{name}.png")
        encoded_image = self._encode_to_image(code)
        if IS_PYODIDE:
            in_memory_storage[image_path] = encoded_image
        else:
            os.makedirs(code_dir, exist_ok=True)
            encoded_image.save(image_path)
        self.v.add_file(code_dir)
        self.r.save_code(name, image_path)
        return f"Saved: {name} -> {image_path}"
    
    def _encode_to_image(self, code):
        data = code.encode('utf-8')
        width = int(len(data)**0.5) + 1
        height = width
        image = Image.new("RGB", (width, height), (0, 0, 0))
        pixels = image.load()
        for i, byte in enumerate(data):
            if i < width * height:
                x, y = i % width, i // width
                pixels[x, y] = (byte, 0, 0)
        return image
    
    def _decode_from_image(self, image_path):
        try:
            if IS_PYODIDE:
                image = in_memory_storage.get(image_path)
                if not image:
                    return None
            else:
                image = Image.open(image_path)
            pixels = image.load()
            width, height = image.size
            data = []
            for y in range(height):
                for x in range(width):
                    r, g, b = pixels[x, y]
                    if r > 0:
                        data.append(r)
            return bytes(data).decode('utf-8', errors='ignore').rstrip('\x00')
        except Exception:
            return None
    
    def _query_system(self, path):
        if path == "/usr":
            return str({"path": "/usr", "size_mb": self.r.code_mapping.get(path, 0) / 1000})
        return "Invalid query path"

class PXBotGUI:
    def __init__(self):
        self.vfs = MiniVFS()
        self.runtime = MiniRT()
        self.pxbot = PXBot(self.vfs, self.runtime)
        self.runtime.set_pxbot(self.pxbot)
        self.root = tk.Tk()
        self.root.title("PXBot Pro - Pixel Code Editor")
        self.root.geometry("800x600")
        self.setup_gui()
    
    def setup_gui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        title_label = tk.Label(main_frame, text="PXBot Pro - Pixel Code Editor", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.setup_editor_tab()
        self.setup_saved_tab()
    
    def setup_editor_tab(self):
        editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(editor_frame, text="Code Editor")
        controls_frame = ttk.Frame(editor_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(controls_frame, text="Code Name:").pack(side=tk.LEFT)
        self.editor_name = tk.Entry(controls_frame, width=20)
        self.editor_name.pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Save Code", command=self.save_editor_code).pack(side=tk.LEFT, padx=5)
        self.code_editor = scrolledtext.ScrolledText(editor_frame, height=20, font=('Consolas', 11))
        self.code_editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def setup_saved_tab(self):
        saved_frame = ttk.Frame(self.notebook)
        self.notebook.add(saved_frame, text="Saved Codes")
        controls_frame = ttk.Frame(saved_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(controls_frame, text="Refresh List", command=self.refresh_saved_list).pack(side=tk.LEFT, padx=5)
        self.saved_listbox = tk.Listbox(saved_frame, height=10)
        self.saved_listbox.pack(fill=tk.X, padx=10, pady=5)
        self.refresh_saved_list()
    
    def save_editor_code(self):
        name = self.editor_name.get().strip()
        code = self.code_editor.get('1.0', tk.END).strip()
        if not name or not code:
            messagebox.showerror("Error", "Name and code are required")
            return
        result = self.pxbot.run(f"save:{name}:{code}")
        messagebox.showinfo("Result", result)
        self.refresh_saved_list()
    
    def refresh_saved_list(self):
        self.saved_listbox.delete(0, tk.END)
        for code_name in self.runtime.list_codes():
            self.saved_listbox.insert(tk.END, code_name)
    
    def run(self):
        self.root.mainloop()

class PXOSInterface:
    def __init__(self):
        self.pixel_memory = pixel_memory
        self.vfs = MiniVFS()
        self.runtime = MiniRT()
        self.pxbot = PXBot(self.vfs, self.runtime)
        self.runtime.set_pxbot(self.pxbot)
    
    def query_blob(self, path: str) -> dict:
        if path == "/usr" and self.pixel_memory[0x0100 // 4] == 5:
            return {"path": "/usr", "size_mb": self.pixel_memory[0x0104 // 4] / 1000}
        return {}
    
    def update_blob(self, path: str, size_mb: int) -> bool:
        if path == "/usr" and 0 <= size_mb <= 8000:
            self.pixel_memory[0x0104 // 4] = int(size_mb * 1000)
            return True
        return False
    
    def execute_command(self, command: str) -> str:
        try:
            from pxos_chatbot import PXBotGUI as FullPXBotGUI
        except ImportError:
            return "Error: pxos_chatbot.py not found"
        if command == "detect_pci":
            return "Detected devices: 8086:1916, 10DE:1347"
        elif command == "launch_gui":
            threading.Thread(target=lambda: FullPXBotGUI().run(), daemon=True).start()
            return "GUI launched"
        elif command.startswith("pxbot:"):
            return self.pxbot.run(command[6:])
        return "Command not recognized"

def main():
    return PXOSInterface()
```
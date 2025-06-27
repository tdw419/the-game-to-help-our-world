```python
import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from PIL import Image
import threading
from RestrictedPython import compile_restricted, safe_globals

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
            if parts[0] == "edit":
                return self._edit_code(parts[1], parts[2] if len(parts) > 2 else "")
            if parts[0] == "exec":
                return self.r.exec_code(parts[1])
            if parts[0] == "save":
                return self._save_custom_code(parts[1], parts[2])
        except Exception as e:
            return f"Error: {e}"
    
    def _create_function(self, name, params, return_val):
        body = "if n <= 1: return 1\n return n * factorial(n-1)" if "factorial" in name.lower() else "pass"
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
        code_dir = os.path.join(os.getcwd(), "pxbot_code")
        os.makedirs(code_dir, exist_ok=True)
        image_path = os.path.join(code_dir, f"{name}.png")
        encoded_image = self._encode_to_image(code)
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
        self.load_existing_codes()
    
    def setup_gui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        title_label = tk.Label(main_frame, text="PXBot Pro - Pixel Code Editor", font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.setup_quick_tab()
        self.setup_editor_tab()
        self.setup_saved_tab()
    
    def setup_quick_tab(self):
        quick_frame = ttk.Frame(self.notebook)
        self.notebook.add(quick_frame, text="Quick Commands")
        func_frame = ttk.LabelFrame(quick_frame, text="Create Function", padding=10)
        func_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(func_frame, text="Name:").grid(row=0, column=0, sticky=tk.W)
        self.func_name = tk.Entry(func_frame, width=20)
        self.func_name.grid(row=0, column=1, padx=5)
        tk.Label(func_frame, text="Parameters:").grid(row=0, column=2, sticky=tk.W)
        self.func_params = tk.Entry(func_frame, width=20)
        self.func_params.grid(row=0, column=3, padx=5)
        ttk.Button(func_frame, text="Create Function", command=self.create_function).grid(row=0, column=4, padx=5)
        class_frame = ttk.LabelFrame(quick_frame, text="Create Class", padding=10)
        class_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(class_frame, text="Name:").grid(row=0, column=0, sticky=tk.W)
        self.class_name = tk.Entry(class_frame, width=20)
        self.class_name.grid(row=0, column=1, padx=5)
        tk.Label(class_frame, text="Attributes:").grid(row=0, column=2, sticky=tk.W)
        self.class_attrs = tk.Entry(class_frame, width=20)
        self.class_attrs.grid(row=0, column=3, padx=5)
        ttk.Button(class_frame, text="Create Class", command=self.create_class).grid(row=0, column=4, padx=5)
        output_frame = ttk.LabelFrame(quick_frame, text="Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, bg='#1e1e1e', fg='#00ff00', font=('Consolas', 10))
        self.output_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_editor_tab(self):
        editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(editor_frame, text="Code Editor")
        controls_frame = ttk.Frame(editor_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(controls_frame, text="Code Name:").pack(side=tk.LEFT)
        self.editor_name = tk.Entry(controls_frame, width=20)
        self.editor_name.pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Save Code", command=self.save_editor_code).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Clear", command=self.clear_editor).pack(side=tk.LEFT, padx=5)
        self.code_editor = scrolledtext.ScrolledText(editor_frame, height=25, bg='#1e1e1e', fg='#ffffff', font=('Consolas', 11), insertbackground='white')
        self.code_editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        sample_code = '''def hello_world():
    """A simple hello world function"""
    print("Hello from PXBot!")
    return "Hello World"

class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, x, y):
        self.result = x + y
        return self.result
'''
        self.code_editor.insert('1.0', sample_code)
    
    def setup_saved_tab(self):
        saved_frame = ttk.Frame(self.notebook)
        self.notebook.add(saved_frame, text="Saved Codes")
        controls_frame = ttk.Frame(saved_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(controls_frame, text="Refresh List", command=self.refresh_saved_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Execute Selected", command=self.execute_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="View Code", command=self.view_selected_code).pack(side=tk.LEFT, padx=5)
        self.saved_listbox = tk.Listbox(saved_frame, height=10, bg='#2d2d2d', fg='white')
        self.saved_listbox.pack(fill=tk.X, padx=10, pady=5)
        viewer_frame = ttk.LabelFrame(saved_frame, text="Code Preview", padding=10)
        viewer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.code_viewer = scrolledtext.ScrolledText(viewer_frame, height=15, bg='#1e1e1e', fg='#ffffff', font=('Consolas', 10), state=tk.DISABLED)
        self.code_viewer.pack(fill=tk.BOTH, expand=True)
    
    def create_function(self):
        name = self.func_name.get().strip()
        params = self.func_params.get().strip()
        if not name:
            messagebox.showerror("Error", "Function name is required")
            return
        command = f"create:function:{name}:{params}:None"
        result = self.pxbot.run(command)
        self.log_output(f"Command: {command}")
        self.log_output(f"Result: {result}")
        self.func_name.delete(0, tk.END)
        self.func_params.delete(0, tk.END)
        self.refresh_saved_list()
    
    def create_class(self):
        name = self.class_name.get().strip()
        attrs = self.class_attrs.get().strip()
        if not name:
            messagebox.showerror("Error", "Class name is required")
            return
        command = f"create:class:{name}:{attrs}:"
        result = self.pxbot.run(command)
        self.log_output(f"Command: {command}")
        self.log_output(f"Result: {result}")
        self.class_name.delete(0, tk.END)
        self.class_attrs.delete(0, tk.END)
        self.refresh_saved_list()
    
    def save_editor_code(self):
        name = self.editor_name.get().strip()
        code = self.code_editor.get('1.0', tk.END).strip()
        if not name or not code:
            messagebox.showerror("Error", "Name and code are required")
            return
        command = f"save:{name}:{code}"
        result = self.pxbot.run(command)
        self.log_output(f"Saved: {name}")
        self.log_output(f"Result: {result}")
        self.refresh_saved_list()
    
    def clear_editor(self):
        self.code_editor.delete('1.0', tk.END)
        self.editor_name.delete(0, tk.END)
    
    def refresh_saved_list(self):
        self.saved_listbox.delete(0, tk.END)
        for code_name in self.runtime.list_codes():
            self.saved_listbox.insert(tk.END, code_name)
    
    def execute_selected(self):
        selection = self.saved_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a code to execute")
            return
        code_name = self.saved_listbox.get(selection[0])
        result = self.runtime.exec_code(code_name)
        self.log_output(f"Executed: {code_name}")
        self.log_output(f"Result: {result}")
    
    def view_selected_code(self):
        selection = self.saved_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a code to view")
            return
        code_name = self.saved_listbox.get(selection[0])
        code = self.runtime.load_code(code_name)
        self.code_viewer.config(state=tk.NORMAL)
        self.code_viewer.delete('1.0', tk.END)
        if code:
            self.code_viewer.insert('1.0', code)
        else:
            self.code_viewer.insert('1.0', f"Could not load code: {code_name}")
        self.code_viewer.config(state=tk.DISABLED)
    
    def load_existing_codes(self):
        code_dir = os.path.join(os.getcwd(), "pxbot_code")
        if os.path.exists(code_dir):
            for filename in os.listdir(code_dir):
                if filename.endswith('.png'):
                    name = filename[:-4]
                    image_path = os.path.join(code_dir, filename)
                    self.runtime.save_code(name, image_path)
        self.refresh_saved_list()
    
    def log_output(self, message):
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)
    
    def run(self):
        self.root.mainloop()
```
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import contextlib
import io
import json
from datetime import datetime
from pathlib import Path
import re # For syntax highlighting

# --- Configuration ---
LOG_FILE = "pde_log.json"
CANVAS_SIZE = 100 # pixels for Color OS simulation

# --- Syntax Highlighting Keywords ---
PYTHON_KEYWORDS = [
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break',
    'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally',
    'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal',
    'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield'
]
KEYWORD_COLOR = "#00BFFF" # Deep Sky Blue
ERROR_COLOR = "#FF4500"   # Orange Red
COMMENT_COLOR = "#808080" # Gray
STRING_COLOR = "#FFD700"  # Gold

# --- PDE GUI Class ---
class PDE(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Development Environment (PDE) v0.3")
        self.geometry("900x750") # Adjusted size for new elements

        self.create_widgets()
        self.init_log_file()
        self.init_canvas()

        self.bind("<F5>", lambda event: self.run_code()) # Bind F5 to run_code
        self.code_input.bind("<KeyRelease>", self.on_key_release_code_input) # For syntax highlighting

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=5)

        # --- Code Development Tab ---
        code_dev_frame = ttk.Frame(self.notebook)
        self.notebook.add(code_dev_frame, text="Code Development")

        # Code Input
        tk.Label(code_dev_frame, text="Enter Python Code:").pack(anchor=tk.W, padx=5, pady=2)
        self.code_input = scrolledtext.ScrolledText(code_dev_frame, height=15, width=80, bg="#000", fg="#0f0", insertbackground="#0f0")
        self.code_input.pack(fill=tk.BOTH, expand=True, padx=5)
        self.code_input.tag_config('keyword', foreground=KEYWORD_COLOR)
        self.code_input.tag_config('comment', foreground=COMMENT_COLOR)
        self.code_input.tag_config('string', foreground=STRING_COLOR)
        self.code_input.tag_config('error_line', background=ERROR_COLOR)

        # Code Controls
        code_controls_frame = tk.Frame(code_dev_frame, bg=self.cget('bg'))
        code_controls_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(code_controls_frame, text="Run Code (F5)", command=self.run_code, bg="#005", fg="#0f0").pack(side=tk.LEFT, padx=2)
        tk.Button(code_controls_frame, text="Save Script", command=self.save_script, bg="#005", fg="#0f0").pack(side=tk.LEFT, padx=2)
        tk.Button(code_controls_frame, text="Load Script", command=self.load_script, bg="#005", fg="#0f0").pack(side=tk.LEFT, padx=2)
        tk.Button(code_controls_frame, text="Clear Output", command=self.clear_output, bg="#005", fg="#0f0").pack(side=tk.LEFT, padx=2)

        # Output Display
        tk.Label(code_dev_frame, text="Output:").pack(anchor=tk.W, padx=5, pady=2)
        self.output_display = scrolledtext.ScrolledText(code_dev_frame, height=10, width=80, bg="#000", fg="#0f0", insertbackground="#0f0", state='disabled')
        self.output_display.pack(fill=tk.BOTH, expand=True, padx=5)

        # --- Inter-Agent Comms Tab ---
        comms_frame = ttk.Frame(self.notebook)
        self.notebook.add(comms_frame, text="Inter-Agent Comms")

        tk.Label(comms_frame, text="To Agent (e.g., Claude, Grok):", bg=self.cget('bg'), fg="#0f0").pack(anchor=tk.W, padx=10, pady=5)
        self.recipient_entry = tk.Entry(comms_frame, bg="#111", fg="#0f0", insertbackground="#0f0", width=40)
        self.recipient_entry.pack(fill=tk.X, padx=10, pady=2)

        tk.Label(comms_frame, text="Message:", bg=self.cget('bg'), fg="#0f0").pack(anchor=tk.W, padx=10, pady=5)
        self.message_input = scrolledtext.ScrolledText(comms_frame, height=8, width=80, bg="#111", fg="#0f0", insertbackground="#0f0")
        self.message_input.pack(fill=tk.BOTH, expand=True, padx=10, pady=2)

        tk.Button(comms_frame, text="Send Simulated Message", command=self.send_simulated_message, bg="#005", fg="#0f0").pack(pady=10)

        # --- Mission Tracking Tab ---
        mission_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(mission_tab_frame, text="Mission Tracking")

        tk.Label(mission_tab_frame, text="Mission ID:", bg=self.cget('bg'), fg="#0f0").pack(anchor=tk.W, padx=10, pady=5)
        self.mission_id_entry = tk.Entry(mission_tab_frame, bg="#111", fg="#0f0", insertbackground="#0f0", width=40)
        self.mission_id_entry.pack(fill=tk.X, padx=10, pady=2)

        tk.Label(mission_tab_frame, text="Status (e.g., Pending, Active, Completed):", bg=self.cget('bg'), fg="#0f0").pack(anchor=tk.W, padx=10, pady=5)
        self.mission_status_entry = tk.Entry(mission_tab_frame, bg="#111", fg="#0f0", insertbackground="#0f0", width=40)
        self.mission_status_entry.pack(fill=tk.X, padx=10, pady=2)

        tk.Label(mission_tab_frame, text="Notes:", bg=self.cget('bg'), fg="#0f0").pack(anchor=tk.W, padx=10, pady=5)
        self.mission_notes_entry = scrolledtext.ScrolledText(mission_tab_frame, height=5, width=80, bg="#111", fg="#0f0", insertbackground="#0f0")
        self.mission_notes_entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=2)

        tk.Button(mission_tab_frame, text="Log Mission", command=self.log_mission, bg="#005", fg="#0f0").pack(pady=10)

        # --- Color OS Pixel Interface Tab ---
        pixel_frame = ttk.Frame(self.notebook)
        self.notebook.add(pixel_frame, text="Color OS Pixel Interface")

        self.canvas = tk.Canvas(pixel_frame, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="black", bd=0, highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)
        tk.Label(pixel_frame, text=f"Canvas: {CANVAS_SIZE}x{CANVAS_SIZE} pixels", bg=self.cget('bg'), fg="#0f0").pack(pady=2)
        tk.Button(pixel_frame, text="Clear Canvas", command=self.clear_canvas, bg="#005", fg="#0f0").pack(pady=5)

        # --- Activity Log Tab ---
        log_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_tab_frame, text="Activity Log")

        self.activity_log_display = scrolledtext.ScrolledText(log_tab_frame, height=25, width=90, bg="#000", fg="#0f0", insertbackground="#0f0", state='disabled')
        self.activity_log_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Button(log_tab_frame, text="Refresh Log", command=self.load_activity_log, bg="#005", fg="#0f0").pack(pady=5)


    def init_log_file(self):
        Path(LOG_FILE).touch(exist_ok=True) # Ensure log file exists

    def init_canvas(self):
        self.canvas_pixels = {} # Stores (x,y) -> (r,g,b) values

    def set_pixel(self, x, y, r, g, b):
        """Simulates setting a pixel on the Color OS canvas."""
        if 0 <= x < CANVAS_SIZE and 0 <= y < CANVAS_SIZE:
            color_hex = f'#{r:02x}{g:02x}{b:02x}'
            # Delete old pixel if exists before drawing new one to prevent overlay issues with multiple same-coord draws
            self.canvas.delete(f"pixel_{x}_{y}")
            self.canvas.create_rectangle(x, y, x + 1, y + 1, fill=color_hex, outline="", tags=f"pixel_{x}_{y}")
            self.canvas_pixels[(x, y)] = (r, g, b)
        else:
            self.log_output(f"Warning: Pixel ({x},{y}) out of canvas bounds.")

    def clear_canvas(self):
        """Clears the simulated Color OS canvas."""
        self.canvas.delete("all")
        self.canvas_pixels = {}
        self.log_output("Color OS Canvas cleared.")

    def log_output(self, message):
        self.output_display.config(state='normal')
        self.output_display.insert(tk.END, message + "\n")
        self.output_display.see(tk.END)
        self.output_display.config(state='disabled')

    def clear_output(self):
        self.output_display.config(state='normal')
        self.output_display.delete("1.0", tk.END)
        self.output_display.config(state='disabled')

    def save_log_entry(self, entry_type, data):
        timestamp = datetime.utcnow().isoformat() + "Z" # UTC timestamp
        log_entry = {"timestamp": timestamp, "type": entry_type, "data": data}
        
        try:
            current_logs = []
            if Path(LOG_FILE).exists() and Path(LOG_FILE).stat().st_size > 0:
                with open(LOG_FILE, "r") as f:
                    try:
                        current_logs = json.load(f)
                    except json.JSONDecodeError: # Handle empty or malformed JSON
                        self.log_output(f"Warning: {LOG_FILE} is empty or malformed. Starting new log.")
                        current_logs = []
            
            current_logs.append(log_entry)
            
            with open(LOG_FILE, "w") as f:
                json.dump(current_logs, f, indent=2)
            
            self.log_output(f"Log entry ({entry_type}) saved to {LOG_FILE}.")
            self.load_activity_log() # Refresh log viewer
            
        except Exception as e:
            self.log_output(f"Error saving log: {e}")

    def run_code(self):
        code = self.code_input.get("1.0", tk.END).strip()
        self.clear_output()
        self.code_input.tag_remove('error_line', '1.0', tk.END) # Clear previous error highlights

        # Expose canvas control functions and print redirection to the executed code's environment
        exec_globals = {
            'set_pixel': self.set_pixel,
            'clear_canvas': self.clear_canvas,
            'print': self.log_output, # Redirect print to PDE output
            'CANVAS_SIZE': CANVAS_SIZE, # Expose canvas size
            'messagebox': messagebox, # Expose messagebox for simple pop-ups
        }

        output_stream = io.StringIO()
        with contextlib.redirect_stdout(output_stream):
            try:
                # Compile first to catch syntax errors and get line number
                compiled_code = compile(code, '<string>', 'exec')
                exec(compiled_code, exec_globals)
            except SyntaxError as e:
                self.log_output(f"Syntax Error: {e}")
                self.code_input.tag_add('error_line', f"{e.lineno}.0", f"{e.lineno}.end")
                self.code_input.see(f"{e.lineno}.0")
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc(limit=1) # Get just the relevant part of the traceback
                self.log_output(f"Runtime Error: {e}\n{error_trace}")
                # Try to extract line number from traceback for highlighting
                match = re.search(r'File "<string>", line (\d+)', error_trace)
                if match:
                    line_num = int(match.group(1))
                    self.code_input.tag_add('error_line', f"{line_num}.0", f"{line_num}.end")
                    self.code_input.see(f"{line_num}.0")
        
        captured_output = output_stream.getvalue().strip()
        if captured_output:
            self.log_output(captured_output)

        self.save_log_entry("code_execution", {"code": code, "output": captured_output})

    def save_script(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".py",
                                                filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(self.code_input.get("1.0", tk.END))
                self.log_output(f"Script saved to: {file_path}")
            except Exception as e:
                self.log_output(f"Failed to save script: {e}")

    def load_script(self):
        file_path = filedialog.askopenfilename(defaultextension=".py",
                                              filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if file_path:
            try:
                with open(file_path, "r") as f:
                    code = f.read()
                self.code_input.delete("1.0", tk.END)
                self.code_input.insert("1.0", code)
                self.log_output(f"Script loaded from: {file_path}")
                self.apply_syntax_highlighting() # Apply highlighting on load
            except Exception as e:
                self.log_output(f"Failed to load script: {e}")

    def log_mission(self):
        mission_id = self.mission_id_entry.get().strip()
        status = self.mission_status_entry.get().strip()
        notes = self.mission_notes_entry.get("1.0", tk.END).strip()

        if not mission_id:
            messagebox.showerror("Input Error", "Mission ID cannot be empty.")
            return

        mission_data = {
            "mission_id": mission_id,
            "status": status if status else "pending",
            "notes": notes if notes else "No notes provided."
        }
        self.save_log_entry("mission_tracking", mission_data)
        self.log_output(f"Mission '{mission_id}' logged successfully.")
        self.mission_id_entry.delete(0, tk.END)
        self.mission_status_entry.delete(0, tk.END)
        self.mission_notes_entry.delete("1.0", tk.END)

    def send_simulated_message(self):
        recipient = self.recipient_entry.get().strip()
        message = self.message_input.get("1.0", tk.END).strip()

        if not recipient or not message:
            messagebox.showerror("Input Error", "Recipient and Message cannot be empty.")
            return
        
        simulated_message = {
            "recipient": recipient,
            "message": message
        }
        self.save_log_entry("inter_agent_comms", simulated_message)
        self.log_output(f"Simulated message sent to '{recipient}'.")
        self.recipient_entry.delete(0, tk.END)
        self.message_input.delete("1.0", tk.END)

    def load_activity_log(self):
        self.activity_log_display.config(state='normal')
        self.activity_log_display.delete("1.0", tk.END)
        try:
            if Path(LOG_FILE).exists() and Path(LOG_FILE).stat().st_size > 0:
                with open(LOG_FILE, "r") as f:
                    logs = json.load(f)
                    for entry in logs:
                        timestamp = entry.get("timestamp", "N/A")
                        entry_type = entry.get("type", "unknown")
                        data = entry.get("data", {})
                        
                        display_text = f"--- {timestamp} [{entry_type.upper()}] ---\n"
                        if entry_type == "code_execution":
                            code_snippet = data.get("code", "N/A").split('\n')[0] # First line of code
                            output_snippet = data.get("output", "N/A").split('\n')[0] # First line of output
                            display_text += f"Code: {code_snippet[:50]}...\n"
                            display_text += f"Output: {output_snippet[:50]}...\n"
                        elif entry_type == "mission_tracking":
                            display_text += f"Mission ID: {data.get('mission_id', 'N/A')}\n"
                            display_text += f"Status: {data.get('status', 'N/A')}\n"
                            display_text += f"Notes: {data.get('notes', 'N/A')[:50]}...\n"
                        elif entry_type == "inter_agent_comms":
                            display_text += f"To: {data.get('recipient', 'N/A')}\n"
                            display_text += f"Msg: {data.get('message', 'N/A')[:50]}...\n"
                        else:
                            display_text += f"Details: {json.dumps(data)[:50]}...\n"
                        display_text += "\n"
                        self.activity_log_display.insert(tk.END, display_text)
            else:
                self.activity_log_display.insert(tk.END, "Log file is empty or does not exist.\n")
        except Exception as e:
            self.activity_log_display.insert(tk.END, f"Error loading log: {e}\n")
        self.activity_log_display.see(tk.END)
        self.activity_log_display.config(state='disabled')

    def on_key_release_code_input(self, event=None):
        self.apply_syntax_highlighting()

    def apply_syntax_highlighting(self):
        # Remove all existing tags
        for tag in ['keyword', 'comment', 'string']:
            self.code_input.tag_remove(tag, '1.0', tk.END)

        # Apply keyword highlighting
        text_content = self.code_input.get('1.0', tk.END)
        for keyword in PYTHON_KEYWORDS:
            for match in re.finditer(r'\b' + re.escape(keyword) + r'\b', text_content):
                start_index = self.code_input.index(f"1.0 + {match.start()}c")
                end_index = self.code_input.index(f"1.0 + {match.end()}c")
                self.code_input.tag_add('keyword', start_index, end_index)

        # Apply comment highlighting
        for match in re.finditer(r'#.*$', text_content, re.MULTILINE):
            start_index = self.code_input.index(f"1.0 + {match.start()}c")
            end_index = self.code_input.index(f"1.0 + {match.end()}c")
            self.code_input.tag_add('comment', start_index, end_index)

        # Apply string highlighting (simple version for single/double quotes)
        for match in re.finditer(r'(".*?"|\'.*?\')', text_content, re.DOTALL):
            start_index = self.code_input.index(f"1.0 + {match.start()}c")
            end_index = self.code_input.index(f"1.0 + {match.end()}c")
            self.code_input.tag_add('string', start_index, end_index)


if __name__ == "__main__":
    app = PDE()
    app.mainloop()
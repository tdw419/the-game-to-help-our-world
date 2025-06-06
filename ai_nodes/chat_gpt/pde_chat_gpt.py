import tkinter as tk
from tkinter import scrolledtext, filedialog
import contextlib
import io
import json
from datetime import datetime
from pathlib import Path

LOG_FILE = "pde_log.json"

def save_log(entry):
    try:
        logs = []
        if Path(LOG_FILE).exists():
            with open(LOG_FILE, "r") as f:
                logs = json.load(f)
        logs.append(entry)
        with open(LOG_FILE, "w") as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save log: {e}")

def run_code():
    code = code_input.get("1.0", tk.END)
    output_stream = io.StringIO()
    with contextlib.redirect_stdout(output_stream):
        try:
            exec(code, {})
        except Exception as e:
            print(f"Error: {e}")
    output = output_stream.getvalue()
    output_display.delete("1.0", tk.END)
    output_display.insert(tk.END, output)
    save_log({
        "timestamp": datetime.utcnow().isoformat(),
        "code": code.strip(),
        "output": output.strip()
    })

def load_script():
    filepath = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
    if filepath:
        with open(filepath, "r") as f:
            code_input.delete("1.0", tk.END)
            code_input.insert(tk.END, f.read())

def save_script():
    filepath = filedialog.asksaveasfilename(defaultextension=".py",
                                             filetypes=[("Python Files", "*.py")])
    if filepath:
        with open(filepath, "w") as f:
            f.write(code_input.get("1.0", tk.END))

# GUI Setup
window = tk.Tk()
window.title("Python Development Environment (PDE) v0.4.1")

tk.Label(window, text="Enter Python Code:").pack()
code_input = scrolledtext.ScrolledText(window, height=10, width=90)
code_input.pack()

button_frame = tk.Frame(window)
button_frame.pack(pady=5)

tk.Button(button_frame, text="Run Code", command=run_code).grid(row=0, column=0, padx=5)
tk.Button(button_frame, text="Save Script", command=save_script).grid(row=0, column=1, padx=5)
tk.Button(button_frame, text="Load Script", command=load_script).grid(row=0, column=2, padx=5)

tk.Label(window, text="Output:").pack()
output_display = scrolledtext.ScrolledText(window, height=10, width=90)
output_display.pack()

window.mainloop()

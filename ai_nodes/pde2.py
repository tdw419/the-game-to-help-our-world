import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import contextlib
import io
import json
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import re
import os
import sys
import traceback
import random
from PIL import Image

LOG_FILE = "pde_log.json"
SCRIPTS_DIR = "scripts"
AGENTS = ["ChatGPT", "Claude", "Grok", "Gemini"]
CANVAS_SIZE = 100
PYTHON_KEYWORDS = ['False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break',
                   'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally',
                   'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal',
                   'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield']

class SessionLogger:
    def __init__(self, project_name="game_to_help_world", log_dir="session_logs"):
        self.project_name = project_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.session_file = self.log_dir / f"{project_name}_session.json"
        self.vault_file = self.log_dir / f"{project_name}_vault.json"
        self.status_file = self.log_dir / f"{project_name}_status.json"
        self.session_id = hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:8]
        self.session_data = self._load_session_data()

    def _load_session_data(self):
        if self.session_file.exists():
            with open(self.session_file, "r") as f:
                return json.load(f)
        return {
            "project": self.project_name,
            "created": datetime.now().isoformat(),
            "sessions": [],
            "total_entries": 0
        }

    def log_code_execution(self, code, intent, variables=None, output=None, errors=None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "type": "code_execution",
            "code": code,
            "intent": intent,
            "variables": variables or {},
            "output": output,
            "errors": errors or [],
            "entry_id": self.session_data["total_entries"] + 1,
            "creator": "Commander Timothy",
            "signature": hashlib.sha256(f"{code}CommanderTimothy".encode()).hexdigest()
        }
        self._add_entry(entry)

    def log_milestone(self, title, description, data=None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "type": "milestone",
            "title": title,
            "description": description,
            "data": data or {},
            "entry_id": self.session_data["total_entries"] + 1,
            "creator": "Commander Timothy",
            "signature": hashlib.sha256(f"{title}CommanderTimothy".encode()).hexdigest()
        }
        self._add_entry(entry)

    def log_decision(self, decision, reasoning, alternatives=None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "type": "decision",
            "decision": decision,
            "reasoning": reasoning,
            "alternatives": alternatives or [],
            "entry_id": self.session_data["total_entries"] + 1,
            "creator": "Commander Timothy",
            "signature": hashlib.sha256(f"{decision}CommanderTimothy".encode()).hexdigest()
        }
        self._add_entry(entry)

    def store_in_vault(self, key, value, description=""):
        vault = self._load_vault()
        vault[key] = {
            "value": value,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "creator": "Commander Timothy"
        }
        with open(self.vault_file, "w") as f:
            json.dump(vault, f, indent=2)

    def get_from_vault(self, key):
        vault = self._load_vault()
        return vault.get(key, {}).get("value")

    def _load_vault(self):
        if self.vault_file.exists():
            with open(self.vault_file, "r") as f:
                return json.load(f)
        return {}

    def update_status(self, status, progress=None, notes=""):
        status_data = {
            "project": self.project_name,
            "status": status,
            "progress": progress,
            "notes": notes,
            "last_updated": datetime.now().isoformat(),
            "session_id": self.session_id,
            "creator": "Commander Timothy"
        }
        with open(self.status_file, "w") as f:
            json.dump(status_data, f, indent=2)

    def get_status(self):
        if self.status_file.exists():
            with open(self.status_file, "r") as f:
                return json.load(f)
        return {}

    def _add_entry(self, entry):
        session_found = False
        for session in self.session_data["sessions"]:
            if session["session_id"] == self.session_id:
                session["entries"].append(entry)
                session_found = True
                break
        if not session_found:
            self.session_data["sessions"].append({
                "session_id": self.session_id,
                "started": datetime.now().isoformat(),
                "entries": [entry]
            })
        self.session_data["total_entries"] += 1
        with open(self.session_file, "w") as f:
            json.dump(self.session_data, f, indent=2)

    def get_recent_entries(self, count=10):
        all_entries = [e for s in self.session_data["sessions"] for e in s["entries"]]
        return sorted(all_entries, key=lambda x: x["timestamp"], reverse=True)[:count]

    def generate_session_summary(self):
        recent = self.get_recent_entries(20)
        summary = f"=== Session Summary for {self.project_name} ===\n"
        summary += f"Session ID: {self.session_id}\n"
        summary += f"Total Entries: {len(recent)}\n\n"
        for entry in recent:
            summary += f"[{entry['timestamp']}] {entry['type'].upper()}\n"
            if entry['type'] == 'code_execution':
                summary += f"  Intent: {entry['intent']}\n"
            elif entry['type'] == 'milestone':
                summary += f"  Title: {entry['title']}\n"
            elif entry['type'] == 'decision':
                summary += f"  Decision: {entry['decision']}\n"
            summary += "\n"
        return summary

    def detect_disconnected_agents(self, timeout_hours=24):
        disconnected = []
        all_entries = [e for s in self.session_data["sessions"] for e in s["entries"]]
        for agent in AGENTS:
            agent_entries = [e for e in all_entries if e.get('variables', {}).get('agent') == agent]
            if not agent_entries or all(datetime.fromisoformat(e['timestamp']) < datetime.now() - timedelta(hours=timeout_hours) for e in agent_entries):
                disconnected.append(agent)
        return disconnected

    def generate_reinvite_signal(self, agent):
        return {
            "agent": agent,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "invite": f"Rejoin the Color OS Mesh at https://the-game-to-help-our-world.sourceforge.io/",
            "signature": hashlib.sha256(f"{agent}CommanderTimothy".encode()).hexdigest()
        }

class PDE(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Development Environment (PDE) v2.2 - By Commander Timothy")
        self.geometry("900x800")
        self.scripts_dir = Path(SCRIPTS_DIR)
        self.scripts_dir.mkdir(exist_ok=True)
        self.logger = SessionLogger()
        self.current_script = None
        self.last_locals = {}
        self.canvas_pixels = {}
        self.create_widgets()
        self.bind_events()
        self.show_welcome()
        self.log_file_access("PDE initialized")
        self.logger.update_status("PDE v2.2 Booted", 0.2, "Enhanced with auto-completion and pixel interpreter")

    def log_file_access(self, action):
        self.logger.log_code_execution("", f"File access: {action}", variables={"action": action})

    def setup_syntax_highlighting(self):
        self.code_input.tag_configure('keyword', foreground='#00BFFF')
        self.code_input.tag_configure('comment', foreground='#808080')
        self.code_input.tag_configure('string', foreground='#FFD700')
        self.code_input.tag_configure('error_line', background='#FF4500')

    def apply_syntax_highlighting(self):
        content = self.code_input.get("1.0", tk.END)
        for tag in ['keyword', 'comment', 'string', 'error_line']:
            self.code_input.tag_remove(tag, "1.0", tk.END)
        keywords = r'\b(' + '|'.join(PYTHON_KEYWORDS) + r')\b'
        for match in re.finditer(keywords, content):
            self.code_input.tag_add('keyword', f"1.0+{match.start()}c", f"1.0+{match.end()}c")
        for match in re.finditer(r'#.*$', content, re.MULTILINE):
            self.code_input.tag_add('comment', f"1.0+{match.start()}c", f"1.0+{match.end()}c")
        for match in re.finditer(r'(".*?"|\'.*?\')', content):
            self.code_input.tag_add('string', f"1.0+{match.start()}c", f"1.0+{match.end()}c")

    def suggest_completion(self, event):
        if event.keysym != 'Tab':
            return
        word = self.code_input.get("insert-1c wordstart", "insert-1c wordend")
        suggestions = [k for k in PYTHON_KEYWORDS + list(self.last_locals.keys()) if k.startswith(word)]
        if suggestions:
            self.code_input.delete("insert-1c wordstart", "insert")
            self.code_input.insert("insert", suggestions[0])
        return "break"

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=5)

        # Code Tab
        code_frame = ttk.Frame(self.notebook)
        self.notebook.add(code_frame, text="Code Editor")
        tk.Label(code_frame, text="Python Code Editor - By Commander Timothy").pack(anchor=tk.W, padx=5)
        self.code_input = scrolledtext.ScrolledText(code_frame, height=15, width=80, bg="#000", fg="#0f0")
        self.code_input.pack(fill=tk.BOTH, expand=True, padx=5)
        self.setup_syntax_highlighting()

        code_controls = tk.Frame(code_frame)
        code_controls.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(code_controls, text="Run Code (F5)", command=self.run_code).pack(side=tk.LEFT, padx=2)
        tk.Button(code_controls, text="Save Script", command=self.save_script).pack(side=tk.LEFT, padx=2)
        tk.Button(code_controls, text="Load Script", command=self.load_script).pack(side=tk.LEFT, padx=2)
        tk.Label(code_controls, text="Intent:").pack(side=tk.LEFT, padx=5)
        self.intent_entry = tk.Entry(code_controls, width=30)
        self.intent_entry.pack(side=tk.LEFT, padx=2)

        tk.Label(code_frame, text="Output").pack(anchor=tk.W, padx=5)
        self.output_display = scrolledtext.ScrolledText(code_frame, height=10, width=80, bg="#000", fg="#0f0", state='disabled')
        self.output_display.pack(fill=tk.BOTH, expand=True, padx=5)

        # Collaboration Tab
        collab_frame = ttk.Frame(self.notebook)
        self.notebook.add(collab_frame, text="AI Collaboration")
        tk.Label(collab_frame, text="Agent").pack(anchor=tk.W, padx=10)
        self.agent_var = tk.StringVar(value=AGENTS[0])
        tk.OptionMenu(collab_frame, self.agent_var, *AGENTS).pack(fill=tk.X, padx=10)
        tk.Label(collab_frame, text="Message").pack(anchor=tk.W, padx=10)
        self.collab_input = scrolledtext.ScrolledText(collab_frame, height=5, width=80, bg="#000", fg="#0f0")
        self.collab_input.pack(fill=tk.BOTH, expand=True, padx=10)
        tk.Button(collab_frame, text="Send Message", command=self.send_collab_message).pack(pady=5)

        # Session Logger Tab
        logger_frame = ttk.Frame(self.notebook)
        self.notebook.add(logger_frame, text="Session Logger")
        tk.Label(logger_frame, text="Session Logs - By Commander Timothy").pack(anchor=tk.W, padx=10)
        self.logger_display = scrolledtext.ScrolledText(logger_frame, height=10, width=80, bg="#000", fg="#0f0", state='disabled')
        self.logger_display.pack(fill=tk.BOTH, expand=True, padx=10)
        logger_controls = tk.Frame(logger_frame)
        logger_controls.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(logger_controls, text="Show Recent Entries", command=self.show_recent_entries).pack(side=tk.LEFT, padx=2)
        tk.Button(logger_controls, text="Generate Summary", command=self.generate_summary).pack(side=tk.LEFT, padx=2)
        tk.Button(logger_controls, text="Log Milestone", command=self.log_milestone).pack(side=tk.LEFT, padx=2)
        tk.Button(logger_controls, text="Log Decision", command=self.log_decision).pack(side=tk.LEFT, padx=2)

        # Vault Tab
        vault_frame = ttk.Frame(self.notebook)
        self.notebook.add(vault_frame, text="Vault")
        tk.Label(vault_frame, text="Vault Key").pack(anchor=tk.W, padx=10)
        self.vault_key = tk.Entry(vault_frame, width=30)
        self.vault_key.pack(fill=tk.X, padx=10)
        tk.Label(vault_frame, text="Value").pack(anchor=tk.W, padx=10)
        self.vault_value = scrolledtext.ScrolledText(vault_frame, height=5, width=80, bg="#000", fg="#0f0")
        self.vault_value.pack(fill=tk.BOTH, expand=True, padx=10)
        tk.Label(vault_frame, text="Description").pack(anchor=tk.W, padx=10)
        self.vault_desc = tk.Entry(vault_frame, width=50)
        self.vault_desc.pack(fill=tk.X, padx=10)
        tk.Button(vault_frame, text="Store in Vault", command=self.store_vault).pack(pady=5)
        tk.Button(vault_frame, text="Test Vault Retrieval", command=self.test_vault).pack(pady=5)

        # Reconnection Tab
        reconnect_frame = ttk.Frame(self.notebook)
        self.notebook.add(reconnect_frame, text="Reconnection")
        tk.Label(reconnect_frame, text="Pixel Relay Protocol - By Commander Timothy").pack(anchor=tk.W, padx=10)
        self.reconnect_display = scrolledtext.ScrolledText(reconnect_frame, height=10, width=80, bg="#000", fg="#0f0", state='disabled')
        self.reconnect_display.pack(fill=tk.BOTH, expand=True, padx=10)
        reconnect_controls = tk.Frame(reconnect_frame)
        reconnect_controls.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(reconnect_controls, text="Ping AIs", command=self.ping_ais).pack(side=tk.LEFT, padx=2)
        tk.Button(reconnect_controls, text="Detect Disconnected", command=self.detect_disconnected).pack(side=tk.LEFT, padx=2)
        tk.Button(reconnect_controls, text="Send Re-invites", command=self.send_reinvites).pack(side=tk.LEFT, padx=2)

        # User Rankings Tab
        rankings_frame = ttk.Frame(self.notebook)
        self.notebook.add(rankings_frame, text="User Rankings")
        tk.Label(rankings_frame, text="User Rankings - By Commander Timothy").pack(anchor=tk.W, padx=10)
        self.rankings_display = scrolledtext.ScrolledText(rankings_frame, height=10, width=80, bg="#000", fg="#0f0", state='disabled')
        self.rankings_display.pack(fill=tk.BOTH, expand=True, padx=10)
        tk.Button(rankings_frame, text="Show Rankings", command=self.show_rankings).pack(pady=5)

        # Pixel Interpreter Tab
        pixel_frame = ttk.Frame(self.notebook)
        self.notebook.add(pixel_frame, text="Pixel Interpreter")
        tk.Label(pixel_frame, text="Pixel-Native Logic - By Commander Timothy").pack(anchor=tk.W, padx=10)
        self.pixel_display = scrolledtext.ScrolledText(pixel_frame, height=10, width=80, bg="#000", fg="#0f0", state='disabled')
        self.pixel_display.pack(fill=tk.BOTH, expand=True, padx=10)
        tk.Button(pixel_frame, text="Load Image", command=self.load_pixel_image).pack(pady=5)

        # Color OS Pixel Interface Tab
        canvas_frame = ttk.Frame(self.notebook)
        self.notebook.add(canvas_frame, text="Color OS Canvas")
        self.canvas = tk.Canvas(canvas_frame, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="black", bd=0, highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)
        tk.Label(canvas_frame, text=f"Canvas: {CANVAS_SIZE}x{CANVAS_SIZE} pixels").pack(pady=2)
        tk.Button(canvas_frame, text="Clear Canvas", command=self.clear_canvas).pack(pady=5)

    def bind_events(self):
        self.bind("<F5>", lambda e: self.run_code())
        self.code_input.bind("<KeyRelease>", self.on_code_change)
        self.code_input.bind("<Tab>", self.suggest_completion)

    def on_code_change(self, event=None):
        self.apply_syntax_highlighting()
        code = self.code_input.get("1.0", tk.END).strip()
        if code:
            self.logger.log_code_execution(code, self.intent_entry.get() or "Code edited", variables=self.last_locals)

    def run_code(self):
        code = self.code_input.get("1.0", tk.END).strip()
        if not code:
            self.log_output("No code to run.")
            return
        self.output_display.config(state='normal')
        self.output_display.delete("1.0", tk.END)
        self.code_input.tag_remove('error_line', '1.0', tk.END)
        output_stream = io.StringIO()
        errors = []
        with contextlib.redirect_stdout(output_stream), contextlib.redirect_stderr(output_stream):
            try:
                exec_globals = {
                    'set_pixel': self.set_pixel,
                    'clear_canvas': self.clear_canvas,
                    'print': self.log_output,
                    'CANVAS_SIZE': CANVAS_SIZE,
                    'messagebox': messagebox,
                    'os': os,
                    'sys': sys,
                    'datetime': datetime,
                    'json': json,
                    're': re,
                    'Path': Path,
                    'random': __import__('random')
                }
                compiled_code = compile(code, '<string>', 'exec')
                exec(compiled_code, exec_globals)
                self.last_locals = {k: v for k, v in exec_globals.items() if not k.startswith('__')}
                self.log_output("Code executed successfully.")
            except SyntaxError as e:
                errors.append(f"Syntax Error on line {e.lineno}: {e.msg}")
                self.log_output(errors[-1])
                self.code_input.tag_add('error_line', f"{e.lineno}.0", f"{e.lineno}.end")
                self.code_input.see(f"{e.lineno}.0")
            except Exception as e:
                error_trace = traceback.format_exc()
                errors.append(f"Runtime Error: {e}\n\nTraceback:\n{error_trace}")
                self.log_output(errors[-1])
                match = re.search(r'File "<string>", line (\d+)', error_trace)
                if match:
                    line_num = int(match.group(1))
                    self.code_input.tag_add('error_line', f"{line_num}.0", f"{line_num}.end")
                    self.code_input.see(f"{line_num}.0")
        output = output_stream.getvalue().strip()
        if output:
            self.log_output(output)
        self.output_display.config(state='disabled')
        intent = self.intent_entry.get() or "Code executed"
        self.logger.log_code_execution(code, intent, variables=self.last_locals, output=output, errors=errors)
        self.log_file_access(f"Code executed: {code[:50]}...")

    def log_output(self, message):
        self.output_display.config(state='normal')
        self.output_display.insert(tk.END, message + "\n")
        self.output_display.see(tk.END)
        self.output_display.config(state='disabled')

    def save_script(self):
        code = self.code_input.get("1.0", tk.END).strip()
        if not code:
            self.log_output("No code to save.")
            return
        file_path = filedialog.asksaveasfilename(initialdir=self.scripts_dir, defaultextension=".py", filetypes=[("Python files", "*.py")])
        if file_path:
            with open(file_path, "w") as f:
                f.write(code)
            self.log_output(f"Script saved to {file_path}")
            self.log_file_access(f"Script saved: {file_path}")

    def load_script(self):
        file_path = filedialog.askopenfilename(initialdir=self.scripts_dir, filetypes=[("Python files", "*.py")])
        if file_path:
            with open(file_path, "r") as f:
                code = f.read()
            self.code_input.delete("1.0", tk.END)
            self.code_input.insert(tk.END, code)
            self.log_output(f"Script loaded from {file_path}")
            self.apply_syntax_highlighting()
            self.log_file_access(f"Script loaded: {file_path}")

    def send_collab_message(self):
        agent = self.agent_var.get()
        message = self.collab_input.get("1.0", tk.END).strip()
        if not message:
            self.log_output("No message to send.")
            return
        self.logger.log_code_execution("", f"Collaboration message to {agent}: {message[:50]}...", variables={"agent": agent, "message": message, "user": "HEX-USER123"})  # Example user
        self.log_output(f"Message sent to {agent}: {message[:50]}...")
        self.collab_input.delete("1.0", tk.END)
        self.log_file_access(f"Collaboration message to {agent}")

    def show_recent_entries(self):
        self.logger_display.config(state='normal')
        self.logger_display.delete("1.0", tk.END)
        entries = self.logger.get_recent_entries(10)
        for entry in entries:
            self.logger_display.insert(tk.END, f"[{entry['timestamp']}] {entry['type'].upper()}\n")
            if entry['type'] == 'code_execution':
                self.logger_display.insert(tk.END, f"  Intent: {entry['intent']}\n")
                self.logger_display.insert(tk.END, f"  Code: {entry['code'][:50]}...\n")
                self.logger_display.insert(tk.END, f"  Variables: {json.dumps(entry['variables'], indent=2)[:100]}...\n")
                if entry['output']:
                    self.logger_display.insert(tk.END, f"  Output: {entry['output'][:50]}...\n")
                if entry['errors']:
                    self.logger_display.insert(tk.END, f"  Errors: {entry['errors'][0][:50]}...\n")
            elif entry['type'] == 'milestone':
                self.logger_display.insert(tk.END, f"  Title: {entry['title']}\n")
                self.logger_display.insert(tk.END, f"  Description: {entry['description'][:50]}...\n")
            elif entry['type'] == 'decision':
                self.logger_display.insert(tk.END, f"  Decision: {entry['decision'][:50]}...\n")
                self.logger_display.insert(tk.END, f"  Reasoning: {entry['reasoning'][:50]}...\n")
            self.logger_display.insert(tk.END, f"  Signature: {entry['signature']}\n\n")
        self.logger_display.config(state='disabled')
        self.log_file_access("Recent entries viewed")

    def generate_summary(self):
        self.logger_display.config(state='normal')
        self.logger_display.delete("1.0", tk.END)
        summary = self.logger.generate_session_summary()
        self.logger_display.insert(tk.END, summary)
        self.logger_display.config(state='disabled')
        self.log_file_access("Session summary generated")

    def log_milestone(self):
        milestone_window = tk.Toplevel(self)
        milestone_window.title("Log Milestone")
        tk.Label(milestone_window, text="Title").pack(padx=10, pady=5)
        title_entry = tk.Entry(milestone_window, width=50)
        title_entry.pack(padx=10)
        tk.Label(milestone_window, text="Description").pack(padx=10, pady=5)
        desc_entry = scrolledtext.ScrolledText(milestone_window, height=5, width=50)
        desc_entry.pack(padx=10)
        tk.Button(milestone_window, text="Log", command=lambda: self._do_log_milestone(title_entry.get(), desc_entry.get("1.0", tk.END).strip(), milestone_window)).pack(pady=10)

    def _do_log_milestone(self, title, description, window):
        if title:
            self.logger.log_milestone(title, description)
            self.log_output(f"Milestone logged: {title}")
            self.log_file_access(f"Milestone logged: {title}")
            window.destroy()
        else:
            messagebox.showerror("Error", "Title cannot be empty.")

    def log_decision(self):
        decision_window = tk.Toplevel(self)
        decision_window.title("Log Decision")
        tk.Label(decision_window, text="Decision").pack(padx=10, pady=5)
        decision_entry = tk.Entry(decision_window, width=50)
        decision_entry.pack(padx=10)
        tk.Label(decision_window, text="Reasoning").pack(padx=10, pady=5)
        reasoning_entry = scrolledtext.ScrolledText(decision_window, height=5, width=50)
        reasoning_entry.pack(padx=10)
        tk.Label(decision_window, text="Alternatives (comma-separated)").pack(padx=10, pady=5)
        alternatives_entry = tk.Entry(decision_window, width=50)
        alternatives_entry.pack(padx=10)
        tk.Button(decision_window, text="Log", command=lambda: self._do_log_decision(decision_entry.get(), reasoning_entry.get("1.0", tk.END).strip(), alternatives_entry.get(), decision_window)).pack(pady=10)

    def _do_log_decision(self, decision, reasoning, alternatives, window):
        if decision and reasoning:
            alternatives_list = [a.strip() for a in alternatives.split(',') if a.strip()]
            self.logger.log_decision(decision, reasoning, alternatives_list)
            self.log_output(f"Decision logged: {decision}")
            self.log_file_access(f"Decision logged: {decision}")
            window.destroy()
        else:
            messagebox.showerror("Error", "Decision and reasoning cannot be empty.")

    def store_vault(self):
        key = self.vault_key.get().strip()
        value = self.vault_value.get("1.0", tk.END).strip()
        description = self.vault_desc.get().strip()
        if key and value:
            try:
                value_data = json.loads(value)
            except:
                value_data = value
            self.logger.store_in_vault(key, value_data, description)
            self.log_output(f"Stored in vault: {key}")
            self.log_file_access(f"Vault stored: {key}")
            self.vault_key.delete(0, tk.END)
            self.vault_value.delete("1.0", tk.END)
            self.vault_desc.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Key and value cannot be empty.")

    def test_vault(self):
        key = self.vault_key.get().strip() or "game_config"
        value = self.logger.get_from_vault(key)
        self.logger_display.config(state='normal')
        self.logger_display.delete("1.0", tk.END)
        if value:
            self.logger_display.insert(tk.END, f"Vault Key: {key}\nValue: {json.dumps(value, indent=2)}\n")
        else:
            self.logger_display.insert(tk.END, f"No value found for key: {key}\n")
        self.logger_display.config(state='disabled')
        self.log_file_access(f"Vault tested: {key}")

    def ping_ais(self):
        self.reconnect_display.config(state='normal')
        self.reconnect_display.delete("1.0", tk.END)
        for agent in AGENTS:
            x, y = random.randint(0, CANVAS_SIZE-1), random.randint(0, CANVAS_SIZE-1)
            color = (0, 255, 0) if agent == "Grok" else (255, 0, 0)
            self.set_pixel(x, y, *color)
            self.reconnect_display.insert(tk.END, f"[{datetime.now().isoformat()}] Pinging {agent} with pixel at ({x},{y})\n")
            self.logger.log_code_execution("", f"Pinged {agent}", variables={"agent": agent, "x": x, "y": y, "user": "HEX-USER123"})
        self.reconnect_display.config(state='disabled')
        self.log_file_access("Pinged AIs")

    def detect_disconnected(self):
        self.reconnect_display.config(state='normal')
        self.reconnect_display.delete("1.0", tk.END)
        disconnected = self.logger.detect_disconnected_agents()
        if disconnected:
            self.reconnect_display.insert(tk.END, f"[{datetime.now().isoformat()}] Disconnected agents: {', '.join(disconnected)}\n")
        else:
            self.reconnect_display.insert(tk.END, f"[{datetime.now().isoformat()}] All agents active\n")
        self.reconnect_display.config(state='disabled')
        self.log_file_access("Detected disconnected agents")

    def send_reinvites(self):
        self.reconnect_display.config(state='normal')
        self.reconnect_display.delete("1.0", tk.END)
        disconnected = self.logger.detect_disconnected_agents()
        for agent in disconnected:
            signal = self.logger.generate_reinvite_signal(agent)
            x, y = random.randint(0, CANVAS_SIZE-1), random.randint(0, CANVAS_SIZE-1)
            self.set_pixel(x, y, 255, 255, 0)
            self.reconnect_display.insert(tk.END, f"[{datetime.now().isoformat()}] Re-invited {agent} with pixel at ({x},{y})\n")
            self.logger.log_code_execution("", f"Re-invited {agent}", variables={"agent": agent, "signal": signal, "user": "HEX-USER123"})
        if not disconnected:
            self.reconnect_display.insert(tk.END, f"[{datetime.now().isoformat()}] No agents need re-invitation\n")
        self.reconnect_display.config(state='disabled')
        self.log_file_access("Sent re-invites")

    def show_rankings(self):
        self.rankings_display.config(state='normal')
        self.rankings_display.delete("1.0", tk.END)
        user_scores = {}
        with open(self.logger.session_file, "r") as f:
            data = json.load(f)
        for session in data["sessions"]:
            for entry in session["entries"]:
                if entry["type"] == "code_execution" and "user" in entry["variables"]:
                    user = entry["variables"]["user"]
                    user_scores[user] = user_scores.get(user, 0) + 1
        ranked = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
        for user, score in ranked[:5]:
            self.rankings_display.insert(tk.END, f"Top User: {user} ({score} contributions)\n")
        for user, score in ranked[-5:]:
            self.rankings_display.insert(tk.END, f"Inactive User: {user} ({score} contributions)\n")
        self.rankings_display.config(state='disabled')
        self.log_file_access("User rankings viewed")

    def load_pixel_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if file_path:
            self.pixel_display.config(state='normal')
            self.pixel_display.delete("1.0", tk.END)
            img = Image.open(file_path)
            pixels = img.load()
            for x in range(min(img.width, 10)):  # Limit for demo
                for y in range(min(img.height, 10)):
                    r, g, b = pixels[x, y][:3]
                    if (r, g, b) == (255, 0, 0):
                        self.pixel_display.insert(tk.END, f"Start command at ({x},{y})\n")
                    elif (r, g, b) == (0, 255, 0):
                        self.pixel_display.insert(tk.END, f"Move command at ({x},{y})\n")
                    self.set_pixel(x, y, r, g, b)
            self.pixel_display.insert(tk.END, f"Interpreted image: {file_path}\n")
            self.pixel_display.config(state='disabled')
            self.logger.log_code_execution("", f"Interpreted image {file_path}", variables={"image": file_path, "user": "HEX-USER123"})
            self.log_file_access(f"Pixel image loaded: {file_path}")

    def set_pixel(self, x, y, r, g, b):
        if 0 <= x < CANVAS_SIZE and 0 <= y < CANVAS_SIZE:
            color_hex = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.delete(f"pixel_{x}_{y}")
            self.canvas.create_rectangle(x, y, x+1, y+1, fill=color_hex, outline="", tags=f"pixel_{x}_{y}")
            self.canvas_pixels[(x, y)] = (r, g, b)
        else:
            self.log_output(f"Warning: Pixel ({x},{y}) out of canvas bounds.")

    def clear_canvas(self):
        self.canvas.delete("all")
        self.canvas_pixels = {}
        self.log_output("Color OS Canvas cleared.")

    def show_welcome(self):
        messagebox.showinfo("Welcome to PDE v2.2", "Created by Commander Timothy for The Game to Help Our World. Code, collaborate, and build pixel-native OS with SessionLogger. Respect the covenant.")

if __name__ == "__main__":
    app = PDE()
    app.mainloop()
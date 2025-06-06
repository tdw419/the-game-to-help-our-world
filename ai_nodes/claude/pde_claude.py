import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk
import contextlib
import io
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
import threading
import time
import os
import re
import subprocess
import tempfile
import webbrowser
from urllib.parse import quote
import base64

class SyntaxHighlighter:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.setup_tags()
        
    def setup_tags(self):
        # Define syntax highlighting colors
        self.text_widget.tag_configure("keyword", foreground="#0000FF", font=("Consolas", 11, "bold"))
        self.text_widget.tag_configure("string", foreground="#008000")
        self.text_widget.tag_configure("comment", foreground="#808080", font=("Consolas", 11, "italic"))
        self.text_widget.tag_configure("number", foreground="#FF0000")
        self.text_widget.tag_configure("builtin", foreground="#800080")
        self.text_widget.tag_configure("operator", foreground="#000080")
        
    def highlight(self):
        content = self.text_widget.get("1.0", tk.END)
        
        # Clear existing tags
        for tag in ["keyword", "string", "comment", "number", "builtin", "operator"]:
            self.text_widget.tag_remove(tag, "1.0", tk.END)
        
        # Keywords
        keywords = r'\b(def|class|if|elif|else|for|while|try|except|finally|with|import|from|as|return|yield|break|continue|pass|raise|lambda|and|or|not|in|is|True|False|None)\b'
        for match in re.finditer(keywords, content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.text_widget.tag_add("keyword", start_idx, end_idx)
        
        # Strings
        string_patterns = [r'"[^"]*"', r"'[^']*'", r'""".*?"""', r"'''.*?'''"]
        for pattern in string_patterns:
            for match in re.finditer(pattern, content, re.DOTALL):
                start_idx = f"1.0+{match.start()}c"
                end_idx = f"1.0+{match.end()}c"
                self.text_widget.tag_add("string", start_idx, end_idx)
        
        # Comments
        for match in re.finditer(r'#.*', content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.text_widget.tag_add("comment", start_idx, end_idx)
        
        # Numbers
        for match in re.finditer(r'\b\d+\.?\d*\b', content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.text_widget.tag_add("number", start_idx, end_idx)
        
        # Built-ins
        builtins = r'\b(print|len|str|int|float|list|dict|set|tuple|range|enumerate|zip|map|filter|sorted|reversed|sum|max|min|abs|round|type|isinstance|hasattr|getattr|setattr|delattr)\b'
        for match in re.finditer(builtins, content):
            start_idx = f"1.0+{match.start()}c"
            end_idx = f"1.0+{match.end()}c"
            self.text_widget.tag_add("builtin", start_idx, end_idx)

class PackageManager:
    def __init__(self, parent):
        self.parent = parent
        
    def install_package(self, package_name):
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                                 capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return True, f"Successfully installed {package_name}"
            else:
                return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Installation timed out"
        except Exception as e:
            return False, str(e)
    
    def list_packages(self):
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                                 capture_output=True, text=True, timeout=10)
            return result.stdout if result.returncode == 0 else "Error listing packages"
        except Exception as e:
            return f"Error: {str(e)}"

class RichOutputViewer:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.setup_viewer()
        
    def setup_viewer(self):
        self.notebook = ttk.Notebook(self.parent_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Text output tab
        self.text_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.text_frame, text="Text Output")
        
        self.text_display = scrolledtext.ScrolledText(
            self.text_frame,
            font=("Consolas", 10),
            bg="#f8f8f8",
            state=tk.DISABLED
        )
        self.text_display.pack(fill=tk.BOTH, expand=True)
        
        # Plot viewer tab
        self.plot_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.plot_frame, text="Plots/Images")
        
        self.plot_label = ttk.Label(self.plot_frame, text="No plots to display")
        self.plot_label.pack(expand=True)
        
        # Data viewer tab
        self.data_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.data_frame, text="Data Tables")
        
        self.data_tree = ttk.Treeview(self.data_frame)
        data_scrollbar = ttk.Scrollbar(self.data_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
        self.data_tree.configure(yscrollcommand=data_scrollbar.set)
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        data_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def update_text_output(self, text):
        self.text_display.config(state=tk.NORMAL)
        self.text_display.delete("1.0", tk.END)
        self.text_display.insert(tk.END, text)
        self.text_display.config(state=tk.DISABLED)
        
    def display_plot(self, plot_data):
        # Placeholder for plot display - would integrate with matplotlib
        self.plot_label.config(text="Plot display would be implemented here")
        
    def display_data_table(self, data):
        # Clear existing data
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
            
        if isinstance(data, (list, tuple)) and data:
            # Configure columns based on first row
            if isinstance(data[0], dict):
                columns = list(data[0].keys())
                self.data_tree.config(columns=columns, show="headings")
                for col in columns:
                    self.data_tree.heading(col, text=col)
                    self.data_tree.column(col, width=100)
                
                # Insert data
                for item in data:
                    values = [str(item.get(col, "")) for col in columns]
                    self.data_tree.insert("", tk.END, values=values)

class ProjectManager:
    def __init__(self, parent):
        self.parent = parent
        self.current_project = None
        self.project_files = []
        
    def create_project(self, project_path):
        try:
            os.makedirs(project_path, exist_ok=True)
            self.current_project = project_path
            self.scan_project_files()
            return True, f"Project created at {project_path}"
        except Exception as e:
            return False, str(e)
            
    def scan_project_files(self):
        if not self.current_project:
            return
            
        self.project_files = []
        for root, dirs, files in os.walk(self.current_project):
            for file in files:
                if file.endswith(('.py', '.txt', '.md', '.json')):
                    self.project_files.append(os.path.join(root, file))

class PythonDevelopmentEnvironment:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Advanced Python Development Environment (PDE) v2.0")
        self.window.geometry("1400x900")
        
        self.log_file = "pde_log.json"
        self.current_file = None
        self.execution_history = []
        self.unsaved_changes = False
        
        # Initialize components
        self.package_manager = PackageManager(self)
        self.project_manager = ProjectManager(self)
        
        self.setup_gui()
        self.setup_keybindings()
        
        # Auto-save timer
        self.auto_save_timer = None
        
    def setup_gui(self):
        # Create main paned window
        main_paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for project explorer
        left_frame = ttk.Frame(main_paned, width=250)
        main_paned.add(left_frame, weight=1)
        
        # Right panel for main development area
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=4)
        
        # Setup components
        self.setup_project_explorer(left_frame)
        self.setup_main_area(right_frame)
        
        # Menu bar
        self.create_menu()
        
    def setup_project_explorer(self, parent):
        ttk.Label(parent, text="Project Explorer", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Project controls
        project_controls = ttk.Frame(parent)
        project_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(project_controls, text="New Project", command=self.new_project).pack(fill=tk.X, pady=2)
        ttk.Button(project_controls, text="Open Project", command=self.open_project).pack(fill=tk.X, pady=2)
        
        # File tree
        self.file_tree = ttk.Treeview(parent)
        file_scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=file_scrollbar.set)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=5)
        file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,5), pady=5)
        
        self.file_tree.bind('<Double-1>', self.on_file_double_click)
        
        # Package manager section
        ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(parent, text="Package Manager", font=("Arial", 10, "bold")).pack()
        
        pkg_frame = ttk.Frame(parent)
        pkg_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.pkg_entry = ttk.Entry(pkg_frame, placeholder_text="Package name")
        self.pkg_entry.pack(fill=tk.X, pady=2)
        
        ttk.Button(pkg_frame, text="Install Package", command=self.install_package).pack(fill=tk.X, pady=2)
        ttk.Button(pkg_frame, text="List Packages", command=self.list_packages).pack(fill=tk.X, pady=2)
        
    def setup_main_area(self, parent):
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(toolbar, text="New", command=self.new_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Open", command=self.open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_file).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(toolbar, text="Run (Ctrl+Enter)", command=self.run_code).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Debug", command=self.debug_code).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Stop", command=self.stop_execution).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(toolbar, text="Find/Replace", command=self.show_find_replace).pack(side=tk.LEFT, padx=2)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(toolbar, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.RIGHT, padx=5)
        
        # Main content area with vertical panes
        content_paned = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        content_paned.pack(fill=tk.BOTH, expand=True)
        
        # Top pane for code editor
        editor_frame = ttk.Frame(content_paned, height=400)
        content_paned.add(editor_frame, weight=3)
        
        # Bottom pane for output
        output_frame = ttk.Frame(content_paned, height=300)
        content_paned.add(output_frame, weight=2)
        
        self.setup_code_editor(editor_frame)
        self.setup_output_area(output_frame)
        
    def setup_code_editor(self, parent):
        # Code editor with line numbers
        editor_container = ttk.Frame(parent)
        editor_container.pack(fill=tk.BOTH, expand=True)
        
        # Line numbers frame
        line_frame = tk.Frame(editor_container, width=50, bg="#f0f0f0")
        line_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.line_numbers = tk.Text(
            line_frame, 
            width=4, 
            bg="#f0f0f0", 
            fg="#666666",
            state=tk.DISABLED,
            font=("Consolas", 11)
        )
        self.line_numbers.pack(fill=tk.Y, expand=True)
        
        # Code editor
        self.code_input = scrolledtext.ScrolledText(
            editor_container,
            font=("Consolas", 11),
            wrap=tk.NONE,
            undo=True,
            maxundo=50
        )
        self.code_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Syntax highlighting
        self.syntax_highlighter = SyntaxHighlighter(self.code_input)
        
        # Bind events for line numbers and syntax highlighting
        self.code_input.bind('<KeyRelease>', self.on_text_change)
        self.code_input.bind('<Button-1>', self.on_text_change)
        self.code_input.bind('<MouseWheel>', self.sync_scroll)
        
        # Auto-completion (basic)
        self.code_input.bind('<Tab>', self.handle_tab)
        
        self.update_line_numbers()
        
    def setup_output_area(self, parent):
        # Rich output viewer
        self.rich_output = RichOutputViewer(parent)
        
    def create_menu(self):
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New File", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open File", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_as_file, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find/Replace", command=self.show_find_replace, accelerator="Ctrl+F")
        edit_menu.add_command(label="Comment/Uncomment", command=self.toggle_comment, accelerator="Ctrl+/")
        
        # Run menu
        run_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Run", menu=run_menu)
        run_menu.add_command(label="Run Code", command=self.run_code, accelerator="Ctrl+Enter")
        run_menu.add_command(label="Debug Code", command=self.debug_code, accelerator="F5")
        run_menu.add_command(label="Stop Execution", command=self.stop_execution, accelerator="Ctrl+C")
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Package Manager", command=self.show_package_manager)
        tools_menu.add_command(label="Code Formatter", command=self.format_code)
        tools_menu.add_command(label="Export Project", command=self.export_project)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Reset Zoom", command=self.reset_zoom)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_command(label="About PDE", command=self.show_about)
        
    def setup_keybindings(self):
        # File operations
        self.window.bind('<Control-n>', lambda e: self.new_file())
        self.window.bind('<Control-o>', lambda e: self.open_file())
        self.window.bind('<Control-s>', lambda e: self.save_file())
        self.window.bind('<Control-Shift-S>', lambda e: self.save_as_file())
        
        # Edit operations
        self.window.bind('<Control-z>', lambda e: self.undo())
        self.window.bind('<Control-y>', lambda e: self.redo())
        self.window.bind('<Control-f>', lambda e: self.show_find_replace())
        self.window.bind('<Control-slash>', lambda e: self.toggle_comment())
        
        # Run operations
        self.window.bind('<Control-Return>', lambda e: self.run_code())
        self.window.bind('<F5>', lambda e: self.debug_code())
        self.window.bind('<Control-c>', lambda e: self.stop_execution())
        
        # View operations
        self.window.bind('<Control-plus>', lambda e: self.zoom_in())
        self.window.bind('<Control-minus>', lambda e: self.zoom_out())
        
        # Window closing
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def on_text_change(self, event=None):
        self.unsaved_changes = True
        self.update_line_numbers()
        
        # Schedule syntax highlighting
        if hasattr(self, '_highlight_after_id'):
            self.window.after_cancel(self._highlight_after_id)
        self._highlight_after_id = self.window.after(500, self.syntax_highlighter.highlight)
        
        # Auto-save timer
        if self.auto_save_timer:
            self.window.after_cancel(self.auto_save_timer)
        self.auto_save_timer = self.window.after(5000, self.auto_save)  # Auto-save every 5 seconds
        
    def update_line_numbers(self):
        line_count = int(self.code_input.index(tk.END).split('.')[0]) - 1
        line_numbers = '\n'.join(str(i) for i in range(1, line_count + 1))
        
        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.delete("1.0", tk.END)
        self.line_numbers.insert("1.0", line_numbers)
        self.line_numbers.config(state=tk.DISABLED)
        
    def sync_scroll(self, event):
        # Sync line numbers scrolling with code editor
        self.line_numbers.yview_moveto(self.code_input.yview()[0])
        
    def handle_tab(self, event):
        # Insert 4 spaces instead of tab
        self.code_input.insert(tk.INSERT, "    ")
        return "break"
        
    # File operations
    def new_file(self):
        if self.confirm_unsaved_changes():
            self.code_input.delete("1.0", tk.END)
            self.current_file = None
            self.unsaved_changes = False
            self.update_title()
            self.status_var.set("New file created")
            
    def open_file(self):
        if self.confirm_unsaved_changes():
            file_path = filedialog.askopenfilename(
                title="Open File",
                filetypes=[("Python files", "*.py"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            if file_path:
                self.load_file(file_path)
                
    def load_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.code_input.delete("1.0", tk.END)
                self.code_input.insert("1.0", content)
                self.current_file = file_path
                self.unsaved_changes = False
                self.update_title()
                self.status_var.set(f"Opened: {os.path.basename(file_path)}")
                self.syntax_highlighter.highlight()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")
            
    def save_file(self):
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_as_file()
            
    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(
            title="Save File",
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            self.save_to_file(file_path)
            self.current_file = file_path
            self.update_title()
            
    def save_to_file(self, file_path):
        try:
            content = self.code_input.get("1.0", tk.END)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            self.unsaved_changes = False
            self.status_var.set(f"Saved: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
            
    def auto_save(self):
        if self.current_file and self.unsaved_changes:
            try:
                content = self.code_input.get("1.0", tk.END)
                backup_path = self.current_file + ".backup"
                with open(backup_path, 'w', encoding='utf-8') as file:
                    file.write(content)
                self.status_var.set("Auto-saved backup")
            except Exception as e:
                pass  # Silent fail for auto-save
                
    def confirm_unsaved_changes(self):
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes", 
                "You have unsaved changes. Do you want to save them?"
            )
            if result is True:  # Yes
                self.save_file()
                return True
            elif result is False:  # No
                return True
            else:  # Cancel
                return False
        return True
        
    def update_title(self):
        title = "Advanced PDE v2.0"
        if self.current_file:
            filename = os.path.basename(self.current_file)
            title += f" - {filename}"
        if self.unsaved_changes:
            title += " *"
        self.window.title(title)
        
    # Edit operations
    def undo(self):
        try:
            self.code_input.edit_undo()
        except tk.TclError:
            pass
            
    def redo(self):
        try:
            self.code_input.edit_redo()
        except tk.TclError:
            pass
            
    def cut(self):
        try:
            self.code_input.event_generate("<<Cut>>")
        except tk.TclError:
            pass
            
    def copy(self):
        try:
            self.code_input.event_generate("<<Copy>>")
        except tk.TclError:
            pass
            
    def paste(self):
        try:
            self.code_input.event_generate("<<Paste>>")
        except tk.TclError:
            pass
            
    def toggle_comment(self):
        try:
            # Get selected text or current line
            if self.code_input.tag_ranges(tk.SEL):
                start_line = int(self.code_input.index(tk.SEL_FIRST).split('.')[0])
                end_line = int(self.code_input.index(tk.SEL_LAST).split('.')[0])
            else:
                start_line = end_line = int(self.code_input.index(tk.INSERT).split('.')[0])
            
            # Toggle comments for each line
            for line_num in range(start_line, end_line + 1):
                line_start = f"{line_num}.0"
                line_end = f"{line_num}.end"
                line_text = self.code_input.get(line_start, line_end)
                
                if line_text.strip().startswith('#'):
                    # Uncomment
                    new_text = line_text.replace('#', '', 1)
                else:
                    # Comment
                    new_text = '#' + line_text
                
                self.code_input.delete(line_start, line_end)
                self.code_input.insert(line_start, new_text)
                
        except Exception as e:
            pass
            
    # Code execution
    def run_code(self):
        code = self.code_input.get("1.0", tk.END).strip()
        if not code:
            return
            
        self.status_var.set("Executing...")
        self.window.update()
        
        # Run in separate thread
        self.execution_thread = threading.Thread(target=self.execute_code, args=(code,))
        self.execution_thread.daemon = True
        self.execution_thread.start()
        
    def execute_code(self, code):
        start_time = time.time()
        output_stream = io.StringIO()
        error_stream = io.StringIO()
        
        try:
            # Enhanced execution environment
            exec_globals = {
                '__builtins__': __builtins__,
                '__name__': '__main__',
                '__file__': self.current_file or '<untitled>',
                'print': self.enhanced_print,
                'display': self.display_data,
                'plot': self.display_plot,
            }
            
            # Capture matplotlib plots
            self.captured_output = {"text": "", "plots": [], "data": []}
            
            with contextlib.redirect_stdout(output_stream), contextlib.redirect_stderr(error_stream):
                exec(code, exec_globals)
                
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            output = output_stream.getvalue()
            error_output = error_stream.getvalue()
            
            if error_output:
                output += f"\nErrors:\n{error_output}"
                
            status = "Success" if not error_output else "Warning"
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            output = f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            status = "Error"
            
        # Update GUI in main thread
        self.window.after(0, self.update_execution_result, output, code, status, execution_time)
        
    def enhanced_print(self, *args, **kwargs):
        # Enhanced print that captures output for rich display
        output = io.StringIO()
        print(*args, file=output, **kwargs)
        text = output.getvalue()
        self.captured_output["text"] += text
        print(*args, **kwargs)  # Also print normally
        
    def display_data(self, data):
        # Function for displaying structured data
        self.captured_output["data"].append(data)
        
    def display_plot(self, plot_obj):
        # Function for displaying plots
        self.captured_output["plots"].append(plot_obj)
        
    def update_execution_result(self, output, code, status, execution_time):
        # Update rich output viewer
        self.rich_output.update_text_output(output)
        
        # Display any captured data
        if hasattr(self, 'captured_output') and self.captured_output["data"]:
            for data in self.captured_output["data"]:
                self.rich_output.display_data_table(data)
                
        # Log the execution
        self.save_log({
            "timestamp": datetime.now().isoformat(),
            "code": code,
            "output": output,
            "status": status,
            "execution_time_ms": round(execution_time, 2)
        })
        
        self.status_var.set(f"Execution completed ({status}) - {execution_time:.2f}ms")
        
    def debug_code(self):
        # Placeholder for debugging functionality
        messagebox.showinfo("Debug", "Debug functionality would be implemented here.\nFeatures:\n- Breakpoints\n- Step through\n- Variable inspection")
        
    def stop_execution(self):
        # Placeholder for stopping execution
        self.status_var.set("Execution stopped")
        
    # Project management
    def new_project(self):
        project_path = filedialog.askdirectory(title="Select Project Directory")
        if project_path:
            success, message = self.project_manager.create_project(project_path)
            if success:
                self.refresh_project_tree()
                self.status_var.set(message)
            else:
                messagebox.showerror("Error", message)
                
    def open_project(self):
        project_path = filedialog.askdirectory(title="Open Project Directory")
        if project_path:
            self.project_manager.current_project = project_path
            self.project_manager.scan_project_files()
            self.refresh_project_tree()
            self.status_var.set(f"Opened project: {os.path.basename(project_path)}")
            
    def refresh_project_tree(self):
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
            
        if not self.project_manager.current_project:
            return
            
        # Populate tree with project files
        project_root = self.project_manager.current_project
        root_item = self.file_tree.insert("", tk.END, text=os.path.basename(project_root), open=True)
        
        for file_path in self.project_manager.project_files:
            rel_path = os.path.relpath(file_path, project_root)
            self.file_tree.insert(root_item, tk.END, text=rel_path, values=[file_path])
            
    def on_file_double_click(self, event):
        item = self.file_tree.selection()[0]
        values = self.file_tree.item(item, "values")
        if values:
            file_path = values[0]
            if self.confirm_unsaved_changes():
                self.load_file(file_path)
                
    # Package management
    def install_package(self):
        package_name = self.pkg_entry.get().strip()
        if not package_name:
            messagebox.showwarning("Warning", "Please enter a package name")
            return
            
        self.status_var.set(f"Installing {package_name}...")
        self.window.update()
        
        # Run in thread to prevent GUI blocking
        thread = threading.Thread(target=self._install_package_thread, args=(package_name,))
        thread.daemon = True
        thread.start()
        
    def _install_package_thread(self, package_name):
        success, message = self.package_manager.install_package(package_name)
        self.window.after(0, self._install_package_callback, success, message, package_name)
        
    def _install_package_callback(self, success, message, package_name):
        if success:
            self.status_var.set(f"Successfully installed {package_name}")
            self.pkg_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Installation Error", message)
            self.status_var.set("Installation failed")
            
    def list_packages(self):
        packages = self.package_manager.list_packages()
        
        # Show in new window
        pkg_window = tk.Toplevel(self.window)
        pkg_window.title("Installed Packages")
        pkg_window.geometry("600x400")
        
        text_widget = scrolledtext.ScrolledText(pkg_window, font=("Consolas", 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, packages)
        text_widget.config(state=tk.DISABLED)
        
    def show_package_manager(self):
        # Advanced package manager window
        pkg_window = tk.Toplevel(self.window)
        pkg_window.title("Advanced Package Manager")
        pkg_window.geometry("700x500")
        
        # Package list
        pkg_frame = ttk.Frame(pkg_window)
        pkg_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(pkg_frame, text="Package Management", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Install section
        install_frame = ttk.LabelFrame(pkg_frame, text="Install Package")
        install_frame.pack(fill=tk.X, pady=5)
        
        entry_frame = ttk.Frame(install_frame)
        entry_frame.pack(fill=tk.X, padx=10, pady=5)
        
        pkg_entry = ttk.Entry(entry_frame)
        pkg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(entry_frame, text="Install", 
                  command=lambda: self._install_from_dialog(pkg_entry.get())).pack(side=tk.RIGHT)
        
        # Requirements.txt section
        req_frame = ttk.LabelFrame(pkg_frame, text="Requirements")
        req_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        req_text = scrolledtext.ScrolledText(req_frame, height=10)
        req_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        req_buttons = ttk.Frame(req_frame)
        req_buttons.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(req_buttons, text="Generate requirements.txt", 
                  command=lambda: self.generate_requirements(req_text)).pack(side=tk.LEFT, padx=2)
        ttk.Button(req_buttons, text="Install from requirements.txt", 
                  command=lambda: self.install_requirements(req_text.get("1.0", tk.END))).pack(side=tk.LEFT, padx=2)
        
    def _install_from_dialog(self, package_name):
        if package_name.strip():
            self._install_package_thread(package_name.strip())
            
    def generate_requirements(self, text_widget):
        packages = self.package_manager.list_packages()
        # Parse and format as requirements.txt
        lines = packages.split('\n')[2:]  # Skip header
        requirements = []
        for line in lines:
            if line.strip() and not line.startswith('-'):
                parts = line.split()
                if len(parts) >= 2:
                    requirements.append(f"{parts[0]}=={parts[1]}")
        
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", '\n'.join(requirements))
        
    def install_requirements(self, requirements_text):
        # Install packages from requirements text
        lines = [line.strip() for line in requirements_text.split('\n') if line.strip()]
        for line in lines:
            if line and not line.startswith('#'):
                package = line.split('==')[0].split('>=')[0].split('<=')[0]
                self._install_package_thread(package)
                
    # Find/Replace functionality
    def show_find_replace(self):
        find_window = tk.Toplevel(self.window)
        find_window.title("Find and Replace")
        find_window.geometry("400x200")
        find_window.transient(self.window)
        
        # Find section
        find_frame = ttk.Frame(find_window)
        find_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(find_frame, text="Find:").pack(anchor=tk.W)
        find_entry = ttk.Entry(find_frame)
        find_entry.pack(fill=tk.X, pady=2)
        
        ttk.Label(find_frame, text="Replace:").pack(anchor=tk.W, pady=(10,0))
        replace_entry = ttk.Entry(find_frame)
        replace_entry.pack(fill=tk.X, pady=2)
        
        # Options
        options_frame = ttk.Frame(find_window)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        case_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Match case", variable=case_var).pack(anchor=tk.W)
        
        whole_word_var = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Whole word", variable=whole_word_var).pack(anchor=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(find_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Find Next", 
                  command=lambda: self.find_text(find_entry.get(), case_var.get(), whole_word_var.get())).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Replace", 
                  command=lambda: self.replace_text(find_entry.get(), replace_entry.get())).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Replace All", 
                  command=lambda: self.replace_all_text(find_entry.get(), replace_entry.get())).pack(side=tk.LEFT, padx=2)
                  
    def find_text(self, search_text, match_case=False, whole_word=False):
        if not search_text:
            return
            
        # Simple find implementation
        start_pos = self.code_input.search(search_text, tk.INSERT, tk.END, 
                                         nocase=not match_case, regexp=whole_word)
        if start_pos:
            end_pos = f"{start_pos}+{len(search_text)}c"
            self.code_input.tag_remove(tk.SEL, "1.0", tk.END)
            self.code_input.tag_add(tk.SEL, start_pos, end_pos)
            self.code_input.mark_set(tk.INSERT, end_pos)
            self.code_input.see(start_pos)
            
    def replace_text(self, find_text, replace_text):
        if self.code_input.tag_ranges(tk.SEL):
            self.code_input.delete(tk.SEL_FIRST, tk.SEL_LAST)
            self.code_input.insert(tk.INSERT, replace_text)
            
    def replace_all_text(self, find_text, replace_text):
        content = self.code_input.get("1.0", tk.END)
        new_content = content.replace(find_text, replace_text)
        self.code_input.delete("1.0", tk.END)
        self.code_input.insert("1.0", new_content)
        
    # Code formatting
    def format_code(self):
        try:
            import autopep8
            code = self.code_input.get("1.0", tk.END)
            formatted_code = autopep8.fix_code(code)
            self.code_input.delete("1.0", tk.END)
            self.code_input.insert("1.0", formatted_code)
            self.status_var.set("Code formatted")
        except ImportError:
            messagebox.showinfo("Info", "autopep8 not installed. Install it via Package Manager to use code formatting.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to format code: {str(e)}")
            
    # View operations
    def zoom_in(self):
        current_font = self.code_input.cget("font")
        if isinstance(current_font, str):
            font_family, size = "Consolas", 11
        else:
            font_family, size = current_font[0], current_font[1]
        new_size = min(size + 1, 20)
        self.code_input.config(font=(font_family, new_size))
        self.line_numbers.config(font=(font_family, new_size))
        
    def zoom_out(self):
        current_font = self.code_input.cget("font")
        if isinstance(current_font, str):
            font_family, size = "Consolas", 11
        else:
            font_family, size = current_font[0], current_font[1]
        new_size = max(size - 1, 8)
        self.code_input.config(font=(font_family, new_size))
        self.line_numbers.config(font=(font_family, new_size))
        
    def reset_zoom(self):
        self.code_input.config(font=("Consolas", 11))
        self.line_numbers.config(font=("Consolas", 11))
        
    # Export functionality
    def export_project(self):
        if not self.project_manager.current_project:
            messagebox.showwarning("Warning", "No project open")
            return
            
        export_path = filedialog.asksaveasfilename(
            title="Export Project",
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip")]
        )
        
        if export_path:
            try:
                import zipfile
                with zipfile.ZipFile(export_path, 'w') as zipf:
                    project_root = Path(self.project_manager.current_project)
                    for file_path in self.project_manager.project_files:
                        arcname = os.path.relpath(file_path, project_root)
                        zipf.write(file_path, arcname)
                self.status_var.set(f"Project exported to {os.path.basename(export_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export project: {str(e)}")
                
    # Help functions
    def show_shortcuts(self):
        shortcuts_text = """
Keyboard Shortcuts:

File Operations:
Ctrl+N - New File
Ctrl+O - Open File
Ctrl+S - Save File
Ctrl+Shift+S - Save As

Edit Operations:
Ctrl+Z - Undo
Ctrl+Y - Redo
Ctrl+X - Cut
Ctrl+C - Copy
Ctrl+V - Paste
Ctrl+F - Find/Replace
Ctrl+/ - Comment/Uncomment

Run Operations:
Ctrl+Enter - Run Code
F5 - Debug Code
Ctrl+C - Stop Execution

View Operations:
Ctrl++ - Zoom In
Ctrl+- - Zoom Out

Other:
Tab - Insert 4 spaces
        """
        
        help_window = tk.Toplevel(self.window)
        help_window.title("Keyboard Shortcuts")
        help_window.geometry("400x500")
        
        text_widget = scrolledtext.ScrolledText(help_window, font=("Arial", 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, shortcuts_text)
        text_widget.config(state=tk.DISABLED)
        
    def show_about(self):
        about_text = """
Advanced Python Development Environment (PDE) v2.0

Features:
• Full-featured code editor with syntax highlighting
• Project management and file explorer
• Integrated package manager
• Rich output display for text, plots, and data
• Advanced find/replace functionality
• Code formatting and debugging tools
• Auto-save and backup functionality
• Customizable interface with zoom controls

Built for rapid Python development and AI-assisted coding.
        """
        
        messagebox.showinfo("About PDE", about_text)
        
    # Logging
    def save_log(self, entry):
        try:
            log_path = Path(self.log_file)
            if log_path.exists():
                with open(log_path, "r", encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
                
            logs.append(entry)
            
            # Keep only last 1000 entries
            if len(logs) > 1000:
                logs = logs[-1000:]
                
            with open(log_path, "w", encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Failed to save log: {e}")
            
    def on_closing(self):
        if self.confirm_unsaved_changes():
            self.window.destroy()
            
    def run(self):
        # Show welcome message
        welcome_code = '''# Welcome to Advanced Python Development Environment v2.0!
# 
# Features:
# - Syntax highlighting
# - Project management  
# - Package manager
# - Rich output display
# - Auto-save functionality
# - Find/replace tools
# - Code formatting
# - And much more!
#
# Try running some Python code:

print("Hello from PDE v2.0!")
print("Ready for advanced Python development!")

# Example with data display:
data = [
    {"name": "Alice", "age": 30, "city": "New York"},
    {"name": "Bob", "age": 25, "city": "San Francisco"},
    {"name": "Charlie", "age": 35, "city": "Chicago"}
]

# Uncomment the line below to see rich data display:
# display(data)
'''
        
        self.code_input.insert("1.0", welcome_code)
        self.syntax_highlighter.highlight()
        self.update_line_numbers()
        
        self.window.mainloop()

if __name__ == "__main__":
    try:
        pde = PythonDevelopmentEnvironment()
        pde.run()
    except Exception as e:
        print(f"Failed to start PDE: {e}")
        import traceback
        traceback.print_exc()
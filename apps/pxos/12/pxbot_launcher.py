#!/usr/bin/env python3
"""
PXBot Pro Launcher - Main application launcher
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sys
import os

# Add current directory to Python path for imports
sys.path.insert(0, os.getcwd())

try:
    from pxbot_runtime import PXBot, MiniVFS, MiniRT, SmartPXBotChatbot
except ImportError:
    print("Creating basic runtime...")
    # Basic placeholder if runtime isn't available yet
    class PXBot:
        def run(self, cmd): return f"Runtime not ready: {cmd}"
    class MiniVFS:
        def add_file(self, path): pass
    class MiniRT:
        def set_pxbot(self, p): pass
        def list_codes(self): return []
    class SmartPXBotChatbot:
        def __init__(self, *args): pass
        def get_response(self, msg): return f"AI: {msg}"

class PXBotLauncher:
    def __init__(self):
        # Initialize core components
        self.vfs = MiniVFS()
        self.runtime = MiniRT()
        self.pxbot = PXBot(self.vfs, self.runtime)
        self.runtime.set_pxbot(self.pxbot)
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("🎨 PXBot Pro - Pixel Programming Environment")
        self.root.geometry("1000x700")
        self.setup_gui()
    
    def setup_gui(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, 
                              text="🎨 PXBot Pro - Pixel Programming Environment 🚀", 
                              font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Welcome tab
        self.setup_welcome_tab()
        
        # Quick commands tab
        self.setup_commands_tab()
        
        # AI Assistant tab
        self.setup_ai_tab()
    
    def setup_welcome_tab(self):
        welcome_frame = ttk.Frame(self.notebook)
        self.notebook.add(welcome_frame, text="🏠 Welcome")
        
        welcome_text = scrolledtext.ScrolledText(welcome_frame, height=20, wrap=tk.WORD)
        welcome_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        welcome_content = f"""🎉 Welcome to PXBot Pro!

🎨 PIXEL PROGRAMMING ENVIRONMENT
Where code becomes art and art becomes code!

✨ FEATURES:
• Pixel-based code storage in PNG files
• AI-powered coding assistant
• Visual programming interface
• Web integration and scraping
• Modular app ecosystem
• Advanced development tools

🚀 QUICK START:
1. Try the "Quick Commands" tab to create your first code
2. Use the "AI Assistant" to get smart coding help
3. Explore the app ecosystem with various utilities
4. Create pixel art from your code!

📚 DOCUMENTATION:
Check the docs/ folder for comprehensive guides and tutorials.

🛠️ DEVELOPMENT:
Copy apps/app_template.py to create your own applications.

🎯 SUPPORT:
Visit the project repository for updates and community support.

Version: {VERSION}
Installation completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Happy pixel programming! 🎨✨"""
        
        welcome_text.insert('1.0', welcome_content)
        welcome_text.config(state=tk.DISABLED)
    
    def setup_commands_tab(self):
        commands_frame = ttk.Frame(self.notebook)
        self.notebook.add(commands_frame, text="⚡ Quick Commands")
        
        # Command input
        input_frame = ttk.Frame(commands_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(input_frame, text="Command:").pack(side=tk.LEFT)
        self.command_entry = tk.Entry(input_frame, width=50)
        self.command_entry.pack(side=tk.LEFT, padx=5)
        self.command_entry.bind('<Return>', self.execute_command)
        
        ttk.Button(input_frame, text="Execute", command=self.execute_command).pack(side=tk.LEFT, padx=5)
        
        # Output area
        self.output_text = scrolledtext.ScrolledText(commands_frame, height=15)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Example commands
        examples_text = """🔧 Example Commands:
create:function:hello_world::None
create:class:Calculator:value:add,subtract
save:my_code:print("Hello PXBot!")

Try these commands to get started!"""
        
        self.output_text.insert('1.0', examples_text)
    
    def setup_ai_tab(self):
        ai_frame = ttk.Frame(self.notebook)
        self.notebook.add(ai_frame, text="🧠 AI Assistant")
        
        # AI chat area
        self.ai_chat = scrolledtext.ScrolledText(ai_frame, height=15)
        self.ai_chat.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # AI input
        ai_input_frame = ttk.Frame(ai_frame)
        ai_input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(ai_input_frame, text="Ask AI:").pack(side=tk.LEFT)
        self.ai_entry = tk.Entry(ai_input_frame, width=50)
        self.ai_entry.pack(side=tk.LEFT, padx=5)
        self.ai_entry.bind('<Return>', self.ask_ai)
        
        ttk.Button(ai_input_frame, text="Ask", command=self.ask_ai).pack(side=tk.LEFT, padx=5)
        
        # Initialize AI
        self.chatbot = SmartPXBotChatbot(self.pxbot, self)
        
        # Welcome message
        self.ai_chat.insert('1.0', """🧠 AI Assistant Ready!

Ask me anything about:
• Python programming
• Code creation and optimization
• Pixel programming concepts
• App development
• System help

Try: "How do I create a function?" or "Show me pixel programming examples"
""")
    
    def execute_command(self, event=None):
        command = self.command_entry.get().strip()
        if not command:
            return
        
        self.output_text.insert(tk.END, f"\n> {command}\n")
        
        try:
            result = self.pxbot.run(command)
            self.output_text.insert(tk.END, f"{result}\n")
        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {e}\n")
        
        self.output_text.see(tk.END)
        self.command_entry.delete(0, tk.END)
    
    def ask_ai(self, event=None):
        question = self.ai_entry.get().strip()
        if not question:
            return
        
        self.ai_chat.insert(tk.END, f"\nYou: {question}\n")
        
        try:
            response = self.chatbot.get_response(question)
            self.ai_chat.insert(tk.END, f"AI: {response}\n")
        except Exception as e:
            self.ai_chat.insert(tk.END, f"AI Error: {e}\n")
        
        self.ai_chat.see(tk.END)
        self.ai_entry.delete(0, tk.END)
    
    def run(self):
        self.root.mainloop()

def main():
    app = PXBotLauncher()
    app.run()

if __name__ == "__main__":
    main()

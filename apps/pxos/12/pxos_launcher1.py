#!/usr/bin/env python3
"""
PXBot Launcher - GUI interface for the pixel code editor
Double Click to Run - Main application launcher
"""

import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from PIL import Image, ImageTk
import threading
import webbrowser
import tempfile
import urllib.request
import urllib.parse
import html
import re
import datetime
import subprocess
import sys

# Import runtime components
from pxbot_runtime import PXBot, MiniVFS, MiniRT, SmartPXBotChatbot

class PXBotGUI:
    def __init__(self):
        # Initialize PXBot components
        self.vfs = MiniVFS()
        self.runtime = MiniRT()
        self.pxbot = PXBot(self.vfs, self.runtime)
        self.runtime.set_pxbot(self.pxbot)
        
        # Initialize Chatbot with GUI reference for smart integration
        self.chatbot = SmartPXBotChatbot(self.pxbot, self)
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("PXBot Pro - Pixel Code Editor & Web Browser & Smart AI")
        self.root.geometry("1000x750")
        self.root.configure(bg='#2d2d2d')
        
        self.setup_gui()
        self.load_existing_codes()
    
    def setup_gui(self):
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="🧠 PXBot Pro - Smart Code Editor & Web Browser & AI 🚀", 
                              font=('Arial', 16, 'bold'), bg='#2d2d2d', fg='white')
        title_label.pack(pady=(0, 10))
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Quick Commands Tab
        self.setup_quick_tab()
        
        # Code Editor Tab
        self.setup_editor_tab()
        
        # Saved Codes Tab
        self.setup_saved_tab()
        
        # Browser Tab (HTML galleries)
        self.setup_browser_tab()
        
        # Web Browser Tab
        self.setup_web_browser_tab()
        
        # AI Chatbot Tab
        self.setup_chatbot_tab()
    
    def setup_quick_tab(self):
        quick_frame = ttk.Frame(self.notebook)
        self.notebook.add(quick_frame, text="Quick Commands")
        
        # Function creator
        func_frame = ttk.LabelFrame(quick_frame, text="Create Function", padding=10)
        func_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(func_frame, text="Name:").grid(row=0, column=0, sticky=tk.W)
        self.func_name = tk.Entry(func_frame, width=20)
        self.func_name.grid(row=0, column=1, padx=5)
        
        tk.Label(func_frame, text="Parameters:").grid(row=0, column=2, sticky=tk.W)
        self.func_params = tk.Entry(func_frame, width=20)
        self.func_params.grid(row=0, column=3, padx=5)
        
        ttk.Button(func_frame, text="Create Function", 
                  command=self.create_function).grid(row=0, column=4, padx=5)
        
        # Class creator
        class_frame = ttk.LabelFrame(quick_frame, text="Create Class", padding=10)
        class_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(class_frame, text="Name:").grid(row=0, column=0, sticky=tk.W)
        self.class_name = tk.Entry(class_frame, width=20)
        self.class_name.grid(row=0, column=1, padx=5)
        
        tk.Label(class_frame, text="Attributes:").grid(row=0, column=2, sticky=tk.W)
        self.class_attrs = tk.Entry(class_frame, width=20)
        self.class_attrs.grid(row=0, column=3, padx=5)
        
        ttk.Button(class_frame, text="Create Class", 
                  command=self.create_class).grid(row=0, column=4, padx=5)
        
        # Output area
        output_frame = ttk.LabelFrame(quick_frame, text="Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, 
                                                    bg='#1e1e1e', fg='#00ff00', 
                                                    font=('Consolas', 10))
        self.output_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_editor_tab(self):
        editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(editor_frame, text="Code Editor")
        
        # Editor controls
        controls_frame = ttk.Frame(editor_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(controls_frame, text="Code Name:").pack(side=tk.LEFT)
        self.editor_name = tk.Entry(controls_frame, width=20)
        self.editor_name.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Save Code", 
                  command=self.save_editor_code).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Clear", 
                  command=self.clear_editor).pack(side=tk.LEFT, padx=5)
        
        # Code editor
        self.code_editor = scrolledtext.ScrolledText(editor_frame, height=25,
                                                    bg='#1e1e1e', fg='#ffffff',
                                                    font=('Consolas', 11),
                                                    insertbackground='white')
        self.code_editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Add some sample code
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
        
        # Controls
        controls_frame = ttk.Frame(saved_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Refresh List", 
                  command=self.refresh_saved_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Execute Selected", 
                  command=self.execute_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="View Code", 
                  command=self.view_selected_code).pack(side=tk.LEFT, padx=5)
        
        # List of saved codes
        self.saved_listbox = tk.Listbox(saved_frame, height=10, bg='#2d2d2d', fg='white')
        self.saved_listbox.pack(fill=tk.X, padx=10, pady=5)
        
        # Code viewer
        viewer_frame = ttk.LabelFrame(saved_frame, text="Code Preview", padding=10)
        viewer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.code_viewer = scrolledtext.ScrolledText(viewer_frame, height=15,
                                                    bg='#1e1e1e', fg='#ffffff',
                                                    font=('Consolas', 10),
                                                    state=tk.DISABLED)
        self.code_viewer.pack(fill=tk.BOTH, expand=True)
    
    def setup_browser_tab(self):
        browser_frame = ttk.Frame(self.notebook)
        self.notebook.add(browser_frame, text="Code Gallery")
        
        # Controls
        controls_frame = ttk.Frame(browser_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Generate HTML Gallery", 
                  command=self.generate_html_view).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Open in Browser", 
                  command=self.open_in_browser).pack(side=tk.LEFT, padx=5)
        
        # HTML preview
        self.html_preview = scrolledtext.ScrolledText(browser_frame, height=25,
                                                     bg='#1e1e1e', fg='#ffffff',
                                                     font=('Consolas', 10))
        self.html_preview.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def setup_web_browser_tab(self):
        """Web browser tab for browsing the internet"""
        web_frame = ttk.Frame(self.notebook)
        self.notebook.add(web_frame, text="🌐 Web Browser")
        
        # URL input frame
        url_frame = ttk.Frame(web_frame)
        url_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(url_frame, text="URL:").pack(side=tk.LEFT)
        self.url_entry = tk.Entry(url_frame, width=60, font=('Arial', 10))
        self.url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.url_entry.bind('<Return>', lambda e: self.load_web_page())
        
        # Buttons frame
        buttons_frame = ttk.Frame(web_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="🔗 Go", 
                  command=self.load_web_page).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🌐 Open in Browser", 
                  command=self.open_url_in_browser).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🗑️ Clear", 
                  command=self.clear_web_content).pack(side=tk.LEFT, padx=5)
        
        # Quick links
        quick_frame = ttk.Frame(web_frame)
        quick_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(quick_frame, text="Quick Links:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        quick_links = [
            ("🔍 Google", "https://www.google.com"),
            ("💻 GitHub", "https://github.com"),
            ("🐍 Python.org", "https://www.python.org"),
            ("📚 Stack Overflow", "https://stackoverflow.com"),
            ("📰 Hacker News", "https://news.ycombinator.com"),
            ("🎯 Reddit", "https://www.reddit.com")
        ]
        
        for name, url in quick_links:
            btn = ttk.Button(quick_frame, text=name, 
                           command=lambda u=url: self.load_quick_url(u))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Status frame
        status_frame = ttk.Frame(web_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=2)
        
        self.web_status = tk.Label(status_frame, text="🌐 Ready to browse the web...", 
                                  fg='green', anchor='w', font=('Arial', 9))
        self.web_status.pack(side=tk.LEFT)
        
        # Content area with tabs
        content_notebook = ttk.Notebook(web_frame)
        content_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Text content tab
        text_frame = ttk.Frame(content_notebook)
        content_notebook.add(text_frame, text="📄 Readable Text")
        
        self.web_content = scrolledtext.ScrolledText(text_frame, height=20,
                                                    bg='#f8f8f8', fg='#333333',
                                                    font=('Arial', 11), wrap=tk.WORD)
        self.web_content.pack(fill=tk.BOTH, expand=True)
        
        # Raw HTML tab
        html_frame = ttk.Frame(content_notebook)
        content_notebook.add(html_frame, text="💻 Raw HTML")
        
        self.raw_html = scrolledtext.ScrolledText(html_frame, height=20,
                                                 bg='#1e1e1e', fg='#ffffff',
                                                 font=('Consolas', 9))
        self.raw_html.pack(fill=tk.BOTH, expand=True)
    
    def setup_chatbot_tab(self):
        """AI chatbot tab with smart pixel programming integration"""
        chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(chat_frame, text="🧠 Smart AI")
        
        # Chat header
        header_frame = ttk.Frame(chat_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        header_label = tk.Label(header_frame, text="🧠 PX Assistant Pro - Smart Coding AI", 
                               font=('Arial', 14, 'bold'), fg='#4CAF50')
        header_label.pack(side=tk.LEFT)
        
        # Control buttons
        ttk.Button(header_frame, text="🗑️ Clear Chat", 
                  command=self.clear_chat).pack(side=tk.RIGHT, padx=5)
        ttk.Button(header_frame, text="💡 Get Help", 
                  command=self.show_chat_help).pack(side=tk.RIGHT, padx=5)
        
        # Chat display area
        chat_display_frame = ttk.Frame(chat_frame)
        chat_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.chat_display = scrolledtext.ScrolledText(chat_display_frame, height=20,
                                                     bg='#f0f0f0', fg='#333333',
                                                     font=('Arial', 11), wrap=tk.WORD,
                                                     state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Configure chat text styles
        self.chat_display.tag_configure("user", foreground="#2196F3", font=('Arial', 11, 'bold'))
        self.chat_display.tag_configure("bot", foreground="#4CAF50", font=('Arial', 11, 'bold'))
        self.chat_display.tag_configure("code", background="#e8e8e8", font=('Consolas', 10))
        self.chat_display.tag_configure("timestamp", foreground="#666666", font=('Arial', 9))
        
        # Input area
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(input_frame, text="Ask me anything:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        # Message input
        message_input_frame = ttk.Frame(input_frame)
        message_input_frame.pack(fill=tk.X, pady=2)
        
        self.chat_input = tk.Entry(message_input_frame, font=('Arial', 11))
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.chat_input.bind('<Return>', lambda e: self.send_chat_message())
        self.chat_input.bind('<KeyPress>', self.on_chat_typing)
        
        self.send_button = ttk.Button(message_input_frame, text="🚀 Send", 
                                     command=self.send_chat_message)
        self.send_button.pack(side=tk.RIGHT)
        
        # Quick suggestion buttons
        suggestions_frame = ttk.Frame(input_frame)
        suggestions_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(suggestions_frame, text="Quick questions:", font=('Arial', 9)).pack(side=tk.LEFT)
        
        suggestions = [
            ("📁 List my codes", "list my saved codes"),
            ("🎨 Create pixel art", "create pixel art from my code"),
            ("🔧 Use tools", "show me pixel programming tools"),
            ("🛠️ Create template", "create calculator template"),
            ("🔍 Analyze pixels", "analyze pixel density"),
            ("⚡ Optimize code", "optimize my code for storage")
        ]
        
        for label, question in suggestions:
            btn = ttk.Button(suggestions_frame, text=label,
                           command=lambda q=question: self.send_quick_question(q))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Initialize chat with enhanced welcome message
        self.add_chat_message("bot", "🧠 Welcome to PX Assistant Pro! 🎨✨\n\nI'm your advanced AI with **Pixel Programming Tools**! I can:\n\n🔧 **Use Tools:** Create pixel art, merge codes, analyze pixels\n📊 **Analyze:** Code quality, pixel density, structure\n💻 **Generate:** Functions, classes, templates from descriptions\n🐛 **Debug:** Smart error detection and solutions\n🔍 **Search:** Web integration for latest coding info\n\n🎯 **Try:** 'Use tools to create pixel art' or 'List my codes'!")
    
    # Chat-related methods
    def send_chat_message(self):
        message = self.chat_input.get().strip()
        if not message:
            return
        
        # Add user message to display
        self.add_chat_message("user", message)
        
        # Clear input
        self.chat_input.delete(0, tk.END)
        
        # Get bot response (in a thread to prevent GUI freezing)
        threading.Thread(target=self._get_bot_response, args=(message,), daemon=True).start()
        
        # Show typing indicator
        self.show_typing_indicator()
    
    def _get_bot_response(self, message):
        try:
            response = self.chatbot.get_response(message)
            # Update GUI in main thread
            self.root.after(0, self._display_bot_response, response)
        except Exception as e:
            error_response = f"Oops! I encountered an error: {str(e)}. Let's try again! 🤖"
            self.root.after(0, self._display_bot_response, error_response)
    
    def _display_bot_response(self, response):
        self.hide_typing_indicator()
        self.add_chat_message("bot", response)
    
    def add_chat_message(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        if sender == "user":
            self.chat_display.insert(tk.END, f"[{timestamp}] You: ", "timestamp")
            self.chat_display.insert(tk.END, f"{message}\n", "user")
        else:
            self.chat_display.insert(tk.END, f"[{timestamp}] PX Assistant: ", "timestamp")
            
            # Handle code blocks in bot responses
            if "```python" in message:
                parts = message.split("```python")
                self.chat_display.insert(tk.END, parts[0], "bot")
                for i in range(1, len(parts)):
                    if "```" in parts[i]:
                        code_part, rest = parts[i].split("```", 1)
                        self.chat_display.insert(tk.END, code_part, "code")
                        self.chat_display.insert(tk.END, rest, "bot")
                    else:
                        self.chat_display.insert(tk.END, parts[i], "code")
            else:
                self.chat_display.insert(tk.END, f"{message}", "bot")
            
            self.chat_display.insert(tk.END, "\n")
        
        self.chat_display.insert(tk.END, "\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def send_quick_question(self, question):
        self.chat_input.delete(0, tk.END)
        self.chat_input.insert(0, question)
        self.send_chat_message()
    
    def show_typing_indicator(self):
        self.send_button.config(text="⏳ ...", state=tk.DISABLED)
    
    def hide_typing_indicator(self):
        self.send_button.config(text="🚀 Send", state=tk.NORMAL)
    
    def on_chat_typing(self, event):
        # Enable send button when user types
        if self.chat_input.get() or event.char:
            self.send_button.config(state=tk.NORMAL)
    
    def clear_chat(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete('1.0', tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        self.chatbot.clear_history()
        self.add_chat_message("bot", "🔄 Chat cleared! I'm ready with my **Pixel Programming Tools**! 🔧🎨\n\nI can create pixel art, merge codes, analyze pixels, generate templates, and much more! What shall we build together? 🚀")
        
        self.log_output("Chat history cleared")
    
    def show_chat_help(self):
        help_text = """🧠 **PX Assistant Pro with Pixel Programming Tools** 🔧

**🎨 Pixel Programming Tools:**
• "create pixel art from [code]" - Turn code into colorful art
• "merge [code1] and [code2] into [new_name]" - Combine codes  
• "analyze pixel density of [code]" - Detailed pixel analysis
• "optimize [code] for storage" - Compress pixel data
• "create [pattern] pattern [size]" - Generate decorative patterns
• "create [template] template" - Make code templates

**🎯 PXBot Integration:**
• "list my codes" - See all saved pixel codes
• "analyze [code name]" - Deep analysis of specific code
• "run [code name]" - Execute saved pixel codes
• "create a function that..." - Generate code from description

**💻 Advanced Coding Help:**
• "analyze my code quality" - Detailed code review
• "how do I..." - Python syntax with examples
• "debug my [error type]" - Specific debugging help
• "best practices for..." - Coding recommendations

**🔍 Smart Features:**
• Web search integration for latest info
• Natural language code generation
• Intelligent error detection
• Security and performance analysis

**🚀 Try These Examples:**
• "create pixel art from my calculator"
• "merge calculator and data_processor into super_tool"  
• "create gradient pattern 48x48"
• "optimize my code for better storage"

I have real tools to manipulate your pixel code system! 🎨✨"""
        self.add_chat_message("bot", help_text)
    
    # Web browser methods
    def load_web_page(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return
        
        # Add http:// if no protocol specified
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
        
        # Load in a separate thread to prevent GUI freezing
        threading.Thread(target=self._fetch_web_content, args=(url,), daemon=True).start()
        
        self.web_status.config(text=f"🔄 Loading {url}...", fg='orange')
        self.log_output(f"Loading web page: {url}")
    
    def _fetch_web_content(self, url):
        try:
            # Create request with headers to appear more like a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read()
                
                # Try to decode content
                try:
                    if hasattr(response, 'headers'):
                        charset = response.headers.get_content_charset()
                        if charset:
                            html_content = content.decode(charset)
                        else:
                            html_content = content.decode('utf-8')
                    else:
                        html_content = content.decode('utf-8')
                except:
                    html_content = content.decode('utf-8', errors='ignore')
                
                # Update GUI in main thread
                self.root.after(0, self._update_web_content, html_content, url)
                
        except urllib.error.HTTPError as e:
            error_msg = f"❌ HTTP Error {e.code}: {e.reason}"
            self.root.after(0, self._show_web_error, error_msg)
        except urllib.error.URLError as e:
            error_msg = f"❌ URL Error: {e.reason}"
            self.root.after(0, self._show_web_error, error_msg)
        except Exception as e:
            error_msg = f"❌ Error loading page: {str(e)}"
            self.root.after(0, self._show_web_error, error_msg)
    
    def _update_web_content(self, html_content, url):
        # Update raw HTML tab
        self.raw_html.delete('1.0', tk.END)
        self.raw_html.insert('1.0', html_content)
        
        # Convert HTML to readable text
        text_content = self._html_to_text(html_content)
        
        # Update text content tab
        self.web_content.delete('1.0', tk.END)
        self.web_content.insert('1.0', text_content)
        
        # Update status
        self.web_status.config(text=f"✅ Loaded: {url}", fg='green')
        self.log_output(f"Successfully loaded: {url}")
    
    def _show_web_error(self, error_msg):
        self.web_status.config(text=error_msg, fg='red')
        self.web_content.delete('1.0', tk.END)
        self.web_content.insert('1.0', f"Error: {error_msg}")
        self.log_output(f"Web error: {error_msg}")
    
    def _html_to_text(self, html_content):
        """Convert HTML to readable text"""
        try:
            # Remove script and style elements
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Convert common HTML elements to text
            html_content = re.sub(r'<br[^>]*>', '\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<p[^>]*>', '\n\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</p>', '', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<h[1-6][^>]*>', '\n\n=== ', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</h[1-6]>', ' ===\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<li[^>]*>', '\n• ', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</li>', '', html_content, flags=re.IGNORECASE)
            
            # Remove all other HTML tags
            html_content = re.sub(r'<[^>]+>', '', html_content)
            
            # Decode HTML entities
            html_content = html.unescape(html_content)
            
            # Clean up whitespace
            html_content = re.sub(r'\n\s*\n\s*\n', '\n\n', html_content)
            html_content = re.sub(r'[ \t]+', ' ', html_content)
            
            return html_content.strip()
        except:
            return "Error parsing HTML content"
    
    def load_quick_url(self, url):
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)
        self.load_web_page()
    
    def open_url_in_browser(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        webbrowser.open(url)
        self.log_output(f"Opened in browser: {url}")
    
    def clear_web_content(self):
        self.web_content.delete('1.0', tk.END)
        self.raw_html.delete('1.0', tk.END)
        self.web_status.config(text="🗑️ Content cleared", fg='blue')
    
    # Core PXBot functionality methods
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
        
        # Clear fields
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
        
        # Clear fields
        self.class_name.delete(0, tk.END)
        self.class_attrs.delete(0, tk.END)
        
        self.refresh_saved_list()
    
    def save_editor_code(self):
        name = self.editor_name.get().strip()
        code = self.code_editor.get('1.0', tk.END).strip()
        
        if not name:
            messagebox.showerror("Error", "Code name is required")
            return
        
        if not code:
            messagebox.showerror("Error", "Code cannot be empty")
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
    
    def generate_html_view(self):
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>PXBot - Pixel Code Gallery</title>
    <style>
        body { font-family: 'Courier New', monospace; background: #1e1e1e; color: #ffffff; margin: 20px; }
        .header { color: #00ff00; font-size: 24px; text-align: center; margin-bottom: 30px; }
        .code-item { background: #2d2d2d; margin: 15px 0; padding: 15px; border-radius: 8px; border-left: 4px solid #00ff00; }
        .code-name { color: #00aaff; font-size: 18px; font-weight: bold; margin-bottom: 10px; }
        .code-content { background: #1a1a1a; padding: 10px; border-radius: 4px; white-space: pre-wrap; overflow-x: auto; }
        .keyword { color: #569cd6; }
        .string { color: #ce9178; }
        .comment { color: #6a9955; }
    </style>
</head>
<body>
    <div class="header">🎨 PXBot Pixel Code Gallery</div>
"""
        
        for code_name in self.runtime.list_codes():
            code = self.runtime.load_code(code_name)
            if code:
                # Basic syntax highlighting
                highlighted_code = self.highlight_syntax(code)
                html_content += f"""
    <div class="code-item">
        <div class="code-name">{code_name}</div>
        <div class="code-content">{highlighted_code}</div>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        self.html_preview.delete('1.0', tk.END)
        self.html_preview.insert('1.0', html_content)
    
    def highlight_syntax(self, code):
        # Basic syntax highlighting
        code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        keywords = ['def', 'class', 'import', 'from', 'return', 'if', 'else', 'elif', 'for', 'while', 'try', 'except']
        for keyword in keywords:
            code = code.replace(f' {keyword} ', f' <span class="keyword">{keyword}</span> ')
            code = code.replace(f'{keyword} ', f'<span class="keyword">{keyword}</span> ')
        
        return code
    
    def open_in_browser(self):
        html_content = self.html_preview.get('1.0', tk.END)
        if not html_content.strip():
            self.generate_html_view()
            html_content = self.html_preview.get('1.0', tk.END)
        
        # Save to temp file and open
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            temp_path = f.name
        
        webbrowser.open(f'file://{temp_path}')
        self.log_output(f"Opened in browser: {temp_path}")
    
    def load_existing_codes(self):
        """Load any existing code files on startup"""
        code_dir = os.path.join(os.getcwd(), "pxbot_code")
        if os.path.exists(code_dir):
            for filename in os.listdir(code_dir):
                if filename.endswith('.png'):
                    name = filename[:-4]  # Remove .png extension
                    image_path = os.path.join(code_dir, filename)
                    self.runtime.save_code(name, image_path)
        
        self.refresh_saved_list()
    
    def log_output(self, message):
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)
    
    def run(self):
        self.root.mainloop()

def main():
    """Main application entry point"""
    try:
        # Check if runtime module can be imported
        try:
            from pxbot_runtime import PXBot, MiniVFS, MiniRT, SmartPXBotChatbot
        except ImportError as e:
            error_msg = f"Error importing PXBot runtime: {e}\n\nPlease ensure 'pxbot_runtime.py' is in the same directory as this launcher."
            
            # Try to show error in a simple window
            try:
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror("Import Error", error_msg)
            except:
                # If GUI fails, print to console
                print(error_msg)
                input("Press Enter to close...")
            return
        
        # Create and run the application
        app = PXBotGUI()
        app.run()
        
    except Exception as e:
        # Fallback error handling
        import traceback
        error_msg = f"Error starting PXBot: {e}\n\n{traceback.format_exc()}"
        
        # Try to show error in a simple window
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("PXBot Error", error_msg)
        except:
            # If GUI fails, print to console
            print(error_msg)
            input("Press Enter to close...")

if __name__ == "__main__":
    main()
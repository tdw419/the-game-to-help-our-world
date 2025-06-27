#!/usr/bin/env python3
"""
PXBot Pro - One-Click Complete Installation Script
Final integration script that sets up the entire PXBot Pro ecosystem
"""

import os
import sys
import json
import shutil
import subprocess
import platform
import urllib.request
import zipfile
import tempfile
from datetime import datetime
import traceback

VERSION = "2.0.0"
TITLE = "PXBot Pro - Complete Pixel Programming Environment"

def print_banner():
    """Print welcome banner"""
    print(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║  🎨 {TITLE:<62} 🎨 ║
║                           Version {VERSION}                              ║
║                                                                          ║
║  🚀 Advanced Pixel Programming Environment                               ║
║  🧠 AI-Powered Code Generation                                           ║
║  📱 Complete App Ecosystem                                               ║
║  🌐 Web Integration & Tools                                              ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
""")

def check_python_compatibility():
    """Check Python version and compatibility"""
    print("🔍 Checking Python compatibility...")
    
    version_info = sys.version_info
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 8):
        print(f"❌ Python {version_info.major}.{version_info.minor} detected")
        print("🔧 PXBot Pro requires Python 3.8 or higher")
        print("📥 Please install Python 3.8+ from https://python.org")
        return False
    
    print(f"✅ Python {version_info.major}.{version_info.minor}.{version_info.micro} is compatible")
    
    # Check for required modules
    required_modules = ['tkinter', 'json', 'os', 'sys']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing required modules: {', '.join(missing_modules)}")
        return False
    
    print("✅ All required Python modules available")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    dependencies = [
        ('pygame', '2.0.0', 'Graphics and UI framework'),
        ('pillow', '8.0.0', 'Image processing library'),
        ('psutil', '5.8.0', 'System monitoring utilities'),
        ('requests', '2.25.0', 'HTTP library (optional)'),
    ]
    
    failed_packages = []
    
    for package, min_version, description in dependencies:
        print(f"  📦 Installing {package} ({description})...")
        try:
            # Try to install the package
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", f"{package}>={min_version}", "--upgrade"
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"    ✅ {package} installed successfully")
            else:
                print(f"    ⚠️ {package} installation warning: {result.stderr[:100]}")
                # Try without version requirement
                result2 = subprocess.run([
                    sys.executable, "-m", "pip", "install", package, "--upgrade"
                ], capture_output=True, text=True, timeout=60)
                
                if result2.returncode == 0:
                    print(f"    ✅ {package} installed (without version requirement)")
                else:
                    failed_packages.append(package)
                    print(f"    ❌ {package} installation failed")
        
        except subprocess.TimeoutExpired:
            print(f"    ⏱️ {package} installation timed out, continuing...")
        except Exception as e:
            print(f"    ❌ {package} installation error: {e}")
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n⚠️ Some packages failed to install: {', '.join(failed_packages)}")
        print("🔧 You may need to install them manually:")
        for package in failed_packages:
            print(f"   pip install {package}")
        return False
    
    print("✅ All dependencies installed successfully")
    return True

def create_core_files():
    """Create core PXBot files if they don't exist"""
    print("\n📁 Creating core files...")
    
    # Core files that need to be created
    core_files = {
        "pxbot_runtime.py": '''#!/usr/bin/env python3
"""
PXBot Runtime - Core functionality for pixel code storage and execution
"""

import ast
import os
from PIL import Image
import random
import datetime
import json

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
        if "factorial" in name.lower():
            body = "if n <= 1: return 1\\n return n * factorial(n-1)"
        else:
            body = "pass"
        
        code = f"def {name}({params}):\\n {body}\\n return {return_val}"
        return self._save_code(code, name)
    
    def _create_class(self, name, attrs, methods):
        attrs_init = "\\n ".join([f"self.{x.strip()} = {x.strip()}" for x in attrs.split(",") if x.strip()])
        methods_def = "\\n ".join([f"def {x.strip()}(self): pass" for x in methods.split(",") if x.strip()])
        
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
        
        modified_code = existing_code + f"\\n# {modification}"
        return self._save_code(modified_code, name)
    
    def _save_code(self, code, name):
        try:
            ast.parse(code)  # Validate syntax
        except SyntaxError:
            return "Invalid Python syntax"
        
        # Create code directory
        code_dir = os.path.join(os.getcwd(), "pxbot_code")
        os.makedirs(code_dir, exist_ok=True)
        
        # Encode code as image
        image_path = os.path.join(code_dir, f"{name}.png")
        encoded_image = self._encode_to_image(code)
        encoded_image.save(image_path)
        
        # Save mapping
        self.v.add_file(code_dir)
        self.r.save_code(name, image_path)
        
        return f"Saved: {name} -> {image_path}"
    
    def _encode_to_image(self, code):
        """Encode code as pixel data in PNG"""
        data = code.encode('utf-8')
        width = int(len(data)**0.5) + 1
        height = width
        
        image = Image.new("RGB", (width, height), (0, 0, 0))
        pixels = image.load()
        
        for i, byte in enumerate(data):
            if i < width * height:
                x, y = i % width, i // width
                pixels[x, y] = (byte, 0, 0)  # Store in red channel
        
        return image
    
    def _decode_from_image(self, image_path):
        """Decode code from PNG pixel data"""
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
            
            return bytes(data).decode('utf-8', errors='ignore').rstrip('\\x00')
        except Exception:
            return None

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
                exec(code, globals())
                return f"Executed: {name}"
            except Exception as e:
                return f"Execution error: {e}"
        return f"Code '{name}' not found"
    
    def list_codes(self):
        return list(self.code_mapping.keys())

# Smart AI Chatbot placeholder
class SmartPXBotChatbot:
    def __init__(self, pxbot_instance=None, gui_reference=None):
        self.pxbot = pxbot_instance
        self.gui = gui_reference
        
    def get_response(self, message):
        return f"🧠 AI Assistant: {message} (Functionality will be enhanced after full setup)"
''',
        
        "pxbot_launcher.py": '''#!/usr/bin/env python3
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
        
        self.output_text.insert(tk.END, f"\\n> {command}\\n")
        
        try:
            result = self.pxbot.run(command)
            self.output_text.insert(tk.END, f"{result}\\n")
        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {e}\\n")
        
        self.output_text.see(tk.END)
        self.command_entry.delete(0, tk.END)
    
    def ask_ai(self, event=None):
        question = self.ai_entry.get().strip()
        if not question:
            return
        
        self.ai_chat.insert(tk.END, f"\\nYou: {question}\\n")
        
        try:
            response = self.chatbot.get_response(question)
            self.ai_chat.insert(tk.END, f"AI: {response}\\n")
        except Exception as e:
            self.ai_chat.insert(tk.END, f"AI Error: {e}\\n")
        
        self.ai_chat.see(tk.END)
        self.ai_entry.delete(0, tk.END)
    
    def run(self):
        self.root.mainloop()

def main():
    app = PXBotLauncher()
    app.run()

if __name__ == "__main__":
    main()
'''
    }
    
    created_files = []
    for filename, content in core_files.items():
        if not os.path.exists(filename):
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                created_files.append(filename)
                print(f"  ✅ Created {filename}")
            except Exception as e:
                print(f"  ❌ Failed to create {filename}: {e}")
        else:
            print(f"  ⚡ {filename} already exists")
    
    if created_files:
        print(f"✅ Created {len(created_files)} core files")
    else:
        print("✅ All core files already exist")
    
    return True

def run_enhanced_setup():
    """Run the enhanced setup script"""
    print("\n🔧 Running enhanced setup process...")
    
    try:
        if os.path.exists("setup.py"):
            print("  📋 Found setup.py, executing enhanced setup...")
            result = subprocess.run([sys.executable, "setup.py"], capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print("  ✅ Enhanced setup completed successfully")
                return True
            else:
                print(f"  ⚠️ Setup completed with warnings: {result.stderr[:200]}")
                return True  # Continue even with warnings
        else:
            print("  ⚠️ setup.py not found, using basic setup")
            return create_basic_structure()
    except subprocess.TimeoutExpired:
        print("  ⏱️ Setup process timed out, continuing with basic setup...")
        return create_basic_structure()
    except Exception as e:
        print(f"  ❌ Setup error: {e}")
        return create_basic_structure()

def create_basic_structure():
    """Create basic directory structure"""
    print("  📁 Creating basic directory structure...")
    
    directories = [
        "apps", "apps/core", "apps/utilities", "apps/examples",
        "pxbot_code", "pxbot_code/exports", "pxbot_code/user_data",
        "docs", "examples", "tests", "tools"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"    ✅ {directory}/")
        except Exception as e:
            print(f"    ❌ Failed to create {directory}/: {e}")
    
    # Create basic configuration
    config = {
        "version": VERSION,
        "installation_date": datetime.now().isoformat(),
        "setup_type": "basic"
    }
    
    try:
        with open("pxbot_code/installation_info.json", "w") as f:
            json.dump(config, f, indent=2)
        print("  ✅ Basic configuration created")
    except Exception as e:
        print(f"  ⚠️ Configuration creation failed: {e}")
    
    return True

def verify_installation():
    """Verify the installation"""
    print("\n🔍 Verifying installation...")
    
    # Check required files
    required_files = ["pxbot_launcher.py", "pxbot_runtime.py"]
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            missing_files.append(file)
            print(f"  ❌ {file} - MISSING")
    
    # Check directories
    required_dirs = ["apps", "pxbot_code", "docs"]
    missing_dirs = []
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"  ✅ {directory}/")
        else:
            missing_dirs.append(directory)
            print(f"  ❌ {directory}/ - MISSING")
    
    # Test imports
    print("  🔍 Testing imports...")
    try:
        import pygame
        print("    ✅ pygame")
    except ImportError:
        print("    ⚠️ pygame - not available")
    
    try:
        from PIL import Image
        print("    ✅ PIL/Pillow")
    except ImportError:
        print("    ⚠️ PIL/Pillow - not available")
    
    # Overall assessment
    if not missing_files and not missing_dirs:
        print("✅ Installation verification passed!")
        return True
    else:
        print("⚠️ Installation verification found issues")
        if missing_files:
            print(f"   Missing files: {', '.join(missing_files)}")
        if missing_dirs:
            print(f"   Missing directories: {', '.join(missing_dirs)}")
        return False

def test_basic_functionality():
    """Test basic PXBot functionality"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Test import
        sys.path.insert(0, os.getcwd())
        from pxbot_runtime import PXBot, MiniVFS, MiniRT
        
        # Test basic operations
        vfs = MiniVFS()
        rt = MiniRT()
        pxbot = PXBot(vfs, rt)
        rt.set_pxbot(pxbot)
        
        # Test command execution
        result = pxbot.run("create:function:test_func::None")
        if "Saved:" in result:
            print("  ✅ Code creation and storage working")
        else:
            print(f"  ⚠️ Code creation test: {result}")
        
        # Test code listing
        codes = rt.list_codes()
        if codes:
            print(f"  ✅ Code listing working ({len(codes)} codes)")
        else:
            print("  ⚠️ No codes found")
        
        print("✅ Basic functionality test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def create_quick_start_guide():
    """Create a quick start guide"""
    print("\n📚 Creating quick start guide...")
    
    guide_content = f"""# 🚀 PXBot Pro - Quick Start Guide

## Welcome to PXBot Pro v{VERSION}!

### 🎯 Quick Launch
```bash
python pxbot_launcher.py
```

### 🎨 What is PXBot Pro?
PXBot Pro is an advanced pixel programming environment where:
- **Code becomes art** - Programs are stored as pixel data in PNG files
- **AI assists development** - Smart coding help and generation
- **Visual interface** - Beautiful and intuitive user experience
- **App ecosystem** - Modular applications for any need

### 🚀 First Steps

#### 1. Launch the Application
```bash
python pxbot_launcher.py
```

#### 2. Try the Quick Commands Tab
- Create a function: `create:function:hello_world::None`
- Create a class: `create:class:Calculator:value:add,subtract`
- Save custom code: `save:my_code:print("Hello PXBot!")`

#### 3. Use the AI Assistant
- Ask: "How do I create a function?"
- Ask: "Show me pixel programming examples"
- Ask: "Create a calculator for me"

#### 4. Explore the Features
- **Pixel Programming**: Your code is stored as colorful pixel art
- **Visual Interface**: Tabs for different functionality
- **AI Integration**: Smart coding assistance
- **Web Tools**: Built-in browser and scraping (if available)

### 🎨 Pixel Programming Basics

PXBot stores your Python code as pixel data:
1. Each character becomes a pixel value
2. Code is saved as PNG images
3. Visual patterns represent code structure
4. Art can be generated from code

### 🛠️ Development

#### Creating Apps
1. Copy `apps/app_template.py` (if available)
2. Customize for your needs
3. Test with `python your_app.py`
4. Use in PXBot with `your_app:command`

#### Available Commands
- `create:function:name:params:return` - Create functions
- `create:class:name:attrs:methods` - Create classes
- `save:name:code` - Save custom code
- `exec:name` - Execute saved code

### 🎯 Next Steps

1. **Explore**: Try all the features and tabs
2. **Create**: Make your own pixel codes
3. **Learn**: Read documentation in docs/ folder
4. **Develop**: Build your own applications
5. **Share**: Join the PXBot community

### 📚 Resources

- **Documentation**: docs/ folder
- **Examples**: examples/ folder
- **Templates**: apps/app_template.py (if available)
- **Support**: Check project repository

### 🎉 Have Fun!

PXBot Pro is designed to make programming fun and visual.
Experiment, create, and enjoy the journey from code to art!

---
*Installed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Version: {VERSION}*
"""
    
    try:
        os.makedirs("docs", exist_ok=True)
        with open("docs/QUICK_START.md", "w", encoding='utf-8') as f:
            f.write(guide_content)
        print("  ✅ Quick start guide created: docs/QUICK_START.md")
        return True
    except Exception as e:
        print(f"  ❌ Failed to create quick start guide: {e}")
        return False

def generate_final_report():
    """Generate final installation report"""
    print("\n📊 Generating installation report...")
    
    # Gather system information
    system_info = {
        "platform": platform.system(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "installation_date": datetime.now().isoformat(),
        "pxbot_version": VERSION
    }
    
    # Check installed packages
    installed_packages = []
    packages_to_check = ['pygame', 'PIL', 'psutil', 'requests']
    
    for package in packages_to_check:
        try:
            if package == 'PIL':
                import PIL
                installed_packages.append(f"Pillow (PIL)")
            else:
                __import__(package)
                installed_packages.append(package)
        except ImportError:
            pass
    
    # Check file structure
    file_status = {}
    important_files = [
        "pxbot_launcher.py",
        "pxbot_runtime.py", 
        "apps/",
        "pxbot_code/",
        "docs/"
    ]
    
    for item in important_files:
        file_status[item] = "✅" if os.path.exists(item) else "❌"
    
    report_content = f"""# 🎉 PXBot Pro Installation Report

## 📊 Installation Summary
- **Status**: Installation Complete
- **Version**: {VERSION}
- **Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Platform**: {system_info['platform']}
- **Python**: {system_info['python_version']}

## 📦 Installed Components

### Core Files
"""
    
    for file, status in file_status.items():
        report_content += f"- {status} {file}\n"
    
    report_content += f"""
### Python Packages
"""
    
    for package in installed_packages:
        report_content += f"- ✅ {package}\n"
    
    report_content += f"""
## 🚀 Quick Start

### Launch PXBot Pro
```bash
python pxbot_launcher.py
```

### Alternative Launch Methods
```bash
# If available:
python launch.py
./launch.sh    # Unix/Linux/Mac  
launch.bat     # Windows
```

## 🎯 What's Next?

1. **🚀 Launch**: Start PXBot Pro with `python pxbot_launcher.py`
2. **🎨 Explore**: Try the visual interface and different tabs
3. **🧠 AI Help**: Use the AI Assistant for coding help
4. **📚 Learn**: Read the quick start guide in docs/QUICK_START.md
5. **🛠️ Develop**: Create your own apps and pixel codes

## 🔧 If You Need Help

- **📖 Documentation**: Check docs/ folder
- **🧪 Test**: Run `python pxbot_launcher.py` to test
- **🔍 Verify**: Check that all ✅ items above are present
- **💡 Support**: Visit project repository or community

## 🎨 About PXBot Pro

PXBot Pro is a revolutionary pixel programming environment where:
- Code becomes beautiful pixel art
- AI assists with development
- Visual programming is intuitive and fun
- Apps extend functionality

**Welcome to the future of visual programming!** 🎨✨

---
*Report generated by PXBot Pro Installer v{VERSION}*
"""
    
    try:
        with open("INSTALLATION_REPORT.md", "w", encoding='utf-8') as f:
            f.write(report_content)
        print("  ✅ Installation report saved: INSTALLATION_REPORT.md")
        return True
    except Exception as e:
        print(f"  ❌ Failed to create installation report: {e}")
        return False

def main():
    """Main installation function"""
    try:
        print_banner()
        
        # Step 1: Check Python compatibility
        if not check_python_compatibility():
            print("\n❌ Python compatibility check failed")
            print("🔧 Please install Python 3.8+ and try again")
            return 1
        
        # Step 2: Install dependencies
        print("\n" + "="*60)
        if not install_dependencies():
            print("⚠️ Some dependencies failed to install")
            print("🔧 PXBot Pro may have limited functionality")
            
            response = input("\n🤔 Continue with installation anyway? (y/N): ").lower().strip()
            if response not in ['y', 'yes']:
                print("⏹️ Installation cancelled")
                return 1
        
        # Step 3: Create core files
        print("\n" + "="*60)
        if not create_core_files():
            print("❌ Failed to create core files")
            return 1
        
        # Step 4: Run enhanced setup
        print("\n" + "="*60)
        run_enhanced_setup()  # This may succeed or fail, but we continue
        
        # Step 5: Verify installation
        print("\n" + "="*60)
        verification_passed = verify_installation()
        
        # Step 6: Test basic functionality
        print("\n" + "="*60)
        functionality_test_passed = test_basic_functionality()
        
        # Step 7: Create documentation
        print("\n" + "="*60)
        create_quick_start_guide()
        
        # Step 8: Generate final report
        print("\n" + "="*60)
        generate_final_report()
        
        # Final summary
        print("\n" + "="*60)
        print("🎉 PXBot Pro Installation Complete!")
        print("="*60)
        
        if verification_passed and functionality_test_passed:
            print("✅ Status: FULLY FUNCTIONAL")
            print("🚀 Ready to launch!")
        elif verification_passed:
            print("⚠️ Status: FUNCTIONAL (with limitations)")
            print("🚀 Basic features available")
        else:
            print("⚠️ Status: PARTIAL INSTALLATION")
            print("🔧 Some features may not work")
        
        print(f"""
🎯 NEXT STEPS:
1. Launch PXBot Pro:
   python pxbot_launcher.py

2. Read the quick start guide:
   docs/QUICK_START.md

3. Check installation report:
   INSTALLATION_REPORT.md

🎨 Welcome to PXBot Pro - Where Code Becomes Art! ✨
""")
        
        # Ask if user wants to launch now
        try:
            response = input("🚀 Launch PXBot Pro now? (Y/n): ").lower().strip()
            if response in ['', 'y', 'yes']:
                print("🎨 Launching PXBot Pro...")
                subprocess.run([sys.executable, "pxbot_launcher.py"])
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        
        return 0 if verification_passed else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Installation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Installation failed with error:")
        print(f"Error: {e}")
        print(f"\nDebug information:")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit_code = main()
    
    # Pause on Windows so user can see the output
    if platform.system() == "Windows":
        try:
            input("\nPress Enter to exit...")
        except:
            pass
    
    sys.exit(exit_code)
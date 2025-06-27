#!/usr/bin/env python3
"""
Complete PXBot Development Environment Setup
Automates the entire setup process for PXBot app development
"""

import os
import sys
import json
import shutil
import subprocess
import urllib.request
from datetime import datetime

class PXBotSetup:
    def __init__(self):
        self.setup_log = []
        self.errors = []
        self.warnings = []
        
    def log(self, message, level="info"):
        """Log setup messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        if level == "error":
            self.errors.append(message)
            print(f"❌ {log_entry}")
        elif level == "warning":
            self.warnings.append(message)
            print(f"⚠️  {log_entry}")
        else:
            print(f"✅ {log_entry}")
        
        self.setup_log.append(log_entry)
    
    def check_python_version(self):
        """Check if Python version is compatible"""
        self.log("Checking Python version...")
        
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.log(f"Python {version.major}.{version.minor} detected. Python 3.8+ required.", "error")
            return False
        else:
            self.log(f"Python {version.major}.{version.minor}.{version.micro} is compatible")
            return True
    
    def check_dependencies(self):
        """Check and install required dependencies"""
        self.log("Checking required dependencies...")
        
        required_packages = [
            'pygame',
            'pillow',
            'psutil'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.log(f"{package} is already installed")
            except ImportError:
                missing_packages.append(package)
                self.log(f"{package} is missing", "warning")
        
        if missing_packages:
            self.log(f"Installing missing packages: {', '.join(missing_packages)}")
            try:
                for package in missing_packages:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    self.log(f"Successfully installed {package}")
                return True
            except subprocess.CalledProcessError as e:
                self.log(f"Failed to install packages: {e}", "error")
                return False
        
        return True
    
    def create_directory_structure(self):
        """Create the complete directory structure"""
        self.log("Creating directory structure...")
        
        directories = [
            "apps",
            "pxbot_code",
            "pxbot_code/package_cache",
            "pxbot_code/app_backups",
            "examples",
            "docs",
            "tests"
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                self.log(f"Created directory: {directory}")
            except Exception as e:
                self.log(f"Failed to create directory {directory}: {e}", "error")
                return False
        
        return True
    
    def create_init_files(self):
        """Create necessary __init__.py files"""
        self.log("Creating __init__.py files...")
        
        init_files = [
            ("apps/__init__.py", '"""PXBot Apps Package"""'),
            ("tests/__init__.py", '"""PXBot Tests Package"""'),
        ]
        
        for file_path, content in init_files:
            try:
                if not os.path.exists(file_path):
                    with open(file_path, "w") as f:
                        f.write(content + "\n")
                    self.log(f"Created {file_path}")
            except Exception as e:
                self.log(f"Failed to create {file_path}: {e}", "error")
    
    def create_core_apps(self):
        """Create core system apps"""
        self.log("Creating core apps...")
        
        # This would contain the app creation code
        # For brevity, I'll simulate the creation
        core_apps = [
            "pxos_app.py",
            "demo_calculator.py", 
            "simple_file_manager.py",
            "advanced_web_scraper.py",
            "app_deployment_manager.py"
        ]
        
        for app in core_apps:
            app_path = os.path.join("apps", app)
            if not os.path.exists(app_path):
                self.log(f"Core app {app} needs to be created manually", "warning")
            else:
                self.log(f"Core app {app} already exists")
    
    def create_config_files(self):
        """Create default configuration files"""
        self.log("Creating configuration files...")
        
        # Main launcher config
        launcher_config = {
            "window_size": [1000, 750],
            "font_size": 16,
            "max_recent_apps": 5,
            "boot_animation": True,
            "visual_mode": True,
            "auto_save": True,
            "theme": "dark"
        }
        
        # App development config
        dev_config = {
            "auto_reload": True,
            "debug_mode": False,
            "log_level": "info",
            "backup_on_save": True,
            "template_dir": "templates",
            "test_mode": False
        }
        
        configs = [
            ("pxbot_code/launcher_config.json", launcher_config),
            ("pxbot_code/development_config.json", dev_config)
        ]
        
        for config_path, config_data in configs:
            try:
                if not os.path.exists(config_path):
                    with open(config_path, "w") as f:
                        json.dump(config_data, f, indent=2)
                    self.log(f"Created config: {config_path}")
                else:
                    self.log(f"Config already exists: {config_path}")
            except Exception as e:
                self.log(f"Failed to create config {config_path}: {e}", "error")
    
    def create_documentation(self):
        """Create comprehensive documentation"""
        self.log("Creating documentation...")
        
        # Main README
        main_readme = """# PXBot - Advanced Pixel Programming Environment

🚀 **Welcome to PXBot!** A revolutionary pixel-based programming environment where code becomes art and art becomes code.

## Quick Start

1. **Launch the visual interface:**
   ```bash
   python pxbot_launcher.py
   ```

2. **Use command mode:**
   ```bash
   python pxbot_launcher.py
   # Press Enter and type commands like:
   # calc:eval:2+2
   # scrape:url:python.org
   # file:ls
   ```

3. **Develop your own apps:**
   ```bash
   cd apps/
   cp app_template.py my_awesome_app.py
   # Edit and customize
   python my_awesome_app.py  # Test
   ```

## Features

### 🎨 **Pixel Programming**
- Store code as pixel data in PNG images
- Visual representation of code structure
- Artistic code generation and analysis

### 🧠 **Smart AI Assistant**
- Natural language code generation
- Intelligent debugging and optimization
- Code quality analysis and suggestions

### 🌐 **Web Integration**
- Built-in web browser and scraper
- API integration tools
- Real-time data processing

### 📱 **App Ecosystem**
- Modular app system
- Package manager for distribution
- Template-based development

## Available Apps

### Core Apps
- **PXOS Core** - System interface and management
- **Demo Calculator** - Advanced calculator with pixel integration
- **File Manager** - File system operations
- **Web Scraper** - Web data extraction and analysis
- **Deployment Manager** - App packaging and distribution

### Development Tools
- **App Template** - Starting point for new apps
- **Setup Script** - Environment configuration
- **Testing Framework** - App validation and testing

## Architecture

```
PXBot/
├── pxbot_launcher.py      # Main launcher with visual interface
├── pxbot_runtime.py       # Core runtime and pixel tools
├── apps/                  # Modular application system
│   ├── pxos_app.py       # Core system interface
│   ├── *.py              # Various apps
│   └── app_template.py   # Template for new apps
├── pxbot_code/           # Generated code and data storage
│   ├── *.png             # Pixel-encoded code files
│   ├── *.json            # Configuration and state
│   └── package_cache/    # Downloaded packages
└── docs/                 # Documentation
```

## Development

### Creating Apps
1. Copy `apps/app_template.py` to your new app name
2. Implement the required methods:
   - `__init__(self, pxbot_instance=None)`
   - `execute_command(self, command)`
   - `main()` function
3. Test with `python your_app.py`
4. Use in launcher with `yourapp:command`

### Command Format
Apps use the format: `appname:action:parameters`

Examples:
- `calc:eval:2+2*3`
- `file:ls:/home/user`
- `scrape:url:example.com`
- `deploy:package:my_app`

## Pixel Programming

PXBot's unique feature is storing code as pixel data:

1. **Code → Pixels**: Python code is encoded into PNG images
2. **Visual Analysis**: Code structure becomes visual patterns
3. **Artistic Output**: Generate pixel art from code patterns
4. **Compression**: Efficient storage and transmission

## Contributing

1. Fork the repository
2. Create your app following the template
3. Test thoroughly
4. Submit pull request with documentation

## License

MIT License - See LICENSE file for details

## Support

- 📖 Read the docs in `docs/`
- 🐛 Report issues on GitHub
- 💬 Join the community discussions
- 📧 Contact: support@pxbot.dev

---

**Happy Pixel Programming!** 🎨✨
"""
        
        # Developer guide
        dev_guide = """# PXBot Developer Guide

## App Development Workflow

### 1. Environment Setup
```bash
python setup.py  # Run the setup script
cd apps/
```

### 2. Create New App
```bash
cp app_template.py my_new_app.py
```

### 3. App Structure
```python
class MyNewApp:
    def __init__(self, pxbot_instance=None):
        self.name = "My New App"
        self.version = "1.0.0"
        self.pxbot = pxbot_instance
    
    def execute_command(self, command):
        # Handle commands starting with "myapp:"
        pass

def main():
    return MyNewApp()
```

### 4. Command Handling
```python
def execute_command(self, command):
    if command.startswith("myapp:"):
        cmd = command[6:]  # Remove prefix
        parts = cmd.split(":")
        action = parts[0]
        
        if action == "hello":
            return "Hello from my app!"
        elif action == "process":
            data = parts[1] if len(parts) > 1 else ""
            return self.process_data(data)
```

### 5. PXBot Integration
```python
def export_to_pixels(self, name):
    if self.pxbot:
        code = "# Generated code\\nprint('Hello!')"
        result = self.pxbot.run(f"save:{name}:{code}")
        return f"Exported as pixel code: {result}"
```

## Testing

### Unit Testing
```python
# tests/test_my_app.py
import unittest
from apps.my_app import MyApp

class TestMyApp(unittest.TestCase):
    def setUp(self):
        self.app = MyApp()
    
    def test_basic_functionality(self):
        result = self.app.execute_command("myapp:hello")
        self.assertIn("Hello", result)
```

### Integration Testing
```bash
python pxbot_launcher.py
# Test commands in the launcher
```

## Deployment

### Package Creation
```bash
deploy:package:my_app
```

### Distribution
1. Creates `.pxapp` file (ZIP format)
2. Contains app file, manifest, documentation
3. Can be shared or uploaded to repositories

### Installation
```bash
deploy:install:my_app.pxapp
```

## Best Practices

### Code Quality
- Use meaningful variable names
- Add docstrings to methods
- Handle errors gracefully
- Follow PEP 8 style guide

### User Experience
- Provide clear help commands
- Use consistent command patterns
- Give informative error messages
- Support common use cases

### Performance
- Minimize startup time
- Cache frequently used data
- Use efficient algorithms
- Clean up resources properly

### Security
- Validate user inputs
- Avoid dangerous operations
- Don't execute arbitrary code
- Respect file system permissions

## Advanced Features

### State Persistence
```python
def save_state(self):
    state_file = os.path.join("pxbot_code", f"{self.name}_state.json")
    with open(state_file, "w") as f:
        json.dump(self.state, f)
```

### Configuration Management
```python
def load_config(self):
    config_file = os.path.join("pxbot_code", f"{self.name}_config.json")
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            return json.load(f)
    return self.default_config
```

### Event Handling
```python
def on_app_loaded(self):
    # Called when app is loaded
    pass

def on_app_unloaded(self):
    # Called when app is unloaded
    self.cleanup()
```

## API Reference

### PXBot Runtime Methods
- `pxbot.run(command)` - Execute PXBot command
- `pxbot.r.list_codes()` - List saved codes
- `pxbot.r.load_code(name)` - Load code content
- `pxbot.r.exec_code(name)` - Execute saved code

### Launcher Integration
- Apps are automatically discovered in `apps/` directory
- Main function must return app instance
- Commands are routed based on prefix

### Pixel Tools
```python
from pxbot_runtime import PixelProgrammingTools

tools = PixelProgrammingTools(pxbot_instance)
tools.create_pixel_art_from_code("my_code")
tools.analyze_pixel_density("my_code")
tools.merge_pixel_codes("code1", "code2", "merged")
```

## Troubleshooting

### Common Issues
1. **Import errors**: Check Python path and dependencies
2. **Command not found**: Verify app prefix and registration
3. **Pixel encoding fails**: Check code syntax and encoding
4. **Performance issues**: Profile code and optimize bottlenecks

### Debug Mode
```bash
python pxbot_launcher.py --debug
```

### Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Resources

- **Examples**: Check `examples/` directory
- **Templates**: Use `apps/app_template.py`
- **Testing**: See `tests/` directory
- **Documentation**: Read `docs/` files

---

Happy developing! 🚀
"""
        
        docs = [
            ("README.md", main_readme),
            ("docs/DEVELOPER_GUIDE.md", dev_guide)
        ]
        
        for doc_path, content in docs:
            try:
                os.makedirs(os.path.dirname(doc_path), exist_ok=True)
                if not os.path.exists(doc_path):
                    with open(doc_path, "w", encoding='utf-8') as f:
                        f.write(content)
                    self.log(f"Created documentation: {doc_path}")
                else:
                    self.log(f"Documentation already exists: {doc_path}")
            except Exception as e:
                self.log(f"Failed to create doc {doc_path}: {e}", "error")
    
    def create_example_files(self):
        """Create example files and tutorials"""
        self.log("Creating example files...")
        
        # Simple example app
        simple_example = '''#!/usr/bin/env python3
"""
Hello World App - Simple example for PXBot
"""

class HelloWorldApp:
    def __init__(self, pxbot_instance=None):
        self.name = "Hello World"
        self.version = "1.0.0"
        self.pxbot = pxbot_instance
        self.message_count = 0
    
    def execute_command(self, command):
        if command.startswith("hello:"):
            cmd = command[6:]
            
            if cmd == "world":
                self.message_count += 1
                return f"Hello, World! (Message #{self.message_count})"
            elif cmd == "user":
                return "Hello, User! Welcome to PXBot!"
            elif cmd.startswith("name:"):
                name = cmd[5:]
                return f"Hello, {name}! Nice to meet you!"
            elif cmd == "stats":
                return f"Hello statistics: {self.message_count} messages sent"
            else:
                return "Commands: hello:world, hello:user, hello:name:YourName, hello:stats"
        
        return "Use hello: prefix for commands"

def main():
    return HelloWorldApp()

if __name__ == "__main__":
    app = main()
    print("Hello World App Test")
    print(app.execute_command("hello:world"))
    print(app.execute_command("hello:name:Alice"))
'''
        
        # Tutorial script
        tutorial_script = '''#!/usr/bin/env python3
"""
PXBot Tutorial - Interactive learning script
"""

def run_tutorial():
    print("🎓 Welcome to the PXBot Tutorial!")
    print("=" * 50)
    
    steps = [
        ("Launch PXBot", "python pxbot_launcher.py"),
        ("Try calculator", "calc:eval:2+3*4"),
        ("List files", "file:ls"),
        ("Create pixel art", "scrape:url:example.com"),
        ("Package an app", "deploy:package:hello_world"),
        ("Get help", "Any command with :help")
    ]
    
    for i, (description, command) in enumerate(steps, 1):
        print(f"\\nStep {i}: {description}")
        print(f"Command: {command}")
        input("Press Enter to continue...")
    
    print("\\n🎉 Tutorial complete! Happy coding!")

if __name__ == "__main__":
    run_tutorial()
'''
        
        examples = [
            ("examples/hello_world_app.py", simple_example),
            ("examples/tutorial.py", tutorial_script)
        ]
        
        for example_path, content in examples:
            try:
                if not os.path.exists(example_path):
                    with open(example_path, "w") as f:
                        f.write(content)
                    self.log(f"Created example: {example_path}")
                else:
                    self.log(f"Example already exists: {example_path}")
            except Exception as e:
                self.log(f"Failed to create example {example_path}: {e}", "error")
    
    def create_test_files(self):
        """Create test framework and example tests"""
        self.log("Creating test files...")
        
        test_runner = '''#!/usr/bin/env python3
"""
PXBot Test Runner - Run all app tests
"""

import unittest
import sys
import os

# Add apps directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps'))

def run_all_tests():
    """Run all tests in the tests directory"""
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
'''
        
        example_test = '''#!/usr/bin/env python3
"""
Example test for PXBot apps
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from apps.demo_calculator import DemoCalculator
except ImportError:
    DemoCalculator = None

class TestDemoCalculator(unittest.TestCase):
    def setUp(self):
        if DemoCalculator:
            self.calc = DemoCalculator()
    
    @unittest.skipIf(DemoCalculator is None, "DemoCalculator not available")
    def test_basic_calculation(self):
        result = self.calc.execute_command("calc:eval:2+2")
        self.assertIn("4", result)
    
    @unittest.skipIf(DemoCalculator is None, "DemoCalculator not available")
    def test_invalid_command(self):
        result = self.calc.execute_command("invalid:command")
        self.assertIn("calc:", result)

if __name__ == "__main__":
    unittest.main()
'''
        
        tests = [
            ("tests/run_tests.py", test_runner),
            ("tests/test_calculator.py", example_test)
        ]
        
        for test_path, content in tests:
            try:
                if not os.path.exists(test_path):
                    with open(test_path, "w") as f:
                        f.write(content)
                    self.log(f"Created test: {test_path}")
                else:
                    self.log(f"Test already exists: {test_path}")
            except Exception as e:
                self.log(f"Failed to create test {test_path}: {e}", "error")
    
    def create_launch_scripts(self):
        """Create convenient launch scripts"""
        self.log("Creating launch scripts...")
        
        # Windows batch file
        windows_launcher = '''@echo off
echo Starting PXBot...
python pxbot_launcher.py %*
pause
'''
        
        # Unix shell script
        unix_launcher = '''#!/bin/bash
echo "Starting PXBot..."
python3 pxbot_launcher.py "$@"
'''
        
        # Development script
        dev_launcher = '''#!/usr/bin/env python3
"""
Development launcher with extra debugging features
"""

import sys
import os
import subprocess

def main():
    print("🚀 PXBot Development Mode")
    print("=" * 30)
    
    # Check for runtime files
    required_files = ["pxbot_launcher.py", "pxbot_runtime.py"]
    missing = [f for f in required_files if not os.path.exists(f)]
    
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return 1
    
    # Add debug flags
    args = ["python", "pxbot_launcher.py"] + sys.argv[1:]
    
    try:
        return subprocess.call(args)
    except KeyboardInterrupt:
        print("\\n👋 Development session ended")
        return 0

if __name__ == "__main__":
    sys.exit(main())
'''
        
        launchers = [
            ("launch.bat", windows_launcher),
            ("launch.sh", unix_launcher),
            ("dev.py", dev_launcher)
        ]
        
        for launcher_path, content in launchers:
            try:
                if not os.path.exists(launcher_path):
                    with open(launcher_path, "w") as f:
                        f.write(content)
                    
                    # Make shell scripts executable
                    if launcher_path.endswith('.sh'):
                        os.chmod(launcher_path, 0o755)
                    
                    self.log(f"Created launcher: {launcher_path}")
                else:
                    self.log(f"Launcher already exists: {launcher_path}")
            except Exception as e:
                self.log(f"Failed to create launcher {launcher_path}: {e}", "error")
    
    def verify_setup(self):
        """Verify that the setup was completed successfully"""
        self.log("Verifying setup...")
        
        # Check critical files
        critical_files = [
            "pxbot_launcher.py",
            "pxbot_runtime.py",
            "apps/__init__.py",
            "README.md"
        ]
        
        missing_critical = []
        for file_path in critical_files:
            if not os.path.exists(file_path):
                missing_critical.append(file_path)
        
        if missing_critical:
            self.log(f"Critical files missing: {', '.join(missing_critical)}", "error")
            return False
        
        # Check directory structure
        required_dirs = ["apps", "pxbot_code", "docs", "examples", "tests"]
        missing_dirs = []
        for directory in required_dirs:
            if not os.path.exists(directory):
                missing_dirs.append(directory)
        
        if missing_dirs:
            self.log(f"Directories missing: {', '.join(missing_dirs)}", "warning")
        
        # Test import
        try:
            sys.path.insert(0, '.')
            import pxbot_runtime
            self.log("PXBot runtime import successful")
        except ImportError as e:
            self.log(f"Failed to import runtime: {e}", "error")
            return False
        
        return True
    
    def generate_setup_report(self):
        """Generate a comprehensive setup report"""
        self.log("Generating setup report...")
        
        report = f"""
# PXBot Setup Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Setup Summary
- ✅ Steps completed: {len(self.setup_log)}
- ⚠️  Warnings: {len(self.warnings)}
- ❌ Errors: {len(self.errors)}

## Setup Log
"""
        
        for entry in self.setup_log:
            report += f"- {entry}\n"
        
        if self.warnings:
            report += f"\n## Warnings\n"
            for warning in self.warnings:
                report += f"- ⚠️  {warning}\n"
        
        if self.errors:
            report += f"\n## Errors\n"
            for error in self.errors:
                report += f"- ❌ {error}\n"
        
        report += f"""
## Next Steps

1. **Test the installation:**
   ```bash
   python pxbot_launcher.py
   ```

2. **Run the tutorial:**
   ```bash
   python examples/tutorial.py
   ```

3. **Create your first app:**
   ```bash
   cd apps/
   cp app_template.py my_first_app.py
   # Edit the file
   python my_first_app.py
   ```

4. **Run tests:**
   ```bash
   python tests/run_tests.py
   ```

## Resources

- 📖 **Documentation:** `docs/DEVELOPER_GUIDE.md`
- 🎯 **Examples:** `examples/` directory
- 🧪 **Tests:** `tests/` directory
- 🚀 **Quick Start:** `README.md`

## Support

If you encounter issues:
1. Check the error messages above
2. Read the documentation
3. Run with debug mode: `python pxbot_launcher.py --debug`
4. Ask for help in the community

Happy coding! 🎨✨
"""
        
        report_path = "SETUP_REPORT.md"
        try:
            with open(report_path, "w", encoding='utf-8') as f:
                f.write(report)
            self.log(f"Setup report saved to: {report_path}")
        except Exception as e:
            self.log(f"Failed to save setup report: {e}", "error")
        
        return report
    
    def run_complete_setup(self):
        """Run the complete setup process"""
        print("🚀 PXBot Complete Development Environment Setup")
        print("=" * 60)
        print("This will set up everything you need for PXBot development.")
        print()
        
        # Confirm setup
        response = input("Do you want to proceed? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            print("Setup cancelled.")
            return False
        
        print("\n🔧 Starting setup process...\n")
        
        # Run all setup steps
        setup_steps = [
            ("Checking Python version", self.check_python_version),
            ("Installing dependencies", self.check_dependencies),
            ("Creating directories", self.create_directory_structure),
            ("Creating init files", self.create_init_files),
            ("Creating configurations", self.create_config_files),
            ("Creating documentation", self.create_documentation),
            ("Creating examples", self.create_example_files),
            ("Creating tests", self.create_test_files),
            ("Creating launchers", self.create_launch_scripts),
            ("Verifying setup", self.verify_setup)
        ]
        
        failed_steps = []
        
        for step_name, step_function in setup_steps:
            print(f"\n📋 {step_name}...")
            try:
                success = step_function()
                if not success:
                    failed_steps.append(step_name)
            except Exception as e:
                self.log(f"Exception in {step_name}: {e}", "error")
                failed_steps.append(step_name)
        
        # Generate report
        print(f"\n📊 Generating setup report...")
        report = self.generate_setup_report()
        
        # Final summary
        print(f"\n🎉 Setup Complete!")
        print(f"=" * 30)
        print(f"✅ Successful steps: {len(setup_steps) - len(failed_steps)}")
        print(f"❌ Failed steps: {len(failed_steps)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if failed_steps:
            print(f"\nFailed steps: {', '.join(failed_steps)}")
            print(f"Check SETUP_REPORT.md for details.")
        
        if not self.errors:
            print(f"\n🚀 Ready to start developing!")
            print(f"Try: python pxbot_launcher.py")
        else:
            print(f"\n⚠️  Setup completed with errors.")
            print(f"Please review the setup report and fix issues.")
        
        return len(failed_steps) == 0

def main():
    """Main setup function"""
    try:
        setup = PXBotSetup()
        success = setup.run_complete_setup()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Setup failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
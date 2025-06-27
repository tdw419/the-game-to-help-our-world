#!/usr/bin/env python3
"""
PXBot Pro - Enhanced Setup Script
Complete environment setup with app ecosystem initialization
"""

import os
import sys
import json
import shutil
import subprocess
import urllib.request
import zipfile
import tempfile
import platform
from datetime import datetime
import traceback

class PXBotProSetup:
    def __init__(self):
        self.setup_log = []
        self.errors = []
        self.warnings = []
        self.version = "2.0.0"
        
    def log(self, message, level="info"):
        """Enhanced logging with colors and levels"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        if level == "error":
            self.errors.append(message)
            print(f"\033[91m❌ {log_entry}\033[0m")
        elif level == "warning":
            self.warnings.append(message)
            print(f"\033[93m⚠️  {log_entry}\033[0m")
        elif level == "success":
            print(f"\033[92m✅ {log_entry}\033[0m")
        else:
            print(f"\033[94mℹ️  {log_entry}\033[0m")
        
        self.setup_log.append(log_entry)
    
    def check_system_requirements(self):
        """Check system requirements and compatibility"""
        self.log("Checking system requirements...", "info")
        
        # Python version check
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.log(f"Python {version.major}.{version.minor} detected. Python 3.8+ required.", "error")
            return False
        else:
            self.log(f"Python {version.major}.{version.minor}.{version.micro} ✓", "success")
        
        # System info
        self.log(f"Platform: {platform.system()} {platform.release()}", "info")
        self.log(f"Architecture: {platform.machine()}", "info")
        
        # Available memory check
        try:
            import psutil
            memory = psutil.virtual_memory()
            self.log(f"Available RAM: {memory.available // (1024**3)} GB", "info")
            if memory.available < 1024**3:  # Less than 1GB
                self.log("Low memory detected - some features may be limited", "warning")
        except ImportError:
            self.log("psutil not available - memory check skipped", "info")
        
        return True
    
    def install_dependencies(self):
        """Install all required dependencies"""
        self.log("Installing dependencies...", "info")
        
        # Core dependencies
        core_packages = [
            'pygame>=2.0.0',
            'pillow>=8.0.0',
            'psutil>=5.8.0'
        ]
        
        # Optional dependencies
        optional_packages = [
            'requests>=2.25.0',
            'beautifulsoup4>=4.9.0',
            'numpy>=1.20.0',
            'matplotlib>=3.3.0'
        ]
        
        # Install core packages
        for package in core_packages:
            self.log(f"Installing {package}...", "info")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package, "--upgrade"
                ], capture_output=True)
                self.log(f"Successfully installed {package}", "success")
            except subprocess.CalledProcessError as e:
                self.log(f"Failed to install {package}: {e}", "error")
                return False
        
        # Install optional packages (non-critical)
        for package in optional_packages:
            self.log(f"Installing optional {package}...", "info")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package, "--upgrade"
                ], capture_output=True)
                self.log(f"Successfully installed optional {package}", "success")
            except subprocess.CalledProcessError:
                self.log(f"Optional package {package} failed - skipping", "warning")
        
        return True
    
    def create_directory_structure(self):
        """Create complete directory structure"""
        self.log("Creating directory structure...", "info")
        
        directories = [
            "apps",
            "apps/core",
            "apps/utilities", 
            "apps/examples",
            "pxbot_code",
            "pxbot_code/package_cache",
            "pxbot_code/app_backups",
            "pxbot_code/user_data",
            "pxbot_code/exports",
            "pxbot_code/temp",
            "examples",
            "examples/basic",
            "examples/advanced",
            "docs",
            "docs/api",
            "docs/tutorials",
            "tests",
            "tests/unit",
            "tests/integration",
            "templates",
            "templates/apps",
            "templates/projects",
            "tools",
            "tools/scripts",
            "tools/utilities"
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                self.log(f"Created directory: {directory}", "success")
            except Exception as e:
                self.log(f"Failed to create directory {directory}: {e}", "error")
                return False
        
        # Create __init__.py files
        init_files = [
            "apps/__init__.py",
            "apps/core/__init__.py", 
            "apps/utilities/__init__.py",
            "apps/examples/__init__.py",
            "tests/__init__.py",
            "tests/unit/__init__.py",
            "tests/integration/__init__.py"
        ]
        
        for init_file in init_files:
            try:
                with open(init_file, "w") as f:
                    f.write(f'"""PXBot Package: {os.path.dirname(init_file)}"""\n')
                self.log(f"Created {init_file}", "success")
            except Exception as e:
                self.log(f"Failed to create {init_file}: {e}", "error")
        
        return True
    
    def create_configuration_files(self):
        """Create comprehensive configuration files"""
        self.log("Creating configuration files...", "info")
        
        # Main PXBot configuration
        main_config = {
            "version": self.version,
            "installation_date": datetime.now().isoformat(),
            "window_size": [1200, 800],
            "font_size": 16,
            "theme": "dark",
            "auto_save": True,
            "boot_animation": True,
            "visual_mode": True,
            "max_recent_apps": 10,
            "debug_mode": False,
            "log_level": "info",
            "backup_on_save": True,
            "max_history": 100
        }
        
        # Development configuration
        dev_config = {
            "auto_reload": True,
            "hot_reload": False,
            "template_dir": "templates",
            "test_mode": False,
            "profiling": False,
            "code_analysis": True,
            "lint_on_save": False,
            "auto_format": False
        }
        
        # App ecosystem configuration
        app_config = {
            "app_directories": ["apps/core", "apps/utilities", "apps/examples"],
            "auto_discover": True,
            "load_order": ["core", "utilities", "examples"],
            "sandbox_mode": True,
            "max_apps": 50,
            "resource_limits": {
                "memory_mb": 256,
                "cpu_percent": 80,
                "file_operations": 1000
            }
        }
        
        # Web scraper configuration
        web_config = {
            "user_agent": "PXBot-Pro/2.0 (+https://pxbot.dev)",
            "timeout": 30,
            "max_retries": 3,
            "delay_between_requests": 1.0,
            "max_content_length": 10485760,  # 10MB
            "allowed_domains": [],
            "blocked_domains": [],
            "respect_robots_txt": True,
            "cache_responses": True,
            "cache_duration": 3600
        }
        
        # Deployment configuration
        deploy_config = {
            "package_format": "zip",
            "compression_level": 6,
            "include_dependencies": True,
            "sign_packages": False,
            "verify_signatures": False,
            "auto_update": False,
            "repositories": {
                "official": "https://github.com/pxbot-official/apps",
                "community": "https://github.com/pxbot-community/apps",
                "local": "./local_repo"
            }
        }
        
        configs = [
            ("pxbot_code/main_config.json", main_config),
            ("pxbot_code/development_config.json", dev_config),
            ("pxbot_code/app_config.json", app_config),
            ("pxbot_code/web_config.json", web_config),
            ("pxbot_code/deployment_config.json", deploy_config)
        ]
        
        for config_path, config_data in configs:
            try:
                with open(config_path, "w") as f:
                    json.dump(config_data, f, indent=2)
                self.log(f"Created config: {config_path}", "success")
            except Exception as e:
                self.log(f"Failed to create config {config_path}: {e}", "error")
        
        return True
    
    def create_utility_apps(self):
        """Create additional utility applications"""
        self.log("Creating utility applications...", "info")
        
        # System Monitor App
        system_monitor_code = '''#!/usr/bin/env python3
"""
PXBot System Monitor - Real-time system monitoring and performance analysis
"""

import psutil
import time
import json
import os
from datetime import datetime

class SystemMonitor:
    def __init__(self, pxbot_instance=None):
        self.name = "System Monitor"
        self.version = "1.0.0"
        self.description = "Real-time system monitoring and performance analysis"
        self.pxbot = pxbot_instance
        
        self.monitoring = False
        self.stats_history = []
        self.alerts = []
        self.thresholds = {
            "cpu_percent": 80,
            "memory_percent": 85,
            "disk_percent": 90,
            "temperature": 70
        }
    
    def execute_command(self, command):
        try:
            if command.startswith("monitor:"):
                cmd = command[8:]
                return self.handle_monitor_command(cmd)
            return "Use monitor: prefix for system monitoring commands"
        except Exception as e:
            return f"Error: {e}"
    
    def handle_monitor_command(self, command):
        parts = command.split(":")
        action = parts[0]
        
        if action == "start":
            self.monitoring = True
            return "🔄 System monitoring started"
        
        elif action == "stop":
            self.monitoring = False
            return "⏹️ System monitoring stopped"
        
        elif action == "current":
            return self.get_current_stats()
        
        elif action == "history":
            count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
            return self.get_stats_history(count)
        
        elif action == "processes":
            count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
            return self.get_top_processes(count)
        
        elif action == "alerts":
            return self.get_alerts()
        
        elif action == "threshold":
            if len(parts) >= 3:
                metric, value = parts[1], parts[2]
                return self.set_threshold(metric, value)
            return self.show_thresholds()
        
        elif action == "benchmark":
            return self.run_benchmark()
        
        elif action == "export":
            filename = parts[1] if len(parts) > 1 else "system_stats"
            return self.export_data(filename)
        
        return "Commands: start, stop, current, history, processes, alerts, threshold, benchmark, export"
    
    def get_current_stats(self):
        try:
            # CPU information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk information
            disk = psutil.disk_usage('/')
            
            # Network information
            network = psutil.net_io_counters()
            
            # Temperature (if available)
            try:
                temps = psutil.sensors_temperatures()
                cpu_temp = temps.get('cpu-thermal', [{}])[0].get('current', 0)
            except:
                cpu_temp = 0
            
            stats = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "frequency": cpu_freq.current if cpu_freq else 0,
                    "temperature": cpu_temp
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "percent": swap.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            }
            
            # Store in history
            self.stats_history.append(stats)
            if len(self.stats_history) > 1000:
                self.stats_history = self.stats_history[-1000:]
            
            # Check thresholds
            self.check_thresholds(stats)
            
            # Format output
            return f"""📊 **Current System Statistics**

**🖥️ CPU:**
• Usage: {cpu_percent:.1f}%
• Cores: {cpu_count}
• Frequency: {cpu_freq.current if cpu_freq else 0:.0f} MHz
• Temperature: {cpu_temp:.1f}°C

**🧠 Memory:**
• Used: {memory.used / (1024**3):.1f} GB / {memory.total / (1024**3):.1f} GB ({memory.percent:.1f}%)
• Available: {memory.available / (1024**3):.1f} GB
• Swap: {swap.used / (1024**3):.1f} GB / {swap.total / (1024**3):.1f} GB ({swap.percent:.1f}%)

**💾 Disk:**
• Used: {disk.used / (1024**3):.1f} GB / {disk.total / (1024**3):.1f} GB ({(disk.used/disk.total)*100:.1f}%)
• Free: {disk.free / (1024**3):.1f} GB

**🌐 Network:**
• Sent: {network.bytes_sent / (1024**2):.1f} MB
• Received: {network.bytes_recv / (1024**2):.1f} MB
• Packets: {network.packets_sent + network.packets_recv:,}"""
            
        except Exception as e:
            return f"❌ Error getting system stats: {e}"
    
    def get_top_processes(self, count=10):
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            result = f"🔍 **Top {count} Processes by CPU Usage:**\\n\\n"
            for i, proc in enumerate(processes[:count], 1):
                result += f"{i:2d}. {proc['name'][:20]:<20} CPU: {proc['cpu_percent']:>5.1f}% RAM: {proc['memory_percent']:>5.1f}%\\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error getting process list: {e}"
    
    def check_thresholds(self, stats):
        alerts = []
        
        if stats['cpu']['percent'] > self.thresholds['cpu_percent']:
            alerts.append(f"High CPU usage: {stats['cpu']['percent']:.1f}%")
        
        if stats['memory']['percent'] > self.thresholds['memory_percent']:
            alerts.append(f"High memory usage: {stats['memory']['percent']:.1f}%")
        
        if stats['disk']['percent'] > self.thresholds['disk_percent']:
            alerts.append(f"High disk usage: {stats['disk']['percent']:.1f}%")
        
        if stats['cpu']['temperature'] > self.thresholds['temperature']:
            alerts.append(f"High temperature: {stats['cpu']['temperature']:.1f}°C")
        
        for alert in alerts:
            self.alerts.append({
                "timestamp": datetime.now().isoformat(),
                "message": alert,
                "level": "warning"
            })
            
        # Keep only recent alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    def run_benchmark(self):
        self.log("Running system benchmark...", "info")
        try:
            import time
            
            # CPU benchmark
            start_time = time.time()
            result = sum(i * i for i in range(100000))
            cpu_time = time.time() - start_time
            
            # Memory benchmark
            start_time = time.time()
            data = [i for i in range(1000000)]
            memory_time = time.time() - start_time
            del data
            
            # Disk benchmark
            start_time = time.time()
            test_file = "pxbot_code/temp/benchmark_test.tmp"
            os.makedirs(os.path.dirname(test_file), exist_ok=True)
            with open(test_file, "w") as f:
                f.write("x" * 1000000)  # 1MB test file
            with open(test_file, "r") as f:
                content = f.read()
            os.remove(test_file)
            disk_time = time.time() - start_time
            
            return f"""⚡ **System Benchmark Results**

**🖥️ CPU Test:** {cpu_time:.3f} seconds
**🧠 Memory Test:** {memory_time:.3f} seconds  
**💾 Disk I/O Test:** {disk_time:.3f} seconds

**📊 Performance Score:**
• CPU: {100/cpu_time:.0f} points
• Memory: {100/memory_time:.0f} points
• Disk: {100/disk_time:.0f} points
• Overall: {(100/cpu_time + 100/memory_time + 100/disk_time)/3:.0f} points"""
            
        except Exception as e:
            return f"❌ Benchmark failed: {e}"
    
    def export_data(self, filename):
        try:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "system_info": {
                    "platform": psutil.os.name,
                    "cpu_count": psutil.cpu_count(),
                    "total_memory": psutil.virtual_memory().total
                },
                "stats_history": self.stats_history[-100:],  # Last 100 entries
                "alerts": self.alerts,
                "thresholds": self.thresholds
            }
            
            export_path = f"pxbot_code/exports/{filename}.json"
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            with open(export_path, "w") as f:
                json.dump(export_data, f, indent=2)
            
            return f"📊 System data exported to: {export_path}"
            
        except Exception as e:
            return f"❌ Export failed: {e}"

def main():
    return SystemMonitor()

if __name__ == "__main__":
    app = main()
    print("System Monitor Test")
    print(app.execute_command("monitor:current"))
'''
        
        # App Template Generator
        template_generator_code = '''#!/usr/bin/env python3
"""
PXBot App Template Generator - Create new apps from templates
"""

import os
import json
from datetime import datetime

class AppTemplateGenerator:
    def __init__(self, pxbot_instance=None):
        self.name = "App Template Generator"
        self.version = "1.0.0"
        self.description = "Generate new apps from customizable templates"
        self.pxbot = pxbot_instance
        
        self.templates = {
            "basic": self.get_basic_template(),
            "advanced": self.get_advanced_template(),
            "utility": self.get_utility_template(),
            "analyzer": self.get_analyzer_template(),
            "web_tool": self.get_web_tool_template()
        }
    
    def execute_command(self, command):
        try:
            if command.startswith("template:"):
                cmd = command[9:]
                return self.handle_template_command(cmd)
            return "Use template: prefix for app template commands"
        except Exception as e:
            return f"Error: {e}"
    
    def handle_template_command(self, command):
        parts = command.split(":")
        action = parts[0]
        
        if action == "list":
            return self.list_templates()
        
        elif action == "create":
            if len(parts) >= 3:
                template_type = parts[1]
                app_name = parts[2]
                description = parts[3] if len(parts) > 3 else "Generated app"
                return self.create_app(template_type, app_name, description)
            return "Usage: template:create:type:name:description"
        
        elif action == "show":
            template_type = parts[1] if len(parts) > 1 else ""
            return self.show_template(template_type)
        
        elif action == "customize":
            return self.customize_template_guide()
        
        return "Commands: list, create:type:name:description, show:type, customize"
    
    def list_templates(self):
        result = "🛠️ **Available App Templates:**\\n\\n"
        
        for template_name, template_info in self.templates.items():
            result += f"• **{template_name}** - {template_info['description']}\\n"
        
        result += "\\n**Usage:** template:create:type:name:description"
        return result
    
    def create_app(self, template_type, app_name, description):
        if template_type not in self.templates:
            return f"❌ Unknown template type: {template_type}\\nAvailable: {', '.join(self.templates.keys())}"
        
        try:
            template = self.templates[template_type]
            
            # Generate app code
            app_code = template['code'].format(
                app_name=app_name,
                class_name=self.to_class_name(app_name),
                description=description,
                creation_date=datetime.now().strftime("%Y-%m-%d"),
                version="1.0.0"
            )
            
            # Save to file
            filename = f"apps/utilities/{app_name.lower().replace(' ', '_')}.py"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, "w") as f:
                f.write(app_code)
            
            # Create documentation
            doc_content = f"""# {app_name}

{description}

## Generated from template: {template_type}
## Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Usage

```bash
{app_name.lower().replace(' ', '_')}:help
```

## Commands

{template.get('usage_examples', 'See app help for available commands')}

## Features

{template.get('features', 'Standard template features')}
"""
            
            doc_filename = f"docs/{app_name.lower().replace(' ', '_')}.md"
            os.makedirs(os.path.dirname(doc_filename), exist_ok=True)
            
            with open(doc_filename, "w") as f:
                f.write(doc_content)
            
            return f"""✅ **App Created Successfully!**

**📱 App:** {app_name}
**📁 File:** {filename}
**📚 Docs:** {doc_filename}
**🛠️ Template:** {template_type}

**Next Steps:**
1. Test: `python {filename}`
2. Customize the code as needed
3. Use in launcher: `{app_name.lower().replace(' ', '_')}:help`"""
            
        except Exception as e:
            return f"❌ Error creating app: {e}"
    
    def to_class_name(self, app_name):
        return ''.join(word.capitalize() for word in app_name.replace('_', ' ').split())
    
    def get_basic_template(self):
        return {
            "description": "Simple app with basic command handling",
            "code": '''#!/usr/bin/env python3
"""
{app_name} - {description}
Generated on {creation_date}
"""

class {class_name}:
    def __init__(self, pxbot_instance=None):
        self.name = "{app_name}"
        self.version = "{version}"
        self.description = "{description}"
        self.pxbot = pxbot_instance
        
        # App state
        self.data = {{}}
        self.config = {{"setting1": "default_value"}}
    
    def execute_command(self, command):
        try:
            prefix = "{app_name}".lower().replace(" ", "_") + ":"
            if command.startswith(prefix):
                cmd = command[len(prefix):]
                return self.handle_command(cmd)
            return f"Use {{prefix}} prefix for commands"
        except Exception as e:
            return f"Error: {{e}}"
    
    def handle_command(self, command):
        parts = command.split(":")
        action = parts[0]
        
        if action == "hello":
            return f"Hello from {{self.name}}!"
        
        elif action == "status":
            return f"{{self.name}} v{{self.version}} - Status: OK"
        
        elif action == "help":
            return self.show_help()
        
        else:
            return f"Unknown command: {{action}}\\nTry: help"
    
    def show_help(self):
        return f"""🔧 **{{self.name}} Help**

**Commands:**
• hello - Say hello
• status - Show app status  
• help - Show this help

**Usage:**
{{self.name.lower().replace(" ", "_")}}:command"""

def main():
    return {class_name}()

if __name__ == "__main__":
    app = main()
    print(f"{{app.name}} Test")
    print(app.execute_command("{app_name}:hello".lower().replace(" ", "_")))
''',
            "features": "Basic command handling, help system, status reporting",
            "usage_examples": "hello, status, help"
        }
    
    def get_advanced_template(self):
        return {
            "description": "Advanced app with configuration, persistence, and error handling",
            "code": '''#!/usr/bin/env python3
"""
{app_name} - {description}
Generated on {creation_date}
"""

import os
import json
from datetime import datetime

class {class_name}:
    def __init__(self, pxbot_instance=None):
        self.name = "{app_name}"
        self.version = "{version}"
        self.description = "{description}"
        self.pxbot = pxbot_instance
        
        # App state
        self.data = {{}}
        self.history = []
        self.config = self.load_config()
        self.session_start = datetime.now()
    
    def load_config(self):
        config_path = os.path.join("pxbot_code", f"{{self.name.lower().replace(' ', '_')}}_config.json")
        default_config = {{
            "auto_save": True,
            "max_history": 100,
            "debug_mode": False
        }}
        
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            print(f"Config load error: {{e}}")
        
        return default_config
    
    def save_config(self):
        config_path = os.path.join("pxbot_code", f"{{self.name.lower().replace(' ', '_')}}_config.json")
        try:
            os.makedirs("pxbot_code", exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Config save error: {{e}}")
    
    def execute_command(self, command):
        try:
            prefix = "{app_name}".lower().replace(" ", "_") + ":"
            if command.startswith(prefix):
                cmd = command[len(prefix):]
                result = self.handle_command(cmd)
                
                # Add to history
                self.history.append({{
                    "timestamp": datetime.now().isoformat(),
                    "command": cmd,
                    "result": result[:100] + "..." if len(result) > 100 else result
                }})
                
                # Keep history size manageable
                if len(self.history) > self.config.get("max_history", 100):
                    self.history = self.history[-self.config["max_history"]:]
                
                return result
            return f"Use {{prefix}} prefix for commands"
        except Exception as e:
            error_msg = f"Error: {{e}}"
            if self.config.get("debug_mode", False):
                import traceback
                error_msg += f"\\nDebug info: {{traceback.format_exc()}}"
            return error_msg
    
    def handle_command(self, command):
        parts = command.split(":")
        action = parts[0]
        
        if action == "hello":
            return f"Hello from {{self.name}}! Running since {{self.session_start.strftime('%H:%M:%S')}}"
        
        elif action == "status":
            uptime = datetime.now() - self.session_start
            return f"""📊 **{{self.name}} Status**

**Version:** {{self.version}}
**Uptime:** {{uptime}}
**Commands executed:** {{len(self.history)}}
**Data entries:** {{len(self.data)}}
**Auto-save:** {{self.config.get('auto_save', True)}}"""
        
        elif action == "config":
            if len(parts) >= 3:
                key, value = parts[1], parts[2]
                return self.set_config(key, value)
            elif len(parts) == 2:
                key = parts[1]
                return f"{{key}} = {{self.config.get(key, 'Not set')}}"
            else:
                return self.show_config()
        
        elif action == "history":
            count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
            return self.show_history(count)
        
        elif action == "data":
            if len(parts) >= 3:
                key, value = parts[1], parts[2]
                self.data[key] = value
                return f"Set {{key}} = {{value}}"
            elif len(parts) == 2:
                key = parts[1]
                return f"{{key}} = {{self.data.get(key, 'Not found')}}"
            else:
                return f"Data entries: {{', '.join(self.data.keys()) if self.data else 'None'}}"
        
        elif action == "export":
            filename = parts[1] if len(parts) > 1 else f"{{self.name.lower().replace(' ', '_')}}_export"
            return self.export_data(filename)
        
        elif action == "help":
            return self.show_help()
        
        else:
            return f"Unknown command: {{action}}\\nTry: help"
    
    def set_config(self, key, value):
        # Type conversion
        if value.lower() in ["true", "false"]:
            value = value.lower() == "true"
        elif value.isdigit():
            value = int(value)
        
        self.config[key] = value
        if self.config.get("auto_save", True):
            self.save_config()
        
        return f"Set {{key}} = {{value}}"
    
    def show_config(self):
        result = f"⚙️ **{{self.name}} Configuration:**\\n\\n"
        for key, value in self.config.items():
            result += f"• {{key}} = {{value}}\\n"
        result += "\\n**To change:** config:key:value"
        return result
    
    def show_history(self, count):
        if not self.history:
            return "📝 No command history"
        
        recent = self.history[-count:]
        result = f"📝 **Command History (last {{len(recent)}}):**\\n\\n"
        
        for i, entry in enumerate(recent, 1):
            timestamp = entry["timestamp"][:19].replace("T", " ")
            result += f"{{i:2d}}. {{timestamp}} - {{entry['command']}}\\n"
        
        return result
    
    def export_data(self, filename):
        try:
            export = {{
                "app_info": {{
                    "name": self.name,
                    "version": self.version,
                    "export_time": datetime.now().isoformat()
                }},
                "config": self.config,
                "data": self.data,
                "history": self.history
            }}
            
            export_path = f"pxbot_code/exports/{{filename}}.json"
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            with open(export_path, "w") as f:
                json.dump(export, f, indent=2)
            
            return f"📊 Data exported to: {{export_path}}"
        except Exception as e:
            return f"❌ Export failed: {{e}}"
    
    def show_help(self):
        return f"""🔧 **{{self.name}} Help**

**Basic Commands:**
• hello - Greeting with uptime
• status - Detailed status information
• help - Show this help

**Configuration:**
• config - Show all settings
• config:key - Get specific setting
• config:key:value - Set configuration

**Data Management:**
• data - List all data keys
• data:key - Get data value
• data:key:value - Set data value

**Utilities:**
• history - Show recent commands
• history:count - Show specific number of entries
• export - Export all data
• export:filename - Export with custom name

**Usage:**
{{self.name.lower().replace(" ", "_")}}:command:parameters"""
    
    def cleanup(self):
        """Called when app is unloaded"""
        if self.config.get("auto_save", True):
            self.save_config()

def main():
    return {class_name}()

if __name__ == "__main__":
    app = main()
    print(f"{{app.name}} Advanced Test")
    print(app.execute_command("{app_name}:status".lower().replace(" ", "_")))
''',
            "features": "Configuration management, command history, data persistence, error handling, export functionality",
            "usage_examples": "hello, status, config, history, data:key:value, export"
        }

def main():
    return AppTemplateGenerator()

if __name__ == "__main__":
    app = main()
    print("App Template Generator Test")
    print(app.execute_command("template:list"))
'''
        
        # Testing Framework
        testing_framework_code = '''#!/usr/bin/env python3
"""
PXBot Testing Framework - Automated testing for apps and system
"""

import os
import sys
import json
import traceback
import time
from datetime import datetime

class PXBotTestFramework:
    def __init__(self, pxbot_instance=None):
        self.name = "PXBot Test Framework"
        self.version = "1.0.0"
        self.description = "Automated testing and validation for PXBot apps"
        self.pxbot = pxbot_instance
        
        self.test_results = []
        self.test_suites = {}
        self.coverage_data = {}
    
    def execute_command(self, command):
        try:
            if command.startswith("test:"):
                cmd = command[5:]
                return self.handle_test_command(cmd)
            return "Use test: prefix for testing commands"
        except Exception as e:
            return f"Error: {{e}}"
    
    def handle_test_command(self, command):
        parts = command.split(":")
        action = parts[0]
        
        if action == "run":
            target = parts[1] if len(parts) > 1 else "all"
            return self.run_tests(target)
        
        elif action == "create":
            if len(parts) >= 2:
                test_name = parts[1]
                return self.create_test_suite(test_name)
            return "Usage: test:create:test_name"
        
        elif action == "list":
            return self.list_tests()
        
        elif action == "report":
            return self.generate_report()
        
        elif action == "validate":
            app_name = parts[1] if len(parts) > 1 else ""
            return self.validate_app(app_name)
        
        elif action == "benchmark":
            return self.run_benchmark_tests()
        
        elif action == "coverage":
            return self.show_coverage()
        
        return "Commands: run[:target], create:name, list, report, validate:app, benchmark, coverage"
    
    def run_tests(self, target="all"):
        start_time = time.time()
        results = []
        
        if target == "all":
            # Test all available apps
            test_targets = self.discover_apps()
        else:
            test_targets = [target]
        
        for app_name in test_targets:
            result = self.test_app(app_name)
            results.append(result)
            self.test_results.append(result)
        
        duration = time.time() - start_time
        
        # Summary
        passed = len([r for r in results if r["status"] == "PASS"])
        failed = len([r for r in results if r["status"] == "FAIL"])
        errors = len([r for r in results if r["status"] == "ERROR"])
        
        return f"""🧪 **Test Execution Complete**

**📊 Results:**
• Tests run: {{len(results)}}
• Passed: {{passed}} ✅
• Failed: {{failed}} ❌  
• Errors: {{errors}} 💥
• Duration: {{duration:.2f}} seconds

**Success rate:** {{(passed/len(results)*100):.1f}}%

Run `test:report` for detailed results."""
    
    def test_app(self, app_name):
        result = {{
            "app_name": app_name,
            "timestamp": datetime.now().isoformat(),
            "status": "UNKNOWN",
            "tests": [],
            "duration": 0,
            "error": None
        }}
        
        start_time = time.time()
        
        try:
            # Try to import and instantiate app
            app_module = self.import_app(app_name)
            if not app_module:
                result["status"] = "ERROR"
                result["error"] = f"Could not import app: {{app_name}}"
                return result
            
            app_instance = app_module.main()
            
            # Basic tests
            tests = [
                ("initialization", self.test_initialization, app_instance),
                ("help_command", self.test_help_command, app_instance),
                ("invalid_command", self.test_invalid_command, app_instance),
                ("command_parsing", self.test_command_parsing, app_instance)
            ]
            
            passed_tests = 0
            for test_name, test_func, *args in tests:
                try:
                    test_result = test_func(*args)
                    result["tests"].append({{
                        "name": test_name,
                        "status": "PASS" if test_result else "FAIL",
                        "message": "OK" if test_result else "Test failed"
                    }})
                    if test_result:
                        passed_tests += 1
                except Exception as e:
                    result["tests"].append({{
                        "name": test_name,
                        "status": "ERROR",
                        "message": str(e)
                    }})
            
            # Overall status
            if passed_tests == len(tests):
                result["status"] = "PASS"
            elif passed_tests > 0:
                result["status"] = "PARTIAL"
            else:
                result["status"] = "FAIL"
            
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
        
        result["duration"] = time.time() - start_time
        return result
    
    def test_initialization(self, app_instance):
        """Test if app initializes properly"""
        return (hasattr(app_instance, 'name') and 
                hasattr(app_instance, 'version') and
                hasattr(app_instance, 'execute_command'))
    
    def test_help_command(self, app_instance):
        """Test if help command works"""
        try:
            prefix = app_instance.name.lower().replace(" ", "_")
            help_command = f"{{prefix}}:help"
            result = app_instance.execute_command(help_command)
            return isinstance(result, str) and len(result) > 10
        except:
            return False
    
    def test_invalid_command(self, app_instance):
        """Test handling of invalid commands"""
        try:
            result = app_instance.execute_command("invalid_test_command_12345")
            return isinstance(result, str)
        except:
            return False
    
    def test_command_parsing(self, app_instance):
        """Test command parsing"""
        try:
            prefix = app_instance.name.lower().replace(" ", "_")
            test_command = f"{{prefix}}:nonexistent"
            result = app_instance.execute_command(test_command)
            return isinstance(result, str)
        except:
            return False
    
    def discover_apps(self):
        """Discover available apps for testing"""
        apps = []
        app_directories = ["apps", "apps/core", "apps/utilities", "apps/examples"]
        
        for directory in app_directories:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.endswith('.py') and not filename.startswith('__'):
                        app_name = filename[:-3]
                        apps.append(app_name)
        
        return apps
    
    def import_app(self, app_name):
        """Safely import an app module"""
        try:
            # Add apps directory to path
            sys.path.insert(0, 'apps')
            sys.path.insert(0, 'apps/core')
            sys.path.insert(0, 'apps/utilities')
            sys.path.insert(0, 'apps/examples')
            
            module = __import__(app_name)
            return module
        except Exception as e:
            print(f"Import error for {{app_name}}: {{e}}")
            return None
    
    def validate_app(self, app_name):
        """Detailed validation of a specific app"""
        if not app_name:
            return "❌ Please specify an app name to validate"
        
        validation_results = []
        
        # File existence
        app_files = [
            f"apps/{{app_name}}.py",
            f"apps/core/{{app_name}}.py", 
            f"apps/utilities/{{app_name}}.py",
            f"apps/examples/{{app_name}}.py"
        ]
        
        app_file = None
        for file_path in app_files:
            if os.path.exists(file_path):
                app_file = file_path
                break
        
        if not app_file:
            return f"❌ App file not found: {{app_name}}"
        
        validation_results.append(f"✅ App file found: {{app_file}}")
        
        # Syntax check
        try:
            with open(app_file, 'r') as f:
                content = f.read()
            compile(content, app_file, 'exec')
            validation_results.append("✅ Python syntax is valid")
        except SyntaxError as e:
            validation_results.append(f"❌ Syntax error: {{e}}")
        
        # Structure check
        required_elements = ["class ", "def main()", "def execute_command("]
        for element in required_elements:
            if element in content:
                validation_results.append(f"✅ {{element.strip()}} found")
            else:
                validation_results.append(f"⚠️  {{element.strip()}} not found")
        
        # Import test
        try:
            app_module = self.import_app(app_name)
            if app_module and hasattr(app_module, 'main'):
                app_instance = app_module.main()
                validation_results.append("✅ App can be imported and instantiated")
                
                # Test basic functionality
                if hasattr(app_instance, 'execute_command'):
                    try:
                        result = app_instance.execute_command("test")
                        validation_results.append("✅ execute_command method works")
                    except Exception as e:
                        validation_results.append(f"⚠️  execute_command error: {{e}}")
                else:
                    validation_results.append("❌ execute_command method missing")
            else:
                validation_results.append("❌ App cannot be instantiated")
        except Exception as e:
            validation_results.append(f"❌ Import failed: {{e}}")
        
        return "\\n".join(validation_results)
    
    def generate_report(self):
        """Generate comprehensive test report"""
        if not self.test_results:
            return "📊 No test results available. Run tests first with `test:run`"
        
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        errors = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        report = f"""📊 **PXBot Test Report**
Generated: {{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}

**📈 Summary:**
• Total apps tested: {{total_tests}}
• Passed: {{passed}} ({{passed/total_tests*100:.1f}}%)
• Failed: {{failed}} ({{failed/total_tests*100:.1f}}%)
• Errors: {{errors}} ({{errors/total_tests*100:.1f}}%)

**📋 Detailed Results:**"""
        
        for result in self.test_results[-10:]:  # Last 10 results
            status_icon = {{"PASS": "✅", "FAIL": "❌", "ERROR": "💥", "PARTIAL": "⚠️"}}
            icon = status_icon.get(result["status"], "❓")
            
            report += f"""
{{icon}} **{{result["app_name"]}}** ({{result["status"]}})
   Duration: {{result["duration"]:.2f}}s
   Tests: {{len(result["tests"])}}"""
            
            if result.get("error"):
                report += f"\\n   Error: {{result['error']}}"
        
        return report
    
    def run_benchmark_tests(self):
        """Run performance benchmark tests"""
        benchmarks = []
        
        # App loading benchmark
        start_time = time.time()
        apps = self.discover_apps()
        load_time = time.time() - start_time
        benchmarks.append(f"App discovery: {{load_time:.3f}}s ({{len(apps)}} apps)")
        
        # Command execution benchmark
        if self.pxbot:
            start_time = time.time()
            for i in range(100):
                self.pxbot.run("create:function:test_func::None")
            exec_time = time.time() - start_time
            benchmarks.append(f"Command execution: {{exec_time:.3f}}s (100 commands)")
        
        return "🏁 **Performance Benchmarks:**\\n\\n" + "\\n".join(benchmarks)

def main():
    return PXBotTestFramework()

if __name__ == "__main__":
    framework = main()
    print("PXBot Testing Framework")
    print(framework.execute_command("test:list"))
'''
        
        utility_apps = [
            ("apps/core/system_monitor.py", system_monitor_code),
            ("apps/utilities/app_template_generator.py", template_generator_code),
            ("apps/utilities/testing_framework.py", testing_framework_code)
        ]
        
        for app_path, app_code in utility_apps:
            try:
                os.makedirs(os.path.dirname(app_path), exist_ok=True)
                with open(app_path, "w") as f:
                    f.write(app_code)
                self.log(f"Created utility app: {app_path}", "success")
            except Exception as e:
                self.log(f"Failed to create {app_path}: {e}", "error")
        
        return True
    
    def create_launch_scripts(self):
        """Create enhanced launch scripts"""
        self.log("Creating launch scripts...", "info")
        
        # Enhanced Windows batch file
        windows_script = '''@echo off
title PXBot Pro - Advanced Launcher
echo.
echo =====================================
echo    PXBot Pro - Advanced Launcher
echo =====================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Launch PXBot
echo Starting PXBot Pro...
echo.
python pxbot_launcher.py %*

if errorlevel 1 (
    echo.
    echo ERROR: PXBot failed to start
    echo Check the error messages above
    pause
)
'''
        
        # Enhanced Unix shell script
        unix_script = '''#!/bin/bash
echo "====================================="
echo "   PXBot Pro - Advanced Launcher"
echo "====================================="
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ first"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "ERROR: Python $python_version detected, but Python $required_version+ is required"
    exit 1
fi

echo "Starting PXBot Pro..."
echo ""
python3 pxbot_launcher.py "$@"

exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo ""
    echo "ERROR: PXBot failed to start (exit code: $exit_code)"
    echo "Check the error messages above"
    read -p "Press Enter to continue..."
fi
'''
        
        # Python launcher script
        python_launcher = '''#!/usr/bin/env python3
"""
PXBot Pro Cross-Platform Launcher
Enhanced launcher with system detection and error handling
"""

import sys
import os
import platform
import subprocess
import traceback

def check_requirements():
    """Check system requirements"""
    print("🔍 Checking system requirements...")
    
    # Python version
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected")
        print("🔧 Python 3.8+ required. Please upgrade Python.")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    
    # Required files
    required_files = [
        "pxbot_launcher.py",
        "pxbot_runtime.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    
    # Required packages
    required_packages = ["pygame", "PIL", "psutil"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"⚠️  Missing packages: {', '.join(missing_packages)}")
        print("🔧 Run setup.py to install missing packages")
        return False
    
    print("✅ All required packages installed")
    return True

def main():
    """Main launcher function"""
    print("🚀 PXBot Pro - Advanced Launcher")
    print("=" * 50)
    
    # System info
    print(f"🖥️  Platform: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print("")
    
    # Check requirements
    if not check_requirements():
        print("\\n❌ Requirements not met. Please run setup.py first.")
        input("Press Enter to exit...")
        return 1
    
    print("\\n🎯 Starting PXBot Pro...")
    print("-" * 30)
    
    try:
        # Launch main application
        result = subprocess.run([
            sys.executable, "pxbot_launcher.py"
        ] + sys.argv[1:])
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\\n\\n⏹️  Interrupted by user")
        return 0
    except Exception as e:
        print(f"\\n\\n💥 Launch failed: {e}")
        print("\\nDebug information:")
        print(traceback.format_exc())
        input("Press Enter to exit...")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
        
        scripts = [
            ("launch.bat", windows_script),
            ("launch.sh", unix_script),
            ("launch.py", python_launcher)
        ]
        
        for script_path, content in scripts:
            try:
                with open(script_path, "w") as f:
                    f.write(content)
                
                # Make executable on Unix
                if script_path.endswith('.sh') or script_path.endswith('.py'):
                    try:
                        os.chmod(script_path, 0o755)
                    except:
                        pass
                
                self.log(f"Created launch script: {script_path}", "success")
            except Exception as e:
                self.log(f"Failed to create {script_path}: {e}", "error")
        
        return True
    
    def create_documentation(self):
        """Create comprehensive documentation"""
        self.log("Creating documentation...", "info")
        
        # API Documentation
        api_docs = '''# PXBot Pro API Documentation

## Core Classes

### PXBot
Main PXBot class for code execution and management.

#### Methods
- `run(command)` - Execute a command
- `save_code(name, code)` - Save code as pixel data
- `load_code(name)` - Load code from pixel data

### MiniVFS
Virtual file system for PXBot.

### MiniRT
Runtime environment for code execution.

### PixelProgrammingTools
Advanced tools for pixel code manipulation.

#### Methods
- `create_pixel_art_from_code(code_name)` - Create pixel art
- `analyze_pixel_density(code_name)` - Analyze pixel data
- `merge_pixel_codes(code1, code2, new_name)` - Merge codes
- `optimize_pixel_storage(code_name)` - Optimize storage

### SmartPXBotChatbot
AI assistant with pixel programming integration.

## App Development

### App Structure
```python
class MyApp:
    def __init__(self, pxbot_instance=None):
        self.name = "My App"
        self.version = "1.0.0"
        self.pxbot = pxbot_instance
    
    def execute_command(self, command):
        # Handle commands
        pass

def main():
    return MyApp()
```

### Command Format
Apps use the format: `appname:action:parameters`

Examples:
- `myapp:hello`
- `myapp:process:data`
- `myapp:config:setting:value`

## Utility Apps

### System Monitor
Real-time system monitoring and performance analysis.

Commands:
- `monitor:current` - Current system stats
- `monitor:processes:10` - Top 10 processes
- `monitor:benchmark` - Run benchmark

### App Template Generator
Generate new apps from templates.

Commands:
- `template:list` - Available templates
- `template:create:type:name:description` - Create app
- `template:show:type` - Show template details

### Testing Framework
Automated testing for apps and system.

Commands:
- `test:run` - Run all tests
- `test:validate:app` - Validate specific app
- `test:report` - Generate test report

## Configuration

### Main Config (pxbot_code/main_config.json)
- `window_size` - Launcher window size
- `theme` - UI theme (dark/light)
- `auto_save` - Automatic saving
- `debug_mode` - Debug mode toggle

### Development Config (pxbot_code/development_config.json)
- `auto_reload` - Automatic app reloading
- `hot_reload` - Hot reload support
- `test_mode` - Testing mode

## Deployment

### Package Creation
```bash
deploy:package:my_app
```

### App Installation
```bash
deploy:install:my_app.pxapp
```

### Repository Management
```bash
deploy:repo:add:name:url
deploy:repo:list
```
'''
        
        # Tutorial Documentation
        tutorial_docs = '''# PXBot Pro Tutorial

## Getting Started

### 1. Installation
```bash
python setup.py
```

### 2. Launch PXBot
```bash
python launch.py
```
or
```bash
./launch.sh  # Unix/Linux/Mac
launch.bat   # Windows
```

### 3. First Steps

#### Visual Mode
- F1 - Open menu
- Enter - Command mode
- Tab - Autocomplete
- Esc - Exit command mode

#### Creating Your First Code
1. Go to "Code Editor" tab
2. Write some Python code
3. Give it a name
4. Click "Save Code"
5. See it appear in "Saved Codes"

### 4. Using the AI Assistant
1. Go to "Smart AI" tab
2. Try: "list my codes"
3. Try: "create pixel art from my_code"
4. Try: "use tools to merge codes"

## Advanced Features

### Pixel Programming
- Code is stored as pixel data in PNG images
- Each character becomes a red pixel value
- Visual representation of code structure
- Artistic code generation

### AI Integration
- Natural language command processing
- Pixel programming tools
- Code analysis and optimization
- Template generation

### App Development
1. Copy `apps/app_template.py`
2. Customize the class and methods
3. Test with `python my_app.py`
4. Use in launcher with `myapp:command`

### Web Integration
- Built-in web browser
- Web scraping capabilities
- API integration
- Real-time data processing

## Tips and Tricks

### Performance
- Use the system monitor to track resource usage
- Run benchmarks to test performance
- Optimize pixel storage for large codes

### Development
- Use the testing framework for validation
- Generate apps from templates
- Utilize the AI for code suggestions

### Troubleshooting
- Check logs in pxbot_code/
- Use debug mode for detailed errors
- Validate apps before deployment
- Run system diagnostics

## Examples

### Basic Calculator
```python
def calculator(a, b, op):
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        return a / b if b != 0 else "Error: Division by zero"
```

### Data Processor
```python
def process_data(data_list):
    processed = []
    for item in data_list:
        if isinstance(item, (int, float)):
            processed.append(item * 2)
        else:
            processed.append(str(item).upper())
    return processed
```

### Web Scraper
```python
import urllib.request

def fetch_page(url):
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return f"Error: {e}"
```
'''
        
        docs = [
            ("docs/api/README.md", api_docs),
            ("docs/tutorials/getting_started.md", tutorial_docs)
        ]
        
        for doc_path, content in docs:
            try:
                os.makedirs(os.path.dirname(doc_path), exist_ok=True)
                with open(doc_path, "w", encoding='utf-8') as f:
                    f.write(content)
                self.log(f"Created documentation: {doc_path}", "success")
            except Exception as e:
                self.log(f"Failed to create {doc_path}: {e}", "error")
        
        return True
    
    def create_examples(self):
        """Create example projects and tutorials"""
        self.log("Creating examples...", "info")
        
        # Basic example
        basic_example = '''#!/usr/bin/env python3
"""
Hello World Example - Basic PXBot app demonstration
"""

class HelloWorldExample:
    def __init__(self, pxbot_instance=None):
        self.name = "Hello World Example"
        self.version = "1.0.0"
        self.description = "Simple demonstration of PXBot app structure"
        self.pxbot = pxbot_instance
        self.counter = 0
    
    def execute_command(self, command):
        try:
            if command.startswith("hello:"):
                cmd = command[6:]
                return self.handle_command(cmd)
            return "Use hello: prefix for commands"
        except Exception as e:
            return f"Error: {e}"
    
    def handle_command(self, command):
        if command == "world":
            self.counter += 1
            return f"Hello, World! (Called {self.counter} times)"
        
        elif command == "reset":
            self.counter = 0
            return "Counter reset to 0"
        
        elif command == "count":
            return f"Hello called {self.counter} times"
        
        elif command == "help":
            return """🔧 Hello World Example Help
            
Commands:
• hello:world - Say hello and increment counter
• hello:reset - Reset counter
• hello:count - Show current count
• hello:help - Show this help"""
        
        else:
            return f"Unknown command: {command}\\nTry: hello:help"

def main():
    return HelloWorldExample()

if __name__ == "__main__":
    app = main()
    print("Hello World Example Test")
    print(app.execute_command("hello:world"))
    print(app.execute_command("hello:count"))
    print(app.execute_command("hello:help"))
'''
        
        # Advanced example
        advanced_example = '''#!/usr/bin/env python3
"""
Data Analyzer Example - Advanced PXBot app with pixel integration
"""

import json
import os
from datetime import datetime

class DataAnalyzerExample:
    def __init__(self, pxbot_instance=None):
        self.name = "Data Analyzer Example"
        self.version = "1.0.0"
        self.description = "Advanced data analysis with pixel visualization"
        self.pxbot = pxbot_instance
        
        self.datasets = {}
        self.analysis_history = []
    
    def execute_command(self, command):
        try:
            if command.startswith("analyze:"):
                cmd = command[8:]
                return self.handle_command(cmd)
            return "Use analyze: prefix for commands"
        except Exception as e:
            return f"Error: {e}"
    
    def handle_command(self, command):
        parts = command.split(":")
        action = parts[0]
        
        if action == "load":
            if len(parts) >= 2:
                data_name = parts[1]
                return self.load_sample_data(data_name)
            return "Usage: analyze:load:dataset_name"
        
        elif action == "stats":
            if len(parts) >= 2:
                data_name = parts[1]
                return self.calculate_stats(data_name)
            return "Usage: analyze:stats:dataset_name"
        
        elif action == "visualize":
            if len(parts) >= 2:
                data_name = parts[1]
                return self.create_visualization(data_name)
            return "Usage: analyze:visualize:dataset_name"
        
        elif action == "export":
            if len(parts) >= 2:
                data_name = parts[1]
                export_name = parts[2] if len(parts) > 2 else f"{data_name}_analysis"
                return self.export_to_pixel_code(data_name, export_name)
            return "Usage: analyze:export:dataset_name[:export_name]"
        
        elif action == "list":
            return self.list_datasets()
        
        elif action == "help":
            return self.show_help()
        
        else:
            return f"Unknown command: {action}\\nTry: analyze:help"
    
    def load_sample_data(self, data_name):
        # Generate sample datasets
        if data_name == "sales":
            self.datasets["sales"] = [100, 150, 200, 175, 300, 250, 400, 350, 500, 450]
        elif data_name == "temperatures":
            self.datasets["temperatures"] = [20, 22, 25, 23, 27, 30, 28, 26, 24, 21]
        elif data_name == "scores":
            self.datasets["scores"] = [85, 92, 78, 95, 88, 91, 87, 94, 89, 93]
        else:
            return f"❌ Unknown dataset: {data_name}\\nAvailable: sales, temperatures, scores"
        
        return f"✅ Loaded dataset '{data_name}' with {len(self.datasets[data_name])} values"
    
    def calculate_stats(self, data_name):
        if data_name not in self.datasets:
            return f"❌ Dataset '{data_name}' not found. Load it first with analyze:load:{data_name}"
        
        data = self.datasets[data_name]
        
        stats = {
            "count": len(data),
            "sum": sum(data),
            "min": min(data),
            "max": max(data),
            "mean": sum(data) / len(data),
            "range": max(data) - min(data)
        }
        
        # Calculate median
        sorted_data = sorted(data)
        n = len(sorted_data)
        if n % 2 == 0:
            stats["median"] = (sorted_data[n//2-1] + sorted_data[n//2]) / 2
        else:
            stats["median"] = sorted_data[n//2]
        
        # Add to history
        self.analysis_history.append({
            "timestamp": datetime.now().isoformat(),
            "dataset": data_name,
            "operation": "stats",
            "result": stats
        })
        
        return f"""📊 **Statistics for '{data_name}'**

• Count: {stats['count']}
• Sum: {stats['sum']:.2f}
• Mean: {stats['mean']:.2f}
• Median: {stats['median']:.2f}
• Min: {stats['min']:.2f}
• Max: {stats['max']:.2f}
• Range: {stats['range']:.2f}"""
    
    def create_visualization(self, data_name):
        if data_name not in self.datasets:
            return f"❌ Dataset '{data_name}' not found"
        
        data = self.datasets[data_name]
        
        # Create ASCII bar chart
        max_val = max(data)
        chart_width = 50
        
        chart = f"📈 **Visualization for '{data_name}'**\\n\\n"
        
        for i, value in enumerate(data):
            bar_length = int((value / max_val) * chart_width)
            bar = "█" * bar_length
            chart += f"{i+1:2d} |{bar:<{chart_width}} {value}\\n"
        
        chart += f"\\nScale: {max_val} = {chart_width} chars"
        
        return chart
    
    def export_to_pixel_code(self, data_name, export_name):
        if data_name not in self.datasets:
            return f"❌ Dataset '{data_name}' not found"
        
        if not self.pxbot:
            return "❌ PXBot instance not available"
        
        data = self.datasets[data_name]
        stats = {
            "mean": sum(data) / len(data),
            "min": min(data),
            "max": max(data)
        }
        
        # Generate Python code for the analysis
        code = f'''# Data Analysis: {data_name}
# Generated by PXBot Data Analyzer
# Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

import matplotlib.pyplot as plt

def analyze_{data_name}():
    """Analysis of {data_name} dataset"""
    data = {data}
    
    # Statistics
    stats = {{
        "count": {len(data)},
        "mean": {stats["mean"]:.2f},
        "min": {stats["min"]},
        "max": {stats["max"]}
    }}
    
    print("Dataset: {data_name}")
    print(f"Count: {{stats['count']}}")
    print(f"Mean: {{stats['mean']}}")
    print(f"Min: {{stats['min']}}")
    print(f"Max: {{stats['max']}}")
    
    # Visualization
    plt.figure(figsize=(10, 6))
    plt.plot(data, marker='o')
    plt.title('{data_name.title()} Data Analysis')
    plt.xlabel('Index')
    plt.ylabel('Value')
    plt.grid(True)
    plt.show()
    
    return stats

def get_data():
    """Get the raw data"""
    return {data}

# Auto-execute analysis
if __name__ == "__main__":
    result = analyze_{data_name}()
    print("Analysis complete!")
'''
        
        try:
            result = self.pxbot.run(f"save:{export_name}:{code}")
            return f"📤 **Exported to Pixel Code!**\\n\\n{result}\\n\\nAnalysis saved as '{export_name}' with visualization code"
        except Exception as e:
            return f"❌ Export failed: {e}"
    
    def list_datasets(self):
        if not self.datasets:
            return "📂 No datasets loaded\\nTry: analyze:load:sales"
        
        result = f"📂 **Loaded Datasets ({len(self.datasets)}):**\\n\\n"
        for name, data in self.datasets.items():
            result += f"• **{name}** - {len(data)} values\\n"
        
        return result
    
    def show_help(self):
        return """🔧 **Data Analyzer Example Help**

**📊 Data Management:**
• analyze:load:dataset_name - Load sample data (sales, temperatures, scores)
• analyze:list - Show loaded datasets

**📈 Analysis:**
• analyze:stats:dataset_name - Calculate statistics
• analyze:visualize:dataset_name - Create ASCII chart

**💾 Export:**
• analyze:export:dataset_name[:export_name] - Export to pixel code with visualization

**Examples:**
```
analyze:load:sales
analyze:stats:sales
analyze:visualize:sales
analyze:export:sales:my_sales_analysis
```

This example demonstrates advanced PXBot features including pixel code export!"""

def main():
    return DataAnalyzerExample()

if __name__ == "__main__":
    app = main()
    print("Data Analyzer Example Test")
    print(app.execute_command("analyze:help"))
'''
        
        examples = [
            ("examples/basic/hello_world.py", basic_example),
            ("examples/advanced/data_analyzer.py", advanced_example)
        ]
        
        for example_path, content in examples:
            try:
                os.makedirs(os.path.dirname(example_path), exist_ok=True)
                with open(example_path, "w") as f:
                    f.write(content)
                self.log(f"Created example: {example_path}", "success")
            except Exception as e:
                self.log(f"Failed to create {example_path}: {e}", "error")
        
        return True
    
    def verify_installation(self):
        """Verify the installation is complete and working"""
        self.log("Verifying installation...", "info")
        
        verification_checks = []
        
        # Check critical files
        critical_files = [
            "pxbot_launcher.py",
            "pxbot_runtime.py", 
            "setup.py",
            "launch.py"
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                verification_checks.append(f"✅ {file_path}")
            else:
                verification_checks.append(f"❌ {file_path} - MISSING")
                self.log(f"Critical file missing: {file_path}", "error")
        
        # Check directory structure
        required_dirs = [
            "apps", "apps/core", "apps/utilities", "pxbot_code", 
            "docs", "examples", "tests", "tools"
        ]
        
        for directory in required_dirs:
            if os.path.exists(directory):
                verification_checks.append(f"✅ {directory}/")
            else:
                verification_checks.append(f"❌ {directory}/ - MISSING")
                self.log(f"Directory missing: {directory}", "warning")
        
        # Check configuration files
        config_files = [
            "pxbot_code/main_config.json",
            "pxbot_code/development_config.json"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                verification_checks.append(f"✅ {config_file}")
            else:
                verification_checks.append(f"❌ {config_file} - MISSING")
        
        # Check utility apps
        utility_apps = [
            "apps/core/system_monitor.py",
            "apps/utilities/app_template_generator.py",
            "apps/utilities/testing_framework.py"
        ]
        
        for app_file in utility_apps:
            if os.path.exists(app_file):
                verification_checks.append(f"✅ {app_file}")
            else:
                verification_checks.append(f"❌ {app_file} - MISSING")
        
        # Test Python imports
        try:
            import pygame
            verification_checks.append("✅ pygame package")
        except ImportError:
            verification_checks.append("❌ pygame package - NOT INSTALLED")
            self.log("pygame not available", "error")
        
        try:
            from PIL import Image
            verification_checks.append("✅ PIL/Pillow package")
        except ImportError:
            verification_checks.append("❌ PIL/Pillow package - NOT INSTALLED")
            self.log("PIL/Pillow not available", "error")
        
        try:
            import psutil
            verification_checks.append("✅ psutil package")
        except ImportError:
            verification_checks.append("❌ psutil package - NOT INSTALLED")
            self.log("psutil not available", "error")
        
        # Count results
        total_checks = len(verification_checks)
        passed_checks = len([check for check in verification_checks if check.startswith("✅")])
        
        self.log(f"Verification complete: {passed_checks}/{total_checks} checks passed", 
                "success" if passed_checks == total_checks else "warning")
        
        return verification_checks, passed_checks == total_checks
    
    def generate_final_report(self):
        """Generate comprehensive setup report"""
        self.log("Generating final setup report...", "info")
        
        verification_checks, all_passed = self.verify_installation()
        
        report = f"""
# 🚀 PXBot Pro Setup Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Version:** {self.version}
**Platform:** {platform.system()} {platform.release()}

## 📊 Setup Summary
- **✅ Steps completed:** {len(self.setup_log)}
- **⚠️  Warnings:** {len(self.warnings)}
- **❌ Errors:** {len(self.errors)}
- **🎯 Overall Status:** {"SUCCESS" if all_passed and not self.errors else "PARTIAL" if not self.errors else "FAILED"}

## 🔍 Verification Results
"""
        
        for check in verification_checks:
            report += f"- {check}\n"
        
        if self.warnings:
            report += f"\n## ⚠️ Warnings\n"
            for warning in self.warnings:
                report += f"- {warning}\n"
        
        if self.errors:
            report += f"\n## ❌ Errors\n"
            for error in self.errors:
                report += f"- {error}\n"
        
        report += f"""
## 🚀 Quick Start Guide

### 1. Launch PXBot Pro
```bash
# Recommended - Cross-platform launcher
python launch.py

# Alternative - Direct launch
python pxbot_launcher.py

# Platform-specific
./launch.sh     # Unix/Linux/Mac
launch.bat      # Windows
```

### 2. First Steps
1. **Visual Mode:** Use F1 for menu, Enter for commands
2. **Create Code:** Go to "Code Editor" tab
3. **AI Assistant:** Try "Smart AI" tab - ask: "list my codes"
4. **Web Browse:** Use "Web Browser" tab for research

### 3. Try the Apps
```bash
# System monitoring
monitor:current

# App development
template:create:basic:my_first_app

# Testing
test:run:all

# Web scraping
scrape:url:python.org
```

### 4. Development
1. Copy `apps/app_template.py` to create new apps
2. Use the template generator: `template:create:advanced:my_app`
3. Test with: `test:validate:my_app`
4. Package with: `deploy:package:my_app`

## 📚 Resources

### Documentation
- **📖 Getting Started:** `docs/tutorials/getting_started.md`
- **🔧 API Reference:** `docs/api/README.md`
- **📱 App Development:** See the existing development guide

### Examples
- **🟢 Basic:** `examples/basic/hello_world.py`
- **🔵 Advanced:** `examples/advanced/data_analyzer.py`

### Tools
- **🧪 Testing:** `apps/utilities/testing_framework.py`
- **🛠️ Templates:** `apps/utilities/app_template_generator.py`
- **📊 Monitoring:** `apps/core/system_monitor.py`

## 🎯 What's Included

### ✨ Core Features
- **Pixel Programming:** Code stored as PNG pixel data
- **AI Assistant:** Smart coding help with pixel tools
- **Visual Interface:** Advanced launcher with multiple tabs
- **Web Integration:** Built-in browser and scraping tools

### 📱 Apps Ecosystem
- **Core Apps:** System Monitor, PXOS interface
- **Utilities:** Template Generator, Testing Framework
- **Web Tools:** Advanced scraper, deployment manager
- **Examples:** Hello World, Data Analyzer

### 🔧 Development Tools
- **Templates:** Multiple app templates (basic, advanced, utility)
- **Testing:** Automated testing and validation
- **Deployment:** Package manager and distribution
- **Documentation:** Comprehensive guides and API docs

### 🎨 Pixel Programming Tools
- **Art Generation:** Turn code into colorful pixel art
- **Code Analysis:** Pixel density and structure analysis
- **Code Merging:** Combine multiple codes intelligently
- **Storage Optimization:** Compress pixel data efficiently

## 💡 Pro Tips

### Performance
- Use `monitor:benchmark` to test system performance
- Enable `auto_save` for better reliability
- Use pixel storage optimization for large codes

### Development
- Start with templates: `template:create:basic:my_app`
- Test apps with: `test:validate:my_app`
- Use the AI for natural language coding
- Package apps with: `deploy:package:my_app`

### Troubleshooting
- Check logs in `pxbot_code/` directory
- Use debug mode: `config:debug_mode:true`
- Run diagnostics: `monitor:current`
- Validate setup: `test:run:all`

---

## 🎉 Next Steps

{"✅ **Installation successful!** PXBot Pro is ready to use." if all_passed and not self.errors else "⚠️ **Installation completed with issues.** Check errors above."}

### Immediate Actions:
1. **Launch:** `python launch.py`
2. **Explore:** Try the visual interface and AI assistant
3. **Create:** Make your first app with the template generator
4. **Learn:** Read the tutorials and try examples

### Advanced Features:
1. **Pixel Art:** Use AI to create art from your code
2. **Web Tools:** Scrape data and build web integrations  
3. **App Store:** Package and share your apps
4. **System Monitor:** Track performance and resources

**Welcome to the future of pixel programming!** 🎨🚀

*PXBot Pro v{self.version} - Where Code Becomes Art* ✨
"""
        
        # Save report
        report_path = "SETUP_REPORT.md"
        try:
            with open(report_path, "w", encoding='utf-8') as f:
                f.write(report)
            self.log(f"Setup report saved: {report_path}", "success")
        except Exception as e:
            self.log(f"Failed to save setup report: {e}", "error")
        
        return report, all_passed
    
    def run_complete_setup(self):
        """Run the complete enhanced setup process"""
        print("\n🚀 PXBot Pro - Enhanced Setup & App Ecosystem")
        print("=" * 70)
        print("🎨 Complete development environment with advanced features")
        print("🧠 AI integration • 📱 App ecosystem • 🌐 Web tools • 🔧 Utilities")
        print()
        
        # Confirm setup
        response = input("🤔 Ready to set up the complete PXBot Pro environment? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            print("⏹️  Setup cancelled.")
            return False
        
        print(f"\n🔧 Starting enhanced setup process...")
        print("-" * 50)
        
        # Enhanced setup steps
        setup_steps = [
            ("System requirements", self.check_system_requirements),
            ("Installing dependencies", self.install_dependencies),
            ("Creating directories", self.create_directory_structure),
            ("Configuration files", self.create_configuration_files),
            ("Utility applications", self.create_utility_apps),
            ("Launch scripts", self.create_launch_scripts),
            ("Documentation", self.create_documentation),
            ("Example projects", self.create_examples),
            ("Installation verification", self.verify_installation)
        ]
        
        failed_steps = []
        
        for step_name, step_function in setup_steps:
            print(f"\n📋 {step_name}...")
            try:
                if step_name == "Installation verification":
                    # Special handling for verification
                    verification_checks, success = step_function()
                    if not success:
                        failed_steps.append(step_name)
                else:
                    success = step_function()
                    if not success:
                        failed_steps.append(step_name)
            except Exception as e:
                self.log(f"Exception in {step_name}: {e}", "error")
                self.log(traceback.format_exc(), "error")
                failed_steps.append(step_name)
        
        # Generate final report
        print(f"\n📊 Generating comprehensive setup report...")
        report, installation_success = self.generate_final_report()
        
        # Final summary
        print(f"\n🎉 Enhanced Setup Complete!")
        print("=" * 40)
        print(f"✅ Successful steps: {len(setup_steps) - len(failed_steps)}/{len(setup_steps)}")
        print(f"❌ Failed steps: {len(failed_steps)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"📋 Setup report: SETUP_REPORT.md")
        
        if failed_steps:
            print(f"\n⚠️  Failed steps: {', '.join(failed_steps)}")
            print(f"🔍 Check SETUP_REPORT.md for detailed information")
        
        if installation_success and not self.errors:
            print(f"\n🚀 **PXBot Pro is ready!**")
            print(f"🎯 Launch with: python launch.py")
            print(f"📚 Read: docs/tutorials/getting_started.md")
            print(f"🧠 Try the AI assistant and pixel programming tools!")
        else:
            print(f"\n⚠️  Setup completed with issues")
            print(f"🔧 Please review SETUP_REPORT.md and fix any errors")
            print(f"💡 Most issues can be resolved by re-running this setup")
        
        return len(failed_steps) == 0 and installation_success

def main():
    """Main setup function with enhanced error handling"""
    try:
        print("🎨 PXBot Pro Enhanced Setup v2.0.0")
        print("🚀 Advanced Pixel Programming Environment")
        print()
        
        setup = PXBotProSetup()
        success = setup.run_complete_setup()
        
        if success:
            print(f"\n✨ Welcome to PXBot Pro! ✨")
            print(f"🎨 Where code becomes art and development becomes adventure!")
            return 0
        else:
            print(f"\n🔧 Setup needs attention - check SETUP_REPORT.md")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Setup interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Setup failed with unexpected error:")
        print(f"Error: {e}")
        print(f"\nDebug information:")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
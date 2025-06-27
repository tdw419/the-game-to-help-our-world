#!/usr/bin/env python3
"""
PXBot Universal App Template - Complete template for creating new PXBot apps
Copy this file and customize it to create your own PXBot application
"""

import os
import json
import time
from datetime import datetime

class AppTemplate:
    """
    Universal template for PXBot applications
    
    This template includes:
    - Basic command handling
    - Configuration management  
    - State persistence
    - Error handling
    - Help system
    - Integration with PXBot runtime
    
    To create a new app:
    1. Copy this file to apps/your_app_name.py
    2. Change the class name and app details
    3. Implement your command handlers
    4. Test and deploy
    """
    
    def __init__(self, pxbot_instance=None):
        # === APP IDENTIFICATION ===
        # Change these values for your app
        self.name = "App Template"  # Change this to your app name
        self.version = "1.0.0"      # Your app version
        self.description = "Universal template for creating PXBot apps"  # App description
        self.author = "PXBot Team"  # Your name
        
        # === CORE SETUP ===
        self.pxbot = pxbot_instance  # PXBot runtime instance
        self.app_prefix = self.name.lower().replace(' ', '_')  # Command prefix
        
        # === APP STATE ===
        self.data = {}              # App data storage
        self.session_stats = {      # Session statistics
            "commands_executed": 0,
            "session_start": datetime.now(),
            "last_command": None
        }
        self.command_history = []   # Command history
        
        # === CONFIGURATION ===
        self.config = self.load_config()  # Load configuration
        
        # === INITIALIZATION ===
        self.initialize_app()
    
    def initialize_app(self):
        """
        Initialize the application
        Override this method to add custom initialization
        """
        try:
            # Create app data directory if needed
            self.data_dir = os.path.join("pxbot_code", "user_data", self.app_prefix)
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Load persistent data
            self.load_app_data()
            
            # App-specific initialization
            self.custom_initialization()
            
        except Exception as e:
            print(f"App initialization warning: {e}")
    
    def custom_initialization(self):
        """
        Override this method for custom app initialization
        Example: database connections, API setup, etc.
        """
        # Add your custom initialization code here
        pass
    
    def load_config(self):
        """Load app configuration from file"""
        config_path = os.path.join("pxbot_code", f"{self.app_prefix}_config.json")
        
        # Default configuration - customize for your app
        default_config = {
            "auto_save": True,
            "max_history": 100,
            "debug_mode": False,
            "cache_enabled": True,
            "timeout": 30,
            "max_data_entries": 1000,
            # Add your app-specific config here
            "custom_setting": "default_value"
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            print(f"Config load error: {e}")
        
        return default_config
    
    def save_config(self):
        """Save app configuration to file"""
        config_path = os.path.join("pxbot_code", f"{self.app_prefix}_config.json")
        try:
            os.makedirs("pxbot_code", exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Config save error: {e}")
    
    def load_app_data(self):
        """Load persistent app data"""
        data_path = os.path.join(self.data_dir, "app_data.json")
        try:
            if os.path.exists(data_path):
                with open(data_path, "r") as f:
                    self.data = json.load(f)
        except Exception as e:
            print(f"Data load error: {e}")
    
    def save_app_data(self):
        """Save persistent app data"""
        if not self.config.get("auto_save", True):
            return
        
        data_path = os.path.join(self.data_dir, "app_data.json")
        try:
            with open(data_path, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Data save error: {e}")
    
    def execute_command(self, command):
        """
        Main command execution entry point
        This method is called by the PXBot launcher
        """
        try:
            # Update session stats
            self.session_stats["commands_executed"] += 1
            self.session_stats["last_command"] = command
            
            # Check if command is for this app
            if command.startswith(f"{self.app_prefix}:"):
                cmd = command[len(self.app_prefix) + 1:]  # Remove prefix
                result = self.handle_command(cmd)
                
                # Add to history
                self.add_to_history(cmd, result)
                
                # Auto-save if enabled
                if self.config.get("auto_save", True):
                    self.save_app_data()
                
                return result
            else:
                return f"Use {self.app_prefix}: prefix for {self.name} commands"
                
        except Exception as e:
            error_msg = f"Command execution error: {e}"
            if self.config.get("debug_mode", False):
                import traceback
                error_msg += f"\nDebug info: {traceback.format_exc()}"
            return error_msg
    
    def handle_command(self, command):
        """
        Handle app-specific commands
        Customize this method for your app's functionality
        """
        parts = command.split(":")
        action = parts[0].lower()
        
        # === CORE COMMANDS (available in all apps) ===
        if action == "help":
            return self.show_help()
        
        elif action == "status":
            return self.show_status()
        
        elif action == "config":
            if len(parts) >= 3:
                key, value = parts[1], parts[2]
                return self.set_config(key, value)
            elif len(parts) == 2:
                key = parts[1]
                return f"{key} = {self.config.get(key, 'Not set')}"
            else:
                return self.show_config()
        
        elif action == "history":
            count = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10
            return self.show_history(count)
        
        elif action == "data":
            return self.handle_data_command(parts[1:] if len(parts) > 1 else [])
        
        elif action == "export":
            filename = parts[1] if len(parts) > 1 else f"{self.app_prefix}_export"
            return self.export_data(filename)
        
        elif action == "clear":
            return self.clear_data()
        
        elif action == "reset":
            return self.reset_app()
        
        # === CUSTOM COMMANDS ===
        # Add your app-specific commands here
        elif action == "hello":
            # Example custom command
            name = parts[1] if len(parts) > 1 else "World"
            return self.handle_hello(name)
        
        elif action == "process":
            # Example data processing command
            if len(parts) > 1:
                data = ":".join(parts[1:])  # Rejoin in case data contains colons
                return self.handle_process(data)
            else:
                return "Usage: process:data_to_process"
        
        elif action == "example":
            # Example feature demonstration
            return self.show_example()
        
        # === UNKNOWN COMMAND ===
        else:
            return f"Unknown command: {action}\nTry: {self.app_prefix}:help"
    
    # === CORE COMMAND HANDLERS ===
    
    def show_help(self):
        """Show comprehensive help for the app"""
        return f"""🔧 **{self.name} v{self.version} Help**

**📋 Core Commands:**
• help - Show this help
• status - Show app status and statistics
• config - Show/set configuration
• history - Show command history
• data - Manage app data
• export - Export app data
• clear - Clear app data
• reset - Reset app to defaults

**🎯 Custom Commands:**
• hello[:name] - Say hello (example command)
• process:data - Process data (example command)
• example - Show example usage

**⚙️ Configuration:**
• config:key:value - Set configuration
• config:key - Get configuration value
• config - Show all settings

**📊 Data Management:**
• data:list - List data keys
• data:get:key - Get data value
• data:set:key:value - Set data value
• data:delete:key - Delete data entry

**💡 Examples:**
```
{self.app_prefix}:hello:Alice
{self.app_prefix}:process:some_data
{self.app_prefix}:config:debug_mode:true
{self.app_prefix}:data:set:my_key:my_value
{self.app_prefix}:export:my_backup
```

**📖 About:**
{self.description}
Author: {self.author}

**🚀 Usage Pattern:**
{self.app_prefix}:command:parameters"""
    
    def show_status(self):
        """Show detailed app status"""
        uptime = datetime.now() - self.session_stats["session_start"]
        
        return f"""📊 **{self.name} Status**

**📱 App Info:**
• Name: {self.name}
• Version: {self.version}
• Author: {self.author}
• Prefix: {self.app_prefix}

**⏱️ Session Info:**
• Uptime: {uptime}
• Commands executed: {self.session_stats["commands_executed"]}
• Last command: {self.session_stats["last_command"] or "None"}

**💾 Data Info:**
• Data entries: {len(self.data)}
• History entries: {len(self.command_history)}
• Auto-save: {self.config.get('auto_save', True)}
• Debug mode: {self.config.get('debug_mode', False)}

**🔧 Configuration:**
• Config entries: {len(self.config)}
• Data directory: {self.data_dir}"""
    
    def show_config(self):
        """Show all configuration settings"""
        result = f"⚙️ **{self.name} Configuration:**\n\n"
        for key, value in self.config.items():
            result += f"• {key} = {value}\n"
        result += f"\n**To change:** {self.app_prefix}:config:key:value"
        return result
    
    def set_config(self, key, value):
        """Set configuration value with type conversion"""
        # Intelligent type conversion
        if value.lower() in ["true", "false"]:
            value = value.lower() == "true"
        elif value.isdigit():
            value = int(value)
        elif value.replace('.', '', 1).isdigit():
            value = float(value)
        
        self.config[key] = value
        
        if self.config.get("auto_save", True):
            self.save_config()
        
        return f"⚙️ Set {key} = {value}"
    
    def show_history(self, count):
        """Show command history"""
        if not self.command_history:
            return "📝 No command history"
        
        recent = self.command_history[-count:] if count > 0 else self.command_history
        result = f"📝 **Command History (last {len(recent)}):**\n\n"
        
        for i, entry in enumerate(recent, 1):
            timestamp = entry["timestamp"][:19].replace("T", " ")
            command = entry["command"][:50] + "..." if len(entry["command"]) > 50 else entry["command"]
            result += f"{i:2d}. {timestamp} - {command}\n"
        
        return result
    
    def handle_data_command(self, parts):
        """Handle data management commands"""
        if not parts:
            return f"📊 Data keys: {', '.join(self.data.keys()) if self.data else 'None'}"
        
        action = parts[0].lower()
        
        if action == "list":
            if not self.data:
                return "📊 No data stored"
            result = f"📊 **Data Entries ({len(self.data)}):**\n\n"
            for key, value in self.data.items():
                value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                result += f"• {key}: {value_str}\n"
            return result
        
        elif action == "get":
            if len(parts) < 2:
                return "Usage: data:get:key"
            key = parts[1]
            return f"{key} = {self.data.get(key, 'Not found')}"
        
        elif action == "set":
            if len(parts) < 3:
                return "Usage: data:set:key:value"
            key = parts[1]
            value = ":".join(parts[2:])  # Rejoin in case value contains colons
            self.data[key] = value
            return f"📊 Set {key} = {value}"
        
        elif action == "delete":
            if len(parts) < 2:
                return "Usage: data:delete:key"
            key = parts[1]
            if key in self.data:
                del self.data[key]
                return f"🗑️ Deleted {key}"
            else:
                return f"❌ Key '{key}' not found"
        
        else:
            return f"Unknown data command: {action}\nAvailable: list, get, set, delete"
    
    def add_to_history(self, command, result):
        """Add command to history"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "result": result[:100] + "..." if len(result) > 100 else result
        }
        
        self.command_history.append(entry)
        
        # Keep history size manageable
        max_history = self.config.get("max_history", 100)
        if len(self.command_history) > max_history:
            self.command_history = self.command_history[-max_history:]
    
    def export_data(self, filename):
        """Export all app data"""
        try:
            export_data = {
                "app_info": {
                    "name": self.name,
                    "version": self.version,
                    "author": self.author,
                    "export_time": datetime.now().isoformat()
                },
                "config": self.config,
                "data": self.data,
                "history": self.command_history,
                "session_stats": self.session_stats
            }
            
            export_path = os.path.join("pxbot_code", "exports", f"{filename}.json")
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            with open(export_path, "w") as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return f"📊 Exported to: {export_path}"
        except Exception as e:
            return f"❌ Export failed: {e}"
    
    def clear_data(self):
        """Clear all app data"""
        self.data.clear()
        self.command_history.clear()
        self.session_stats = {
            "commands_executed": 0,
            "session_start": datetime.now(),
            "last_command": None
        }
        return f"🗑️ All {self.name} data cleared"
    
    def reset_app(self):
        """Reset app to default state"""
        self.clear_data()
        self.config = self.load_config()  # Reload default config
        return f"🔄 {self.name} reset to defaults"
    
    # === CUSTOM COMMAND HANDLERS ===
    # Implement your app-specific functionality here
    
    def handle_hello(self, name):
        """Example command: say hello"""
        greeting = f"Hello, {name}! Welcome to {self.name}."
        
        # Store greeting in data for demonstration
        self.data[f"last_greeting"] = greeting
        self.data[f"greeting_time"] = datetime.now().isoformat()
        
        return f"👋 {greeting}"
    
    def handle_process(self, data):
        """Example command: process data"""
        # Example processing: reverse the data and count characters
        processed = data[::-1]  # Reverse
        char_count = len(data)
        word_count = len(data.split())
        
        # Store processing result
        self.data["last_processed"] = {
            "original": data,
            "processed": processed,
            "char_count": char_count,
            "word_count": word_count,
            "timestamp": datetime.now().isoformat()
        }
        
        return f"""📊 **Data Processed:**

**Original:** {data}
**Processed:** {processed}
**Stats:** {char_count} chars, {word_count} words
**Timestamp:** {datetime.now().strftime('%H:%M:%S')}"""
    
    def show_example(self):
        """Show example usage of the app"""
        return f"""💡 **{self.name} Examples:**

**🎯 Basic Usage:**
```
{self.app_prefix}:hello:Alice           # Say hello to Alice
{self.app_prefix}:process:Hello World   # Process some text
{self.app_prefix}:status                # Check app status
```

**⚙️ Configuration:**
```
{self.app_prefix}:config:debug_mode:true    # Enable debug mode
{self.app_prefix}:config:auto_save:false    # Disable auto-save
{self.app_prefix}:config                    # Show all settings
```

**📊 Data Management:**
```
{self.app_prefix}:data:set:name:Alice       # Store data
{self.app_prefix}:data:get:name             # Retrieve data
{self.app_prefix}:data:list                 # List all data
```

**🔧 Utilities:**
```
{self.app_prefix}:history:5                 # Show last 5 commands
{self.app_prefix}:export:my_backup          # Export all data
{self.app_prefix}:clear                     # Clear all data
```

**🚀 Advanced Integration:**
If you have PXBot runtime access, you can:
- Save data as pixel codes
- Create pixel art from app data
- Integrate with other PXBot apps
- Use AI assistant features

**📖 Next Steps:**
1. Try the example commands above
2. Customize this template for your needs
3. Add your own command handlers
4. Test and deploy your app!"""
    
    # === PXBOT INTEGRATION ===
    
    def export_to_pixel_code(self, name):
        """Export app data as PXBot pixel code"""
        if not self.pxbot:
            return "❌ PXBot instance not available"
        
        try:
            # Create Python code representation of app data
            code = f'''# {self.name} Export
# Generated: {datetime.now().isoformat()}

app_data = {json.dumps(self.data, indent=2)}
config = {json.dumps(self.config, indent=2)}

def get_app_data():
    """Get exported app data"""
    return app_data

def get_config():
    """Get exported configuration"""
    return config

def search_data(query):
    """Search through app data"""
    results = []
    for key, value in app_data.items():
        if query.lower() in str(key).lower() or query.lower() in str(value).lower():
            results.append((key, value))
    return results

# Auto-display on import
if __name__ == "__main__":
    print(f"📱 {self.name} Data Export")
    print(f"📊 Data entries: {{len(app_data)}}")
    print(f"⚙️ Config entries: {{len(config)}}")
    for key in list(app_data.keys())[:5]:
        print(f"  • {{key}}: {{app_data[key]}}")
    if len(app_data) > 5:
        print(f"  ... and {{len(app_data) - 5}} more entries")
'''
            
            result = self.pxbot.run(f"save:{name}:{code}")
            return f"🎨 Exported to pixel code: {result}"
        except Exception as e:
            return f"❌ Pixel export failed: {e}"
    
    def get_pxbot_integration_info(self):
        """Get information about PXBot integration capabilities"""
        if not self.pxbot:
            return "❌ No PXBot integration available"
        
        return f"""🎨 **PXBot Integration Available:**

**✨ Capabilities:**
• Export data as pixel codes
• Access to pixel programming tools
• AI assistant integration
• Code visualization features

**🔧 Available Methods:**
• export_to_pixel_code(name) - Save app data as pixel art
• pxbot.run(command) - Execute PXBot commands
• Access to pixel tools and AI features

**💡 Usage Examples:**
```python
# In your custom commands:
def my_export_command(self):
    return self.export_to_pixel_code("my_app_data")

def my_ai_command(self):
    if self.pxbot:
        return self.pxbot.run("create:function:my_func:param:None")
```"""
    
    # === CLEANUP ===
    
    def cleanup(self):
        """
        Cleanup when app is being unloaded
        Override this method to add custom cleanup
        """
        try:
            # Save data if auto-save is enabled
            if self.config.get("auto_save", True):
                self.save_app_data()
                self.save_config()
            
            # Custom cleanup
            self.custom_cleanup()
            
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def custom_cleanup(self):
        """
        Override this method for custom cleanup
        Example: close database connections, save files, etc.
        """
        # Add your custom cleanup code here
        pass

# === REQUIRED MAIN FUNCTION ===
def main():
    """
    Entry point for the app - REQUIRED
    This function must return an instance of your app class
    """
    return AppTemplate()

# === TESTING AND DEVELOPMENT ===
if __name__ == "__main__":
    """
    Test the app directly for development
    Run: python app_template.py
    """
    print("🧪 App Template Development Test")
    print("=" * 40)
    
    # Create app instance
    app = main()
    
    # Test basic functionality
    test_commands = [
        "app_template:help",
        "app_template:hello:Developer",
        "app_template:process:Test Data",
        "app_template:status",
        "app_template:data:set:test_key:test_value",
        "app_template:data:list",
        "app_template:example"
    ]
    
    print(f"Testing {len(test_commands)} commands...\n")
    
    for i, command in enumerate(test_commands, 1):
        print(f"Test {i}: {command}")
        result = app.execute_command(command)
        # Show first 200 chars of result
        short_result = result[:200] + "..." if len(result) > 200 else result
        print(f"Result: {short_result}")
        print("-" * 40)
    
    print("✅ Template test complete!")
    print("\n📖 To create your own app:")
    print("1. Copy this file to apps/your_app_name.py")
    print("2. Change the class name and app details")
    print("3. Implement your custom commands") 
    print("4. Test with: python apps/your_app_name.py")
    print("5. Use in PXBot: your_app_name:command")
    
    # Cleanup
    app.cleanup()
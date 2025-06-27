# PXBot Developer Guide

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
        code = "# Generated code\nprint('Hello!')"
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

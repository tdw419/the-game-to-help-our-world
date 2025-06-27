# 🚀 PXBot App Development Guide

## Overview
The PXBot launcher supports a modular app system where you can create custom applications that integrate seamlessly with the pixel programming environment. Apps are Python modules placed in the `apps/` directory.

## 📁 Directory Structure
```
your_project/
├── pxbot_launcher.py
├── pxbot_runtime.py
└── apps/
    ├── __init__.py
    ├── pxos_app.py          # Core system app
    ├── my_custom_app.py     # Your custom app
    ├── pixel_editor.py      # Example: Pixel art editor
    ├── code_analyzer.py     # Example: Code analysis tool
    └── web_scraper.py       # Example: Web scraping tool
```

## 🔧 App Structure Requirements

### Basic App Template
```python
#!/usr/bin/env python3
"""
My Custom App - Description of what it does
"""

import os
import json
from datetime import datetime

class MyCustomApp:
    def __init__(self, pxbot_instance=None):
        self.name = "My Custom App"
        self.version = "1.0.0"
        self.description = "Description of my app"
        self.pxbot = pxbot_instance
        
        # App state
        self.data = {}
        self.config = self.load_config()
    
    def load_config(self):
        """Load app configuration"""
        config_path = os.path.join("pxbot_code", f"{self.name.lower().replace(' ', '_')}_config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Config load error: {e}")
        return {"setting1": "default_value"}
    
    def save_config(self):
        """Save app configuration"""
        config_path = os.path.join("pxbot_code", f"{self.name.lower().replace(' ', '_')}_config.json")
        try:
            os.makedirs("pxbot_code", exist_ok=True)
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Config save error: {e}")
    
    def execute_command(self, command):
        """Handle commands from the launcher"""
        try:
            if command.startswith("myapp:"):
                # Remove app prefix
                cmd = command[6:]
                return self.handle_app_command(cmd)
            else:
                return f"Unknown command: {command}"
        except Exception as e:
            return f"Error: {e}"
    
    def handle_app_command(self, command):
        """Handle app-specific commands"""
        parts = command.split(":")
        action = parts[0]
        
        if action == "hello":
            return f"Hello from {self.name}!"
        elif action == "status":
            return self.get_status()
        elif action == "config":
            if len(parts) > 1:
                key, value = parts[1], parts[2] if len(parts) > 2 else None
                if value:
                    self.config[key] = value
                    self.save_config()
                    return f"Set {key} = {value}"
                else:
                    return f"{key} = {self.config.get(key, 'Not set')}"
        
        return f"Available commands: hello, status, config"
    
    def get_status(self):
        """Get app status information"""
        return f"{self.name} v{self.version} - Status: OK"
    
    def cleanup(self):
        """Cleanup when app is unloaded"""
        self.save_config()

# Required: main() function that returns app instance
def main():
    """Entry point for the app"""
    return MyCustomApp()

# Optional: Direct execution for testing
if __name__ == "__main__":
    app = main()
    print(app.execute_command("myapp:hello"))
```

## 🎨 Example Apps

### 1. Pixel Art Editor App
```python
#!/usr/bin/env python3
"""
Pixel Art Editor - Create and edit pixel art with PXBot integration
"""

import os
import json
from PIL import Image, ImageDraw

class PixelArtEditor:
    def __init__(self, pxbot_instance=None):
        self.name = "Pixel Art Editor"
        self.version = "1.0.0"
        self.pxbot = pxbot_instance
        
        self.canvas_size = (64, 64)
        self.current_canvas = None
        self.color_palette = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255),
            (255, 255, 255), (0, 0, 0)
        ]
        self.current_color = (255, 255, 255)
    
    def execute_command(self, command):
        try:
            if command.startswith("pixedit:"):
                cmd = command[8:]
                return self.handle_command(cmd)
            return "Use pixedit: prefix for commands"
        except Exception as e:
            return f"Error: {e}"
    
    def handle_command(self, command):
        parts = command.split(":")
        action = parts[0]
        
        if action == "new":
            size = int(parts[1]) if len(parts) > 1 else 64
            return self.new_canvas(size)
        elif action == "load":
            filename = parts[1] if len(parts) > 1 else "canvas"
            return self.load_canvas(filename)
        elif action == "save":
            filename = parts[1] if len(parts) > 1 else "canvas"
            return self.save_canvas(filename)
        elif action == "pixel":
            x, y = int(parts[1]), int(parts[2])
            color = parts[3] if len(parts) > 3 else None
            return self.set_pixel(x, y, color)
        elif action == "color":
            if len(parts) > 1:
                r, g, b = map(int, parts[1:4])
                self.current_color = (r, g, b)
                return f"Color set to RGB({r}, {g}, {b})"
            return f"Current color: RGB{self.current_color}"
        elif action == "export":
            filename = parts[1] if len(parts) > 1 else "pixel_art"
            return self.export_to_pxbot(filename)
        
        return "Commands: new, load, save, pixel:x:y[:color], color:r:g:b, export"
    
    def new_canvas(self, size=64):
        self.canvas_size = (size, size)
        self.current_canvas = Image.new("RGB", self.canvas_size, (0, 0, 0))
        return f"Created new {size}x{size} canvas"
    
    def set_pixel(self, x, y, color=None):
        if not self.current_canvas:
            self.new_canvas()
        
        if color:
            # Parse color from hex or rgb
            if color.startswith("#"):
                hex_color = color[1:]
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            else:
                rgb = self.current_color
        else:
            rgb = self.current_color
        
        pixels = self.current_canvas.load()
        if 0 <= x < self.canvas_size[0] and 0 <= y < self.canvas_size[1]:
            pixels[x, y] = rgb
            return f"Set pixel ({x}, {y}) to RGB{rgb}"
        return f"Pixel ({x}, {y}) out of bounds"
    
    def save_canvas(self, filename):
        if not self.current_canvas:
            return "No canvas to save"
        
        filepath = os.path.join("pxbot_code", f"{filename}.png")
        os.makedirs("pxbot_code", exist_ok=True)
        self.current_canvas.save(filepath)
        return f"Canvas saved to {filepath}"
    
    def load_canvas(self, filename):
        filepath = os.path.join("pxbot_code", f"{filename}.png")
        try:
            self.current_canvas = Image.open(filepath)
            self.canvas_size = self.current_canvas.size
            return f"Loaded canvas from {filepath} ({self.canvas_size[0]}x{self.canvas_size[1]})"
        except Exception as e:
            return f"Failed to load {filepath}: {e}"
    
    def export_to_pxbot(self, name):
        if not self.current_canvas or not self.pxbot:
            return "No canvas or PXBot instance available"
        
        # Convert image to code representation
        width, height = self.current_canvas.size
        pixels = self.current_canvas.load()
        
        code = f'''# Generated pixel art: {name}
import matplotlib.pyplot as plt
import numpy as np

def draw_{name}():
    """Generated pixel art function"""
    data = ['''
        
        for y in range(height):
            row = []
            for x in range(width):
                r, g, b = pixels[x, y]
                row.append(f"[{r}, {g}, {b}]")
            code += f"\n        [{', '.join(row)}],"
        
        code += f'''
    ]
    
    plt.imshow(data)
    plt.axis('off')
    plt.title('{name}')
    plt.show()
    return data

# Auto-execute
if __name__ == "__main__":
    draw_{name}()
'''
        
        # Save to PXBot
        result = self.pxbot.run(f"save:{name}_art:{code}")
        return f"Exported to PXBot as '{name}_art': {result}"

def main():
    return PixelArtEditor()
```

### 2. Code Analyzer App
```python
#!/usr/bin/env python3
"""
Code Analyzer - Analyze and improve PXBot code quality
"""

import ast
import os
import re
from collections import defaultdict

class CodeAnalyzer:
    def __init__(self, pxbot_instance=None):
        self.name = "Code Analyzer"
        self.version = "1.0.0"
        self.pxbot = pxbot_instance
        self.analysis_results = {}
    
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
        
        if action == "code":
            code_name = parts[1] if len(parts) > 1 else None
            return self.analyze_code(code_name)
        elif action == "all":
            return self.analyze_all_codes()
        elif action == "quality":
            code_name = parts[1] if len(parts) > 1 else None
            return self.quality_report(code_name)
        elif action == "suggest":
            code_name = parts[1] if len(parts) > 1 else None
            return self.suggest_improvements(code_name)
        elif action == "complexity":
            code_name = parts[1] if len(parts) > 1 else None
            return self.complexity_analysis(code_name)
        
        return "Commands: code:name, all, quality:name, suggest:name, complexity:name"
    
    def analyze_code(self, code_name):
        if not self.pxbot:
            return "No PXBot instance available"
        
        if not code_name:
            codes = self.pxbot.r.list_codes()
            return f"Available codes: {', '.join(codes)}"
        
        code = self.pxbot.r.load_code(code_name)
        if not code:
            return f"Code '{code_name}' not found"
        
        try:
            # Parse the code
            tree = ast.parse(code)
            analysis = self.perform_analysis(tree, code)
            self.analysis_results[code_name] = analysis
            
            return self.format_analysis_report(code_name, analysis)
        except SyntaxError as e:
            return f"Syntax error in {code_name}: {e}"
    
    def perform_analysis(self, tree, code):
        analysis = {
            'lines': len(code.split('\n')),
            'functions': 0,
            'classes': 0,
            'imports': 0,
            'complexity': 0,
            'docstrings': 0,
            'comments': 0,
            'issues': []
        }
        
        # Count code elements
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                analysis['functions'] += 1
                if ast.get_docstring(node):
                    analysis['docstrings'] += 1
            elif isinstance(node, ast.ClassDef):
                analysis['classes'] += 1
                if ast.get_docstring(node):
                    analysis['docstrings'] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                analysis['imports'] += 1
            elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                analysis['complexity'] += 1
        
        # Count comments
        analysis['comments'] = len([line for line in code.split('\n') 
                                  if line.strip().startswith('#')])
        
        # Check for common issues
        if analysis['functions'] > 0 and analysis['docstrings'] == 0:
            analysis['issues'].append("No function docstrings found")
        
        if analysis['lines'] > 100 and analysis['comments'] < analysis['lines'] * 0.1:
            analysis['issues'].append("Low comment ratio for large file")
        
        if 'print(' in code:
            analysis['issues'].append("Contains print statements (consider logging)")
        
        return analysis
    
    def format_analysis_report(self, code_name, analysis):
        report = f"📊 **Analysis Report for '{code_name}'**\n\n"
        report += f"**📈 Metrics:**\n"
        report += f"• Lines of code: {analysis['lines']}\n"
        report += f"• Functions: {analysis['functions']}\n"
        report += f"• Classes: {analysis['classes']}\n"
        report += f"• Imports: {analysis['imports']}\n"
        report += f"• Complexity score: {analysis['complexity']}\n"
        report += f"• Docstrings: {analysis['docstrings']}\n"
        report += f"• Comments: {analysis['comments']}\n\n"
        
        if analysis['issues']:
            report += f"**⚠️ Issues Found:**\n"
            for issue in analysis['issues']:
                report += f"• {issue}\n"
        else:
            report += f"**✅ No issues found!**\n"
        
        return report
    
    def quality_report(self, code_name):
        if code_name not in self.analysis_results:
            self.analyze_code(code_name)
        
        if code_name not in self.analysis_results:
            return f"No analysis data for '{code_name}'"
        
        analysis = self.analysis_results[code_name]
        
        # Calculate quality score
        score = 100
        
        # Deduct points for issues
        score -= len(analysis['issues']) * 10
        
        # Adjust for complexity
        if analysis['complexity'] > analysis['functions'] * 3:
            score -= 20  # High complexity
        
        # Adjust for documentation
        if analysis['functions'] > 0:
            doc_ratio = analysis['docstrings'] / analysis['functions']
            if doc_ratio < 0.5:
                score -= 15
        
        quality = "Excellent" if score >= 90 else "Good" if score >= 70 else "Fair" if score >= 50 else "Poor"
        
        return f"🎯 **Quality Score for '{code_name}': {score}/100 ({quality})**"
    
    def suggest_improvements(self, code_name):
        if code_name not in self.analysis_results:
            self.analyze_code(code_name)
        
        if code_name not in self.analysis_results:
            return f"No analysis data for '{code_name}'"
        
        analysis = self.analysis_results[code_name]
        suggestions = []
        
        if analysis['functions'] > 0 and analysis['docstrings'] < analysis['functions']:
            suggestions.append("Add docstrings to functions for better documentation")
        
        if analysis['complexity'] > 10:
            suggestions.append("Consider breaking down complex functions")
        
        if analysis['lines'] > 200:
            suggestions.append("Consider splitting large files into modules")
        
        if analysis['comments'] < analysis['lines'] * 0.05:
            suggestions.append("Add more comments to explain complex logic")
        
        if not suggestions:
            suggestions.append("Code looks good! No specific improvements suggested.")
        
        report = f"💡 **Improvement Suggestions for '{code_name}':**\n\n"
        for i, suggestion in enumerate(suggestions, 1):
            report += f"{i}. {suggestion}\n"
        
        return report

def main():
    return CodeAnalyzer()
```

### 3. Web Scraper App
```python
#!/usr/bin/env python3
"""
Web Scraper - Fetch and process web content for PXBot
"""

import urllib.request
import urllib.parse
import json
import re
import html
from datetime import datetime

class WebScraper:
    def __init__(self, pxbot_instance=None):
        self.name = "Web Scraper"
        self.version = "1.0.0"
        self.pxbot = pxbot_instance
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.scraped_data = {}
    
    def execute_command(self, command):
        try:
            if command.startswith("scrape:"):
                cmd = command[7:]
                return self.handle_command(cmd)
            return "Use scrape: prefix for commands"
        except Exception as e:
            return f"Error: {e}"
    
    def handle_command(self, command):
        parts = command.split(":")
        action = parts[0]
        
        if action == "url":
            url = parts[1] if len(parts) > 1 else None
            return self.scrape_url(url)
        elif action == "github":
            repo = parts[1] if len(parts) > 1 else None
            return self.scrape_github_repo(repo)
        elif action == "news":
            topic = parts[1] if len(parts) > 1 else "technology"
            return self.scrape_news(topic)
        elif action == "save":
            name = parts[1] if len(parts) > 1 else "scraped_data"
            return self.save_to_pxbot(name)
        elif action == "list":
            return self.list_scraped_data()
        
        return "Commands: url:URL, github:user/repo, news:topic, save:name, list"
    
    def scrape_url(self, url):
        if not url:
            return "Please provide a URL to scrape"
        
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            req = urllib.request.Request(url, headers=self.headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8', errors='ignore')
                
                # Extract text content
                text_content = self.extract_text(content)
                
                # Store scraped data
                self.scraped_data[url] = {
                    'timestamp': datetime.now().isoformat(),
                    'content': text_content,
                    'length': len(text_content)
                }
                
                return f"✅ Scraped {len(text_content)} characters from {url}"
                
        except Exception as e:
            return f"❌ Failed to scrape {url}: {e}"
    
    def extract_text(self, html_content):
        """Extract readable text from HTML"""
        # Remove script and style elements
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Convert common HTML elements to text
        html_content = re.sub(r'<br[^>]*>', '\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<p[^>]*>', '\n\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<h[1-6][^>]*>', '\n\n## ', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'</h[1-6]>', '\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'<li[^>]*>', '\n• ', html_content, flags=re.IGNORECASE)
        
        # Remove all other HTML tags
        html_content = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode HTML entities
        html_content = html.unescape(html_content)
        
        # Clean up whitespace
        html_content = re.sub(r'\n\s*\n\s*\n', '\n\n', html_content)
        html_content = re.sub(r'[ \t]+', ' ', html_content)
        
        return html_content.strip()
    
    def scrape_github_repo(self, repo):
        if not repo or '/' not in repo:
            return "Please provide a GitHub repo in format: user/repository"
        
        api_url = f"https://api.github.com/repos/{repo}"
        
        try:
            req = urllib.request.Request(api_url, headers=self.headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                info = {
                    'name': data.get('name', 'Unknown'),
                    'description': data.get('description', 'No description'),
                    'language': data.get('language', 'Unknown'),
                    'stars': data.get('stargazers_count', 0),
                    'forks': data.get('forks_count', 0),
                    'url': data.get('html_url', ''),
                    'created': data.get('created_at', ''),
                    'updated': data.get('updated_at', '')
                }
                
                self.scraped_data[f"github:{repo}"] = info
                
                report = f"📦 **GitHub Repo: {info['name']}**\n\n"
                report += f"**Description:** {info['description']}\n"
                report += f"**Language:** {info['language']}\n"
                report += f"**Stars:** {info['stars']} ⭐\n"
                report += f"**Forks:** {info['forks']} 🍴\n"
                report += f"**URL:** {info['url']}\n"
                
                return report
                
        except Exception as e:
            return f"❌ Failed to scrape GitHub repo {repo}: {e}"
    
    def scrape_news(self, topic):
        # Simple news scraping using a news aggregator
        # In a real implementation, you'd use a proper news API
        search_url = f"https://news.google.com/search?q={urllib.parse.quote(topic)}"
        
        try:
            result = self.scrape_url(search_url)
            if "✅" in result:
                return f"📰 Scraped news about '{topic}': {result}"
            else:
                return result
        except Exception as e:
            return f"❌ Failed to scrape news about {topic}: {e}"
    
    def save_to_pxbot(self, name):
        if not self.scraped_data or not self.pxbot:
            return "No scraped data or PXBot instance available"
        
        # Convert scraped data to Python code
        code = f'''# Scraped data: {name}
# Generated on {datetime.now().isoformat()}

scraped_data = {json.dumps(self.scraped_data, indent=2)}

def get_scraped_content(key=None):
    """Get scraped content by key or all data"""
    if key:
        return scraped_data.get(key, {{}})
    return scraped_data

def list_scraped_keys():
    """List all available scraped data keys"""
    return list(scraped_data.keys())

def search_content(query):
    """Search for content containing the query"""
    results = []
    query = query.lower()
    for key, data in scraped_data.items():
        content = str(data.get('content', ''))
        if query in content.lower():
            results.append({{
                'key': key,
                'snippet': content[:200] + '...' if len(content) > 200 else content
            }})
    return results

# Auto-display on import
if __name__ == "__main__":
    print(f"Scraped data available for {len(scraped_data)} sources")
    for key in scraped_data:
        print(f"  • {key}")
'''
        
        result = self.pxbot.run(f"save:{name}:{code}")
        return f"💾 Saved scraped data to PXBot as '{name}': {result}"
    
    def list_scraped_data(self):
        if not self.scraped_data:
            return "No scraped data available"
        
        report = f"📋 **Scraped Data ({len(self.scraped_data)} items):**\n\n"
        for key, data in self.scraped_data.items():
            timestamp = data.get('timestamp', 'Unknown')
            length = data.get('length', len(str(data)))
            report += f"• **{key}** - {length} chars - {timestamp[:10]}\n"
        
        return report

def main():
    return WebScraper()
```

## 🔌 API Integration

### Accessing PXBot Runtime
```python
def my_function(self, pxbot_instance):
    # Access saved codes
    codes = pxbot_instance.r.list_codes()
    
    # Load specific code
    code_content = pxbot_instance.r.load_code("my_code")
    
    # Execute code
    result = pxbot_instance.r.exec_code("my_code")
    
    # Save new code
    pxbot_instance.run("save:new_code:print('Hello World')")
```

### Command System Integration
```python
def execute_command(self, command):
    # Your app should handle commands in this format:
    # "appname:action:param1:param2"
    
    if command.startswith("myapp:"):
        action = command[6:]  # Remove "myapp:" prefix
        return self.handle_action(action)
```

## 🚀 Installation & Testing

### 1. Create App Directory
```bash
mkdir apps
cd apps
touch __init__.py
```

### 2. Create Your App
```python
# Save as apps/my_app.py
# Use one of the templates above
```

### 3. Test Your App
```bash
# Test directly
python apps/my_app.py

# Test in launcher
python pxbot_launcher.py
# Then use: myapp:hello
```

### 4. Advanced Features

#### Configuration Management
```python
def load_config(self):
    # Apps can save/load their own config files
    config_path = os.path.join("pxbot_code", f"{self.name}_config.json")
    # ... implementation
```

#### State Persistence
```python
def save_state(self):
    # Save app state between sessions
    state_path = os.path.join("pxbot_code", f"{self.name}_state.json")
    # ... implementation
```

#### GUI Integration
```python
def create_gui(self):
    # Apps can create their own GUI windows
    import tkinter as tk
    window = tk.Toplevel()
    # ... implementation
```

## 📚 Best Practices

### 1. **Error Handling**
- Always wrap operations in try-catch blocks
- Return meaningful error messages
- Log errors for debugging

### 2. **Resource Management**
- Clean up resources in `cleanup()` method
- Save state before app shutdown
- Handle file operations safely

### 3. **Command Structure**
- Use consistent command prefixes
- Provide help commands
- Support tab completion

### 4. **Integration**
- Make use of PXBot's pixel programming features
- Save results as pixel codes when appropriate
- Follow the established patterns

### 5. **Testing**
- Test apps independently
- Test integration with launcher
- Handle edge cases gracefully

## 🎯 Publishing Your App

1. **Package Structure**
```
my_awesome_app/
├── __init__.py
├── my_awesome_app.py
├── README.md
├── requirements.txt
└── examples/
    └── example_usage.py
```

2. **Documentation**
- Include clear usage instructions
- Provide example commands
- Document any dependencies

3. **Share with Community**
- Create GitHub repository
- Add to app marketplace (if available)
- Contribute to PXBot ecosystem

Happy coding! 🚀✨
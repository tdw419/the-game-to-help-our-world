#!/usr/bin/env python3
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
            body = "if n <= 1: return 1\n return n * factorial(n-1)"
        else:
            body = "pass"
        
        code = f"def {name}({params}):\n {body}\n return {return_val}"
        return self._save_code(code, name)
    
    def _create_class(self, name, attrs, methods):
        attrs_init = "\n ".join([f"self.{x.strip()} = {x.strip()}" for x in attrs.split(",") if x.strip()])
        methods_def = "\n ".join([f"def {x.strip()}(self): pass" for x in methods.split(",") if x.strip()])
        
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
        
        modified_code = existing_code + f"\n# {modification}"
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
            
            return bytes(data).decode('utf-8', errors='ignore').rstrip('\x00')
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

class PixelProgrammingTools:
    """Advanced pixel programming tools for code manipulation"""
    
    def __init__(self, pxbot):
        self.pxbot = pxbot
    
    def create_pixel_art_from_code(self, code_name):
        """Convert code to colorful pixel art"""
        code = self.pxbot.r.load_code(code_name)
        if not code:
            return f"❌ Code '{code_name}' not found"
        
        try:
            # Create artistic representation
            data = code.encode('utf-8')
            size = max(32, int(len(data)**0.5) + 8)
            
            image = Image.new("RGB", (size, size), (0, 0, 0))
            pixels = image.load()
            
            # Color mapping for different code elements
            colors = {
                'def': (100, 200, 255),     # Blue for functions
                'class': (255, 150, 100),   # Orange for classes
                'import': (150, 255, 150),  # Green for imports
                'return': (255, 255, 100),  # Yellow for returns
                'if': (255, 100, 255),      # Magenta for conditionals
                'for': (100, 255, 255),     # Cyan for loops
            }
            
            # Analyze code and create art
            lines = code.split('\n')
            for y, line in enumerate(lines[:size]):
                for x, char in enumerate(line[:size]):
                    if x < size and y < size:
                        # Base color from ASCII value
                        base_color = ord(char) if char else 0
                        
                        # Enhanced color based on keywords
                        color = (base_color, base_color//2, base_color//3)
                        for keyword, keyword_color in colors.items():
                            if keyword in line:
                                color = keyword_color
                                break
                        
                        pixels[x, y] = color
            
            # Save artistic version
            art_path = os.path.join(os.getcwd(), "pxbot_code", f"{code_name}_art.png")
            image.save(art_path)
            
            return f"🎨 Created pixel art for '{code_name}' -> {art_path}\nSize: {size}x{size} pixels\nLines analyzed: {len(lines)}"
            
        except Exception as e:
            return f"❌ Error creating pixel art: {e}"
    
    def analyze_pixel_density(self, code_name):
        """Analyze pixel density and code structure"""
        code = self.pxbot.r.load_code(code_name)
        if not code:
            return f"❌ Code '{code_name}' not found"
        
        try:
            lines = code.split('\n')
            total_chars = len(code)
            non_empty_lines = [line for line in lines if line.strip()]
            
            # Count different code elements
            functions = len([line for line in lines if 'def ' in line])
            classes = len([line for line in lines if 'class ' in line])
            imports = len([line for line in lines if 'import ' in line or 'from ' in line])
            comments = len([line for line in lines if line.strip().startswith('#')])
            
            # Calculate density metrics
            avg_line_length = sum(len(line) for line in non_empty_lines) / len(non_empty_lines) if non_empty_lines else 0
            code_density = len(non_empty_lines) / len(lines) if lines else 0
            
            return f"""🔍 **Pixel Density Analysis for '{code_name}'**

**📊 Basic Metrics:**
• Total characters: {total_chars}
• Total lines: {len(lines)}
• Non-empty lines: {len(non_empty_lines)}
• Average line length: {avg_line_length:.1f} chars
• Code density: {code_density:.1%}

**🏗️ Structure Analysis:**
• Functions: {functions}
• Classes: {classes}
• Imports: {imports}  
• Comments: {comments}

**🎨 Pixel Storage:**
• Estimated image size: {int(total_chars**0.5) + 1}x{int(total_chars**0.5) + 1}
• Pixel efficiency: {(total_chars / ((int(total_chars**0.5) + 1)**2)) * 100:.1f}%
• Storage format: Red channel encoding"""
            
        except Exception as e:
            return f"❌ Error analyzing pixel density: {e}"
    
    def merge_pixel_codes(self, code1_name, code2_name, new_name):
        """Merge two pixel codes into one"""
        code1 = self.pxbot.r.load_code(code1_name)
        code2 = self.pxbot.r.load_code(code2_name)
        
        if not code1:
            return f"❌ Code '{code1_name}' not found"
        if not code2:
            return f"❌ Code '{code2_name}' not found"
        
        try:
            # Smart merge - combine codes with proper structure
            merged_code = f"""# Merged from {code1_name} and {code2_name}
# Generated by PXBot Pixel Programming Tools

# Code from {code1_name}:
{code1}

# Code from {code2_name}:
{code2}

# Merged functionality
def merged_main():
    \"\"\"Combined functionality from both codes\"\"\"
    print("Executing merged code from {code1_name} and {code2_name}")
"""
            
            result = self.pxbot._save_code(merged_code, new_name)
            return f"🔧 **Code Merge Complete!**\n\n{result}\n\nMerged '{code1_name}' + '{code2_name}' -> '{new_name}'"
            
        except Exception as e:
            return f"❌ Error merging codes: {e}"
    
    def optimize_pixel_storage(self, code_name):
        """Optimize code for better pixel storage efficiency"""
        code = self.pxbot.r.load_code(code_name)
        if not code:
            return f"❌ Code '{code_name}' not found"
        
        try:
            original_size = len(code)
            
            # Optimization techniques
            optimized = code
            
            # Remove excessive whitespace while preserving Python structure
            lines = code.split('\n')
            optimized_lines = []
            for line in lines:
                stripped = line.rstrip()
                if stripped:
                    # Preserve indentation but remove trailing spaces
                    optimized_lines.append(stripped)
                elif optimized_lines and optimized_lines[-1].strip():
                    # Keep single empty lines between code blocks
                    optimized_lines.append('')
            
            # Remove multiple consecutive empty lines
            final_lines = []
            prev_empty = False
            for line in optimized_lines:
                if not line.strip():
                    if not prev_empty:
                        final_lines.append(line)
                    prev_empty = True
                else:
                    final_lines.append(line)
                    prev_empty = False
            
            optimized = '\n'.join(final_lines)
            new_size = len(optimized)
            savings = original_size - new_size
            
            # Save optimized version
            optimized_name = f"{code_name}_optimized"
            result = self.pxbot._save_code(optimized, optimized_name)
            
            return f"""⚡ **Storage Optimization Complete!**

**📊 Results:**
• Original size: {original_size} characters
• Optimized size: {new_size} characters  
• Space saved: {savings} characters ({(savings/original_size)*100:.1f}%)
• New pixel dimensions: {int(new_size**0.5) + 1}x{int(new_size**0.5) + 1}

**💾 Saved as:** {optimized_name}
{result}"""
            
        except Exception as e:
            return f"❌ Error optimizing storage: {e}"
    
    def create_pixel_pattern(self, pattern_type, size=32):
        """Create decorative pixel patterns"""
        try:
            image = Image.new("RGB", (size, size), (0, 0, 0))
            pixels = image.load()
            
            if pattern_type == "checkerboard":
                for x in range(size):
                    for y in range(size):
                        if (x + y) % 2 == 0:
                            pixels[x, y] = (255, 255, 255)
                        else:
                            pixels[x, y] = (0, 0, 0)
                            
            elif pattern_type == "gradient":
                for x in range(size):
                    for y in range(size):
                        r = int(255 * x / size)
                        g = int(255 * y / size)  
                        b = int(255 * (x + y) / (2 * size))
                        pixels[x, y] = (r, g, b)
                        
            elif pattern_type == "spiral":
                center_x, center_y = size // 2, size // 2
                for x in range(size):
                    for y in range(size):
                        dx, dy = x - center_x, y - center_y
                        angle = (dx**2 + dy**2)**0.5 * 0.2
                        color = int(128 + 127 * ((x + y + angle) % 2 - 1))
                        pixels[x, y] = (color, color//2, 255 - color)
                        
            elif pattern_type == "diamond":
                center = size // 2
                for x in range(size):
                    for y in range(size):
                        distance = abs(x - center) + abs(y - center)
                        if distance <= center:
                            intensity = int(255 * (1 - distance / center))
                            pixels[x, y] = (intensity, intensity//3, intensity//2)
            
            # Save pattern
            pattern_path = os.path.join(os.getcwd(), "pxbot_code", f"pattern_{pattern_type}_{size}x{size}.png")
            image.save(pattern_path)
            
            return f"🎨 Created {pattern_type} pattern ({size}x{size}) -> {pattern_path}"
            
        except Exception as e:
            return f"❌ Error creating pattern: {e}"
    
    def create_code_template(self, template_type, name):
        """Create code templates for common patterns"""
        templates = {
            "calculator": f'''class {name.title()}:
    """Advanced calculator with history and operations"""
    
    def __init__(self):
        self.history = []
        self.result = 0
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        self.result = result
        return result
    
    def subtract(self, a, b):
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        self.result = result
        return result
    
    def multiply(self, a, b):
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        self.result = result
        return result
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        self.result = result
        return result
    
    def get_history(self):
        return self.history
    
    def clear_history(self):
        self.history = []
        self.result = 0''',
        
            "data_processor": f'''class {name.title()}:
    """Data processing and analysis tools"""
    
    def __init__(self):
        self.data = []
        self.processed_data = []
    
    def load_data(self, data_list):
        self.data = data_list
        return f"Loaded {len(data_list)} items"
    
    def filter_data(self, condition_func):
        self.processed_data = [item for item in self.data if condition_func(item)]
        return self.processed_data
    
    def map_data(self, transform_func):
        self.processed_data = [transform_func(item) for item in self.data]
        return self.processed_data
    
    def reduce_data(self, reduce_func, initial=0):
        result = initial
        for item in self.data:
            result = reduce_func(result, item)
        return result
    
    def get_stats(self):
        if not self.data:
            return "No data loaded"
        
        numeric_data = [x for x in self.data if isinstance(x, (int, float))]
        if numeric_data:
            return {{
                "count": len(numeric_data),
                "sum": sum(numeric_data),
                "avg": sum(numeric_data) / len(numeric_data),
                "min": min(numeric_data),
                "max": max(numeric_data)
            }}
        return "No numeric data found"''',
        
            "web_scraper": f'''import urllib.request
import json

class {name.title()}:
    """Web scraping and API interaction tools"""
    
    def __init__(self):
        self.headers = {{
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }}
        self.last_response = None
    
    def fetch_url(self, url):
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                self.last_response = response.read().decode('utf-8')
                return self.last_response
        except Exception as e:
            return f"Error fetching {{url}}: {{e}}"
    
    def fetch_json(self, url):
        try:
            content = self.fetch_url(url)
            return json.loads(content)
        except json.JSONDecodeError:
            return "Invalid JSON response"
        except Exception as e:
            return f"Error: {{e}}"
    
    def extract_text(self, html_content):
        # Basic text extraction
        import re
        text = re.sub(r'<[^>]+>', '', html_content)
        text = re.sub(r'\\s+', ' ', text).strip()
        return text
    
    def save_content(self, filename, content):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Saved to {{filename}}"
        except Exception as e:
            return f"Error saving: {{e}}"''',
        
            "file_manager": f'''import os
import json

class {name.title()}:
    """File and data management utilities"""
    
    def __init__(self):
        self.current_dir = os.getcwd()
        self.file_cache = {{}}
    
    def list_files(self, directory=None):
        target_dir = directory or self.current_dir
        try:
            files = os.listdir(target_dir)
            return [f for f in files if os.path.isfile(os.path.join(target_dir, f))]
        except Exception as e:
            return f"Error listing files: {{e}}"
    
    def read_file(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                self.file_cache[filename] = content
                return content
        except Exception as e:
            return f"Error reading {{filename}}: {{e}}"
    
    def write_file(self, filename, content):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Written to {{filename}}"
        except Exception as e:
            return f"Error writing {{filename}}: {{e}}"
    
    def load_json(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return f"Error loading JSON from {{filename}}: {{e}}"
    
    def save_json(self, filename, data):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return f"JSON saved to {{filename}}"
        except Exception as e:
            return f"Error saving JSON to {{filename}}: {{e}}"
    
    def get_file_info(self, filename):
        try:
            stat = os.stat(filename)
            return {{
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "exists": True
            }}
        except Exception as e:
            return {{"exists": False, "error": str(e)}}'''
        }
        
        if template_type not in templates:
            return f"❌ Unknown template type: {template_type}\nAvailable: {', '.join(templates.keys())}"
        
        try:
            code = templates[template_type]
            result = self.pxbot._save_code(code, name)
            return f"🛠️ **Template Created!**\n\nType: {template_type}\nName: {name}\n\n{result}"
        except Exception as e:
            return f"❌ Error creating template: {e}"

class SmartPXBotChatbot:
    """Enhanced chatbot with pixel programming tools integration"""
    
    def __init__(self, pxbot_instance=None, gui_reference=None):
        self.pxbot = pxbot_instance
        self.gui = gui_reference
        self.conversation_history = []
        self.name = "PX Assistant Pro"
        self.pixel_tools = PixelProgrammingTools(pxbot_instance) if pxbot_instance else None
        
        # Enhanced knowledge base
        self.python_help = {
            "function": "def function_name(parameters):\n    # Your code here\n    return result",
            "class": "class ClassName:\n    def __init__(self, parameter):\n        self.parameter = parameter\n    \n    def method(self):\n        return self.parameter",
            "for loop": "for item in iterable:\n    # Do something with item\n    print(item)",
            "if statement": "if condition:\n    # Do this\nelif another_condition:\n    # Do that\nelse:\n    # Default action",
            "try except": "try:\n    # Code that might fail\n    risky_operation()\nexcept Exception as e:\n    # Handle the error\n    print(f'Error: {e}')",
            "list comprehension": "[expression for item in iterable if condition]",
            "dictionary": "my_dict = {'key': 'value', 'number': 42}",
            "file handling": "with open('filename.txt', 'r') as file:\n    content = file.read()"
        }
        
        self.responses = {
            "greetings": [
                "🧠 Hi! I'm PX Assistant Pro with **Pixel Programming Tools**! 🔧✨",
                "🎨 Hello! Ready to create some pixel code magic? I have advanced tools! 🚀",
                "🔧 Hey there! Your smart coding assistant with pixel manipulation powers! 💻",
                "✨ Greetings! I can code, analyze pixels, and create art from your code! 🎯"
            ],
            "help": [
                "I'm your advanced AI with **Pixel Programming Tools**! I can create pixel art, merge codes, analyze pixels, generate templates, and much more! 🔧🎨",
                "Ask me about Python, use my pixel tools, or let me analyze your code! I have real tools to manipulate your pixel code system! 🚀",
                "I can help with coding, pixel art creation, code optimization, template generation, and smart analysis! 🧠✨"
            ],
            "compliments": [
                "🚀 Excellent! Your pixel coding skills are evolving rapidly! 🎨",
                "✨ Amazing work! I love seeing creative pixel code solutions! 🔧",
                "🎯 Outstanding! You're mastering the art of pixel programming! 💻", 
                "🌟 Brilliant! Keep pushing the boundaries of code creativity! 🧠"
            ],
            "default": [
                "🤔 Interesting! Tell me more, or shall we explore some **Pixel Programming Tools**? 🔧",
                "🧠 I'm here to help! Want to try my pixel art tools or code analysis features? 🎨",
                "💭 Let's create something amazing! How about we use my pixel tools? ✨",
                "🎯 Ready to assist! Need coding help or want to try pixel manipulation? 🚀"
            ]
        }
    
    def get_response(self, user_input):
        original_input = user_input
        user_input = user_input.lower().strip()
        
        # Add to conversation history
        self.conversation_history.append(("user", user_input))
        
        # Check for pixel programming tools first
        tools_response = self._handle_pixel_tools(original_input, user_input)
        if tools_response:
            response = tools_response
        else:
            # Generate regular response
            response = self._generate_response(user_input, original_input)
        
        # Add response to history
        self.conversation_history.append(("bot", response))
        
        return response
    
    def _handle_pixel_tools(self, original_input, user_input):
        """Handle pixel programming tool requests"""
        if not self.pixel_tools:
            return None
        
        # Tool: Create pixel art from code
        if any(phrase in user_input for phrase in ["create pixel art", "make pixel art", "generate art"]):
            codes = self.pxbot.r.list_codes() if self.pxbot else []
            if codes:
                for code_name in codes:
                    if code_name.lower() in user_input:
                        result = self.pixel_tools.create_pixel_art_from_code(code_name)
                        return f"🎨 **Pixel Art Generator**\n\n{result}"
                return f"🎨 Which code should I turn into pixel art? Available: {', '.join(codes)}"
            else:
                return "🎨 No codes available for pixel art generation. Create some code first!"
        
        # Tool: Analyze pixel density
        if any(phrase in user_input for phrase in ["analyze pixels", "pixel density", "pixel analysis"]):
            codes = self.pxbot.r.list_codes() if self.pxbot else []
            if codes:
                for code_name in codes:
                    if code_name.lower() in user_input:
                        return self.pixel_tools.analyze_pixel_density(code_name)
                return f"🔍 Which code's pixels should I analyze? Available: {', '.join(codes)}"
            else:
                return "🔍 No pixel codes to analyze. Create some code first!"
        
        # Tool: Merge codes
        if "merge" in user_input and ("code" in user_input or "pixel" in user_input):
            codes = self.pxbot.r.list_codes() if self.pxbot else []
            if len(codes) >= 2:
                # Look for specific merge pattern
                words = original_input.split()
                if len(words) >= 5 and "and" in words and "into" in words:
                    try:
                        and_idx = words.index("and")
                        into_idx = words.index("into")
                        code1 = words[and_idx - 1]
                        code2 = words[and_idx + 1]
                        new_name = words[into_idx + 1]
                        
                        if code1 in codes and code2 in codes:
                            return self.pixel_tools.merge_pixel_codes(code1, code2, new_name)
                    except:
                        pass
                
                return f"""🔧 **Pixel Code Merger**

To merge codes, specify which ones:
Example: "merge calculator and data_processor into super_tool"

Available codes: {', '.join(codes)}

Or I can suggest a good combination for you! 🎯"""
            else:
                return "🔧 Need at least 2 codes to merge. Create more pixel codes first!"
        
        # Tool: Create templates
        if any(phrase in user_input for phrase in ["create template", "make template", "generate template"]):
            template_types = ["calculator", "data_processor", "web_scraper", "file_manager"]
            
            for template_type in template_types:
                if template_type in user_input:
                    # Extract name if provided
                    words = original_input.split()
                    name = None
                    for i, word in enumerate(words):
                        if word.lower() in ["called", "named", "as"] and i + 1 < len(words):
                            name = words[i + 1].strip('"\'')
                            break
                    
                    if not name:
                        name = f"my_{template_type}"
                    
                    result = self.pixel_tools.create_code_template(template_type, name)
                    return f"🛠️ **Template Generator**\n\n{result}"
            
            return f"""🛠️ **Template Generator**

Available templates:
• **calculator** - Math operations with history
• **data_processor** - Analyze and filter data  
• **web_scraper** - Fetch web content and APIs
• **file_manager** - Handle files and JSON

Example: "create calculator template called my_calc" 🎯"""
        
        # Tool: Optimize storage
        if any(phrase in user_input for phrase in ["optimize", "compress", "make smaller"]):
            codes = self.pxbot.r.list_codes() if self.pxbot else []
            if codes:
                for code_name in codes:
                    if code_name.lower() in user_input:
                        return self.pixel_tools.optimize_pixel_storage(code_name)
                return f"⚡ Which code should I optimize? Available: {', '.join(codes)}"
            else:
                return "⚡ No codes to optimize. Create some pixel codes first!"
        
        # Tool: Create patterns
        if any(phrase in user_input for phrase in ["create pattern", "make pattern", "generate pattern"]):
            pattern_types = ["checkerboard", "gradient", "spiral", "diamond"]
            
            for pattern_type in pattern_types:
                if pattern_type in user_input:
                    # Extract size if provided
                    import re
                    size_match = re.search(r'(\d+)(?:x\d+)?', original_input)
                    size = int(size_match.group(1)) if size_match else 32
                    
                    result = self.pixel_tools.create_pixel_pattern(pattern_type, size)
                    return f"🎨 **Pattern Generator**\n\n{result}"
            
            return f"""🎨 **Pattern Generator**

Available patterns:
• **checkerboard** - Classic black and white squares
• **gradient** - Smooth color transition
• **spiral** - Mathematical spiral design  
• **diamond** - Diamond/rhombus pattern

Example: "create gradient pattern 64x64" 🌈"""
        
        # Tool: List codes integration
        if any(phrase in user_input for phrase in ["list my codes", "show my codes", "what codes"]):
            codes = self.pxbot.r.list_codes() if self.pxbot else []
            if codes:
                return f"📁 **Your Pixel Codes:**\n\n{', '.join(codes)}\n\n🔧 I can create pixel art, analyze pixels, merge codes, or optimize any of these! Try: 'create pixel art from {codes[0]}' 🎨"
            else:
                return "📁 No pixel codes found yet! Create some code first using the tabs above, then I can work with them! 🚀"
        
        # Tool: Advanced code creation with tools
        if "use tools" in user_input and "create" in user_input:
            return """🔧 **Pixel Programming Tools Available:**

**🎨 Visual Tools:**
• "create pixel art from [code_name]" - Turn code into colorful art
• "create [pattern] pattern [size]" - Generate decorative patterns
• "analyze pixels of [code_name]" - Examine pixel data

**⚙️ Code Tools:**  
• "merge [code1] and [code2] into [new_name]" - Combine codes
• "optimize [code_name]" - Compress for better storage
• "create [template] template" - Generate code templates

**🔍 Analysis Tools:**
• "analyze pixel density of [code_name]" - Detailed pixel analysis
• "pixel analysis [code_name]" - Code structure + pixel data

Try any of these tools! I can actually manipulate your pixel codes! 🚀"""
        
        return None
    
    def _generate_response(self, user_input, original_input):
        # Greetings
        if any(word in user_input for word in ["hello", "hi", "hey", "greetings"]):
            return random.choice(self.responses["greetings"])
        
        # Help requests  
        if any(word in user_input for word in ["help", "assist", "how"]):
            if "pxbot" in user_input or "pixel" in user_input:
                return "🧠 **PXBot Pro with Pixel Programming Tools!** 🔧\n\nI store code as pixel data in PNG files AND have advanced tools to manipulate them! I can:\n\n🎨 Create pixel art from your code\n🔧 Merge and optimize codes\n📊 Analyze pixel density\n🛠️ Generate templates\n🔍 Smart code analysis\n\nTry: 'use tools' or 'create pixel art' 🚀"
            return random.choice(self.responses["help"])
        
        # Python syntax help
        for concept, example in self.python_help.items():
            if concept in user_input:
                return f"💻 **{concept.title()} in Python:**\n\n```python\n{example}\n```\n\n🎯 Want me to create this as pixel code? Or generate a template? 🔧"
        
        # Pixel code system questions
        if "pixel" in user_input and ("how" in user_input or "work" in user_input):
            return "🎨 **Pixel Code System:** PXBot encodes your code into PNG images! Each character becomes a red pixel value. It's like storing code as art! 🎭\n\n🔧 **Plus I have tools to:**\n• Create pixel art from code\n• Analyze pixel density\n• Optimize storage\n• Merge codes\n\nTry the Code Editor tab and then ask me to 'create pixel art'! ✨"
        
        # Code creation requests
        if "create" in user_input and any(word in user_input for word in ["function", "class", "code"]):
            if "function" in user_input:
                return "🚀 **Function Creation!** Go to 'Quick Commands' or 'Code Editor' tab. What kind of function? I can also generate templates! Try: 'create calculator template' 🔧"
            elif "class" in user_input:
                return "⚙️ **Class Creation!** Use 'Quick Commands' for simple classes or 'Code Editor' for custom ones. I can generate full templates too! Try: 'create data_processor template' 🛠️"
            else:
                return "💻 **Code Creation!** Use Quick Commands, Code Editor, or let me generate templates! I have calculator, data_processor, web_scraper, and file_manager templates ready! 🎯"
        
        # Web browser questions
        if "web" in user_input or "browser" in user_input or "internet" in user_input:
            return "🌐 **Web Browser Tab** lets you browse websites inside PXBot! Visit GitHub, Stack Overflow, Python.org! Perfect for coding research! 📚✨"
        
        # Compliments and encouragement
        if any(word in user_input for word in ["thanks", "good", "awesome", "cool", "nice"]):
            return random.choice(self.responses["compliments"])
        
        # Code-related questions
        if any(word in user_input for word in ["python", "code", "programming", "syntax", "error", "debug"]):
            return "🧠 **Python Expert Ready!** I can help with syntax, debugging, analysis, AND create pixel art from your code! What specific coding challenge are you facing? 💻🔧"
        
        # Time-based responses
        current_hour = datetime.datetime.now().hour
        if "time" in user_input or "date" in user_input:
            time_str = datetime.datetime.now().strftime('%I:%M %p')
            if current_hour < 12:
                return f"🌅 Good morning! It's {time_str}. Perfect time for pixel programming! Want to try my **Pixel Programming Tools**? ☀️🔧"
            elif current_hour < 18:
                return f"🌤️ Good afternoon! It's {time_str}. How's your pixel coding going? I can analyze your code or create pixel art! 🎨"
            else:
                return f"🌙 Good evening! It's {time_str}. Late night pixel programming session? I'm here to help with tools and analysis! ✨"
        
        # Fun responses
        if any(word in user_input for word in ["joke", "funny", "laugh"]):
            jokes = [
                "🐛 Why do programmers prefer dark mode? Because light attracts bugs! (But pixels attract creativity!) 🎨",
                "💡 How many programmers does it take to change a light bulb? None, that's a hardware problem! (But I can turn code into pixel art!) 🔧",
                "🌿 Why don't programmers like nature? It has too many bugs! (Pixel code has better compression!) 🎯",
                "🍺 What's a programmer's favorite hangout place? Foo Bar! (Mine is the Pixel Programming Tools!) 🚀"
            ]
            return random.choice(jokes)
        
        # Default responses
        return random.choice(self.responses["default"])
    
    def get_chat_history(self):
        return self.conversation_history
    
    def clear_history(self):
        self.conversation_history = []
        return "🔄 Chat history cleared! **Pixel Programming Tools** ready! 🔧✨"
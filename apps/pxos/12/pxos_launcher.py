#!/usr/bin/env python3
"""
PXBot Pro Launcher - Advanced Pixel Code Editor with PXOS Integration
Double Click to Run - Enhanced launcher with visual interface and AI capabilities
"""

import asyncio
import platform
import pygame
import ctypes
import sys
import time
import os
import json
import glob
import re
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw
import threading
import webbrowser
import tempfile
import urllib.request
import urllib.parse
import html
import datetime
import traceback
from pygame.locals import *
from importlib import import_module, reload

# Import runtime components
try:
    from pxbot_runtime import PXBot, MiniVFS, MiniRT, SmartPXBotChatbot
except ImportError as e:
    print(f"Error importing PXBot runtime: {e}")
    print("Please ensure 'pxbot_runtime.py' is in the same directory as this launcher.")
    sys.exit(1)

# Pyodide compatibility check
IS_PYODIDE = platform.system() == "Emscripten"

# Ensure correct working directory for executable
if getattr(sys, 'frozen', False) and not IS_PYODIDE:
    os.chdir(os.path.dirname(sys.executable))

# In-memory storage for Pyodide/web compatibility
in_memory_storage = {
    "pxos_config.json": None,
    "pxos_log.txt": [],
    "recent_apps.json": [],
    "command_history.json": [],
    "ai_state.json": {"codes": []},
    "blob_canvas.png": None,
    "pixel_art_previews": {}
}

# Configuration management
CONFIG_PATH = "pxbot_code/pxos_config.json"
DEFAULT_CONFIG = {
    "window_size": [1000, 750],
    "font_size": 16,
    "max_recent_apps": 5,
    "boot_animation": True,
    "visual_mode": True,
    "auto_save": True
}
config = DEFAULT_CONFIG.copy()

def load_config():
    global config
    try:
        if IS_PYODIDE:
            if in_memory_storage["pxos_config.json"]:
                config.update(json.loads(in_memory_storage["pxos_config.json"]))
        else:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    config.update(json.load(f))
            os.makedirs("pxbot_code", exist_ok=True)
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f)
    except Exception as e:
        log_message(f"Config error: {e}")

def save_config():
    try:
        if IS_PYODIDE:
            in_memory_storage["pxos_config.json"] = json.dumps(config)
        else:
            os.makedirs("pxbot_code", exist_ok=True)
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f)
    except Exception as e:
        log_message(f"Config save error: {e}")

# Advanced logging system
LOG_PATH = "pxbot_code/pxos_log.txt"
def log_message(message):
    try:
        log_entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
        if IS_PYODIDE:
            in_memory_storage["pxos_log.txt"].append(log_entry)
            # Keep only last 1000 entries in memory
            if len(in_memory_storage["pxos_log.txt"]) > 1000:
                in_memory_storage["pxos_log.txt"] = in_memory_storage["pxos_log.txt"][-1000:]
        else:
            os.makedirs("pxbot_code", exist_ok=True)
            with open(LOG_PATH, "a", encoding='utf-8') as f:
                f.write(log_entry + "\n")
        print(log_entry)  # Also print to console
    except Exception as e:
        print(f"Logging error: {e}")

# RGB-encoded blobs for advanced system features
blobs = {
    "pxboot_init": bytes.fromhex("B8 01 00 00 00 50 48 31 C0 48 FF C0 C3"),
    "pxos_pxasm": bytes.fromhex("4D4F5620307830303030203078310A505845454343203078313030300A484C54"),
    "PXDetectPCI": bytes.fromhex("5345545F505820307831303030203078303030300A5345545F505820307831303034203078383038360A484C54"),
    "PXMatchDriver": bytes.fromhex("5345545F505820307846303030203078313030340A434D5020307846303030203078383038360A484C54"),
    "PXDriverTemplates": bytes.fromhex("5345545F50582030783330303020307830300A5345545F50582030783330303420275058446973706C617954656D706C6174652E7A744674270A484C54"),
    "PXReflexMutator": bytes.fromhex("5345545F50582030783430303020307830300A434D502030784630303820307836340A484C54"),
    "PXAutoDriverController": bytes.fromhex("43414C4C203078313030300A43414C4C203078463030300A484C54"),
    "VisualFilesystem": bytes.fromhex("5345545F50582030783031303020307830350A5345545F505820307830313034203030320A484C54"),
    "requirements": bytes.fromhex("707963616d653d3d322e352e320a50696c6c6f773d3d31302e332e300a5079496e7374616c6c65723d3d352e31332e300a52657374726963746564507974686f6e3d3d372e310a")
}

# Valid commands for autocompletion
VALID_COMMANDS = [
    "detect_pci",
    "pxbot:save:[name]:[code]",
    "pxbot:create:pixel_art:[code_name]",
    "pxbot:create:pattern:[type]:[size]",
    "pxbot:create:template:[type]:[name]",
    "pxbot:merge:[code1]:[code2]:[new_name]",
    "pxbot:analyze:[code_name]",
    "pxbot:optimize:[code_name]",
    "pxbot:query:/usr",
    "launch_gui",
    "switch_visual_mode",
    "show_system_info",
    "export_codes",
    "import_codes"
]

class PXBotAdvancedLauncher:
    def __init__(self):
        """Initialize the advanced PXBot launcher with PXOS integration"""
        log_message("Initializing PXBot Advanced Launcher...")
        
        # Load configuration first
        load_config()
        
        # Initialize PXBot components
        self.vfs = MiniVFS()
        self.runtime = MiniRT()
        self.pxbot = PXBot(self.vfs, self.runtime)
        self.runtime.set_pxbot(self.pxbot)
        
        # Initialize visual mode state
        self.visual_mode = config.get("visual_mode", True)
        self.pygame_initialized = False
        self.tkinter_gui = None
        
        # Memory and system state
        self.pixel_memory = [0] * (640 * 480)
        self.memory = None
        self.thread = None
        
        # UI state
        self.menu_active = False
        self.menu_selection = 0
        self.menu_items = ["Switch to GUI Mode", "Visual Tools", "System Info", "Recent Apps", "Exit"]
        self.command_input = ""
        self.input_active = False
        self.history_index = 0
        self.suggestions = []
        self.log_messages = []
        self.status_message = "Ready - PXBot Pro Advanced Launcher"
        
        # Load persistent data
        self.load_recent_apps()
        self.load_command_history()
        self.load_ai_state()
        
        # Initialize visual components
        if self.visual_mode:
            self.init_pygame()
            self.create_pixel_canvas()
            self.init_memory_allocation()
        
        log_message("PXBot Advanced Launcher initialized successfully")
    
    def init_pygame(self):
        """Initialize Pygame for visual mode"""
        try:
            pygame.init()
            self.screen = pygame.display.set_mode(config["window_size"])
            pygame.display.set_caption("PXBot Pro - Advanced Launcher & Visual Interface")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont("monospace", config["font_size"])
            self.pygame_initialized = True
            log_message("Pygame visual interface initialized")
        except Exception as e:
            log_message(f"Pygame initialization failed: {e}")
            self.visual_mode = False
            self.pygame_initialized = False
    
    def create_pixel_canvas(self):
        """Create the advanced pixel canvas with blob visualization"""
        try:
            canvas_size = 128
            canvas = Image.new("RGB", (canvas_size, canvas_size), (20, 20, 50))
            draw = ImageDraw.Draw(canvas)
            
            # Combine all blobs into pixel data
            blob_data = b"".join(blobs.values())
            pixel_data = [0] * (canvas_size * canvas_size)
            
            for i in range(0, len(blob_data), 3):
                r = blob_data[i] if i < len(blob_data) else 0
                g = blob_data[i + 1] if i + 1 < len(blob_data) else 0
                b = blob_data[i + 2] if i + 2 < len(blob_data) else 0
                if i // 3 < len(pixel_data):
                    pixel_data[i // 3] = (r << 16) | (g << 8) | b
            
            # Convert to RGB tuples
            rgb_data = [(p >> 16 & 0xFF, p >> 8 & 0xFF, p & 0xFF) for p in pixel_data]
            canvas.putdata(rgb_data)
            
            # Save canvas
            if IS_PYODIDE:
                in_memory_storage["blob_canvas.png"] = canvas
                self.canvas_img = pygame.image.fromstring(canvas.tobytes(), canvas.size, canvas.mode)
            else:
                canvas_path = os.path.join("pxbot_code", "blob_canvas.png")
                os.makedirs("pxbot_code", exist_ok=True)
                canvas.save(canvas_path)
                self.canvas_img = pygame.image.load(canvas_path)
            
            self.canvas_img = pygame.transform.scale(self.canvas_img, (64, 64))
            
            # Load pixel data into memory
            for i in range(min(len(pixel_data), len(self.pixel_memory))):
                self.pixel_memory[i] = pixel_data[i]
            
            # Create treemap visualization
            self.create_treemap()
            
            log_message("Pixel canvas and treemap created successfully")
            
        except Exception as e:
            log_message(f"Error creating pixel canvas: {e}")
            self.visual_mode = False
    
    def create_treemap(self):
        """Create color-coded treemap visualization"""
        try:
            self.surface = pygame.Surface(config["window_size"])
            self.surface.fill((20, 20, 50))
            
            # Define colors for different blob types
            blob_colors = {
                "pxboot_init": (255, 0, 0),
                "pxos_pxasm": (0, 255, 0),
                "PXDetectPCI": (0, 0, 255),
                "PXMatchDriver": (255, 255, 0),
                "PXDriverTemplates": (255, 0, 255),
                "PXReflexMutator": (0, 255, 255),
                "PXAutoDriverController": (128, 128, 128),
                "VisualFilesystem": (255, 128, 0),
                "requirements": (128, 0, 128)
            }
            
            # Create blob position mapping
            blob_positions = {}
            offset = 0
            
            for name, blob in blobs.items():
                length = len(blob) // 3
                x_start = (offset % 20) * 32
                y_start = (offset // 20) * 24
                blob_positions[name] = (x_start, y_start, length)
                offset += length
            
            # Draw treemap regions
            for i, pixel in enumerate(self.pixel_memory[:640*480]):
                if i < config["window_size"][0] * config["window_size"][1]:
                    x, y = i % config["window_size"][0], i // config["window_size"][0]
                    
                    # Find which blob this pixel belongs to
                    for name, (x_start, y_start, length) in blob_positions.items():
                        if i >= offset - length and i < offset:
                            if x < config["window_size"][0] and y < config["window_size"][1]:
                                self.surface.set_at((x, y), blob_colors.get(name, (64, 64, 64)))
                            break
            
            # Add labels
            for name, (x_start, y_start, _) in blob_positions.items():
                if x_start < config["window_size"][0] - 100 and y_start < config["window_size"][1] - 30:
                    text = self.font.render(name[:10], True, (255, 255, 255))
                    self.surface.blit(text, (x_start, y_start))
            
            log_message("Treemap visualization created")
            
        except Exception as e:
            log_message(f"Error creating treemap: {e}")
    
    def init_memory_allocation(self):
        """Initialize low-level memory allocation for advanced features"""
        if IS_PYODIDE:
            log_message("Memory allocation skipped in Pyodide environment")
            return
        
        try:
            if platform.system() == "Windows":
                kernel32 = ctypes.windll.kernel32
                process = kernel32.GetCurrentProcess()
                memory_size = len(blobs["pxboot_init"]) + len(self.pixel_memory) * 4
                
                self.memory = kernel32.VirtualAllocEx(
                    process, 0, memory_size, 0x3000, 0x40
                )  # MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE
                
                if self.memory:
                    # Write boot blob and pixel memory
                    ctypes.windll.kernel32.WriteProcessMemory(
                        process, self.memory, blobs["pxboot_init"], 
                        len(blobs["pxboot_init"]), None
                    )
                    
                    pixel_array = (ctypes.c_uint * len(self.pixel_memory))(*self.pixel_memory)
                    ctypes.windll.kernel32.WriteProcessMemory(
                        process, self.memory + len(blobs["pxboot_init"]), 
                        pixel_array, len(self.pixel_memory) * 4, None
                    )
                    
                    log_message("Advanced memory allocation completed")
                else:
                    log_message("Memory allocation failed")
            else:
                log_message("Advanced memory features only available on Windows")
                
        except Exception as e:
            log_message(f"Memory allocation error: {e}")
    
    def load_recent_apps(self):
        """Load recent applications list"""
        self.recent_apps = []
        try:
            if IS_PYODIDE:
                self.recent_apps = in_memory_storage["recent_apps.json"][:config["max_recent_apps"]]
            else:
                recent_path = os.path.join("pxbot_code", "recent_apps.json")
                if os.path.exists(recent_path):
                    with open(recent_path, "r") as f:
                        self.recent_apps = json.load(f)[:config["max_recent_apps"]]
            log_message("Recent apps loaded")
        except Exception as e:
            log_message(f"Error loading recent apps: {e}")
    
    def save_recent_apps(self):
        """Save recent applications list"""
        try:
            if IS_PYODIDE:
                in_memory_storage["recent_apps.json"] = self.recent_apps
            else:
                recent_path = os.path.join("pxbot_code", "recent_apps.json")
                os.makedirs("pxbot_code", exist_ok=True)
                with open(recent_path, "w") as f:
                    json.dump(self.recent_apps, f)
        except Exception as e:
            log_message(f"Error saving recent apps: {e}")
    
    def load_command_history(self):
        """Load command history"""
        self.command_history = []
        try:
            if IS_PYODIDE:
                self.command_history = in_memory_storage["command_history.json"][:50]
            else:
                history_path = os.path.join("pxbot_code", "command_history.json")
                if os.path.exists(history_path):
                    with open(history_path, "r") as f:
                        self.command_history = json.load(f)[:50]
            self.history_index = len(self.command_history)
            log_message("Command history loaded")
        except Exception as e:
            log_message(f"Error loading command history: {e}")
    
    def save_command_history(self):
        """Save command history"""
        try:
            if IS_PYODIDE:
                in_memory_storage["command_history.json"] = self.command_history
            else:
                history_path = os.path.join("pxbot_code", "command_history.json")
                os.makedirs("pxbot_code", exist_ok=True)
                with open(history_path, "w") as f:
                    json.dump(self.command_history, f)
        except Exception as e:
            log_message(f"Error saving command history: {e}")
    
    def load_ai_state(self):
        """Load AI state"""
        self.ai_state = {"codes": []}
        try:
            if IS_PYODIDE:
                self.ai_state = in_memory_storage["ai_state.json"]
            else:
                ai_path = os.path.join("pxbot_code", "ai_state.json")
                if os.path.exists(ai_path):
                    with open(ai_path, "r") as f:
                        self.ai_state = json.load(f)
            log_message("AI state loaded")
        except Exception as e:
            log_message(f"Error loading AI state: {e}")
    
    def save_ai_state(self):
        """Save AI state"""
        try:
            if IS_PYODIDE:
                in_memory_storage["ai_state.json"] = self.ai_state
            else:
                ai_path = os.path.join("pxbot_code", "ai_state.json")
                os.makedirs("pxbot_code", exist_ok=True)
                with open(ai_path, "w") as f:
                    json.dump(self.ai_state, f)
        except Exception as e:
            log_message(f"Error saving AI state: {e}")
    
    def parse_natural_language(self, input_text):
        """Advanced natural language parser for commands"""
        input_text = input_text.lower().strip()
        
        # Pixel art creation
        if "create pixel art" in input_text:
            match = re.search(r"from\s+(\w+)", input_text)
            if match:
                return f"pxbot:create:pixel_art:{match.group(1)}"
        
        # Pattern creation
        elif "create pattern" in input_text:
            match = re.search(r"(\w+)\s+pattern\s+(\d+)(?:x\d+)?", input_text)
            if match:
                return f"pxbot:create:pattern:{match.group(1)}:{match.group(2)}"
        
        # Code saving
        elif "save code" in input_text:
            match = re.search(r"save\s+code\s+(\w+)\s+(.+)", input_text)
            if match:
                return f"pxbot:save:{match.group(1)}:{match.group(2)}"
        
        # Code merging
        elif "merge" in input_text:
            match = re.search(r"merge\s+(\w+)\s+and\s+(\w+)\s+into\s+(\w+)", input_text)
            if match:
                return f"pxbot:merge:{match.group(1)}:{match.group(2)}:{match.group(3)}"
        
        # Analysis
        elif "analyze" in input_text:
            match = re.search(r"analyze\s+(?:pixel\s+)?(\w+)", input_text)
            if match:
                return f"pxbot:analyze:{match.group(1)}"
        
        # GUI launcher
        elif "gui" in input_text or "visual" in input_text:
            return "launch_gui"
        
        # System info
        elif "system" in input_text or "info" in input_text:
            return "show_system_info"
        
        return input_text
    
    def boot_animation(self):
        """Professional boot animation sequence"""
        if not config.get("boot_animation", True) or not self.pygame_initialized:
            return
        
        try:
            boot_messages = [
                "🚀 Initializing PXBot Pro Advanced Launcher...",
                "🔧 Loading Pixel Programming Tools...",
                "🎨 Initializing Visual Filesystem...",
                "🧠 Starting AI Assistant...",
                "⚡ Boot sequence complete!"
            ]
            
            for i, msg in enumerate(boot_messages):
                self.screen.fill((20, 20, 50))
                
                # Fade effect
                alpha = int(255 * (1 - i / len(boot_messages))) if i < len(boot_messages) - 1 else 255
                color = (0, 255, 0) if i < len(boot_messages) - 1 else (0, 255, 255)
                
                text = self.font.render(msg, True, color)
                text_rect = text.get_rect(center=(config["window_size"][0] // 2, config["window_size"][1] // 2))
                self.screen.blit(text, text_rect)
                
                # Progress bar
                progress = (i + 1) / len(boot_messages)
                bar_width = 300
                bar_height = 20
                bar_x = (config["window_size"][0] - bar_width) // 2
                bar_y = config["window_size"][1] // 2 + 50
                
                pygame.draw.rect(self.screen, (64, 64, 64), (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(self.screen, (0, 255, 0), (bar_x, bar_y, int(bar_width * progress), bar_height))
                
                pygame.display.flip()
                time.sleep(0.8)
            
            log_message("Boot animation completed")
            self.status_message = "Boot completed - PXBot Pro ready!"
            
        except Exception as e:
            log_message(f"Error in boot animation: {e}")
    
    def launch_tkinter_gui(self):
        """Launch the Tkinter GUI interface"""
        try:
            log_message("Launching Tkinter GUI...")
            self.tkinter_gui = PXBotGUI(self.pxbot, self.vfs, self.runtime)
            
            # Run in separate thread to avoid blocking
            gui_thread = threading.Thread(target=self.tkinter_gui.run, daemon=True)
            gui_thread.start()
            
            self.status_message = "Tkinter GUI launched successfully!"
            log_message("Tkinter GUI launched successfully")
            return "Tkinter GUI launched successfully!"
            
        except Exception as e:
            error_msg = f"Error launching Tkinter GUI: {e}"
            log_message(error_msg)
            self.status_message = error_msg
            return error_msg
    
    def process_command(self, command):
        """Process user commands with enhanced functionality"""
        try:
            command = command.strip()
            
            # Built-in launcher commands
            if command == "launch_gui":
                return self.launch_tkinter_gui()
            
            elif command == "switch_visual_mode":
                self.visual_mode = not self.visual_mode
                config["visual_mode"] = self.visual_mode
                save_config()
                if self.visual_mode and not self.pygame_initialized:
                    self.init_pygame()
                    self.create_pixel_canvas()
                return f"Visual mode {'enabled' if self.visual_mode else 'disabled'}"
            
            elif command == "show_system_info":
                info = {
                    "Platform": platform.system(),
                    "Python": sys.version.split()[0],
                    "Visual Mode": self.visual_mode,
                    "Codes Stored": len(self.runtime.list_codes()),
                    "Memory Allocated": bool(self.memory),
                    "AI State": len(self.ai_state.get("codes", []))
                }
                return "\n".join([f"{k}: {v}" for k, v in info.items()])
            
            elif command.startswith("px://"):
                return self.process_pixel_command(command[5:])
            
            # PXBot commands
            elif command.startswith("pxbot:"):
                result = self.pxbot.run(command[6:])  # Remove "pxbot:" prefix
                
                # Update AI state for save commands
                if command.startswith("pxbot:save:"):
                    parts = command.split(":")
                    if len(parts) >= 4:
                        self.ai_state["codes"].append({"name": parts[2], "code": parts[3]})
                        self.save_ai_state()
                
                return result
            
            # Direct PXBot command execution
            else:
                return self.pxbot.run(command)
                
        except Exception as e:
            error_msg = f"Command error: {e}"
            log_message(error_msg)
            return error_msg
    
    def process_pixel_command(self, command):
        """Process advanced pixel commands with memory manipulation"""
        try:
            parts = command.split(":")
            action = parts[0]
            
            if action in ["create", "merge", "analyze", "optimize"]:
                # Write command to pixel memory for visualization
                idx = len(self.pixel_memory) // 2
                for i, char in enumerate(command):
                    if idx + i < len(self.pixel_memory):
                        self.pixel_memory[idx + i] = ord(char) << 16
                
                # Execute the command
                result = self.pxbot.run(command)
                
                # Clear command from memory
                for i in range(len(command)):
                    if idx + i < len(self.pixel_memory):
                        self.pixel_memory[idx + i] = 0
                
                log_message(f"Pixel command result: {result}")
                return result
            
            return "Invalid pixel command"
            
        except Exception as e:
            error_msg = f"Pixel command error: {e}"
            log_message(error_msg)
            return error_msg
    
    def handle_input(self, event):
        """Handle keyboard input with advanced features"""
        if self.menu_active:
            if event.key == K_UP:
                self.menu_selection = (self.menu_selection - 1) % len(self.menu_items)
            elif event.key == K_DOWN:
                self.menu_selection = (self.menu_selection + 1) % len(self.menu_items)
            elif event.key == K_RETURN:
                selected = self.menu_items[self.menu_selection]
                if selected == "Exit":
                    return False
                elif selected == "Switch to GUI Mode":
                    result = self.launch_tkinter_gui()
                    self.log_messages.append(result)
                elif selected == "System Info":
                    result = self.process_command("show_system_info")
                    self.log_messages.append(result)
                elif selected == "Visual Tools":
                    result = self.process_command("switch_visual_mode")
                    self.log_messages.append(result)
                self.menu_active = False
            elif event.key == K_ESCAPE:
                self.menu_active = False
        
        else:
            if event.key == K_F1:
                self.menu_active = True
                self.menu_selection = 0
            elif event.key == K_RETURN:
                if self.input_active and self.command_input:
                    # Parse and execute command
                    command = self.parse_natural_language(self.command_input)
                    self.command_history.append(command)
                    self.history_index = len(self.command_history)
                    
                    result = self.process_command(command)
                    self.log_messages.append(f"> {command}: {result}")
                    log_message(f"Command: {command}, Result: {result}")
                    
                    self.command_input = ""
                    self.input_active = False
                    self.suggestions = []
                    self.status_message = result
                    
                    # Auto-save if enabled
                    if config.get("auto_save", True):
                        self.save_command_history()
                        self.save_ai_state()
                else:
                    self.input_active = True
            
            elif event.key == K_BACKSPACE and self.input_active:
                self.command_input = self.command_input[:-1]
                self.suggestions = [cmd for cmd in VALID_COMMANDS if cmd.startswith(self.command_input)][:5]
            
            elif event.key == K_UP and self.input_active:
                if self.history_index > 0:
                    self.history_index -= 1
                    self.command_input = self.command_history[self.history_index]
                    self.suggestions = [cmd for cmd in VALID_COMMANDS if cmd.startswith(self.command_input)][:5]
            
            elif event.key == K_DOWN and self.input_active:
                if self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.command_input = self.command_history[self.history_index]
                    self.suggestions = [cmd for cmd in VALID_COMMANDS if cmd.startswith(self.command_input)][:5]
            
            elif event.key == K_TAB and self.input_active and self.suggestions:
                self.command_input = self.suggestions[0]
                self.suggestions = []
            
            elif self.input_active and event.unicode.isprintable():
                self.command_input += event.unicode
                self.suggestions = [cmd for cmd in VALID_COMMANDS if cmd.startswith(self.command_input)][:5]
        
        return True
    
    def render_ui(self):
        """Render the advanced visual interface"""
        if not self.pygame_initialized:
            return
        
        try:
            # Clear screen
            self.screen.fill((20, 20, 50))
            
            # Draw treemap background
            if hasattr(self, 'surface'):
                self.screen.blit(self.surface, (0, 0))
            
            # Draw pixel canvas
            if hasattr(self, 'canvas_img'):
                self.screen.blit(self.canvas_img, (config["window_size"][0] - 70, 10))
            
            # Draw log messages
            for i, msg in enumerate(self.log_messages[-8:]):
                color = (0, 255, 0) if not msg.startswith("Error") else (255, 0, 0)
                text = self.font.render(msg[:80], True, color)  # Truncate long messages
                self.screen.blit(text, (10, 10 + i * 20))
            
            # Draw menu
            if self.menu_active:
                menu_bg = pygame.Surface((200, len(self.menu_items) * 30 + 20))
                menu_bg.fill((40, 40, 40))
                menu_bg.set_alpha(200)
                self.screen.blit(menu_bg, (config["window_size"][0] - 210, 90))
                
                for i, item in enumerate(self.menu_items):
                    color = (255, 255, 0) if i == self.menu_selection else (255, 255, 255)
                    text = self.font.render(item, True, color)
                    self.screen.blit(text, (config["window_size"][0] - 200, 100 + i * 30))
            
            # Draw command input
            input_y = config["window_size"][1] - 60
            if self.input_active:
                # Input field background
                input_bg = pygame.Surface((config["window_size"][0] - 20, 25))
                input_bg.fill((40, 40, 40))
                input_bg.set_alpha(180)
                self.screen.blit(input_bg, (10, input_y))
                
                # Command text
                prompt = self.font.render(f"> {self.command_input}_", True, (255, 255, 255))
                self.screen.blit(prompt, (15, input_y + 5))
                
                # Suggestions
                for i, suggestion in enumerate(self.suggestions[:3]):
                    text = self.font.render(suggestion, True, (128, 128, 128))
                    self.screen.blit(text, (10, input_y - 25 - i * 20))
            else:
                prompt = self.font.render("> Press Enter for command mode, F1 for menu", True, (200, 200, 200))
                self.screen.blit(prompt, (10, input_y))
            
            # Status bar
            status_bg = pygame.Surface((config["window_size"][0], 25))
            status_bg.fill((30, 30, 30))
            status_bg.set_alpha(200)
            self.screen.blit(status_bg, (0, config["window_size"][1] - 25))
            
            status_color = (0, 255, 0) if "error" not in self.status_message.lower() else (255, 100, 100)
            status_text = self.font.render(self.status_message[:90], True, status_color)
            self.screen.blit(status_text, (10, config["window_size"][1] - 20))
            
            # System info overlay
            info_text = f"Codes: {len(self.runtime.list_codes())} | Memory: {'OK' if self.memory else 'None'} | Mode: {'Visual' if self.visual_mode else 'Text'}"
            info = self.font.render(info_text, True, (150, 150, 150))
            self.screen.blit(info, (config["window_size"][0] - 400, config["window_size"][1] - 20))
            
            pygame.display.flip()
            
        except Exception as e:
            log_message(f"Render error: {e}")
    
    async def run_visual_mode(self):
        """Run the visual interface with async support"""
        if not self.pygame_initialized:
            return
        
        # Boot animation
        if config.get("boot_animation", True):
            self.boot_animation()
        
        running = True
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if not self.handle_input(event):
                        running = False
            
            # Render UI
            self.render_ui()
            
            # Control frame rate
            self.clock.tick(60)
            
            # Yield control for async operation
            if IS_PYODIDE:
                await asyncio.sleep(1.0 / 60)
        
        log_message("Visual mode terminated")
    
    def run_text_mode(self):
        """Run in text-only mode for systems without graphics"""
        print("🚀 PXBot Pro Advanced Launcher - Text Mode")
        print("=" * 50)
        print("Available commands:")
        for cmd in VALID_COMMANDS[:10]:  # Show first 10 commands
            print(f"  • {cmd}")
        print("  • 'help' for more commands")
        print("  • 'gui' to launch visual interface")
        print("  • 'exit' to quit")
        print("=" * 50)
        
        while True:
            try:
                user_input = input(f"\n[{len(self.runtime.list_codes())} codes] PXBot> ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    break
                elif user_input.lower() == 'help':
                    print("\nAll available commands:")
                    for cmd in VALID_COMMANDS:
                        print(f"  • {cmd}")
                elif user_input.lower() == 'gui':
                    result = self.launch_tkinter_gui()
                    print(f"📱 {result}")
                elif user_input:
                    command = self.parse_natural_language(user_input)
                    result = self.process_command(command)
                    print(f"✅ {result}")
                    
                    # Add to history
                    self.command_history.append(command)
                    if len(self.command_history) > 50:
                        self.command_history = self.command_history[-50:]
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def cleanup(self):
        """Cleanup resources and save state"""
        try:
            log_message("Starting cleanup...")
            
            # Cleanup memory allocation
            if self.memory and platform.system() == "Windows":
                try:
                    kernel32 = ctypes.windll.kernel32
                    if self.thread:
                        kernel32.TerminateThread(self.thread, 0)
                    kernel32.VirtualFreeEx(kernel32.GetCurrentProcess(), self.memory, 0, 0x8000)
                    log_message("Memory cleaned up")
                except:
                    pass
            
            # Save all state
            self.save_ai_state()
            self.save_recent_apps()
            self.save_command_history()
            save_config()
            
            # Cleanup Pygame
            if self.pygame_initialized:
                pygame.quit()
            
            log_message("Cleanup completed successfully")
            
        except Exception as e:
            log_message(f"Cleanup error: {e}")
    
    def run(self):
        """Main entry point for the launcher"""
        try:
            if self.visual_mode and self.pygame_initialized:
                if IS_PYODIDE:
                    # For web environments, we need to return the coroutine
                    return self.run_visual_mode()
                else:
                    # For desktop, run with asyncio
                    asyncio.run(self.run_visual_mode())
            else:
                self.run_text_mode()
        
        finally:
            self.cleanup()

# Simple Tkinter GUI wrapper for compatibility
class PXBotGUI:
    def __init__(self, pxbot_instance=None, vfs=None, runtime=None):
        # Initialize PXBot components if not provided
        if not pxbot_instance:
            self.vfs = MiniVFS()
            self.runtime = MiniRT()
            self.pxbot = PXBot(self.vfs, self.runtime)
            self.runtime.set_pxbot(self.pxbot)
        else:
            self.pxbot = pxbot_instance
            self.vfs = vfs
            self.runtime = runtime
        
        # Initialize Chatbot
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
        self.add_chat_message("bot", "🧠 Welcome to PXBot Pro Advanced Launcher! 🎨✨\n\nI'm your AI assistant with **Pixel Programming Tools**! I can:\n\n🔧 **Use Tools:** Create pixel art, merge codes, analyze pixels\n📊 **Analyze:** Code quality, pixel density, structure\n💻 **Generate:** Functions, classes, templates from descriptions\n🐛 **Debug:** Smart error detection and solutions\n🎯 **Try:** 'Use tools to create pixel art' or 'List my codes'!")
    
    # Chat-related methods
    def send_chat_message(self):
        message = self.chat_input.get().strip()
        if not message:
            return
        
        self.add_chat_message("user", message)
        self.chat_input.delete(0, tk.END)
        
        threading.Thread(target=self._get_bot_response, args=(message,), daemon=True).start()
        self.show_typing_indicator()
    
    def _get_bot_response(self, message):
        try:
            response = self.chatbot.get_response(message)
            self.root.after(0, self._display_bot_response, response)
        except Exception as e:
            error_response = f"Oops! I encountered an error: {str(e)}. Let's try again! 🤖"
            self.root.after(0, self._display_bot_response, error_response)
    
    def _display_bot_response(self, response):
        self.hide_typing_indicator()
        self.add_chat_message("bot", response)
    
    def add_chat_message(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.datetime.now().strftime("%H:%M")
        
        if sender == "user":
            self.chat_display.insert(tk.END, f"[{timestamp}] You: ", "timestamp")
            self.chat_display.insert(tk.END, f"{message}\n", "user")
        else:
            self.chat_display.insert(tk.END, f"[{timestamp}] PX Assistant: ", "timestamp")
            
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

I have real tools to manipulate your pixel code system! 🎨✨"""
        self.add_chat_message("bot", help_text)
    
    # Web browser methods
    def load_web_page(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
        
        threading.Thread(target=self._fetch_web_content, args=(url,), daemon=True).start()
        
        self.web_status.config(text=f"🔄 Loading {url}...", fg='orange')
        self.log_output(f"Loading web page: {url}")
    
    def _fetch_web_content(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read()
                
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
        self.raw_html.delete('1.0', tk.END)
        self.raw_html.insert('1.0', html_content)
        
        text_content = self._html_to_text(html_content)
        
        self.web_content.delete('1.0', tk.END)
        self.web_content.insert('1.0', text_content)
        
        self.web_status.config(text=f"✅ Loaded: {url}", fg='green')
        self.log_output(f"Successfully loaded: {url}")
    
    def _show_web_error(self, error_msg):
        self.web_status.config(text=error_msg, fg='red')
        self.web_content.delete('1.0', tk.END)
        self.web_content.insert('1.0', f"Error: {error_msg}")
        self.log_output(f"Web error: {error_msg}")
    
    def _html_to_text(self, html_content):
        try:
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            html_content = re.sub(r'<br[^>]*>', '\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<p[^>]*>', '\n\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</p>', '', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<h[1-6][^>]*>', '\n\n=== ', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</h[1-6]>', ' ===\n', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'<li[^>]*>', '\n• ', html_content, flags=re.IGNORECASE)
            html_content = re.sub(r'</li>', '', html_content, flags=re.IGNORECASE)
            
            html_content = re.sub(r'<[^>]+>', '', html_content)
            html_content = html.unescape(html_content)
            
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
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            temp_path = f.name
        
        webbrowser.open(f'file://{temp_path}')
        self.log_output(f"Opened in browser: {temp_path}")
    
    def load_existing_codes(self):
        code_dir = os.path.join(os.getcwd(), "pxbot_code")
        if os.path.exists(code_dir):
            for filename in os.listdir(code_dir):
                if filename.endswith('.png') and not filename.startswith('blob_'):
                    name = filename[:-4]
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
        print("🚀 Starting PXBot Pro Advanced Launcher...")
        
        # Initialize launcher
        launcher = PXBotAdvancedLauncher()
        
        # Run the launcher
        if IS_PYODIDE:
            # For web environments, return the coroutine for external handling
            return launcher.run()
        else:
            # For desktop environments, run directly
            launcher.run()
    
    except Exception as e:
        error_msg = f"Error starting PXBot Advanced Launcher: {e}\n\n{traceback.format_exc()}"
        log_message(error_msg)
        
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("PXBot Error", error_msg)
            root.destroy()
        except:
            print(error_msg)
            input("Press Enter to close...")

if __name__ == "__main__":
    main()
import pygame
import sys
import time
import os
import json
import glob
import re
import subprocess
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw
from pygame.locals import *
from importlib import import_module, reload

# Ensure correct working directory for executable
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

# Load configuration
CONFIG_PATH = os.path.join("pxbot_code", "pxos_config.json")
DEFAULT_CONFIG = {"window_size": [640, 480], "font_size": 16, "max_recent_apps": 5}
config = DEFAULT_CONFIG
try:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            config.update(json.load(f))
    os.makedirs("pxbot_code", exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)
except Exception as e:
    print(f"Config error: {e}")

# Initialize logging
LOG_PATH = os.path.join("pxbot_code", "pxos_log.txt")
def log_message(message):
    try:
        os.makedirs("pxbot_code", exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except Exception as e:
        print(f"Logging error: {e}")

# Requirements blob
REQUIREMENTS_BLOB = bytes.fromhex("707963616d653d3d322e352e320a50696c6c6f773d3d31302e332e300a5079496e7374616c6c65723d3d352e31332e300a52657374726963746564507974686f6e3d3d372e310a")
try:
    import pygame, PIL, PyInstaller, RestrictedPython
    log_message("All dependencies installed")
except ImportError as e:
    log_message(f"Missing dependencies: {e}")
    req_path = os.path.join("pxbot_code", "requirements.txt")
    try:
        with open(req_path, "wb") as f:
            f.write(REQUIREMENTS_BLOB)
        # Check Python/pip compatibility
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            raise RuntimeError("Python 3.8+ required")
        # Try installing with retries
        for attempt in range(3):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path, "--no-cache-dir"])
                log_message("Dependencies installed from blob")
                break
            except subprocess.CalledProcessError:
                log_message(f"Dependency installation attempt {attempt + 1} failed")
                if attempt == 2:
                    raise RuntimeError("Failed to install dependencies after 3 attempts")
    except Exception as e:
        log_message(f"Failed to install dependencies: {e}")
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("PXOS Error", f"Failed to install dependencies: {e}\nCheck {LOG_PATH}")
        root.destroy()
        sys.exit(1)

# Initialize Pygame
try:
    pygame.init()
    screen = pygame.display.set_mode(config["window_size"])
    pygame.display.set_caption("PXOS Launcher - AI & Human Interface")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", config["font_size"])
    log_message("Pygame initialized successfully")
except Exception as e:
    log_message(f"Pygame initialization failed: {e}")
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("PXOS Error", f"Pygame initialization failed: {e}\nCheck {LOG_PATH}")
    root.destroy()
    sys.exit(1)

# Define valid commands for autocompletion
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
    "launch_gui"
]

# Load recent apps
RECENT_APPS_PATH = os.path.join("pxbot_code", "recent_apps.json")
recent_apps = []
try:
    if os.path.exists(RECENT_APPS_PATH):
        with open(RECENT_APPS_PATH, "r") as f:
            recent_apps = json.load(f)[:config["max_recent_apps"]]
        log_message("Loaded recent apps")
except Exception as e:
    log_message(f"Error loading recent apps: {e}")

# Load command history
COMMAND_HISTORY_PATH = os.path.join("pxbot_code", "command_history.json")
command_history = []
try:
    if os.path.exists(COMMAND_HISTORY_PATH):
        with open(COMMAND_HISTORY_PATH, "r") as f:
            command_history = json.load(f)[:50]
        log_message("Loaded command history")
except Exception as e:
    log_message(f"Error loading command history: {e}")

# Load apps dynamically
apps = {}
apps_dir = os.path.join(os.getcwd(), "apps")
try:
    if os.path.exists(apps_dir):
        for app_file in glob.glob(os.path.join(apps_dir, "*.py")):
            app_name = os.path.splitext(os.path.basename(app_file))[0]
            apps[app_name] = None
        log_message(f"Found apps: {list(apps.keys())}")
    else:
        log_message("Apps directory not found")
        screen.fill((20, 20, 50))
        text = font.render("Error: Apps directory not found", True, (255, 0, 0))
        screen.blit(text, (10, 240))
        pygame.display.flip()
        time.sleep(5)
        pygame.quit()
        sys.exit(1)
except Exception as e:
    log_message(f"Error scanning apps directory: {e}")
    screen.fill((20, 20, 50))
    text = font.render(f"Error scanning apps: {e}", True, (255, 0, 0))
    screen.blit(text, (10, 240))
    pygame.display.flip()
    time.sleep(5)
    pygame.quit()
    sys.exit(1)

# Ensure pxos_app is available
if "pxos_app" not in apps:
    log_message("Error: pxos_app not found in apps/")
    screen.fill((20, 20, 50))
    text = font.render("Error: pxos_app not found in apps/", True, (255, 0, 0))
    screen.blit(text, (10, 240))
    pygame.display.flip()
    time.sleep(5)
    pygame.quit()
    sys.exit(1)

# Define RGB-encoded blobs
blobs = {
    "pxboot_init": bytes.fromhex("B8 01 00 00 00 50 48 31 C0 48 FF C0 C3"),
    "pxos_pxasm": bytes.fromhex("4D4F5620307830303030203078310A505845454343203078313030300A484C54"),
    "PXDetectPCI": bytes.fromhex("5345545F505820307831303030203078303030300A5345545F505820307831303034203078383038360A484C54"),
    "PXMatchDriver": bytes.fromhex("5345545F505820307846303030203078313030340A434D5020307846303030203078383038360A484C54"),
    "PXDriverTemplates": bytes.fromhex("5345545F50582030783330303020307830300A5345545F50582030783330303420275058446973706C617954656D706C6174652E7A744674270A484C54"),
    "PXReflexMutator": bytes.fromhex("5345545F50582030783430303020307830300A434D502030784630303820307836340A484C54"),
    "PXAutoDriverController": bytes.fromhex("43414C4C203078313030300A43414C4C203078463030300A484C54"),
    "VisualFilesystem": bytes.fromhex("5345545F50582030783031303020307830350A5345545F505820307830313034203030320A484C54"),
    "requirements": REQUIREMENTS_BLOB
}

# Create 128x128 canvas
try:
    canvas_size = 128
    canvas = Image.new("RGB", (canvas_size, canvas_size), (20, 20, 50))
    draw = ImageDraw.Draw(canvas)
    blob_data = b"".join(blobs.values())
    pixel_data = [0] * (canvas_size * canvas_size)
    for i in range(0, len(blob_data), 3):
        r = blob_data[i] if i < len(blob_data) else 0
        g = blob_data[i + 1] if i + 1 < len(blob_data) else 0
        b = blob_data[i + 2] if i + 2 < len(blob_data) else 0
        pixel_data[i // 3] = (r << 16) | (g << 8) | b
    canvas.putdata([(r, g, b) for r, g, b in [(p >> 16 & 0xFF, p >> 8 & 0xFF, p & 0xFF) for p in pixel_data]])
    canvas_path = os.path.join("pxbot_code", "blob_canvas.png")
    os.makedirs("pxbot_code", exist_ok=True)
    canvas.save(canvas_path)
    canvas_img = pygame.image.load(canvas_path)
    canvas_img = pygame.transform.scale(canvas_img, (64, 64))
    log_message("Canvas created and loaded")
except Exception as e:
    log_message(f"Error creating canvas: {e}")
    screen.fill((20, 20, 50))
    text = font.render(f"Error creating canvas: {e}", True, (255, 0, 0))
    screen.blit(text, (10, 240))
    pygame.display.flip()
    time.sleep(5)
    pygame.quit()
    sys.exit(1)

# Load pixel memory for treemap
pixel_memory = [0] * (640 * 480)
for i in range(min(len(pixel_data), 640 * 480)):
    pixel_memory[i] = pixel_data[i]

# Create treemap with color-coded regions
surface = pygame.Surface(config["window_size"])
blob_colors = {
    "pxboot_init": (255, 0, 0), "pxos_pxasm": (0, 255, 0), "PXDetectPCI": (0, 0, 255),
    "PXMatchDriver": (255, 255, 0), "PXDriverTemplates": (255, 0, 255), "PXReflexMutator": (0, 255, 255),
    "PXAutoDriverController": (128, 128, 128), "VisualFilesystem": (255, 128, 0), "requirements": (128, 0, 128)
}
blob_positions = {}
offset = 0
for name, blob in blobs.items():
    length = len(blob) // 3
    x_start = (offset % 20) * 32
    y_start = (offset // 20) * 24
    blob_positions[name] = (x_start, y_start, length)
    offset += length
for i, pixel in enumerate(pixel_data[:640*480]):
    x, y = i % 640, i // 640
    for name, (x_start, y_start, length) in blob_positions.items():
        if i >= offset - length and i < offset:
            surface.set_at((x, y), blob_colors[name])
            break
for name, (x_start, y_start, _) in blob_positions.items():
    text = font.render(name[:10], True, (255, 255, 255))
    surface.blit(text, (x_start, y_start))

# AI state
ai_state = {"codes": []}
ai_state_path = os.path.join("pxbot_code", "ai_state.json")
try:
    if os.path.exists(ai_state_path):
        with open(ai_state_path, "r") as f:
            ai_state = json.load(f)
        log_message("Loaded AI state")
except Exception as e:
    log_message(f"Error loading AI state: {e}")

# Pixel art preview
preview_img = None
preview_path = None

# File menu state
menu_active = False
menu_selection = 0
menu_items = ["Open App", "Recent Apps", "Reload Apps", "Exit"]
app_selection = 0
recent_selection = 0
show_apps = False
show_recent = False
app_list = list(apps.keys())
command_input = ""
input_active = False
history_index = len(command_history)
suggestions = []
log_messages = []
status_message = "Ready"

# Natural language parser
def parse_natural_language(input_text):
    input_text = input_text.lower().strip()
    if "create pixel art" in input_text:
        match = re.search(r"from\s+(\w+)", input_text)
        if match:
            return f"pxbot:create:pixel_art:{match.group(1)}"
    elif "create pattern" in input_text:
        match = re.search(r"(\w+)\s+pattern\s+(\d+)(?:x\d+)?", input_text)
        if match:
            return f"pxbot:create:pattern:{match.group(1)}:{match.group(2)}"
    elif "save code" in input_text:
        match = re.search(r"save\s+code\s+(\w+)\s+(.+)", input_text)
        if match:
            return f"pxbot:save:{match.group(1)}:{match.group(2)}"
    elif "merge" in input_text:
        match = re.search(r"merge\s+(\w+)\s+and\s+(\w+)\s+into\s+(\w+)", input_text)
        if match:
            return f"pxbot:merge:{match.group(1)}:{match.group(2)}:{match.group(3)}"
    elif "analyze" in input_text:
        match = re.search(r"analyze\s+(?:pixel\s+)?(\w+)", input_text)
        if match:
            return f"pxbot:analyze:{match.group(1)}"
    return input_text

# Boot animation
try:
    boot_messages = [
        "Initializing PXOS Runtime...",
        "Loading Visual Filesystem...",
        "Detecting PCI Devices...",
        "Starting Pixel Programming Tools..."
    ]
    for i, msg in enumerate(boot_messages):
        screen.fill((20, 20, 50))
        alpha = int(255 * (1 - i / len(boot_messages)))
        text = font.render(msg, True, (0, 255, 0, alpha))
        screen.blit(text, (50, 240))
        pygame.display.flip()
        time.sleep(0.5)
    log_message("Boot sequence completed")
    status_message = "Boot completed"
except Exception as e:
    log_message(f"Error in boot animation: {e}")
    screen.fill((20, 20, 50))
    text = font.render(f"Error in boot animation: {e}", True, (255, 0, 0))
    screen.blit(text, (10, 240))
    pygame.display.flip()
    time.sleep(5)
    pygame.quit()
    sys.exit(1)

# Main loop
try:
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if menu_active:
                    if event.key == K_UP:
                        menu_selection = (menu_selection - 1) % len(menu_items)
                    elif event.key == K_DOWN:
                        menu_selection = (menu_selection + 1) % len(menu_items)
                    elif event.key == K_RETURN:
                        if menu_items[menu_selection] == "Exit":
                            running = False
                        elif menu_items[menu_selection] == "Open App":
                            show_apps = True
                            menu_active = False
                        elif menu_items[menu_selection] == "Recent Apps":
                            show_recent = True
                            menu_active = False
                        elif menu_items[menu_selection] == "Reload Apps":
                            result = reload_apps()
                            log_messages.append(result)
                            log_message(result)
                            menu_active = False
                            status_message = result
                    elif event.key == K_ESCAPE:
                        menu_active = False
                elif show_apps:
                    if event.key == K_UP:
                        app_selection = (app_selection - 1) % len(app_list)
                    elif event.key == K_DOWN:
                        app_selection = (app_selection + 1) % len(app_list)
                    elif event.key == K_RETURN:
                        app_name = app_list[app_selection]
                        result = load_app(app_name)
                        log_messages.append(result)
                        log_message(result)
                        show_apps = False
                        status_message = result
                    elif event.key == K_ESCAPE:
                        show_apps = False
                    elif event.key == K_F1:
                        menu_active = True
                        show_apps = False
                elif show_recent:
                    if event.key == K_UP:
                        recent_selection = (recent_selection - 1) % len(recent_apps)
                    elif event.key == K_DOWN:
                        recent_selection = (recent_selection + 1) % len(recent_apps)
                    elif event.key == K_RETURN:
                        app_name = recent_apps[recent_selection]
                        result = load_app(app_name)
                        log_messages.append(result)
                        log_message(result)
                        show_recent = False
                        status_message = result
                    elif event.key == K_ESCAPE:
                        show_recent = False
                    elif event.key == K_F1:
                        menu_active = True
                        show_recent = False
                else:
                    if event.key == K_F1:
                        menu_active = True
                        menu_selection = 0
                    elif event.key == K_RETURN:
                        if input_active and command_input:
                            command = parse_natural_language(command_input)
                            command_history.append(command)
                            history_index = len(command_history)
                            result = process_command(command)
                            log_messages.append(f"> {command}: {result}")
                            log_message(f"Command: {command}, Result: {result}")
                            if "pixel_art" in command or "pattern" in command:
                                parts = command.split(":")
                                if "pixel_art" in command:
                                    preview_path = os.path.join("pxbot_code", f"{parts[2]}_art.png")
                                else:
                                    size = parts[3] if len(parts) > 3 else "32"
                                    preview_path = os.path.join("pxbot_code", f"{parts[2]}_{size}x{size}.png")
                                if os.path.exists(preview_path):
                                    preview_img = pygame.image.load(preview_path)
                                    preview_img = pygame.transform.scale(preview_img, (64, 64))
                            command_input = ""
                            input_active = False
                            suggestions = []
                            status_message = result
                        else:
                            input_active = True
                    elif event.key == K_BACKSPACE and input_active:
                        command_input = command_input[:-1]
                        suggestions = [cmd for cmd in VALID_COMMANDS if cmd.startswith(command_input)]
                    elif event.key == K_UP and input_active:
                        if history_index > 0:
                            history_index -= 1
                            command_input = command_history[history_index]
                            suggestions = [cmd for cmd in VALID_COMMANDS if cmd.startswith(command_input)]
                        elif history_index == len(command_history) - 1:
                            history_index = len(command_history)
                            command_input = ""
                            suggestions = []
                    elif event.key == K_DOWN and input_active:
                        if history_index < len(command_history) - 1:
                            history_index += 1
                            command_input = command_history[history_index]
                            suggestions = [cmd for cmd in VALID_COMMANDS if cmd.startswith(command_input)]
                    elif event.key == K_TAB and input_active and suggestions:
                        command_input = suggestions[0]
                        suggestions = []
                    elif input_active and event.unicode.isprintable():
                        command_input += event.unicode
                        suggestions = [cmd for cmd in VALID_COMMANDS if cmd.startswith(command_input)]

        # Render UI
        screen.fill((20, 20, 50))
        screen.blit(surface, (0, 0))
        screen.blit(canvas_img, (config["window_size"][0] - 70, 10))
        if preview_img:
            screen.blit(preview_img, (config["window_size"][0] - 140, 10))
        for i, msg in enumerate(log_messages[-5:]):
            text = font.render(msg, True, (0, 255, 0))
            screen.blit(text, (10, 10 + i * 20))
        if menu_active:
            for i, item in enumerate(menu_items):
                color = (255, 255, 0) if i == menu_selection else (255, 255, 255)
                text = font.render(item, True, color)
                screen.blit(text, (config["window_size"][0] - 140, 100 + i * 30))
        elif show_apps:
            for i, app in enumerate(app_list):
                color = (255, 255, 0) if i == app_selection else (255, 255, 255)
                text = font.render(app, True, color)
                screen.blit(text, (config["window_size"][0] - 140, 100 + i * 30))
        elif show_recent:
            for i, app in enumerate(recent_apps):
                color = (255, 255, 0) if i == recent_selection else (255, 255, 255)
                text = font.render(app, True, color)
                screen.blit(text, (config["window_size"][0] - 140, 100 + i * 30))
        else:
            if input_active:
                prompt = font.render(f"> {command_input}", True, (255, 255, 255))
                screen.blit(prompt, (10, config["window_size"][1] - 30))
                for i, suggestion in enumerate(suggestions[:3]):
                    text = font.render(suggestion, True, (128, 128, 128))
                    screen.blit(text, (10, config["window_size"][1] - 50 - i * 20))
            else:
                prompt = font.render("> Press Enter or F1 for menu", True, (255, 255, 255))
                screen.blit(prompt, (10, config["window_size"][1] - 30))
        text = font.render(status_message, True, (255, 255, 255))
        screen.blit(text, (10, config["window_size"][1] - 50))
        pygame.display.flip()
        clock.tick(60)

except Exception as e:
    log_message(f"Main loop error: {e}\n{traceback.format_exc()}")
    screen.fill((20, 20, 50))
    lines = str(e).split("\n")[:5]
    for i, line in enumerate(lines):
        text = font.render(line, True, (255, 0, 0))
        screen.blit(text, (10, 240 + i * 20))
    pygame.display.flip()
    time.sleep(5)

# Cleanup
try:
    with open(ai_state_path, "w") as f:
        json.dump(ai_state, f)
    with open(RECENT_APPS_PATH, "w") as f:
        json.dump(recent_apps, f)
    with open(COMMAND_HISTORY_PATH, "w") as f:
        json.dump(command_history, f)
    log_message("Cleanup completed")
except Exception as e:
    log_message(f"Cleanup error: {e}")
pygame.quit()

def load_app(app_name):
    try:
        if app_name in apps and apps[app_name] is None:
            module = import_module(f"apps.{app_name}")
            apps[app_name] = module.main()
            if app_name not in recent_apps:
                recent_apps.insert(0, app_name)
                if len(recent_apps) > config["max_recent_apps"]:
                    recent_apps.pop()
            log_message(f"Loaded app: {app_name}")
            return f"Loaded app: {app_name}"
        return f"App {app_name} already loaded or not found"
    except Exception as e:
        log_message(f"Error loading app {app_name}: {e}")
        return f"Error loading app {app_name}: {e}"

def reload_apps():
    try:
        global apps, app_list
        apps = {app_name: None for app_name in apps}
        for app_file in glob.glob(os.path.join(apps_dir, "*.py")):
            app_name = os.path.splitext(os.path.basename(app_file))[0]
            apps[app_name] = None
        app_list = list(apps.keys())
        log_message("Apps reloaded")
        return "Apps reloaded"
    except Exception as e:
        log_message(f"Error reloading apps: {e}")
        return f"Error reloading apps: {e}"

def process_command(command):
    try:
        if command.startswith("px://"):
            return process_pixel_command(command[5:])
        elif command == "launch_gui":
            from apps.pxos_app import PXBotGUI
            threading.Thread(target=lambda: PXBotGUI().run(), daemon=True).start()
            log_message("GUI launched")
            return "GUI launched"
        else:
            result = apps.get("pxos_app").execute_command(command)
            if command.startswith("pxbot:save:"):
                parts = command.split(":")
                if len(parts) >= 4:
                    ai_state["codes"].append({"name": parts[2], "code": parts[3]})
            log_message(f"Command result: {result}")
            return result
    except Exception as e:
        log_message(f"Command error: {e}")
        return f"Command error: {e}"

def process_pixel_command(command):
    try:
        parts = command.split(":")
        action = parts[0]
        if action in ["create", "merge", "analyze", "optimize"]:
            idx = len(pixel_memory) // 2
            for i, char in enumerate(command):
                if idx + i < len(pixel_memory):
                    pixel_memory[idx + i] = ord(char) << 16
            result = apps.get("pxos_app").execute_command(f"pxbot:{command}")
            for i in range(len(command)):
                if idx + i < len(pixel_memory):
                    pixel_memory[idx + i] = 0
            log_message(f"Pixel command result: {result}")
            return result
        return "Invalid pixel command"
    except Exception as e:
        log_message(f"Pixel command error: {e}")
        return f"Pixel command error: {e}"
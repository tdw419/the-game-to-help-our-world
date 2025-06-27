import pygame
import ctypes
import sys
import time
import os
import json
import glob
from PIL import Image, ImageDraw
from pygame.locals import *
from importlib import import_module

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("PXOS Launcher - AI & Human Interface")
clock = pygame.time.Clock()
font = pygame.font.SysFont("monospace", 16)

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
if os.path.exists(RECENT_APPS_PATH):
    with open(RECENT_APPS_PATH, "r") as f:
        recent_apps = json.load(f)[:5]  # Limit to 5 recent apps

# Load apps dynamically from apps/ folder
apps = {}
apps_dir = os.path.join(os.getcwd(), "apps")
if os.path.exists(apps_dir):
    for app_file in glob.glob(os.path.join(apps_dir, "*.py")):
        app_name = os.path.splitext(os.path.basename(app_file))[0]
        apps[app_name] = None  # Initialize as unloaded

# Ensure pxos_app is available
if "pxos_app" not in apps:
    print("Error: pxos_app not found in apps/")
    pygame.quit()
    sys.exit(1)

# Define RGB-encoded blobs for visualization
blobs = {
    "pxboot_init": bytes.fromhex("B8 01 00 00 00 50 48 31 C0 48 FF C0 C3"),
    "pxos_pxasm": bytes.fromhex("4D4F5620307830303030203078310A505845454343203078313030300A484C54"),
    "PXDetectPCI": bytes.fromhex("5345545F505820307831303030203078303030300A5345545F505820307831303034203078383038360A484C54"),
    "PXMatchDriver": bytes.fromhex("5345545F505820307846303030203078313030340A434D5020307846303030203078383038360A484C54"),
    "PXDriverTemplates": bytes.fromhex("5345545F50582030783330303020307830300A5345545F50582030783330303420275058446973706C617954656D706C6174652E7A744674270A484C54"),
    "PXReflexMutator": bytes.fromhex("5345545F50582030783430303020307830300A434D502030784630303820307836340A484C54"),
    "PXAutoDriverController": bytes.fromhex("43414C4C203078313030300A43414C4C203078463030300A484C54"),
    "VisualFilesystem": bytes.fromhex("5345545F50582030783031303020307830350A5345545F505820307830313034203030320A484C54")
}

# Create 128x128 canvas for visualization
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

# Load pixel memory for treemap
pixel_memory = [0] * (640 * 480)
for i in range(min(len(pixel_data), 640 * 480)):
    pixel_data[i] = pixel_data[i]

# Create Pygame surface for treemap
surface = pygame.Surface((640, 480))
pygame.pixelcopy.array_to_surface(surface, pixel_memory)

# Load blob_canvas.png as thumbnail
canvas_img = pygame.image.load(canvas_path)
canvas_img = pygame.transform.scale(canvas_img, (64, 64))

# Allocate memory for ASM stub
kernel32 = ctypes.windll.kernel32
process = kernel32.GetCurrentProcess()
memory_size = len(blobs["pxboot_init"]) + len(pixel_memory) * 4
memory = kernel32.VirtualAllocEx(process, 0, memory_size, 0x3000, 0x40)
if not memory:
    print("Error: VirtualAlloc failed!")
    pygame.quit()
    sys.exit(1)

# Write ASM stub and pixel memory
ctypes.windll.kernel32.WriteProcessMemory(process, memory, blobs["pxboot_init"], len(blobs["pxboot_init"]), None)
ctypes.windll.kernel32.WriteProcessMemory(process, memory + len(blobs["pxboot_init"]), (ctypes.c_uint * len(pixel_memory))(*pixel_memory), len(pixel_memory) * 4, None)

# Create thread to execute ASM
thread = kernel32.CreateThread(None, 0, memory, None, 0, None)
if not thread:
    print("Error: CreateThread failed!")
    kernel32.VirtualFreeEx(process, memory, 0, 0x8000)
    pygame.quit()
    sys.exit(1)

# AI state for collaboration
ai_state = {"codes": []}
ai_state_path = os.path.join("pxbot_code", "ai_state.json")
if os.path.exists(ai_state_path):
    with open(ai_state_path, "r") as f:
        ai_state = json.load(f)

# Log file setup
log_path = os.path.join("pxbot_code", "pxos_log.txt")
def log_message(message):
    with open(log_path, "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

# File menu state
menu_active = False
menu_selection = 0
menu_items = ["Open App", "Recent Apps", "Exit"]
app_selection = 0
recent_selection = 0
show_apps = False
show_recent = False
app_list = list(apps.keys())

# Boot animation
boot_messages = [
    "Initializing PXOS Runtime...",
    "Loading Visual Filesystem...",
    "Detecting PCI Devices...",
    "Starting Pixel Programming Tools..."
]
for i, msg in enumerate(boot_messages):
    screen.fill((20, 20, 50))
    alpha = int(255 * (1 - i / len(boot_messages)))  # Fade effect
    text = font.render(msg, True, (0, 255, 0, alpha))
    screen.blit(text, (50, 240))
    pygame.display.flip()
    time.sleep(0.5)
log_message("Boot sequence completed")

# Main loop
running = True
command_input = ""
input_active = False
command_history = []
history_index = -1
suggestions = []
log_messages = []

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
                elif event.key == K_ESCAPE:
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
                elif event.key == K_ESCAPE:
                    show_recent = False
            else:
                if event.key == K_F1:  # F1 to open menu
                    menu_active = True
                    menu_selection = 0
                elif event.key == K_RETURN:
                    if input_active and command_input:
                        command_history.append(command_input)
                        history_index = len(command_history)
                        result = process_command(command_input)
                        log_messages.append(f"> {command_input}: {result}")
                        log_message(f"Command: {command_input}, Result: {result}")
                        command_input = ""
                        input_active = False
                        suggestions = []
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
                elif event.key == K_DOWN and input_active:
                    if history_index < len(command_history) - 1:
                        history_index += 1
                        command_input = command_history[history_index]
                        suggestions = [cmd for cmd in VALID_COMMANDS if cmd.startswith(command_input)]
                    elif history_index == len(command_history) - 1:
                        history_index = len(command_history)
                        command_input = ""
                        suggestions = []
                elif event.key == K_TAB and input_active and suggestions:
                    command_input = suggestions[0]
                    suggestions = []
                elif input_active and event.unicode.isprintable():
                    command_input += event.unicode
                    suggestions = [cmd for cmd in VALID_COMMANDS if cmd.startswith(command_input)]

    # Render UI
    screen.fill((20, 20, 50))
    # Treemap visualization
    screen.blit(surface, (0, 0))
    # Blob canvas thumbnail
    screen.blit(canvas_img, (570, 10))
    # Log messages
    for i, msg in enumerate(log_messages[-5:]):
        text = font.render(msg, True, (0, 255, 0))
        screen.blit(text, (10, 10 + i * 20))
    # Menu or command prompt
    if menu_active:
        for i, item in enumerate(menu_items):
            color = (255, 255, 0) if i == menu_selection else (255, 255, 255)
            text = font.render(item, True, color)
            screen.blit(text, (500, 100 + i * 30))
    elif show_apps:
        for i, app in enumerate(app_list):
            color = (255, 255, 0) if i == app_selection else (255, 255, 255)
            text = font.render(app, True, color)
            screen.blit(text, (500, 100 + i * 30))
    elif show_recent:
        for i, app in enumerate(recent_apps):
            color = (255, 255, 0) if i == recent_selection else (255, 255, 255)
            text = font.render(app, True, color)
            screen.blit(text, (500, 100 + i * 30))
    else:
        if input_active:
            prompt = font.render(f"> {command_input}", True, (255, 255, 255))
            screen.blit(prompt, (10, 450))
            for i, suggestion in enumerate(suggestions[:3]):
                text = font.render(suggestion, True, (128, 128, 128))
                screen.blit(text, (10, 430 - i * 20))
        else:
            prompt = font.render("> Press Enter or F1 for menu", True, (255, 255, 255))
            screen.blit(prompt, (10, 450))
    pygame.display.flip()
    clock.tick(60)

# Cleanup
with open(ai_state_path, "w") as f:
    json.dump(ai_state, f)
with open(RECENT_APPS_PATH, "w") as f:
    json.dump(recent_apps, f)
kernel32.TerminateThread(thread, 0)
kernel32.VirtualFreeEx(process, memory, 0, 0x8000)
pygame.quit()

def load_app(app_name):
    if app_name in apps and apps[app_name] is None:
        try:
            module = import_module(f"apps.{app_name}")
            apps[app_name] = module.main()
            if app_name not in recent_apps:
                recent_apps.insert(0, app_name)
                if len(recent_apps) > 5:
                    recent_apps.pop()
            return f"Loaded app: {app_name}"
        except Exception as e:
            return f"Error loading app {app_name}: {e}"
    return f"App {app_name} already loaded or not found"

def process_command(command):
    if command.startswith("px://"):
        return process_pixel_command(command[5:])
    elif command == "launch_gui":
        try:
            from apps.pxos_app import PXBotGUI
            threading.Thread(target=lambda: PXBotGUI().run(), daemon=True).start()
            return "GUI launched"
        except Exception as e:
            return f"Error launching GUI: {e}"
    else:
        result = apps.get("pxos_app").execute_command(command)
        if command.startswith("pxbot:save:"):
            parts = command.split(":")
            if len(parts) >= 4:
                ai_state["codes"].append({"name": parts[2], "code": parts[3]})
        return result

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
            return result
        return "Invalid pixel command"
    except Exception as e:
        return f"Pixel command error: {e}"
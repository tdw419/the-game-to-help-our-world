import pygame
import ctypes
import sys
import time
import os
from PIL import Image, ImageDraw
from apps.pxos_app import PXOSInterface, MiniVFS, MiniRT, PXBot

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("PXOS Launcher - AI & Human Interface")
clock = pygame.time.Clock()

# Define RGB-encoded blobs (core PXOS components, duplicated for launcher visualization)
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

# Create 128x128 canvas and encode blobs as RGB for visualization
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

# Load pixel memory for 640x480 runtime
pixel_memory = [0] * (640 * 480)
for i in range(min(len(pixel_data), 640 * 480)):
    pixel_memory[i] = pixel_data[i]

# Create Pygame surface and blit initial treemap
surface = pygame.Surface((640, 480))
pygame.pixelcopy.array_to_surface(surface, pixel_memory)
screen.blit(surface, (0, 0))
pygame.display.flip()

# Allocate memory and copy ASM stub
kernel32 = ctypes.windll.kernel32
process = kernel32.GetCurrentProcess()
memory_size = len(blobs["pxboot_init"]) + len(pixel_memory) * 4
memory = kernel32.VirtualAllocEx(process, 0, memory_size, 0x3000, 0x40)  # MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE
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
    kernel32.VirtualFreeEx(process, memory, 0, 0x8000)  # MEM_RELEASE
    pygame.quit()
    sys.exit(1)

# Initialize PXOSInterface from apps/pxos_app.py
try:
    pxos = PXOSInterface()
except Exception as e:
    print(f"Error initializing PXOS: {e}")
    kernel32.TerminateThread(thread, 0)
    kernel32.VirtualFreeEx(process, memory, 0, 0x8000)
    pygame.quit()
    sys.exit(1)

# Boot animation
font = pygame.font.SysFont("monospace", 20)
boot_messages = [
    "Initializing PXOS Runtime...",
    "Loading Visual Filesystem...",
    "Detecting PCI Devices...",
    "Starting Pixel Programming Tools..."
]
for msg in boot_messages:
    screen.fill((20, 20, 50))
    text = font.render(msg, True, (0, 255, 0))
    screen.blit(text, (50, 240))
    pygame.display.flip()
    time.sleep(1)

# Main loop with interactive interface
running = True
command_input = ""
input_active = False
input_surface = font.render("Enter command: ", True, (255, 255, 255))
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if input_active and command_input:
                    result = pxos.execute_command(command_input)
                    boot_messages.append(f"> {command_input}: {result}")
                    command_input = ""
                    input_active = False
                else:
                    input_active = True
            elif event.key == pygame.K_BACKSPACE and input_active:
                command_input = command_input[:-1]
            elif input_active and event.unicode.isprintable():
                command_input += event.unicode

    # Render UI
    screen.fill((20, 20, 50))
    # Display boot messages (scrolling log)
    for i, msg in enumerate(boot_messages[-5:]):  # Show last 5 messages
        text = font.render(msg, True, (0, 255, 0))
        screen.blit(text, (10, 10 + i * 30))
    # Display input prompt
    if input_active:
        prompt = font.render(f"Enter command: {command_input}", True, (255, 255, 255))
        screen.blit(prompt, (10, 400))
    else:
        screen.blit(input_surface, (10, 400))
    pygame.display.flip()
    clock.tick(60)

# Cleanup
kernel32.TerminateThread(thread, 0)
kernel32.VirtualFreeEx(process, memory, 0, 0x8000)
pygame.quit()
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw

# === Settings ===
WORLD_SIZE = 25000
VIEW_WIDTH = 800
VIEW_HEIGHT = 600

# === World canvas (25k x 25k image) ===
world_image = Image.new("RGB", (WORLD_SIZE, WORLD_SIZE), color=(0, 0, 0))
draw = ImageDraw.Draw(world_image)

# === Viewport state ===
viewport_x = WORLD_SIZE // 2 - VIEW_WIDTH // 2
viewport_y = WORLD_SIZE // 2 - VIEW_HEIGHT // 2
zoom = 1.0

# === GUI setup ===
root = tk.Tk()
root.title("ColorOS Python Canvas Viewer")
canvas = tk.Canvas(root, width=VIEW_WIDTH, height=VIEW_HEIGHT)
canvas.pack()

# === Draw the current view ===
def render():
    box = (
        int(viewport_x),
        int(viewport_y),
        int(viewport_x + VIEW_WIDTH / zoom),
        int(viewport_y + VIEW_HEIGHT / zoom)
    )
    cropped = world_image.crop(box)
    scaled = cropped.resize((VIEW_WIDTH, VIEW_HEIGHT), Image.NEAREST)
    tk_img = ImageTk.PhotoImage(scaled)
    canvas.image = tk_img
    canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
    root.title(f"ColorOS Viewer - View: ({int(viewport_x)}, {int(viewport_y)}) Zoom: {zoom:.2f}")

# === Input handlers ===
def on_key(event):
    global viewport_x, viewport_y
    pan = 100 / zoom
    if event.keysym == 'Up': viewport_y -= pan
    elif event.keysym == 'Down': viewport_y += pan
    elif event.keysym == 'Left': viewport_x -= pan
    elif event.keysym == 'Right': viewport_x += pan
    render()

def on_click(event):
    global world_image
    gx = int(viewport_x + event.x / zoom)
    gy = int(viewport_y + event.y / zoom)
    if 0 <= gx < WORLD_SIZE and 0 <= gy < WORLD_SIZE:
        draw.point((gx, gy), fill=(255, 0, 255))  # Magenta
    render()

def on_scroll(event):
    global zoom
    if event.delta > 0:
        zoom *= 1.1
    else:
        zoom /= 1.1
    zoom = max(0.1, min(zoom, 10.0))
    render()

# === Bind controls ===
canvas.bind("<Button-1>", on_click)
canvas.bind("<MouseWheel>", on_scroll)
root.bind("<Key>", on_key)

# === Initial render ===
render()
root.mainloop()

# eight_png_manager.py
# This module now renders the conceptual pixel display into actual PNG image files,
# with support for defined visual zones.

import logging
import os
from PIL import Image, ImageDraw, ImageFont
import time
from datetime import datetime # Import datetime for timestamps

# Import the new pixel_zones definitions
from pixel_zones import get_zone_coordinates, PIXEL_ZONES

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Configuration for the Visual Display ---
DISPLAY_WIDTH = 800  # Pixels wide (standard for 8.png)
DISPLAY_HEIGHT = 600  # Pixels high (standard for 8.png)
OUTPUT_DIR = "./display_output" # Directory to save rendered images
FONT_PATH = "arial.ttf" # Path to a .ttf font file. 
                         # On Linux, try "DejaVuSans.ttf" or "arial.ttf" if available.
                         # On Windows, "arial.ttf" is usually in C:\Windows\Fonts.
                         # If not found, a default generic font will be used by Pillow.
FONT_SIZE_DEFAULT = 12 # Default font size
PIXEL_RENDER_INTERVAL = 0.5 # Minimum time between rendering updates to file

# Global state for Pillow image and draw object
_current_image = None
_current_draw = None
_last_render_time = 0

# Global state for managing zones' current content and color
# This maps zone names (from PIXEL_ZONES) to their current rendered state.
_zone_properties = {} 

def _get_font(size):
    """Attempts to load a font, falls back to default if not found."""
    try:
        if os.name == 'nt': # Windows
            return ImageFont.truetype("arial.ttf", size)
        elif os.name == 'posix': # Linux/macOS
            # Common Linux paths
            for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                      "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]:
                if os.path.exists(p):
                    return ImageFont.truetype(p, size)
            # Common macOS path
            if os.path.exists("/Library/Fonts/Arial.ttf"):
                 return ImageFont.truetype("/Library/Fonts/Arial.ttf", size)
        # Fallback to Pillow's default bitmap font
        logging.warning(f"Font file '{FONT_PATH}' not found or system font not detected. Using default Pillow bitmap font.")
        return ImageFont.load_default()
    except IOError:
        logging.warning(f"IOError loading font. Using default Pillow bitmap font.")
        return ImageFont.load_default()
    except Exception as e:
        logging.warning(f"Unexpected error loading font: {e}. Using default Pillow bitmap font.")
        return ImageFont.load_default()

def _initialize_display_surface():
    """Initializes the PIL Image and ImageDraw objects."""
    global _current_image, _current_draw
    # Create a new black image (RGB mode) with standard 8.png dimensions
    _current_image = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), color = 'black')
    _current_draw = ImageDraw.Draw(_current_image)
    logging.info(f"Eight PNG Manager: Initialized display surface: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}.")

def _render_display_to_file():
    """
    Renders the current state of the display to a PNG file in the OUTPUT_DIR,
    drawing each zone based on its properties.
    """
    global _last_render_time
    current_time = time.time()
    if (current_time - _last_render_time) < PIXEL_RENDER_INTERVAL:
        return # Don't render too frequently

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3] # ms precision
    filepath = os.path.join(OUTPUT_DIR, f"display_frame_{timestamp}.png")

    try:
        # Clear the entire canvas first with a base color (e.g., black)
        _current_draw.rectangle([0, 0, DISPLAY_WIDTH, DISPLAY_HEIGHT], fill=(0,0,0))

        # Iterate through all DEFINED zones from PIXEL_ZONES to ensure proper order and coverage
        # and draw their current state (background color then text)
        for zone_name_key in PIXEL_ZONES.keys(): # Iterate by key to ensure order if defined
            zone_coords = PIXEL_ZONES[zone_name_key]
            props = _zone_properties.get(zone_name_key, {"text": "", "color": (0,0,0), "font": f"{FONT_SIZE_DEFAULT}px Inter"}) # Get current properties

            # Draw zone background color
            display_color = props["color"]
            _current_draw.rectangle(zone_coords, fill=display_color)

            # Draw text within the zone
            if props["text"]:
                font = _get_font(int(props["font"].split('px')[0])) # Extract font size from string
                
                # Calculate text position to center within its zone
                x1, y1, x2, y2 = zone_coords
                zone_width = x2 - x1
                zone_height = y2 - y1

                # Use textbbox for more accurate text measurement and centering
                text_bbox = _current_draw.textbbox((0, 0), props["text"], font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]

                # Center text horizontally and vertically within the zone
                text_x = x1 + (zone_width - text_width) / 2
                text_y = y1 + (zone_height - text_height) / 2 # Basic vertical center, adjust for font baseline if needed

                _current_draw.text((text_x, text_y), props["text"], fill=(255,255,255), font=font) # Text color always white for visibility


        _current_image.save(filepath)
        logging.info(f"Eight PNG Manager: Rendered display to '{filepath}'.")
        _last_render_time = current_time
    except Exception as e:
        logging.error(f"Eight PNG Manager: Failed to render display to file: {e}", exc_info=True)


def initialize_display():
    """
    Initializes the conceptual display and the rendering surface.
    Sets up initial zone properties.
    """
    _initialize_display_surface()
    # Initialize properties for all predefined zones
    for zone_name_key, zone_coords in PIXEL_ZONES.items():
        _zone_properties[zone_name_key] = {
            "text": "",
            "color": (0, 0, 0), # Default black
            "font": f"{FONT_SIZE_DEFAULT}px Inter" # Default font string
        }
    _render_display_to_file() # Initial render
    logging.info("Eight PNG Manager: Display initialized with visual rendering enabled.")

def set_active_zone(zone_name: str):
    """
    Sets the conceptually active zone. Used for tracking, not direct rendering in this module.
    """
    # In this new rendering approach, this function primarily serves for logging
    # as updates directly target zones by name via updateZoneText/Color.
    # It doesn't affect rendering directly.
    logging.debug(f"Eight PNG Manager: Conceptually active zone set to '{zone_name}'.")

def update_zone_text(zone_name: str, text_string: str, font_size: int = FONT_SIZE_DEFAULT):
    """
    Updates the text content for a specified zone and triggers a re-render.
    """
    zone_key = zone_name.upper()
    if zone_key not in _zone_properties:
        logging.warning(f"Eight PNG Manager: Zone '{zone_name}' not defined in PIXEL_ZONES. Cannot update text.")
        return
    _zone_properties[zone_key]['text'] = text_string
    _zone_properties[zone_key]['font'] = f"{font_size}px Inter" # Update font size if provided
    _render_display_to_file()

def set_zone_color(zone_name: str, r: int, g: int, b: int):
    """
    Sets the background or overall color for a specified zone and triggers a re-render.
    """
    zone_key = zone_name.upper()
    if zone_key not in _zone_properties:
        logging.warning(f"Eight PNG Manager: Zone '{zone_name}' not defined in PIXEL_ZONES. Cannot set color.")
        return
    _zone_properties[zone_key]['color'] = (r, g, b)
    _render_display_to_file()

def clear_zone(zone_name: str, color=(0,0,0)):
    """
    Clears a named rectangular zone by filling it with a specified color.
    """
    zone_key = zone_name.upper()
    if zone_key not in _zone_properties:
        logging.warning(f"Eight PNG Manager: Zone '{zone_name}' not defined in PIXEL_ZONES. Cannot clear.")
        return
    _zone_properties[zone_key]['text'] = "" # Clear text
    _zone_properties[zone_key]['color'] = color # Set color
    _render_display_to_file()

def get_zone_state(zone_name: str):
    """
    Retrieves the current conceptual state of a zone. Useful for debugging.
    """
    return _zone_properties.get(zone_name.upper(), {"text": "", "color": (0,0,0)})

def shutdown_display():
    """
    Shuts down the display, performs a final render.
    """
    logging.info("Eight PNG Manager: Display shutdown (conceptual).")
    _render_display_to_file() # Final render on shutdown


# Example Usage (for testing this module standalone)
if __name__ == "__main__":
    print("--- Testing eight_png_manager.py (Visual Output with Zones) ---")
    initialize_display()

    # Initial system message
    update_zone_text("STATUS_BAR", "System booting up...", font_size=10)
    set_zone_color("STATUS_BAR", 50, 50, 50) # Dark grey status bar
    time.sleep(1)

    # Main content display
    update_zone_text("MAIN_CONTENT", "Welcome to PixelVault!", font_size=24)
    set_zone_color("MAIN_CONTENT", 0, 0, 100) # Dark blue main content
    time.sleep(2)

    # AI Feedback area update
    update_zone_text("AI_FEEDBACK", "AI Ready.", font_size=12)
    set_zone_color("AI_FEEDBACK", 0, 50, 0) # Dark green AI feedback
    time.sleep(1)
    
    # Clear main content and display new text
    clear_zone("MAIN_CONTENT", color=(100,0,0)) # Clear to red
    update_zone_text("MAIN_CONTENT", "ALERT!", font_size=32)
    time.sleep(1)

    update_zone_text("STATUS_BAR", "System shut down.", font_size=10)
    set_zone_color("STATUS_BAR", 100, 0, 0)
    time.sleep(0.5)

    shutdown_display()
    print(f"Check the '{OUTPUT_DIR}' directory for generated PNG images.")

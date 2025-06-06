import os
import hashlib
from PIL import Image

# --- Configuration (MUST match snapshot_generator_code) ---
# These constants define the layout of the .pxl.png files
CHAR_WIDTH = 3
CHAR_HEIGHT = 5
CHAR_SPACING = 1
LINE_SPACING = 1

PROMPT_ROW_HEIGHT = CHAR_HEIGHT + LINE_SPACING
CONTROL_ZONE_HEIGHT = 1
LEGEND_AREA_WIDTH = 60
LEGEND_ITEM_HEIGHT = 8

# --- Pixel Colors (RGB tuples - MUST match snapshot_generator_code) ---
COLOR_BACKGROUND = (0, 0, 0) # Black
COLOR_GRID_LINE = (50, 50, 50) # Dark Grey
COLOR_AGENT = (0, 0, 255) # Blue
COLOR_GOAL = (0, 255, 0) # Green
COLOR_PROMPT_TEXT_ON = (255, 255, 255) # White for text pixels
COLOR_PROMPT_TEXT_OFF = (0, 0, 0) # Black for background text pixels (within char block)
COLOR_CONTROL_OPCODE = (255, 0, 255) # Magenta for command pixel (ColorShim)
COLOR_PYTHON_REQUEST = (255, 165, 0) # Orange for PYTHON_REQUEST signal
COLOR_LEGEND_TEXT = (200, 200, 200) # Light grey for legend text

# --- Simplified 3x5 pixel font for text decoding (MUST match snapshot_generator_code) ---
PIXEL_FONT = {
    "000000000000000": ' ', # 3x5 all off
    "010101111101101": 'A', "110101110101110": 'B', "011100100100011": 'C',
    "110101101101110": 'D', "111100110100111": 'E', "111100110100100": 'F',
    "011100101101011": 'G', "101101111101101": 'H', "111010010010111": 'I',
    "011001001101011": 'J', "101101110101101": 'K', "100100100100111": 'L',
    "101111101101101": 'M', "101101111101101": 'N', "011101101101011": 'O',
    "110101110100100": 'P', "011101101111001": 'Q', "110101110101101": 'R',
    "011100010001110": 'S', "111010010010010": 'T', "101101101101011": 'U',
    "101101101010010": 'V', "101101101111101": 'W', "101010010010101": 'X',
    "101010010010010": 'Y', "111001010100111": 'Z',
    "000000000000010": '.', "010010010000010": '!', "110001010000010": '?',
    "000010000010000": ':', "000000010010000": ',', "000000111000000": '-',
    "011101101101011": '0', "010110010010111": '1', "110001010100111": '2',
    "111001011001111": '3', "100100111001001": '4', "111100111001111": '5',
    "011100111101011": '6', "111001010010010": '7', "011101011101011": '8',
    "011101111001011": '9',
}

# Invert PIXEL_FONT for easy encoding from RGB to char
PIXEL_FONT_REVERSE = {
    "".join(row_pattern): char for char, rows in PIXEL_FONT.items() 
    for row_pattern in [("".join(rows))] # Flatten to single string key
}

class CanvasInterpreter:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.img = None
        self.pixels = None
        self.width = 0
        self.height = 0
        self._load_image()

    def _load_image(self):
        """Loads the image and gets pixel access."""
        if not os.path.exists(self.image_path):
            raise FileNotFoundError(f"Image not found at: {self.image_path}")
        self.img = Image.open(self.image_path).convert('RGB')
        self.pixels = self.img.load()
        self.width, self.height = self.img.size

    def _get_pixel_color(self, x: int, y: int) -> Tuple[int, int, int]:
        """Gets the RGB color of a pixel at (x, y). Handles out-of-bounds."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.pixels[x, y]
        return COLOR_BACKGROUND # Return black for out-of-bounds

    def _decode_pixel_text(self, x_start: int, y_start: int, max_width: int) -> str:
        """Decodes pixel-art text from a given area."""
        decoded_text = ""
        current_x = x_start
        while current_x < x_start + max_width:
            char_pattern_str = ""
            is_empty_column = True
            for row_idx in range(CHAR_HEIGHT):
                for col_idx in range(CHAR_WIDTH):
                    px_x = current_x + col_idx
                    px_y = y_start + row_idx
                    color = self._get_pixel_color(px_x, px_y)
                    if color == COLOR_PROMPT_TEXT_ON:
                        char_pattern_str += '1'
                        is_empty_column = False
                    elif color == COLOR_PROMPT_TEXT_OFF:
                        char_pattern_str += '0'
                    else:
                        # If it's not a text pixel color, it's likely background or end of text
                        char_pattern_str += '0' # Treat as off for pattern matching

            # Check if this 3x5 block is entirely background (space)
            if all(self._get_pixel_color(current_x + cx, y_start + ry) == COLOR_BACKGROUND 
                   for ry in range(CHAR_HEIGHT) for cx in range(CHAR_WIDTH)):
                if decoded_text and decoded_text[-1] != ' ': # Avoid multiple spaces
                    decoded_text += ' '
            else:
                # Try to find the character in the font map
                char = PIXEL_FONT_REVERSE.get(char_pattern_str, '?') # Default to '?' if not found
                decoded_text += char
            
            current_x += CHAR_WIDTH + CHAR_SPACING
            if current_x >= self.width: # Stop if we hit image boundary
                break

            # Heuristic to stop if we hit a long sequence of background pixels after text
            if len(decoded_text) > 0 and decoded_text[-1] != ' ':
                next_char_start_x = current_x
                is_end_of_text = True
                for ry in range(CHAR_HEIGHT):
                    for cx_offset in range(CHAR_WIDTH + CHAR_SPACING):
                        if self._get_pixel_color(next_char_start_x + cx_offset, y_start + ry) != COLOR_BACKGROUND:
                            is_end_of_text = False
                            break
                    if not is_end_of_text:
                        break
                if is_end_of_text and (current_x - x_start) > CHAR_WIDTH * 2: # Ensure some text was read
                    break

        return decoded_text.strip() # Remove leading/trailing spaces


    def interpret_snapshot(self) -> Dict[str, Any]:
        """Interprets the entire snapshot and returns a structured state."""
        
        interpreted_state = {
            "filename": os.path.basename(self.image_path),
            "image_dimensions": {"width": self.width, "height": self.height},
            "prompt_text": "",
            "grid_state": [], # List of (x, y, color) for non-background/gridline pixels
            "agent_position": None,
            "goal_zone": [],
            "control_zone_signals": [],
            "covenant_hash": None,
            "raw_pixel_data": {} # Optional: for debugging or full pixel access
        }

        # --- 1. Interpret Prompt Row ---
        prompt_max_width = self.width - LEGEND_AREA_WIDTH # Prompt is left of legend
        interpreted_state["prompt_text"] = self._decode_pixel_text(0, 0, prompt_max_width)

        # --- 2. Interpret Grid Area ---
        grid_start_y = PROMPT_ROW_HEIGHT
        grid_width_actual = self.width - LEGEND_AREA_WIDTH # Grid is left of legend
        grid_height_actual = self.height - PROMPT_ROW_HEIGHT - CONTROL_ZONE_HEIGHT - LINE_SPACING # Grid height

        for y in range(grid_start_y, grid_start_y + grid_height_actual):
            for x in range(grid_width_actual):
                color = self._get_pixel_color(x, y)
                # Store only non-background and non-gridline pixels
                if color != COLOR_BACKGROUND and color != COLOR_GRID_LINE:
                    # Adjust y-coordinate to be relative to grid top-left (0,0)
                    relative_y = y - grid_start_y
                    interpreted_state["grid_state"].append({"x": x, "y": relative_y, "color": color})

                    if color == COLOR_AGENT:
                        interpreted_state["agent_position"] = {"x": x, "y": relative_y}
                    elif color == COLOR_GOAL:
                        interpreted_state["goal_zone"].append({"x": x, "y": relative_y})
                
                # Optional: Store all raw pixel data if needed
                # interpreted_state["raw_pixel_data"][f"{x},{y}"] = color

        # --- 3. Interpret Control Zone ---
        control_zone_y_start = grid_start_y + grid_height_actual
        for x in range(grid_width_actual): # Control zone also left of legend
            color = self._get_pixel_color(x, control_zone_y_start)
            if color == COLOR_CONTROL_OPCODE:
                interpreted_state["control_zone_signals"].append({"x": x, "y": 0, "color": color, "type": "CONTROL_OPCODE"})
            elif color == COLOR_PYTHON_REQUEST:
                interpreted_state["control_zone_signals"].append({"x": x, "y": 0, "color": color, "type": "PYTHON_REQUEST"})
            # Add other control signals here as they are defined

        # --- 4. Interpret Covenant Hash (bottom-right 3 pixels) ---
        if self.width >= 3 and self.height >= 3: # Ensure enough space for hash pixels
            hash_pixel_1 = self._get_pixel_color(self.width - 1, self.height - 1)
            hash_pixel_2 = self._get_pixel_color(self.width - 2, self.height - 1)
            hash_pixel_3 = self._get_pixel_color(self.width - 1, self.height - 2)
            
            # Simple reconstruction based on how it was encoded
            # This assumes the hash values are small enough not to overflow byte values
            covenant_r = hash_pixel_1[0]
            covenant_g = hash_pixel_2[1]
            covenant_b = hash_pixel_3[2]
            
            # Reconstruct the original integer value (simplified for demo)
            # This is a basic example; a real hash would use a cryptographic hash of the image content
            interpreted_state["covenant_hash"] = (covenant_b * (256*256)) + (covenant_g * 256) + covenant_r
            # For a true hash, you'd hash the image data and compare.
            # Here, we're just reading back the encoded integer.

        return interpreted_state

# --- Example Usage ---
if __name__ == "__main__":
    # Ensure you have run snapshot_generator_code.py to create these files
    # and that the 'coloros_pxl_snapshots' folder is in the same directory.
    snapshot_dir = "coloros_pxl_snapshots"

    print("--- Testing Canvas Interpreter ---")

    # Test Snapshot 001: Color OS Intro
    print("\n--- Interpreting snapshot_001_intro.pxl.png ---")
    interpreter1 = CanvasInterpreter(os.path.join(snapshot_dir, "snapshot_001_intro.pxl.png"))
    state1 = interpreter1.interpret_snapshot()
    print(json.dumps(state1, indent=2))
    assert state1["prompt_text"] == "YOU ARE INSIDE COLOR OS."
    assert state1["agent_position"] == {"x": 5, "y": 5}
    print("Interpretation for snapshot_001_intro.pxl.png: SUCCESS")

    # Test Snapshot 002: Navigation Mission
    print("\n--- Interpreting snapshot_002_navigation.pxl.png ---")
    interpreter2 = CanvasInterpreter(os.path.join(snapshot_dir, "snapshot_002_navigation.pxl.png"))
    state2 = interpreter2.interpret_snapshot()
    print(json.dumps(state2, indent=2))
    assert state2["prompt_text"] == "MOVE TO THE GREEN ZONE. REPORT EACH STEP."
    assert state2["agent_position"] == {"x": 2, "y": 2}
    assert len(state2["goal_zone"]) == 4 # 2x2 goal zone
    print("Interpretation for snapshot_002_navigation.pxl.png: SUCCESS")

    # Test Snapshot 003: ColorShim Activation
    print("\n--- Interpreting snapshot_003_colorshim.pxl.png ---")
    interpreter3 = CanvasInterpreter(os.path.join(snapshot_dir, "snapshot_003_colorshim.pxl.png"))
    state3 = interpreter3.interpret_snapshot()
    print(json.dumps(state3, indent=2))
    assert state3["prompt_text"] == "ACTIVATE COLORSHIM PROTOCOL."
    assert state3["agent_position"] == {"x": 7, "y": 7}
    assert any(s["type"] == "CONTROL_OPCODE" for s in state3["control_zone_signals"])
    assert any(s["type"] == "PYTHON_REQUEST" for s in state3["control_zone_signals"])
    print("Interpretation for snapshot_003_colorshim.pxl.png: SUCCESS")

    print("\nAll Canvas Interpreter tests passed successfully!")


# scroll_runner_daemon.py

import time
import os
import logging
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil # For moving files to processed/error directories

from eight_png_manager import EightPNGManager
from pixel_zones import get_zone_coordinates, PIXEL_ZONES # Import get_zone_coordinates and PIXEL_ZONES
from ai_brain import simple_ai_query # Import our AI brain (now potentially Gemini)

# --- Configuration ---
SCROLLS_DIR = 'scrolls'
PROCESSED_SCROLLS_DIR = os.path.join(SCROLLS_DIR, "processed")
ERROR_SCROLLS_DIR = os.path.join(SCROLLS_DIR, "error")
OUTPUT_DIR = 'output' # General output directory (e.g., for AI responses, logs)
LOG_FILE = 'scroll_runner_daemon.log'
EIGHT_PNG_PATH = '8.png'

# --- Set up logging ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(LOG_FILE),
                        logging.StreamHandler()
                    ])

# Ensure directories exist
os.makedirs(SCROLLS_DIR, exist_ok=True)
os.makedirs(PROCESSED_SCROLLS_DIR, exist_ok=True)
os.makedirs(ERROR_SCROLLS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "ai_responses"), exist_ok=True) # For AI_QUERY output files

class ScrollEventHandler(FileSystemEventHandler):
    """
    Handles file system events (e.g., file creation, modification) for scrolls.
    """
    def __init__(self, runner_func):
        super().__init__()
        self.runner_func = runner_func
        self.processed_files = set() # To prevent reprocessing files on every event

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.pxl'):
            self.process_scroll(event.src_path)

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.pxl'):
            self.process_scroll(event.src_path)

    def process_scroll(self, scroll_path):
        # Basic debouncing: wait a moment to ensure file is fully written
        time.sleep(0.5) # Increased sleep slightly for better stability on file writes
        if scroll_path not in self.processed_files:
            logging.info(f"Detected new or modified scroll: {scroll_path}")
            self.runner_func(scroll_path)
            self.processed_files.add(scroll_path)
            # Remove from processed_files after a short delay to allow re-processing on subsequent changes
            # For a production system, consider file hashing or a more robust debouncing mechanism
            time.sleep(0.5) # Wait for processing to potentially complete before allowing re-detection
            self.processed_files.discard(scroll_path)


def parse_pxl_command(line):
    """Parses a single line from a .pxl file for key-value pairs."""
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    match = re.match(r'([A-Z_]+):\s*(.*)', line)
    if match:
        key = match.group(1)
        value = match.group(2).strip()
        return key, value
    return None

def hex_to_rgb(hex_color):
    """Converts a hex color string (e.g., 'FF0000') to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def execute_pixel_scroll(scroll_path):
    """
    Executes a .pxl scroll by parsing its commands and
    manipulating the 8.png image, using named zones, and performing file operations.
    """
    scroll_name = os.path.basename(scroll_path)
    logging.info(f"Executing scroll: {scroll_name}")

    manager = EightPNGManager(image_path=EIGHT_PNG_PATH)
    manager.load_image()

    scroll_success = True # Track if the scroll executed without major errors
    try:
        with open(scroll_path, 'r') as f:
            scroll_content_lines = f.readlines()

        commands_list = [] # Store all parsed key-value pairs
        for line in scroll_content_lines:
            parsed = parse_pxl_command(line)
            if parsed:
                commands_list.append(parsed)

        # Extract overall scroll metadata/target before processing commands
        # TARGET_ZONE is the *default* zone for commands within this scroll
        target_zone_name = None
        for key, value in commands_list:
            if key == "TARGET_ZONE": # Look for top-level TARGET_ZONE
                target_zone_name = value.upper()
                logging.debug(f"Scroll's default TARGET_ZONE set to: {target_zone_name}")
                break # Assuming TARGET_ZONE is defined once at the top if used globally

        # Process commands block-by-block
        current_command_type = None
        command_params = {}

        for key, value in commands_list:
            if key == "COMMAND":
                # If there was a previous command block, process it
                if current_command_type:
                    # Renamed to process_command as it now handles more than just drawing
                    if not process_command(current_command_type, command_params, manager, target_zone_name):
                        scroll_success = False # Mark scroll as failed if a command fails
                current_command_type = value
                command_params = {} # Reset params for the new command
            elif current_command_type: # Accumulate parameters for the current command
                command_params[key] = value
            elif key == "CONSOLE_LOG":
                logging.info(f"Scroll Console Log: {value}")
            # Other root-level directives (like OUTPUT_TO_8PNG_ZONE) are handled specifically below

        # Process the last command if any
        if current_command_type:
            if not process_command(current_command_type, command_params, manager, target_zone_name):
                scroll_success = False


        # Handle specific OUTPUT_TO_8PNG_ZONE directives after all general commands are processed
        for key, value in commands_list:
            if key == "OUTPUT_TO_8PNG_ZONE":
                zone_to_output = value.upper()
                output_text = None
                output_color = "FFFFFF"

                current_block_index = commands_list.index((key,value))
                for i in range(current_block_index + 1, len(commands_list)):
                    param_key, param_value = commands_list[i]
                    if param_key == "OUTPUT_TEXT":
                        output_text = param_value
                    elif param_key == "OUTPUT_COLOR":
                        output_color = param_value
                    if param_key in ["COMMAND", "OUTPUT_TO_8PNG_ZONE", "TARGET_ZONE", "CONSOLE_LOG"]: # Stop at next major directive
                        break
                    if output_text is not None and output_color is not None: # Found both, break early
                        break

                if output_text:
                    try:
                        # Clear the zone before writing to prevent overlaying
                        manager.clear_zone(zone_name=zone_to_output, color=(0,0,0)) # Clear with black
                        final_text = output_text.replace("TIMESTAMP", time.strftime("%H:%M:%S"))
                        manager.write_text(final_text, 5, 5, font_size=16, color=hex_to_rgb(output_color), zone_name=zone_to_output)
                        logging.info(f"Updated 8.png zone '{zone_to_output}' with: '{final_text}'")
                    except KeyError:
                        logging.error(f"Error: OUTPUT_TO_8PNG_ZONE '{zone_to_output}' not defined in pixel_zones.py")
                        scroll_success = False
                else:
                    logging.warning(f"OUTPUT_TO_8PNG_ZONE '{zone_to_output}' specified but no OUTPUT_TEXT found.")
        
        manager.save_image() # Save changes to 8.png

    except Exception as e:
        logging.error(f"Error executing scroll {scroll_name}: {e}", exc_info=True)
        scroll_success = False
    
    # Move the scroll file after execution
    if scroll_success:
        shutil.move(scroll_path, os.path.join(PROCESSED_SCROLLS_DIR, scroll_name))
        logging.info(f"Moved processed scroll to: {os.path.join(PROCESSED_SCROLLS_DIR, scroll_name)}")
    else:
        shutil.move(scroll_path, os.path.join(ERROR_SCROLLS_DIR, scroll_name))
        logging.error(f"Moved failed scroll to: {os.path.join(ERROR_SCROLLS_DIR, scroll_name)}")


def process_command(command_type, params, manager, default_scroll_zone=None) -> bool:
    """
    Processes various command types (drawing, file operations, AI queries, etc.).
    A command's TARGET_ZONE parameter overrides the scroll's default_scroll_zone for drawing.
    Returns True on success, False on failure.
    """
    # Determine the actual zone to use for this specific command (primarily for drawing commands)
    command_specific_zone = params.get("TARGET_ZONE", default_scroll_zone)
    if command_specific_zone:
        command_specific_zone = command_specific_zone.upper() # Ensure uppercase consistency

    try:
        if command_type == "WRITE_TEXT":
            text = params.get("TEXT", "")
            x = int(params.get("X", 0))
            y = int(params.get("Y", 0))
            font_size = int(params.get("FONT_SIZE", 12))
            color_rgb = hex_to_rgb(params.get("COLOR", "FFFFFF"))
            manager.write_text(text, x, y, font_size, color_rgb, zone_name=command_specific_zone)

        elif command_type == "DRAW_RECTANGLE":
            x1 = int(params.get("X", 0))
            y1 = int(params.get("Y", 0))
            width = int(params.get("WIDTH", 0))
            height = int(params.get("HEIGHT", 0))
            x2 = x1 + width
            y2 = y1 + height
            fill = params.get("FILL", "False").lower() == "true"
            color_rgb = hex_to_rgb(params.get("COLOR", "FFFFFF"))
            manager.draw_rectangle(x1, y1, x2, y2, color_rgb, fill, zone_name=command_specific_zone)

        elif command_type == "CLEAR_ZONE":
            zone_to_clear = params.get("ZONE_NAME", command_specific_zone)
            if not zone_to_clear:
                 logging.warning(f"CLEAR_ZONE command requires a 'ZONE_NAME' parameter or a default target zone must be set for the scroll.")
                 return False
            clear_color_hex = params.get("COLOR", "000000")
            clear_color_rgb = hex_to_rgb(clear_color_hex)
            manager.clear_zone(zone_name=zone_to_clear.upper(), color=clear_color_rgb)

        elif command_type == "WRITE_FILE":
            file_path_relative = params.get("FILE_PATH")
            content = params.get("CONTENT", "")
            mode = params.get("MODE", "OVERWRITE").lower() # Default to overwrite

            if not file_path_relative:
                logging.error("WRITE_FILE command missing FILE_PATH parameter.")
                return False

            full_file_path = os.path.join(OUTPUT_DIR, file_path_relative)
            os.makedirs(os.path.dirname(full_file_path), exist_ok=True)

            write_mode = 'w' if mode == 'overwrite' else 'a'

            with open(full_file_path, write_mode) as f:
                f.write(content)
            logging.info(f"Successfully wrote to file: {full_file_path} (Mode: {mode})")

        elif command_type == "AI_QUERY":
            prompt = params.get("PROMPT")
            output_target_file = params.get("OUTPUT_FILE") # File to save AI response
            output_target_zone = params.get("OUTPUT_ZONE") # Zone on 8.png to display response
            output_color_hex = params.get("OUTPUT_COLOR", "FFFFFF")
            output_color_rgb = hex_to_rgb(output_color_hex)
            display_length = int(params.get("DISPLAY_LENGTH", 100))
            output_scroll_path = params.get("OUTPUT_SCROLL_PATH") 

            if not prompt:
                logging.error("AI_QUERY command missing PROMPT parameter.")
                return False

            logging.info(f"Sending prompt to AI: '{prompt}'")
            ai_response = simple_ai_query(prompt) # Call the AI brain
            logging.info(f"AI response received (first 100 chars): '{ai_response[:100]}'")

            if ai_response.startswith("ERROR:"): # Handle AI errors
                logging.error(f"AI_QUERY failed: {ai_response}")
                return False

            # Write AI response to file if specified
            if output_target_file:
                ai_output_dir = os.path.join(OUTPUT_DIR, "ai_responses")
                os.makedirs(ai_output_dir, exist_ok=True)
                full_ai_file_path = os.path.join(ai_output_dir, output_target_file)
                
                with open(full_ai_file_path, 'w') as f:
                    f.write(ai_response)
                logging.info(f"AI response written to: {full_ai_file_path}")

            # Write AI response as a new scroll if specified
            if output_scroll_path:
                full_scroll_path = os.path.join(SCROLLS_DIR, output_scroll_path)
                os.makedirs(os.path.dirname(full_scroll_path), exist_ok=True)

                if ai_response.strip().startswith("# PXLSCROLL_ID:") or ai_response.strip().startswith("COMMAND:"):
                    with open(full_scroll_path, 'w') as f:
                        f.write(ai_response)
                    logging.info(f"AI-generated scroll deployed to: {full_scroll_path}. Daemon will auto-execute!")
                else:
                    logging.warning(f"AI response for OUTPUT_SCROLL_PATH '{output_scroll_path}' does not look like a PXL scroll. Not deploying.")

            # Display AI response in 8.png zone if specified
            if output_target_zone:
                try:
                    manager.clear_zone(zone_name=output_target_zone.upper(), color=(0,0,0))
                    display_text = f"AI: {ai_response[:display_length]}"
                    if len(ai_response) > display_length:
                        display_text += "..."
                    manager.write_text(display_text, 5, 5, font_size=14, color=output_color_rgb, zone_name=output_target_zone.upper())
                    logging.info(f"AI response displayed in zone '{output_target_zone.upper()}'")
                except KeyError:
                    logging.error(f"Error: AI_QUERY OUTPUT_ZONE '{output_target_zone}' not defined in pixel_zones.py")
                    return False
            return True # AI_QUERY command successfully processed

        else:
            logging.warning(f"Unknown command type: {command_type} with params: {params}")
            return False # Unknown command implies failure
    except ValueError as ve:
        logging.error(f"Invalid parameter for command {command_type}: {ve}. Params: {params}", exc_info=True)
        return False
    except Exception as e:
        logging.error(f"Error processing command {command_type}: {e}", exc_info=True)
        return False


def start_daemon():
    """
    Starts the scroll runner daemon.
    """
    logging.info("Starting Pixel Scroll Runner Daemon...")

    # Ensure all configured directories exist
    os.makedirs(SCROLLS_DIR, exist_ok=True)
    os.makedirs(PROCESSED_SCROLLS_DIR, exist_ok=True)
    os.makedirs(ERROR_SCROLLS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "ai_responses"), exist_ok=True) # Ensure AI responses directory exists

    logging.info(f"Watching for scrolls in: {os.path.abspath(SCROLLS_DIR)}")
    logging.info(f"Processed scrolls moved to: {os.path.abspath(PROCESSED_SCROLLS_DIR)}")
    logging.info(f"Error scrolls moved to: {os.path.abspath(ERROR_SCROLLS_DIR)}")
    logging.info(f"Output directory for generated files: {os.path.abspath(OUTPUT_DIR)}")
    logging.info(f"8.png will be managed at: {os.path.abspath(EIGHT_PNG_PATH)}")

    # Initialize 8.png manager to ensure 8.png exists at startup
    initial_manager = EightPNGManager(image_path=EIGHT_PNG_PATH)
    initial_manager.load_image() # This will create 8.png if it doesn't exist

    # Perform initial clear of key zones and display startup message
    try:
        if PIXEL_ZONES.get("STATUS_BAR"):
            initial_manager.clear_zone(zone_name="STATUS_BAR", color=(0,0,0))
            initial_manager.write_text("Daemon Initialized. Awaiting Scrolls...", 5, 5, font_size=16, color=(0,255,0), zone_name="STATUS_BAR")
        if PIXEL_ZONES.get("MAIN_CONTENT"):
            initial_manager.clear_zone(zone_name="MAIN_CONTENT", color=(0,0,0))
            initial_manager.write_text("Drop .pxl files into /scrolls/", 10, 10, font_size=20, color=(255,255,255), zone_name="MAIN_CONTENT")
        initial_manager.save_image()
        logging.info("Initial 8.png display updated.")
    except Exception as e:
        logging.error(f"Error during initial 8.png setup: {e}", exc_info=True)


    event_handler = ScrollEventHandler(execute_pixel_scroll)
    observer = Observer()
    observer.schedule(event_handler, SCROLLS_DIR, recursive=False) # Only watch top level for .pxl files
    observer.start()

    try:
        while True:
            time.sleep(1) # Keep the main thread alive
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Pixel Scroll Runner Daemon stopped.")
    observer.join()

if __name__ == "__main__":
    start_daemon()

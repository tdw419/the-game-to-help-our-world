# pixelnet_transmitter.py

import serial # This library needs to be installed: pip install pyserial
import binascii # For converting hex strings to bytes
import time
import logging
import os

# --- Configuration ---
PIXELNET_SERIAL_PORT = os.getenv("PIXELNET_SERIAL_PORT", "/dev/ttyUSB0")  # Change as needed (e.g., 'COM3' on Windows)
PIXELNET_BAUD_RATE = int(os.getenv("PIXELNET_BAUD_RATE", "115200"))       # Typical baud for PixelNet
PIXELNET_FRAME_DELAY = 0.05  # 50ms between frames for hardware stability

# --- Setup logging (ensure this does not conflict with main app's logging setup) ---
# For standalone running, enable this. For integration, main app logs.
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Global serial port object ---
_serial_port = None

def _initialize_serial_port():
    """
    Initializes and returns the serial port object.
    Uses a global variable to avoid re-initializing if already open.
    """
    global _serial_port
    if _serial_port is None or not _serial_port.is_open:
        try:
            _serial_port = serial.Serial(
                port=PIXELNET_SERIAL_PORT,
                baudrate=PIXELNET_BAUD_RATE,
                timeout=0.1 # Read timeout in seconds
            )
            logging.info(f"DEBUG: Successfully opened serial port {PIXELNET_SERIAL_PORT}")
        except serial.SerialException as e:
            logging.error(f"ERROR: Could not open serial port {PIXELNET_SERIAL_PORT}: {e}")
            _serial_port = None # Ensure it's None if opening fails
        except Exception as e:
            logging.error(f"ERROR: Unexpected error opening serial port {PIXELNET_SERIAL_PORT}: {e}")
            _serial_port = None
    return _serial_port

def send_pixelnet_frame(hex_data_string):
    """
    Parses a hexadecimal color sequence string and sends it as bytes
    over the configured serial port (PixelNet bus).

    Args:
        hex_data_string (str): A string of hexadecimal characters representing
                                RGB data (e.g., "FF000000FF000000FF" for Red, Green, Blue pixels).
                                Must be an even number of characters.

    Returns:
        bool: True if data was successfully sent, False otherwise.
    """
    if not hex_data_string:
        logging.warning("WARNING: No hexadecimal data provided to send_pixelnet_frame.")
        return False

    if len(hex_data_string) % 2 != 0:
        logging.error(f"ERROR: Invalid hex data length. Must be even: {hex_data_string}")
        return False

    # Initialize serial port if not already open
    ser = _initialize_serial_port()
    if ser is None:
        logging.error("ERROR: Serial port not available. Cannot send PixelNet frame.")
        return False

    try:
        # Convert hex string to bytes
        data_bytes = binascii.unhexlify(hex_data_string)

        # Construct the full frame: [START_BYTE][DATA_BYTES...]
        # Assuming a simple protocol where 0xAA (170 decimal) is a start byte
        PIXELNET_START_BYTE = 0xAA # Defined locally or from a config
        frame_to_send = bytes([PIXELNET_START_BYTE]) + data_bytes

        logging.info(f"DEBUG: Attempting to send {len(frame_to_send)} bytes to PixelNet:")
        logging.debug(f"DEBUG: Hex to send: {frame_to_send.hex().upper()}") # Use debug for raw hex

        ser.write(frame_to_send)
        time.sleep(PIXELNET_FRAME_DELAY) # Optional: Add a small delay if your hardware needs time between frames
        logging.info("DEBUG: PixelNet frame sent successfully (simulated/actual).")
        return True
    except binascii.Error as e:
        logging.error(f"ERROR: Invalid hexadecimal data provided: {hex_data_string} - {e}")
        return False
    except Exception as e:
        logging.error(f"ERROR: Failed to send data over serial port: {e}", exc_info=True)
        return False

def close_serial_port():
    """
    Closes the serial port if it's open.
    """
    global _serial_port
    if _serial_port and _serial_port.is_open:
        logging.info(f"DEBUG: Closing serial port {PIXELNET_SERIAL_PORT}.")
        _serial_port.close()
    _serial_port = None

# --- Simulation / Testing for standalone execution ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s") # Enable logging for standalone test
    logging.info("--- Testing pixelnet_transmitter.py (simulated) ---")
    logging.info("NOTE: This test will attempt to open a real serial port if configured.")
    logging.info("      If no port is available, it will report an error.")

    # Example 1: Send 3 Red pixels
    test_hex_data_1 = "FF0000FF0000FF0000" # R, R, R (3 pixels)
    logging.info(f"\nAttempting to send frame 1: {test_hex_data_1}")
    send_pixelnet_frame(test_hex_data_1)

    # Example 2: Send the sequence from the AI-generated scroll (Red, Blue, Green for 6 pixels)
    test_hex_data_2 = "FF0000FF00000000FF0000FF00FF0000FF00"
    logging.info(f"\nAttempting to send frame 2 (AI-generated example): {test_hex_data_2}")
    send_pixelnet_frame(test_hex_data_2)

    # Example 3: Invalid hex data
    test_hex_data_invalid = "FF00GGOO"
    logging.info(f"\nAttempting to send invalid frame: {test_hex_data_invalid}")
    send_pixelnet_frame(test_hex_data_invalid)

    # Example 4: Empty data
    test_hex_data_empty = ""
    logging.info(f"\nAttempting to send empty frame: {test_hex_data_empty}")
    send_pixelnet_frame(test_hex_data_empty)

    # Always close the port when done
    close_serial_port()

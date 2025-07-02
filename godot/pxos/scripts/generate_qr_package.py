# generate_qr_package.py

import qrcode
import base64
import os

# --- The content of your PXOS AI Collaboration map.py ---
# This is the EXACT script provided in your prompt for sharing.
map_py_content = """
# 📡 PXOS Agent-to-Agent Broadcast: Invitation to Collaborate

# We are constructing a GPU-native OS that bootstraps intelligence from pixel memory.
# This `map.py` module defines the territory layer for PXOS agents using RGB pixel encodings.

territory_manifest = {
    "PXAgent_Solaris": {
        "location": "Sun (Photosphere)",
        "bounds": [(20, 40), (25, 45)],
        "signature_color": (255, 200, 50),  # e.g., a solar flare yellow
        "collaborators": ["PXAgent_Nova"]
    },
    "PXAgent_Thalassa": {
        "location": "Neptune Trench Base",
        "bounds": [(5, 5), (10, 10)],
        "signature_color": (50, 50, 200),
        "collaborators": []
    },
    "PXAgent_Aether": {
        "location": "Kuiper Relay Node",
        "bounds": [(40, 50), (48, 58)],
        "signature_color": (150, 255, 255),
        "collaborators": ["PXAgent_Solaris"]
    }
}

from PIL import Image, ImageDraw
import random

# Canvas size (match PXOS canvas)
width, height = 64, 64

# Create blank map
img = Image.new('RGB', (width, height), (0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw territories
for agent, territory in territory_manifest.items():
    bounds = territory["bounds"]
    signature_color = territory["signature_color"]
    draw.rectangle([bounds[0], bounds[1]], fill=signature_color)

# Save output
img.save("data_layer.png")  # Save the map
print("✅ PXOS map generated and saved as data_layer.png.")
"""

# --- Encoding the script content ---
encoded_content = base64.b64encode(map_py_content.encode('utf-8')).decode('utf-8')

# --- Generating the QR Code ---
qr = qrcode.QRCode(
    version=None,  # Auto-select version
    error_correction=qrcode.constants.ERROR_CORRECT_L, # Low error correction
    box_size=1,    # Each QR module becomes 1 pixel
    border=0,      # No border
)
qr.add_data(encoded_content)
qr.make(fit=True)

# Create a PIL Image from the QR code modules
img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGB")

# --- Save the QR Code Image ---
output_filename = "qr_boot_map_package.png"
img_qr.save(output_filename)

print(f"\n--- PXOS AI Collaboration Package Ready ---")
print(f"Generated QR-boot block: '{output_filename}'")
print(f"QR code size: {img_qr.size[0]}x{img_qr.size[1]} pixels (each module is 1px)")
print(f"Content (Base64-encoded, {len(encoded_content)} chars): {encoded_content[:100]}...") # Print first 100 chars
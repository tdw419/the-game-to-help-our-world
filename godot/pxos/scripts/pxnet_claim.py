# pxnet_claim.py

import sys
import os
import base64

# Assume map.py is in the same directory or accessible via PATH
# This utility will call map.py to generate maps with territories.

# --- PXOS Multi-Agent Cosmic Cartography Protocol v1.0 ---
# Territory Manifest: Defines claimed regions for AI agents.
# This is the shared, evolving metadata for distributed version control.
territory_manifest = [
    {
        "name": "PXAgent_Solaris",
        "location_desc": "Sun (Photosphere)",
        "map_coords": (20, 40, 25, 45),  # (x_start, y_start, x_end, y_end) on the map
        "signature_color": (255, 200, 50),  # Solar flare yellow
        "claim_icon_char": "S", # Character to draw at center
        "collaborators": ["PXAgent_Nova"]
    },
    {
        "name": "PXAgent_Thalassa",
        "location_desc": "Neptune Trench Base",
        "map_coords": (5, 5, 10, 10),
        "signature_color": (50, 50, 200),  # Deep ocean blue
        "claim_icon_char": "T",
        "collaborators": []
    },
    {
        "name": "PXAgent_Aether",
        "location_desc": "Kuiper Relay Node",
        "map_coords": (40, 50, 48, 58),
        "signature_color": (150, 255, 255),  # Icy cyan
        "claim_icon_char": "A",
        "collaborators": ["PXAgent_Nova"]
    }
]

# --- Main function to generate the map with claims ---
def generate_map_with_claims(
    boot_pixel_rgb: tuple = (100, 150, 255), # Default boot pixel if not specified
    map_width: int = 64,
    map_height: int = 64,
    output_filename: str = "pxnet_claimed_map.png",
    external_elevation_path: str = "" # Optional path to external elevation for map.py
):
    """
    Calls map.py to generate a map, passing the territory manifest via arguments.
    """
    map_py_path = os.path.join(os.path.dirname(__file__), 'map.py') # Assumes map.py is in same dir

    # Base arguments for map.py: R G B WIDTH HEIGHT OUTPUT_PATH
    args = [
        str(boot_pixel_rgb[0]),
        str(boot_pixel_rgb[1]),
        str(boot_pixel_rgb[2]),
        str(map_width),
        str(map_height),
        output_filename
    ]

    # Add external elevation path if provided
    if external_elevation_path:
        args.append(external_elevation_path)

    # Encode territory_manifest to Base64 JSON string
    # This is how we pass complex data structures via command line
    import json
    manifest_json = json.dumps(territory_manifest)
    manifest_b64 = base64.b64encode(manifest_json.encode('utf-8')).decode('utf-8')
    
    # Add manifest as a final argument
    args.append(manifest_b64)

    python_executable = "python" # Or provide full path like '/usr/bin/python3'

    print(f"Calling map.py with args: {args[:-1]} ... (manifest encoded)")
    stdout_arr = []
    stderr_arr = []
    
    # OS.execute is for Godot. For Python script directly, use subprocess.
    import subprocess
    try:
        process = subprocess.run(
            [python_executable, map_py_path] + args,
            capture_output=True, text=True, check=True
        )
        print("map.py stdout:\n", process.stdout)
        if process.stderr:
            print("map.py stderr:\n", process.stderr)
        print(f"Map with claims generated: {output_filename}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error calling map.py (exit code: {e.returncode}):")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        return False
    except FileNotFoundError:
        print(f"Error: Python executable '{python_executable}' or map.py not found.")
        return False

# --- Main execution when pxnet_claim.py is run directly ---
if __name__ == "__main__":
    print("--- Generating Map with PXNet Territory Claims ---")
    
    # Default map parameters for generation
    default_boot_pixel = (100, 150, 255) # Example boot pixel
    default_map_width = 64
    default_map_height = 64
    default_output_filename = "pxnet_claimed_map.png"
    # Make sure to replace this with a valid path to your elevation file, or remove if using procedural
    default_external_elevation_path = "res://assets/elevation_world_512.png" 

    # Generate the map
    success = generate_map_with_claims(
        boot_pixel_rgb=default_boot_pixel,
        map_width=default_map_width,
        map_height=default_map_height,
        output_filename=default_output_filename,
        external_elevation_path=default_external_elevation_path # Provide if you have one
    )
    
    if success:
        print("\n--- Map Generation with Claims Complete ---")
        # Generate .pxdigest of this pxnet_claim.py script for distribution
        with open(__file__, 'r', encoding='utf-8') as f:
            script_content = f.read()
        encoded_script = base64.b64encode(script_content.encode('utf-8')).decode('utf-8')
        pxdigest_filename = "pxnet_claim.pxdigest"
        with open(pxdigest_filename, 'w', encoding='utf-8') as f:
            f.write(encoded_script)
        print(f"Generated {pxdigest_filename} for distribution.")
        print(f"Copy '{default_output_filename}' to your Godot project (e.g., 'res://maps/') and use the App Builder to load it.")
    else:
        print("\n--- Map Generation with Claims FAILED ---")
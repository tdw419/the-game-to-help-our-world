# pixel_zones.py

# Define named pixel zones on the 8.png canvas.
# Coordinates are (x1, y1, x2, y2) where (x1, y1) is top-left and (x2, y2) is bottom-right.
# The total canvas size is assumed to be 800x600 (from eight_png_manager.py defaults).

PIXEL_ZONES = {
    "STATUS_BAR": (5, 5, 795, 30),  # Top bar for system status, time, alerts
    "MAIN_CONTENT": (5, 35, 795, 450), # Large central area for primary scroll output
    "TASK_LIST": (5, 455, 395, 595), # Bottom-left for ongoing tasks or scroll proposals
    "AI_FEEDBACK": (405, 455, 795, 595), # Bottom-right for AI-generated content or feedback
    # Add more zones as needed for your evolving system
}

def get_zone_coordinates(zone_name):
    """
    Returns the coordinates (x1, y1, x2, y2) for a given zone name.
    Raises KeyError if the zone name is not found.
    """
    return PIXEL_ZONES[zone_name.upper()]

if __name__ == "__main__":
    print("Defined Pixel Zones:")
    for name, coords in PIXEL_ZONES.items():
        print(f"  {name}: {coords}")

    print("\nFetching specific zone:")
    try:
        status_coords = get_zone_coordinates("STATUS_BAR")
        print(f"  STATUS_BAR coordinates: {status_coords}")
        main_coords = get_zone_coordinates("MAIN_CONTENT")
        print(f"  MAIN_CONTENT coordinates: {main_coords}")
    except KeyError as e:
        print(f"Error: Zone not found - {e}")

    # Example of invalid zone
    try:
        invalid_coords = get_zone_coordinates("NON_EXISTENT_ZONE")
    except KeyError as e:
        print(f"  Attempted to fetch invalid zone: {e}")

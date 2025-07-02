# pxos_terminal.py (Extended with PXFS and Godot Sync)
# [Previous PXFS logic remains intact here...]

# Add new function to import Godot-encoded FS JSON into PXOS

def import_godot_fs_from_json(json_path='pxos_godot_export.json'):
    if not os.path.exists(json_path):
        print(f"PXOS FS Error: File '{json_path}' not found.")
        return False
    try:
        with open(json_path, 'r') as f:
            godot_fs = json.load(f)
        # Replace internal PXFS with this
        pxos_bot.pxfs.fs = godot_fs
        pxos_bot.pxfs.cwd = ["root"]
        print("PXOS> Successfully imported FS from Godot JSON.")
        pxos_bot.pxfs.save_fs()
        return True
    except Exception as e:
        print(f"PXOS FS Error: Could not import Godot FS - {e}")
        return False

# Add new function to extract PXOSCore.gd logic from PXFS and save it locally

def extract_pxos_logic_from_fs(target_filename="PXOSCore_extracted.gd"):
    known_paths = [
        ["root", "users", "admin", "PXOSCore.gd"],
        ["root", "system", "PXOSCore.gd"],
        ["root", "PXOSCore.gd"]
    ]
    for path_parts in known_paths:
        node = pxos_bot.pxfs.fs
        for i, part in enumerate(path_parts):
            if i == len(path_parts) - 1:
                if "files" in node and part in node["files"]:
                    content = node["files"][part]
                    with open(target_filename, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"PXOS> PXOSCore logic extracted and saved to '{target_filename}'.")
                    return True
            else:
                node = node.get("dirs", {}).get(part, {})
    print("PXOS> PXOSCore.gd not found in PXFS.")
    return False

# Inside run_pxos_terminal(), you can support a command like:
# elif user_input.lower().startswith("import godot fs"):
#     import_godot_fs_from_json()
# elif user_input.lower().startswith("extract pxlogic"):
#     extract_pxos_logic_from_fs()

# pixel-vault/metadata.py

import json
import os
import time

def generate_metadata(file_path):
    stat = os.stat(file_path)
    return {
        "original_filename": os.path.basename(file_path),
        "size_bytes": stat.st_size,
        "modified_time": time.ctime(stat.st_mtime),
        "created_time": time.ctime(stat.st_ctime)
    }

def save_metadata(metadata, output_path):
    json_path = output_path + ".json"
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=4)

def load_metadata(json_path):
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    return None

# black-vault/file_utils.py

import hashlib
import mimetypes
import os

def calculate_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def detect_file_type(file_path):
    filetype, _ = mimetypes.guess_type(file_path)
    return filetype or "unknown"

def get_file_extension(file_path):
    return os.path.splitext(file_path)[1].lower()

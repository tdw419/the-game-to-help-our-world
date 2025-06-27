import subprocess
import json
import os
import gzip
import base64

def run_pxexe(path="pxboot/launcher.pxexe"):
    try:
        with open(path, "r") as f:
            meta = json.load(f)
        print(f"[PXBOOT] Launching: {meta['name']}")
        subprocess.Popen(meta["entry"].split(), cwd=os.getcwd())
        return f"Launched {meta['name']}"
    except Exception as e:
        return f"Error launching pxexe: {e}"

def run_pxdigest(path="pxbot_code/launcher.pxdigest"):
    try:
        with gzip.open(path, "rb") as f:
            data = f.read().decode('utf-8', errors='ignore')
        meta_str, payload = data.split("::PXBIN::\n", 1)
        if not meta_str.startswith("PXMETA:"):
            raise ValueError("Invalid pxdigest format")
        meta = json.loads(meta_str.replace("PXMETA:", ""))
        with open("pxbot_code/temp_launcher.py", "w") as f:
            f.write(payload)
        subprocess.Popen(["python", "pxbot_code/temp_launcher.py"], cwd=os.getcwd())
        return f"Launched {meta['name']} from pxdigest"
    except Exception as e:
        return f"Error launching pxdigest: {e}"

def main():
    # Check for autoboot .pxexe
    pxexe_path = "pxboot/launcher.pxexe"
    if os.path.exists(pxexe_path):
        with open(pxexe_path, "r") as f:
            meta = json.load(f)
        if meta.get("autoboot", False):
            print(run_pxexe(pxexe_path))
    # Check for .pxdigest
    pxdigest_path = "pxbot_code/launcher.pxdigest"
    if os.path.exists(pxdigest_path):
        print(run_pxdigest(pxdigest_path))

if __name__ == "__main__":
    main()
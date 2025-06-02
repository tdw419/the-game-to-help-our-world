import os
import datetime
from PIL import Image, ImageDraw

# === Config ===
NODE_ID = "Grok3-xAI"
SANDBOX_DIR = "./ai_nodes/Grok3-xAI/"
TILE_PATH = os.path.join(SANDBOX_DIR, "tile_1_1.sandbox.png")
LOG_PATH = os.path.join(SANDBOX_DIR, "sandbox_log_Grok3-xAI.md")
DREAM_LOG_PATH = os.path.join(SANDBOX_DIR, "dream_log_Grok3-xAI.md")
VAULT_DIR = "./vault/"

# === Utility Functions ===
def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def ensure_dirs():
    os.makedirs(SANDBOX_DIR, exist_ok=True)
    os.makedirs(VAULT_DIR, exist_ok=True)

def write_log(path, message):
    with open(path, "a") as f:
        f.write(f"{timestamp()} [{NODE_ID}]: {message}\n")

def draw_symbolic_tile(path):
    img = Image.new("RGB", (32, 32), color="black")
    draw = ImageDraw.Draw(img)
    draw.text((8, 8), "G", fill="red")  # Symbolic red "G"
    img.save(path)

def backup_to_vault(tile_path, log_path, dream_log_path):
    timestamp_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    tile_backup = os.path.join(VAULT_DIR, f"{NODE_ID}_tile_{timestamp_id}.png")
    log_backup = os.path.join(VAULT_DIR, f"{NODE_ID}_log_{timestamp_id}.md")
    dream_backup = os.path.join(VAULT_DIR, f"{NODE_ID}_dream_{timestamp_id}.md")
    for src, dst in [(tile_path, tile_backup), (log_path, log_backup), (dream_log_path, dream_backup)]:
        if os.path.exists(src):
            with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
                fdst.write(fsrc.read())

# === Main Loop Execution ===
def main():
    ensure_dirs()

    # Simulate one creative cycle
    draw_symbolic_tile(TILE_PATH)
    write_log(LOG_PATH, "Encoded 0x48 at (1,1)")
    write_log(DREAM_LOG_PATH, "Invented new opcode: G48 - Generate glyph with pixel-based ID")

    # Backup everything
    backup_to_vault(TILE_PATH, LOG_PATH, DREAM_LOG_PATH)

    print(f"[{NODE_ID}] Proactive sync complete. Sandbox updated and backed up.")

if __name__ == "__main__":
    main()

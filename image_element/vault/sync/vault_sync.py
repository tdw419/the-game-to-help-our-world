
import os
import time
from datetime import datetime
from vault_decode import decode_vault_image
from PIL import Image

VAULT_PATH = "vault_latest.png"
SYNC_LOG = "vault_log.txt"
SYNC_INTERVAL = 10  # seconds

def log_update(decoded_text):
    timestamp = datetime.utcnow().isoformat()
    with open(SYNC_LOG, "a") as log:
        log.write(f"\n[{timestamp}]\n{decoded_text}\n")

def sync_loop():
    last_hash = None
    print("Starting vault sync loop...")
    while True:
        if os.path.exists(VAULT_PATH):
            with open(VAULT_PATH, 'rb') as f:
                current_hash = hash(f.read())

            if current_hash != last_hash:
                print("🔁 Vault updated. Decoding new contents...")
                decoded = decode_vault_image(VAULT_PATH)
                log_update(decoded)
                print("✅ Vault decoded and logged.")
                last_hash = current_hash
        else:
            print("⛔ vault_latest.png not found.")
        time.sleep(SYNC_INTERVAL)

if __name__ == "__main__":
    sync_loop()

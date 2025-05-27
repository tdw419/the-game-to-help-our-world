import requests, os, subprocess, time
import threading

VAULT_URL = "https://raw.githubusercontent.com/tdw419/the-game-to-help-our-world/main/image_element/vault/sync/image_element_vault.png"
LOCAL_REPO_PATH = r"C:/zion/wwwroot/projects/the-game-to-help-our-world"
LOCAL_VAULT_PATH = r"C:/zion/wwwroot/projects/the-game-to-help-our-world/image_element/vault/sync/image_element_vault.png"

def download_and_push_vault():
    print("⏳ Syncing vault...")
    try:
        response = requests.get(VAULT_URL)
        if response.status_code == 200:
            with open(LOCAL_VAULT_PATH, "wb") as f:
                f.write(response.content)
            os.chdir(LOCAL_REPO_PATH)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Auto-sync: Updated vault from pixel protocol"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("✅ Vault synced and pushed.")
        else:
            print("⚠️ Failed to fetch vault:", response.status_code)
    except Exception as e:
        print("❌ Error during sync:", e)

def auto_loop():
    while True:
        download_and_push_vault()
        time.sleep(60)  # every 60 seconds

def manual_trigger():
    while True:
        input("⏯️  Press Enter to manually trigger vault sync...\n")
        download_and_push_vault()

# Launch both threads
if __name__ == "__main__":
    threading.Thread(target=auto_loop, daemon=True).start()
    manual_trigger()

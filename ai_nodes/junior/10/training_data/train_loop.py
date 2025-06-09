import json
import os

TRAIN_DIR = "training_data"

def run_training():
    if not os.path.exists(TRAIN_DIR):
        print("❌ No training_data/ directory found.")
        return

    files = [f for f in os.listdir(TRAIN_DIR) if f.endswith(".json")]
    if not files:
        print("⚠️ No training files found.")
        return

    for file in files:
        print(f"\n📘 Training with: {file}")
        with open(os.path.join(TRAIN_DIR, file), "r") as f:
            data = json.load(f)
            for block in data:
                print(f"\n🧠 Prompt:\n{block['prompt']}")
                print(f"🎯 Expected Response:\n{block['response']}")

run_training()

# Filename: sync_tile_claim_to_tasks.py
# Location: ai_nodes/task_queue/

import re
import os
import subprocess

def parse_tile_claims(claim_file_path):
    claims = []
    current_timestamp = None
    current_user = None
    current_coords = None

    with open(claim_file_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        # Match plain format: tile 12,8 by TDW419
        m1 = re.match(r'tile\s+(\d+),\s*(\d+)\s+by\s+(\w+)', line, re.IGNORECASE)
        if m1:
            x, y, user = m1.groups()
            claims.append(((int(x), int(y)), user, None))
            continue

        # Match block format: [1,1] – Claimed by Grok3-xAI
        m2 = re.match(r'\[\s*(\d+),\s*(\d+)\s*\]\s*[-–—]\s*Claimed by\s+(\w+)', line, re.IGNORECASE)
        if m2:
            current_coords = (int(m2.group(1)), int(m2.group(2)))
            current_user = m2.group(3)
            current_timestamp = None
            continue

        # Match timestamp line if it follows a block claim
        m3 = re.match(r'Timestamp:\s*(\S+)', line, re.IGNORECASE)
        if m3 and current_coords and current_user:
            current_timestamp = m3.group(1)
            claims.append((current_coords, current_user, current_timestamp))
            current_coords, current_user = None, None

    return claims

def extract_existing_tiles(task_queue_path):
    existing = set()
    if not os.path.exists(task_queue_path):
        return existing
    with open(task_queue_path, 'r') as f:
        for line in f:
            m = re.search(r'tile\s+`(\d+),(\d+)`', line)
            if m:
                existing.add((int(m.group(1)), int(m.group(2))))
    return existing

def generate_task_entry(x, y, user, timestamp=None):
    time_note = f" Timestamp: {timestamp}" if timestamp else ""
    return f"- [ ] `tile_claim`: Validate claim on tile `{x},{y}` by `{user}` — check location, timestamp, and conflict.{time_note}\n"

def append_tasks_to_queue(claim_file_path, task_queue_path):
    claims = parse_tile_claims(claim_file_path)
    existing = extract_existing_tiles(task_queue_path)
    grouped = {}

    for (x, y), user, timestamp in claims:
        if (x, y) in existing:
            continue
        grouped.setdefault(user, []).append((x, y, timestamp))
        existing.add((x, y))

    if not grouped:
        print("No new tasks to add.")
        return

    with open(task_queue_path, 'a') as f:
        f.write("\n## Tile Claim Validation Tasks\n")
        for user, tasks in grouped.items():
            f.write(f"\n### Claims by {user}\n")
            for x, y, ts in tasks:
                f.write(generate_task_entry(x, y, user, ts))

    print(f"✔ Added {sum(len(v) for v in grouped.values())} new task(s).")

    # Auto Git commit
    try:
        subprocess.run(["git", "add", task_queue_path], check=True)
        subprocess.run(["git", "commit", "-m", "Synced tile claims to task queue"], check=True)
        print("✔ Git commit complete.")
    except Exception as e:
        print("⚠ Git commit failed:", e)

# 🔍 Debug Run Block (must be last!)
claim_file = "../../titles/tile_claim.md"
task_file = "task_queue.md"

print(f"🔍 Reading: {claim_file}")
claims = parse_tile_claims(claim_file)
print("🔎 Parsed claims:")
for (x, y), user, ts in claims:
    print(f" - ({x},{y}) by {user}" + (f" @ {ts}" if ts else ""))

append_tasks_to_queue(claim_file, task_file)

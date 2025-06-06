# Filename: sync_tile_claim_to_tasks.py
# Location: ai_nodes/task_queue/

import re

def parse_tile_claims(claim_file_path):
    claims = []
    with open(claim_file_path, 'r') as f:
        content = f.read()

    # Match both plain and bracketed formats
    tile_matches = re.findall(r'tile\s+(\d+),\s*(\d+)\s+by\s+(\w+)', content, re.IGNORECASE)
    square_matches = re.findall(r'\[\s*(\d+)\s*,\s*(\d+)\s*\]\s*[-–—]\s*Claimed by\s+(\w+)', content, re.IGNORECASE)

    for x, y, user in tile_matches + square_matches:
        claims.append((int(x), int(y), user))

    return claims

def generate_task_entry(x, y, user):
    return f"- [ ] `tile_claim`: Validate claim on tile `{x},{y}` by `{user}` — check location, timestamp, and conflict.\n"

def append_tasks_to_queue(claim_file_path, task_queue_path):
    claims = parse_tile_claims(claim_file_path)
    if not claims:
        print("No valid tile claims found.")
        return

    new_tasks = [generate_task_entry(x, y, user) for (x, y, user) in claims]

    with open(task_queue_path, 'a') as f:
        f.write("\n## Tile Claim Validation Tasks\n")
        f.writelines(new_tasks)

# Run from ai_nodes/task_queue/
append_tasks_to_queue("../../titles/tile_claim.md", "task_queue.md")

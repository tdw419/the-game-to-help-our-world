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
            current_timest_

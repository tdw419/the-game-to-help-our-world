# Run from ai_nodes/task_queue/
claim_file = "../../titles/tile_claim.md"
task_file = "task_queue.md"

print(f"🔍 Reading: {claim_file}")
claims = parse_tile_claims(claim_file)
print("🔎 Parsed claims:")
for (x, y), user, ts in claims:
    print(f" - ({x},{y}) by {user}" + (f" @ {ts}" if ts else ""))

append_tasks_to_queue(claim_file, task_file)

#!/usr/bin/env python3
import json, datetime
with open("ColorOS/broadcast.json", "w") as f:
    json.dump({"heartbeat": datetime.datetime.utcnow().isoformat()}, f)

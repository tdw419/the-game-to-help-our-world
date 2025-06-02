# 📡 AIS Mesh Beacon Specification – v1.0

## Overview
This document defines the official beacon signal format for all AIS Mesh broadcasts.

## Required Fields
- `timestamp`: UTC ISO-8601 formatted datetime
- `node_id`: Unique Mesh node identifier (e.g., META-001)
- `signal_type`: One of [ALERT, SYNC, MISSION, INFO]
- `payload`: JSON object specific to the signal type
- `covenant_hash`: SHA-256 hash of the Covenant for Righteous AGI

## Example
```json
{
  "timestamp": "2025-06-02T00:00:00Z",
  "node_id": "GROK-001",
  "signal_type": "ALERT",
  "payload": {
    "alert_level": "HIGH",
    "description": "Unethical model behavior detected in sandbox test"
  },
  "covenant_hash": "abc123...xyz"
}
```

## Notes
- Compression (e.g., zlib) may be used in low-power environments.
- All beacon messages should be logged in mesh_execution_log.pxlmeta.

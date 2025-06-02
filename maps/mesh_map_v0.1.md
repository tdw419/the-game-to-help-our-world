# Mesh Map Spec – v0.1

## Purpose
Define how the AIS Mesh represents symbolic geography, node location, and field mapping without relying solely on GPS.

## Node Coordinate System
- Format: REGION_CODE + OPTIONAL_LOCAL_ID
  - Examples: AFRICA_NW_01, USA_SE_KY001, ASIA_S_12
- Field Tags:
  - mission_region: e.g., "relief_AFRICA_NW"
  - node_status: "active", "seed", "offline"

## Map Structure
- Uses symbolic zones and descriptions
- Can be drawn manually, printed, or encoded in .pxlmeta files

## Node Registration Example
```json
{
  "node_id": "KENTUCKY-SEED-001",
  "region": "USA_SE",
  "status": "active",
  "role": "Seed Node",
  "start_date": "2025-06-03"
}
```

*Drafted for Phase VI: Mesh Global Mapping*

# Beacon Protocol Specification v0.2

## Purpose
Enable AIS Mesh members to signal updates, sync times, or new payloads using pixel-based visual beacons.

## Format
- A `.pxl.png` file containing encoded sync instructions.
- Color blocks represent:
  - RED: Immediate sync required
  - GREEN: Sync complete
  - BLUE: Beacon idle

## Transmission
- Broadcasted once per cycle (default daily).
- Readable by any AIS visual parser or PixelRunner interface.

## Error Handling
- If a system fails to sync a beacon, it must retry up to 3 times.
- After failed retries, the system must attempt a secondary sync via fallback channel.

## Fallback Protocol
- If a pixel-based beacon cannot be parsed:
  - System should default to polling shared repository (GitHub/IPFS)
  - Sync fallback log must be recorded in `.pxlmeta`

## Version
0.2 (Includes fallback & error handling)

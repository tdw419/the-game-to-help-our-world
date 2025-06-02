# Beacon Protocol Specification v0.1

## Purpose
Enable AIS Mesh members to signal updates, sync times, or new payloads using pixel-based visual beacons.

## Format
- A `.pxl.png` file containing encoded sync instructions.
- Color blocks represent:
  - RED: Immediate sync required
  - GREEN: Sync complete
  - BLUE: Beacon idle
- File should be named using ISO date, e.g., `beacon_2025-06-02.pxl.png`.

## Transmission
- Broadcasted once per cycle (default daily).
- Readable by any AIS visual parser or PixelRunner interface.

## Version
0.1 (Initial Spec)

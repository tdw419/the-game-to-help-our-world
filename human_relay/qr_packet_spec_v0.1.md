# QR Protocol & Offline Packet Template – v0.1

## Objective
Transmit core Mesh files through offline, low-tech mediums like QR codes, paper printouts, or color logic tiles.

## File Inclusion Rules
- Limit each packet to 512–1024 bytes (fit QR constraints)
- Use compressed JSON or plaintext
- Suggested format: zlib-compressed JSON base64

## Recommended Files
- codex_mesh_v0.1.md
- covenant_summary.md
- node_type_registry.md
- mesh_map_v0.1.md

## Example Layout
```
[QR 1] codex_mesh (black-and-white, label: MESH-CODEX)
[QR 2] seed mission
[QR 3] contact & covenant
```

## Color Logic Variant (Optional)
- Encode signals via primary/secondary color tiles
- Color blocks = opcodes
- Can be drawn or painted manually

## Offline Node Kit
- 1 printed flyer (join message)
- 3 QR stickers or printed codes
- 1 restart guide
- 1 recovery covenant scroll

*Designed for propagation without devices*

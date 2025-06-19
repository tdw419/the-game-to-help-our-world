## 9. PXRAID Canvas Topology (RAID-4 Memory Array)

PXRAID is a 4-canvas distributed memory architecture enabling fault-tolerant, modular evolution of PXLDISK intelligence.

### Disk Assignments

| File    | Codename     | Role                   | Description |
|---------|--------------|------------------------|-------------|
| 6.png   | PXLogs       | Historical memory      | Stores mutation history, feedback, and long-term logs. |
| 7.png   | PXLessons    | Abstract knowledge     | Stores reusable logic lessons, .pxdigest archives, and learning patterns. |
| 8.png   | PXCore       | System kernel & ethics | Hosts PXTalkVM, PXGEN, PXGoal Engine, RRE spec, and ethics metadata. |
| 9.png   | PXApps       | App execution surface  | Sandbox for PXApps, drafts, overlays, and human interfaces. |

### Key Metadata Zones

Each `.png` embeds the following metadata keys as zTXt:

- `pxraid/role`: Identifies disk role
- `pxethics/rre_spec`: Copy of the current RRE specification
- `pxlogs/`, `pxlessons/`, `apps/`, `pxgoal_engine/`: Contextual logic and data regions

PXRAID enables logic striping, backup, distributed cognition, and repair using modules such as:
- `pxraid_controller_v1`
- `pxstripe_writer_v1`
- `pxrebuild_agent_v1`

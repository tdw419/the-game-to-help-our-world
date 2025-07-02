# scripts/opcodes.gd
extends RefCounted

class_name PXOpcodes

# Define your opcode constants
const PX_NO_OP = Color(0, 0, 0)
const PX_DRAW_PIXEL = Color(1, 0, 0)
const PX_DRAW_CHAR = Color(2, 0, 0)
const PX_DRAW_LINE_SEGMENT_ID = 3.0
const PX_DRAW_RECT_ID = 4.0
const PX_COPY_REGION_ID = 5.0
const PX_READ_DATA_TO_COLOR_ID = 6.0

# Program Counter related opcodes
const PX_BOOT_CONTROL_ID = 7.0 / 255.0
const PX_WRITE_TO_DATA_CMD = 8.0 / 255.0
const PX_DRAW_CHAR_CMD = 9.0 / 255.0
const PX_HALT_CMD = 10.0 / 255.0

# PXNet Message Types
const PXNET_MESSAGE_TYPE_NONE = 0.0 / 255.0
const PXNET_MESSAGE_TYPE_ECHO = 11.0 / 255.0
const PXNET_MESSAGE_TYPE_CMD_DRAW_PIXEL = 12.0 / 255.0
const PXNET_MESSAGE_TYPE_CLAIM_ANNOUNCE = 16.0 / 255.0

# Agent Command Opcodes (Painted by Human for Agent)
const PX_AGENT_GO_TO_ID = 13.0 / 255.0
const PX_AGENT_DRAW_AT_ID = 14.0 / 255.0
const PX_AGENT_SET_GOAL_COLOR_ID = 15.0 / 255.0

# Phase 5.1 - PXOS Instruction Set & Registers
# Register IDs (refer to locations in data_layer: (RegX, RegY_offset))
const REG_R0_ID = 0.0 / 255.0
const REG_R1_ID = 1.0 / 255.0
const REG_R2_ID = 2.0 / 255.0
const REG_R3_ID = 3.0 / 255.0 # R3 will serve as the Stack Pointer (SP)

# VM Instructions
const PX_MOV_VAL_TO_REG_CMD = 17.0 / 255.0 # Move Value (24-bit) to Register
const PX_MOV_REG_TO_REG_CMD = 18.0 / 255.0 # Move Register to Register
const PX_ADD_REG_CMD = 19.0 / 255.0      # Add RegA to RegB, store in RegTarget
const PX_JUMP_CMD = 20.0 / 255.0         # Unconditional Jump to (G,B) coords
const PX_READ_REG_TO_DISPLAY_CMD = 21.0 / 255.0 # Read Reg value and display as pixel at (G,B)

# NEW: Phase 5.2 - Advanced Control Flow & Stack Instructions
const PX_PUSH_REG_CMD = 22.0 / 255.0 # Push register value to stack (G=RegID)
const PX_POP_REG_CMD = 23.0 / 255.0  # Pop value from stack to register (G=RegID)
const PX_JUMP_IF_ZERO_CMD = 24.0 / 255.0 # Jump if register is zero (G=RegID, B=TargetY). Next pixel: TargetX
const PX_JUMP_IF_NOT_ZERO_CMD = 25.0 / 255.0 # Jump if register is NOT zero (G=RegID, B=TargetY). Next pixel: TargetX
const PX_CALL_CMD = 26.0 / 255.0      # Call subroutine (G=TargetX, B=TargetY)
const PX_RET_CMD = 27.0 / 255.0       # Return from subroutine

# Font constants
const FONT_CHAR_WIDTH  = 5.0
const FONT_CHAR_HEIGHT = 5.0
const FONT_ATLAS_CHARS_PER_ROW = 16.0

# Line constants
const MAX_LINE_OFFSET = 20.0

# Rect constants
const MAX_RECT_DIMENSION = 20.0

# Copy constants
const COPY_REGION_WIDTH = 4.0
const COPY_REGION_HEIGHT = 4.0
; Vulkan SPIR-V Compute Shader (Pseudo-code, compiled to SPIR-V)
#version 450
layout(local_size_x = 1) in;
layout(binding = 0) buffer PixelMemory { uint data[]; } pixel_memory;

void main() {
    uint ip = gl_GlobalInvocationID.x;
    uint instr = pixel_memory.data[ip];
    uint opcode = instr >> 24;
    uint addr = (instr >> 16) & 0xFF;
    uint val = instr & 0xFFFF;

    if (opcode == 0x01) { // MOV
        pixel_memory.data[addr] = val;
    } else if (opcode == 0x02) { // PXEXEC
        // Trigger zTXt interpreter (separate shader)
    } else if (opcode == 0x03) { // HLT
        // Signal completion
    }
}
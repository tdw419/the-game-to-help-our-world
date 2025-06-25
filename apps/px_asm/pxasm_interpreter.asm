; PXASM Interpreter for Intel HD 520 (x86_64)
section .text
global _start

_start:
    mov rsi, pixel_memory  ; Load pixel memory (RAM)
    mov rcx, 0            ; Instruction pointer

execute:
    mov eax, [rsi + rcx*4] ; Read 32-bit instruction
    shr eax, 24           ; Extract opcode
    cmp eax, 0x01         ; MOV
    je handle_mov
    cmp eax, 0x02         ; PXEXEC
    je handle_pxexec
    cmp eax, 0x03         ; HLT
    je halt
    jmp next

handle_mov:
    mov ebx, [rsi + rcx*4]
    mov edx, ebx
    shr ebx, 16           ; Address
    and edx, 0xFFFF       ; Value
    mov [pixel_memory + ebx], edx
    call draw_pixel       ; Update framebuffer
    jmp next

handle_pxexec:
    mov ebx, [rsi + rcx*4]
    shr ebx, 16           ; Target address
    call ztxt_interpreter
    jmp next

halt:
    mov eax, 60           ; Syscall: exit
    xor edi, edi
    syscall

draw_pixel:
    ; Simplified GDI-like draw to HD 520 framebuffer
    ret

next:
    inc rcx
    jmp execute

section .data
pixel_memory: times 640*480 dd 0  ; 2MB RAM for HD 520
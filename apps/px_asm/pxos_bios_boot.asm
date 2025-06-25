; PXOS BIOS Bootloader (x86_64)
org 0x7C00
bits 16

start:
    ; Initialize real mode
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax

    ; Load pxboot_stub.bin from disk
    mov ah, 0x02
    mov al, 1
    mov ch, 0
    mov cl, 2
    mov dh, 0
    mov bx, 0x1000
    int 0x13

    ; Switch to protected mode
    lgdt [gdt_descriptor]
    mov eax, cr0
    or eax, 1
    mov cr0, eax
    jmp 0x08:protected_mode

bits 32
protected_mode:
    ; Jump to pxboot_init
    jmp 0x1000

gdt_descriptor:
    dw gdt_end - gdt - 1
    dd gdt

gdt:
    dd 0, 0
    dd 0x0000FFFF, 0x00CF9A00 ; Code segment
    dd 0x0000FFFF, 0x00CF9200 ; Data segment
gdt_end:

times 510-($-$$) db 0
dw 0xAA55
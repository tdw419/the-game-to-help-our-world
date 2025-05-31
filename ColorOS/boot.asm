[BITS 16]
[ORG 0x7C00]

start:
    ; Set video mode 13h (320x200, 256 colors)
    mov ah, 0x00
    mov al, 0x13
    int 0x10

    ; Fill screen with color (test)
    mov ax, 0xA000
    mov es, ax
    xor di, di
    mov al, 0x1F         ; light blue or any test color
    mov cx, 320*200
rep stosb

    ; Infinite loop
hang:
    jmp hang

times 510-($-$$) db 0
dw 0xAA55               ; Boot signature

; x86_64 Linux bootstrapper for PXOS_Sovereign.pxos
; Allocates pixel grid, loads zTXt interpreter, runs pxboot.ztxt
; No external dependencies, uses /dev/fb0 for rendering

section .data
    ; Embedded zTXt scripts (placeholder, use xxd to embed)
    px_runtime_ztxt db "zTXt::pxruntime.ztxt", 0x0A
                    db "[INTERPRETER]", 0x0A
                    db "Name: PXRuntime", 0x0A
                    db "LOAD pxboot.ztxt", 0x0A
                    db "RUN", 0x0A, 0
    px_boot_ztxt db "zTXt::pxboot.ztxt", 0x0A
                 db "[BOOTLOADER]", 0x0A
                 db "Name: PXBoot", 0x0A
                 db "SET_MEMORY 1024x768xRGBA", 0x0A
                 db "MOUNT /pxmodules/", 0x0A
                 db "PX_EXEC PX_UPGRADE.pxexe", 0x0A, 0

    ; Pixel grid (1024x768 RGBA, 3MB)
    pixel_grid times 1024*768*4 db 0

    ; Framebuffer device
    fb_dev db "/dev/fb0", 0

section .bss
    fb_fd resq 1  ; File descriptor for /dev/fb0
    ztxt_ptr resq 1  ; Pointer to current zTXt script

section .text
global _start

_start:
    ; Open /dev/fb0 for rendering
    mov rax, 2        ; sys_open
    mov rdi, fb_dev
    mov rsi, 2        ; O_RDWR
    mov rdx, 0
    syscall
    mov [fb_fd], rax

    ; Initialize pixel grid (clear to black)
    mov rdi, pixel_grid
    mov rcx, 1024*768*4
    xor rax, rax
    rep stosb

    ; Load zTXt interpreter (pxruntime.ztxt)
    mov [ztxt_ptr], px_runtime_ztxt
    call execute_ztxt

    ; Exit
    mov rax, 60       ; sys_exit
    xor rdi, rdi
    syscall

execute_ztxt:
    ; Simplified zTXt interpreter
    ; Check for "LOAD pxboot.ztxt" and run pxboot.ztxt
    mov rsi, [ztxt_ptr]
    cmp byte [rsi], 'z'  ; Check for zTXt header
    jne .done

    ; Search for "LOAD pxboot.ztxt"
    mov rcx, 1000  ; Max script length
.search:
    cmp byte [rsi], 'L'
    je .check_load
    inc rsi
    loop .search
    jmp .done

.check_load:
    cmp dword [rsi], 'LOAD'
    jne .search
    cmp dword [rsi+5], 'pxbo'
    jne .search

    ; Execute pxboot.ztxt
    mov [ztxt_ptr], px_boot_ztxt
    call execute_ztxt_boot
    ret

execute_ztxt_boot:
    ; Simulate PXBoot: mount /pxmodules/, run PX_UPGRADE.pxexe
    ; Write pixel to framebuffer (placeholder for rendering)
    mov rax, [fb_fd]
    mov rdi, rax
    mov rax, 4        ; sys_write
    mov rsi, pixel_grid
    mov rdx, 1024*768*4
    syscall

    ; Log boot (placeholder)
    mov rax, pixel_grid
    mov dword [rax], 0xFF0000FF  ; Red pixel at (0,0)

    ret

.done:
    ret
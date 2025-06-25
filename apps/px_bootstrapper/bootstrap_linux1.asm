; x86_64 Linux bootstrapper for PXOS_Sovereign.pxos
; Allocates pixel grid, runs zTXt interpreter, executes pxboot.ztxt
; Uses /dev/fb0, no dependencies

section .data
    ; Embedded zTXt scripts (generated via xxd)
    px_runtime_ztxt incbin "pxruntime.ztxt.bin"
    px_boot_ztxt incbin "pxboot.ztxt.bin"
    px_upgrade_pxexe incbin "PX_UPGRADE.pxexe.bin"
    px_executor_pxmod incbin "pxexecutor.pxmod.bin"
    pxos_config_json incbin "PXOS.config.json.bin"

    ; Pixel grid (1024x768 RGBA, 3MB)
    pixel_grid times 1024*768*4 db 0

    ; Framebuffer device
    fb_dev db "/dev/fb0", 0

    ; /pxmodules/ (in-memory filesystem)
    modules db "pxexecutor.pxmod", 0
            db "PX_UPGRADE.pxexe", 0
            db "PXOS.config.json", 0
            db 0

section .bss
    fb_fd resq 1  ; File descriptor for /dev/fb0
    ztxt_ptr resq 1  ; Current zTXt script
    log_buffer resb 1024  ; Log buffer for PX_UPGRADE_LOG.zTXT

section .text
global _start

_start:
    ; Open /dev/fb0
    mov rax, 2        ; sys_open
    mov rdi, fb_dev
    mov rsi, 2        ; O_RDWR
    mov rdx, 0
    syscall
    mov [fb_fd], rax

    ; Initialize pixel grid
    mov rdi, pixel_grid
    mov rcx, 1024*768*4
    xor rax, rax
    rep stosb

    ; Load zTXt interpreter
    mov [ztxt_ptr], px_runtime_ztxt
    call execute_ztxt

    ; Exit
    mov rax, 60       ; sys_exit
    xor rdi, rdi
    syscall

execute_ztxt:
    mov rsi, [ztxt_ptr]
    mov rcx, 10000  ; Max script length
    xor rbx, rbx  ; Opcode counter

.parse_loop:
    cmp byte [rsi], 0
    je .done
    cmp byte [rsi], '['
    je .section
    cmp byte [rsi], 'M'
    je .check_mov
    cmp byte [rsi], 'S'
    je .check_set_px
    cmp byte [rsi], 'P'
    je .check_px
    cmp byte [rsi], 'L'
    je .check_log
    inc rsi
    loop .parse_loop
    jmp .done

.section:
    inc rsi
    cmp dword [rsi], 'EXEC'
    je .execute
    jmp .parse_loop

.check_mov:
    cmp dword [rsi], 'MOV '
    jne .parse_loop
    ; Simulate MOV (placeholder)
    inc rbx
    add rsi, 8
    jmp .parse_loop

.check_set_px:
    cmp dword [rsi], 'SET_'
    jne .parse_loop
    ; Set pixel (write to pixel_grid)
    mov rax, pixel_grid
    mov dword [rax], 0xFF0000FF  ; Red pixel at (0,0)
    inc rbx
    add rsi, 12
    jmp .parse_loop

.check_px:
    cmp dword [rsi], 'PX_W'
    je .px_write
    cmp dword [rsi], 'PX_R'
    je .px_reload
    cmp dword [rsi], 'PX_E'
    je .px_exec
    jmp .parse_loop

.px_write:
    ; Simulate PX_WRITE
    mov rdi, log_buffer
    mov byte [rdi], 'W'
    inc rbx
    add rsi, 20
    jmp .parse_loop

.px_reload:
    ; Simulate PX_RELOAD
    mov [ztxt_ptr], px_executor_pxmod
    call execute_ztxt
    inc rbx
    add rsi, 15
    jmp .parse_loop

.px_exec:
    ; Execute file (e.g., PX_UPGRADE.pxexe)
    mov [ztxt_ptr], px_upgrade_pxexe
    call execute_ztxt
    inc rbx
    add rsi, 15
    jmp .parse_loop

.check_log:
    cmp dword [rsi], 'LOG '
    jne .parse_loop
    ; Write to log_buffer
    mov rdi, log_buffer
    mov byte [rdi], 'L'
    inc rbx
    add rsi, 10
    jmp .parse_loop

.execute:
    ; Check for "LOAD pxboot.ztxt"
    mov rsi, px_boot_ztxt
    mov [ztxt_ptr], rsi
    call execute_ztxt
    jmp .done

.done:
    ; Write pixel grid to framebuffer
    mov rax, [fb_fd]
    mov rdi, rax
    mov rax, 4        ; sys_write
    mov rsi, pixel_grid
    mov rdx, 1024*768*4
    syscall
    ret
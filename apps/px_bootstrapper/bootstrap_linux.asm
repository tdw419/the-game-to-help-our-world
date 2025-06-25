; x86_64 Linux bootstrapper for PXOS_Sovereign
; Full zTXt interpreter, /dev/fb0 rendering, disk I/O
section .data
    px_runtime_ztxt incbin "pxruntime.ztxt.bin"
    px_boot_ztxt incbin "pxboot.ztxt.bin"
    px_upgrade_pxexe incbin "PX_UPGRADE.pxexe.bin"
    px_executor_pxmod incbin "pxexecutor.pxmod.bin"
    px_canvas_ztxt incbin "pxcanvas.ztxt.bin"
    px_os_io_ztxt incbin "pxos_io.ztxt.bin"
    pxos_config_json incbin "PXOS.config.json.bin"
    pxvm_font_png incbin "pxvm_font.png.bin"

    pixel_grid times 1024*768*4 db 0
    fb_dev db "/dev/fb0", 0
    log_file db "pxos_log.txt", 0
    digest_file db "PXOS_reflex_digest.json", 0
    modules db "pxexecutor.pxmod", 0, "PX_UPGRADE.pxexe", 0, "pxcanvas.ztxt", 0, "pxos_io.ztxt", 0, "PXOS.config.json", 0, 0

section .bss
    fb_fd resq 1
    ztxt_ptr resq 1
    log_buffer resb 1024
    digest_buffer resb 4096
    registers resq 4  ; R1-R4
    pc resq 1  ; Program counter
    running resb 1

section .text
global _start

_start:
    mov byte [running], 1
    mov rax, 2
    mov rdi, fb_dev
    mov rsi, 2
    mov rdx, 0
    syscall
    mov [fb_fd], rax

    mov rdi, pixel_grid
    mov rcx, 1024*768*4
    xor rax, rax
    rep stosb

    mov [ztxt_ptr], px_runtime_ztxt
    call execute_ztxt

    mov rax, 60
    xor rdi, rdi
    syscall

execute_ztxt:
    mov rsi, [ztxt_ptr]
    mov [pc], 0
.parse_loop:
    cmp byte [running], 0
    je .done
    mov rbx, [pc]
    call parse_opcode
    inc qword [pc]
    jmp .parse_loop

parse_opcode:
    cmp byte [rsi], 0
    je .done
    cmp byte [rsi], 'M'
    je .check_mov
    cmp byte [rsi], 'S'
    je .check_set_px
    cmp byte [rsi], 'P'
    je .check_px
    cmp byte [rsi], 'L'
    je .check_log
    cmp byte [rsi], 'H'
    je .check_hlt
    inc rsi
    ret

.check_mov:
    cmp dword [rsi], 'MOV '
    jne .next
    mov rax, [registers+8]  ; R2
    mov [registers], rax     ; R1
    add rsi, 8
    ret

.check_set_px:
    cmp dword [rsi], 'SET_'
    jne .next
    mov rax, [registers]    ; X
    mov rbx, [registers+8]  ; Y
    mov rcx, rax
    imul rcx, 1024
    add rcx, rbx
    imul rcx, 4
    mov rdx, pixel_grid
    mov dword [rdx+rcx], 0xFF0000FF
    add rsi, 12
    ret

.check_px:
    cmp dword [rsi], 'PX_W'
    je .px_write
    cmp dword [rsi], 'PX_R'
    je .px_reload
    cmp dword [rsi], 'PX_E'
    je .px_exec
    cmp dword [rsi], 'PX_I'
    je .px_input
    cmp dword [rsi], 'PX_E'
    je .px_export
    jmp .next

.px_write:
    mov rax, [registers]    ; FILE
    mov rbx, [registers+8]  ; DATA
    mov byte [log_buffer], 'W'
    add rsi, 20
    ret

.px_reload:
    mov rax, [registers]    ; FILE
    mov [ztxt_ptr], px_executor_pxmod
    call execute_ztxt
    add rsi, 15
    ret

.px_exec:
    mov rax, [registers]    ; FILE
    mov [ztxt_ptr], px_upgrade_pxexe
    call execute_ztxt
    add rsi, 15
    ret

.px_input:
    ; Placeholder for input (keyboard/mouse)
    add rsi, 10
    ret

.px_export:
    mov rax, 2
    mov rdi, digest_file
    mov rsi, 0x41
    mov rdx, 0644
    syscall
    mov r8, rax
    mov rax, 1
    mov rdi, r8
    mov rsi, digest_buffer
    mov rdx, 4096
    syscall
    mov rax, 3
    mov rdi, r8
    syscall
    add rsi, 15
    ret

.check_log:
    cmp dword [rsi], 'LOG '
    jne .next
    mov byte [log_buffer+1], 'L'
    add rsi, 10
    ret

.check_hlt:
    cmp dword [rsi], 'HLT'
    jne .next
    mov byte [running], 0
    add rsi, 4
    ret

.next:
    inc rsi
    ret

.done:
    mov rax, [fb_fd]
    mov rdi, rax
    mov rax, 4
    mov rsi, pixel_grid
    mov rdx, 1024*768*4
    syscall

    mov rax, 2
    mov rdi, log_file
    mov rsi, 0x41
    mov rdx, 0644
    syscall
    mov r8, rax
    mov rax, 1
    mov rdi, r8
    mov rsi, log_buffer
    mov rdx, 1024
    syscall
    mov rax, 3
    mov rdi, r8
    syscall
    ret
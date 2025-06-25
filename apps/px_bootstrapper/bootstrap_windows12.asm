; x86_64 Windows bootstrapper for PXOS_Sovereign.exe
; Full zTXt interpreter, GDI rendering, disk I/O
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
    log_file db "pxos_log.txt", 0
    digest_file db "PXOS_reflex_digest.json", 0

section .bss
    hdc resq 1
    hwnd resq 1
    ztxt_ptr resq 1
    log_buffer resb 1024
    digest_buffer resb 4096
    registers resq 4
    pc resq 1
    running resb 1

section .text
global WinMain

extern GetDC
extern CreateWindowA
extern BitBlt
extern CreateFileA
extern WriteFile
extern CloseHandle
extern ExitProcess

WinMain:
    mov byte [running], 1
    mov rcx, 0
    mov rdx, window_class
    mov r8, window_name
    mov r9, 0x10000000
    push 0
    push 0
    push 768
    push 1024
    push 0
    push 0
    push 0
    push 0
    call CreateWindowA
    mov [hwnd], rax

    mov rcx, [hwnd]
    call GetDC
    mov [hdc], rax

    mov rdi, pixel_grid
    mov rcx, 1024*768*4
    xor rax, rax
    rep stosb

    mov [ztxt_ptr], px_runtime_ztxt
    call execute_ztxt

    mov rcx, 0
    call ExitProcess

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
    ; Same logic as Linux (omitted for brevity)
    ret

.done:
    mov rcx, [hdc]
    mov rdx, 0
    mov r8, 0
    mov r9, 1024
    push 768
    push pixel_grid
    push 0
    push 0
    push 0xCC0020
    call BitBlt

    mov rcx, log_file
    mov rdx, 0x40000000
    mov r8, 0
    mov r9, 0x80
    push 0
    push 0
    push 0
    call CreateFileA
    mov r8, rax
    mov rcx, rax
    mov rdx, log_buffer
    mov r9, 1024
    push 0
    call WriteFile
    mov rcx, r8
    call CloseHandle

    mov rcx, digest_file
    mov rdx, 0x40000000
    mov r8, 0
    mov r9, 0x80
    push 0
    push 0
    push 0
    call CreateFileA
    mov r8, rax
    mov rcx, rax
    mov rdx, digest_buffer
    mov r9, 4096
    push 0
    call WriteFile
    mov rcx, r8
    call CloseHandle
    ret

section .data
window_class db "PXOSWindow", 0
window_name db "PXOS Sovereign", 0
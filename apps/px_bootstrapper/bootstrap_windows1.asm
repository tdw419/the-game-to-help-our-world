; x86_64 Windows bootstrapper for PXOS_Sovereign.exe
; Uses GDI for rendering, no dependencies

section .data
    ; Embedded zTXt scripts (same as Linux)
    px_runtime_ztxt incbin "pxruntime.ztxt.bin"
    px_boot_ztxt incbin "pxboot.ztxt.bin"
    px_upgrade_pxexe incbin "PX_UPGRADE.pxexe.bin"
    px_executor_pxmod incbin "pxexecutor.pxmod.bin"
    pxos_config_json incbin "PXOS.config.json.bin"

    ; Pixel grid
    pixel_grid times 1024*768*4 db 0

    ; GDI objects
    hdc dq 0
    hwnd dq 0

section .bss
    ztxt_ptr resq 1
    log_buffer resb 1024

section .text
global WinMain

extern GetDC
extern CreateWindowA
extern BitBlt
extern ExitProcess

WinMain:
    ; Create window
    mov rcx, 0
    mov rdx, window_class
    mov r8, window_name
    mov r9, 0x10000000  ; WS_VISIBLE
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

    ; Get device context
    mov rcx, [hwnd]
    call GetDC
    mov [hdc], rax

    ; Initialize pixel grid
    mov rdi, pixel_grid
    mov rcx, 1024*768*4
    xor rax, rax
    rep stosb

    ; Load zTXt interpreter
    mov [ztxt_ptr], px_runtime_ztxt
    call execute_ztxt

    ; Exit
    mov rcx, 0
    call ExitProcess

execute_ztxt:
    ; Same logic as Linux (simplified for brevity)
    mov rsi, [ztxt_ptr]
    mov rcx, 10000
    xor rbx, rbx

.parse_loop:
    cmp byte [rsi], 0
    je .done
    cmp byte [rsi], 'S'
    je .check_set_px
    inc rsi
    loop .parse_loop
    jmp .done

.check_set_px:
    cmp dword [rsi], 'SET_'
    jne .parse_loop
    mov rax, pixel_grid
    mov dword [rax], 0xFF0000FF
    inc rbx
    add rsi, 12
    jmp .parse_loop

.done:
    ; Render to GDI
    mov rcx, [hdc]
    mov rdx, 0
    mov r8, 0
    mov r9, 1024
    push 768
    push pixel_grid
    push 0
    push 0
    push 0xCC0020  ; SRCCOPY
    call BitBlt
    ret

section .data
window_class db "PXOSWindow", 0
window_name db "PXOS Sovereign", 0
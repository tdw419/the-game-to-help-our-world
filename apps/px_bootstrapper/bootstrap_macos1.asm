; x86_64 macOS bootstrapper for PXOS_Sovereign.app
; Uses Quartz, no dependencies

section .data
    ; Embedded zTXt scripts (same as Linux)
    px_runtime_ztxt incbin "pxruntime.ztxt.bin"
    px_boot_ztxt incbin "pxboot.ztxt.bin"
    px_upgrade_pxexe incbin "PX_UPGRADE.pxexe.bin"
    px_executor_pxmod incbin "pxexecutor.pxmod.bin"
    pxos_config_json incbin "PXOS.config.json.bin"

    ; Pixel grid
    pixel_grid times 1024*768*4 db 0

section .bss
    ztxt_ptr resq 1
    log_buffer resb 1024

section .text
global _start

_start:
    ; Initialize pixel grid
    mov rdi, pixel_grid
    mov rcx, 1024*768*4
    xor rax, rax
    rep stosb

    ; Load zTXt interpreter
    mov [ztxt_ptr], px_runtime_ztxt
    call execute_ztxt

    ; Exit
    mov rax, 0x2000001  ; exit syscall
    xor rdi, rdi
    syscall

execute_ztxt:
    ; Same logic as Linux (simplified)
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
    ; Quartz rendering placeholder
    ret
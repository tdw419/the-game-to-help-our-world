@echo off
title TinyCore Pixel Processor Control Panel
color 0A

:MAIN_LOOP
cls
echo.
echo ████████████████████████████████████████████████████████
echo    TinyCore Linux Pixel Processor Bootloader v2.0
echo ████████████████████████████████████████████████████████
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Node.js not found
    echo    Please install Node.js from https://nodejs.org/
    echo.
    echo Press any key to retry...
    pause >nul
    goto MAIN_LOOP
)

echo ✅ Node.js detected and ready
echo.

echo Select your pixel processor mode:
echo.
echo ┌─────────────────────────────────────────────────────┐
echo │  1. 💻 Basic Boot Sequence (70 bytes)              │
echo │  2. 🖥️  Interactive Shell Mode                      │
echo │  3. 🎨 TinyCore GUI Desktop (25MB compressed)       │
echo │  4. 📦 Create PXDigest from file                    │
echo │  5. ℹ️  System Information                          │
echo │  6. 🛑 Exit                                         │
echo └─────────────────────────────────────────────────────┘
echo.

set /p choice="👉 Enter your choice (1-6): "
echo.

if "%choice%"=="1" goto BASIC_BOOT
if "%choice%"=="2" goto INTERACTIVE_BOOT
if "%choice%"=="3" goto GUI_BOOT
if "%choice%"=="4" goto CREATE_DIGEST
if "%choice%"=="5" goto SYSTEM_INFO
if "%choice%"=="6" goto EXIT

echo ❌ Invalid choice. Please select 1-6.
timeout /t 2 /nobreak >nul
goto MAIN_LOOP

:BASIC_BOOT
echo ════════════════════════════════════════════════════════
echo 💻 BASIC BOOT SEQUENCE
echo ════════════════════════════════════════════════════════
echo.
echo Starting basic pixel processor boot...
echo.

if not exist "boot_tinycore.js" (
    echo ❌ ERROR: boot_tinycore.js not found
    echo    Please ensure the file is in the current directory
    goto BOOT_ERROR
)

node boot_tinycore.js

echo.
echo ════════════════════════════════════════════════════════
echo ✅ Basic boot sequence completed
echo ════════════════════════════════════════════════════════
goto RETURN_TO_MENU

:INTERACTIVE_BOOT
echo ════════════════════════════════════════════════════════
echo 🖥️  INTERACTIVE SHELL MODE
echo ════════════════════════════════════════════════════════
echo.
echo This will start a persistent shell session.
echo Commands: help, ls, ps, echo, pixel, framebuffer, halt
echo.
echo Press Enter to continue or Ctrl+C to cancel...
pause >nul

if exist "boot_interactive.js" (
    node boot_interactive.js
) else (
    echo 📝 Interactive version not found, using enhanced basic mode...
    echo.
    node boot_tinycore.js
    echo.
    echo ┌─────────────────────────────────────────────────────┐
    echo │ SIMPLE INTERACTIVE SHELL                            │
    echo │ Commands: help, status, reboot, menu               │
    echo └─────────────────────────────────────────────────────┘
    echo.
    
    :SIMPLE_SHELL_LOOP
    set /p shellcmd="tinycore@pixel:~$ "
    
    if "%shellcmd%"=="help" (
        echo Available commands: help, status, reboot, menu, exit
        goto SIMPLE_SHELL_LOOP
    )
    if "%shellcmd%"=="status" (
        echo Pixel Processor Status: Running
        echo Memory: 1024x768 RGB framebuffer
        echo Processes: PXScreenVM active
        goto SIMPLE_SHELL_LOOP
    )
    if "%shellcmd%"=="reboot" goto MAIN_LOOP
    if "%shellcmd%"=="menu" goto MAIN_LOOP
    if "%shellcmd%"=="exit" goto MAIN_LOOP
    if "%shellcmd%"=="" goto SIMPLE_SHELL_LOOP
    
    echo Command processed: %shellcmd%
    goto SIMPLE_SHELL_LOOP
)

goto RETURN_TO_MENU

:GUI_BOOT
echo ════════════════════════════════════════════════════════
echo 🎨 TINYCORE GUI DESKTOP (25MB)
echo ════════════════════════════════════════════════════════
echo.
echo Preparing to launch full graphical desktop environment...
echo Features: FLWM Window Manager, Applications, Taskbar
echo.

if not exist "boot_tinycore_gui.js" (
    echo ❌ ERROR: boot_tinycore_gui.js not found
    echo.
    echo This file contains the GUI desktop bootloader.
    echo Please save the GUI bootloader code as boot_tinycore_gui.js
    echo.
    goto BOOT_ERROR
)

echo Press Enter to launch desktop or Ctrl+C to cancel...
pause >nul
echo.
echo 🚀 Launching TinyCore GUI Desktop...
echo.

node boot_tinycore_gui.js

goto RETURN_TO_MENU

:CREATE_DIGEST
echo ════════════════════════════════════════════════════════
echo 📦 PXDIGEST CREATOR
echo ════════════════════════════════════════════════════════
echo.

if not exist "digestmaker.js" (
    echo ❌ ERROR: digestmaker.js not found
    goto BOOT_ERROR
)

echo Enter the path to your input file (ISO, BIN, IMG):
set /p inputfile="📁 Input file: "

if not exist "%inputfile%" (
    echo ❌ ERROR: File not found: %inputfile%
    goto RETURN_TO_MENU
)

echo Enter the output PXDigest filename:
set /p outputfile="💾 Output file: "

echo.
echo Creating PXDigest...
echo ┌─────────────────────────────────────────────────────┐
node digestmaker.js "%inputfile%" "%outputfile%"
echo └─────────────────────────────────────────────────────┘

goto RETURN_TO_MENU

:SYSTEM_INFO
echo ════════════════════════════════════════════════════════
echo ℹ️  SYSTEM INFORMATION
echo ════════════════════════════════════════════════════════
echo.
echo 🖥️  System: TinyCore Pixel Processor
echo 🧠 Architecture: Recursive Binary Substrate Computing
echo 📺 Display: RGB Framebuffer Virtual Machine
echo 🎨 Color Depth: 24-bit (16.7M colors)
echo.
echo 📁 Current Directory: %CD%
echo.
echo 📄 Required Files:
if exist "boot_tinycore.js" (echo ✅ boot_tinycore.js) else (echo ❌ boot_tinycore.js)
if exist "boot_interactive.js" (echo ✅ boot_interactive.js) else (echo ⚠️  boot_interactive.js ^(optional^))
if exist "boot_tinycore_gui.js" (echo ✅ boot_tinycore_gui.js) else (echo ⚠️  boot_tinycore_gui.js ^(for GUI mode^))
if exist "digestmaker.js" (echo ✅ digestmaker.js) else (echo ❌ digestmaker.js)
echo.
echo 🔗 Node.js Version:
node --version 2>nul || echo ❌ Node.js not installed
echo.

goto RETURN_TO_MENU

:BOOT_ERROR
echo.
echo ⚠️  Boot Error Encountered
echo    Check that all required files are present
echo    and Node.js is properly installed.
echo.
goto RETURN_TO_MENU

:RETURN_TO_MENU
echo.
echo ════════════════════════════════════════════════════════
echo Session completed. Choose your next action:
echo.
echo 1. Return to main menu
echo 2. Exit program
echo ════════════════════════════════════════════════════════
echo.
set /p nextaction="👉 Choice (1-2): "

if "%nextaction%"=="1" goto MAIN_LOOP
if "%nextaction%"=="2" goto EXIT
goto MAIN_LOOP

:EXIT
cls
echo.
echo ████████████████████████████████████████████████████████
echo    Thank you for using TinyCore Pixel Processor!
echo ████████████████████████████████████████████████████████
echo.
echo 🎨 Your journey into pixel-based computing continues...
echo 🚀 Every RGB value is a step toward the future!
echo.
echo Window will close in 3 seconds...
timeout /t 3 /nobreak >nul
exit
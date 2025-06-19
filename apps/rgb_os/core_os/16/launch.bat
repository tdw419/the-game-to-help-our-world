@echo off
echo ================================================
echo    TinyCore Linux Pixel Processor Bootloader
echo ================================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found. Please install Node.js from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo ✅ Node.js detected
echo.

REM Check if boot script exists
if not exist "boot_tinycore.js" (
    echo ❌ boot_tinycore.js not found in current directory
    echo Please ensure all files are in the same folder
    echo.
    pause
    exit /b 1
)

echo 🚀 Launching TinyCore Pixel Processor...
echo.
echo Press Ctrl+C to stop the boot sequence
echo.

REM Run the bootloader
node boot_tinycore.js

echo.
echo ================================================
echo Boot sequence completed
echo ================================================
pause
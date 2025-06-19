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

:MENU
echo ================================================
echo Select an option:
echo ================================================
echo 1. Run Basic Boot Sequence
echo 2. Run Interactive Shell Mode  
echo 3. Create PXDigest from file
echo 4. Exit
echo ================================================
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto BASIC_BOOT
if "%choice%"=="2" goto INTERACTIVE_BOOT
if "%choice%"=="3" goto CREATE_DIGEST
if "%choice%"=="4" goto EXIT
echo Invalid choice. Please try again.
goto MENU

:BASIC_BOOT
echo.
echo 🚀 Launching Basic TinyCore Boot...
echo ================================================
node boot_tinycore.js
echo ================================================
echo Boot sequence completed. Press any key to return to menu...
pause > nul
goto MENU

:INTERACTIVE_BOOT
echo.
echo 🎮 Launching Interactive Shell Mode...
echo ================================================
if not exist "boot_interactive.js" (
    echo ❌ boot_interactive.js not found!
    echo Creating it now from the basic version...
    echo.
    echo For now, running basic boot with persistent window...
    echo ================================================
    node boot_tinycore.js
    echo.
    echo ================================================
    echo Boot completed. You can now interact here.
    echo Commands: Type any text and press Enter
    echo Type 'menu' to return to main menu
    echo ================================================
    :SIMPLE_SHELL
    set /p cmd="tinycore@pixel:~$ "
    if "%cmd%"=="menu" goto MENU
    if "%cmd%"=="exit" goto MENU
    if "%cmd%"=="halt" goto MENU
    echo Processing: %cmd%
    echo Command executed on pixel processor
    goto SIMPLE_SHELL
) else (
    echo This will start a persistent shell session.
    echo Type 'halt' or Ctrl+C to return to menu.
    echo ================================================
    pause
    node boot_interactive.js
)
echo.
echo Shell session ended. Press any key to return to menu...
pause > nul
goto MENU

:CREATE_DIGEST
echo.
echo 📦 PXDigest Creator
echo ================================================
set /p inputfile="Enter path to input file (ISO/BIN): "
if not exist "%inputfile%" (
    echo ❌ File not found: %inputfile%
    pause
    goto MENU
)
set /p outputfile="Enter output name (e.g. myfile.pxdigest): "
echo.
echo Creating PXDigest...
node digestmaker.js "%inputfile%" "%outputfile%"
echo.
echo Press any key to return to menu...
pause > nul
goto MENU

:EXIT
echo.
echo 👋 Goodbye!
echo.
exit /b 0
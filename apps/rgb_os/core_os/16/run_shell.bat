@echo off
title TinyCore Pixel Shell
echo ================================================
echo    TinyCore Pixel Shell - Direct Access
echo ================================================
echo.
echo Starting interactive pixel processor...
echo Type 'help' for commands, 'halt' to exit
echo ================================================
echo.

REM Keep the window open and run the interactive shell
node boot_interactive.js

echo.
echo ================================================
echo Shell session ended
echo ================================================
echo Window will close in 5 seconds...
timeout /t 5 /nobreak > nul
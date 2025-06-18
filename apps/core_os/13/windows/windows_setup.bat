@echo off
REM Windows Direct Screen Renderer Setup
echo.
echo 🪟 Windows Direct Screen Renderer Setup
echo =======================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install Node.js first.
    echo 💡 Download from: https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Node.js found

REM Check if npm is available
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm not found. Please install Node.js with npm.
    pause
    exit /b 1
)

echo ✅ npm found

REM Create package.json if it doesn't exist
if not exist package.json (
    echo 📦 Creating Node.js environment...
    echo {> package.json
    echo   "name": "windows-direct-renderer",>> package.json
    echo   "version": "1.0.0",>> package.json
    echo   "description": "Direct Windows screen renderer for HTML",>> package.json
    echo   "dependencies": {>> package.json
    echo     "puppeteer": "^21.0.0">> package.json
    echo   }>> package.json
    echo }>> package.json
)

REM Install dependencies
echo 📦 Installing dependencies...
call npm install

REM Create temp directory
if not exist "%TEMP%\html_renderer" (
    mkdir "%TEMP%\html_renderer"
)

echo.
echo ✅ Setup complete!
echo.
echo 📋 Usage:
echo   node windows_direct_renderer.js your_file.html [fps]
echo.
echo 📝 Example:
echo   node windows_direct_renderer.js test.html 3
echo.
echo ⚠️  WARNING: This will take over your entire screen!
echo ⌨️  Press Ctrl+C to stop and restore desktop
echo.

REM Create test HTML if it doesn't exist
if not exist test.html (
    echo 📄 Creating test HTML file...
    echo ^<!DOCTYPE html^>> test.html
    echo ^<html^>>> test.html
    echo ^<head^>>> test.html
    echo     ^<title^>Windows Direct Test^</title^>>> test.html
    echo     ^<style^>>> test.html
    echo         body { margin: 0; background: linear-gradient(45deg, #000080, #4169E1, #87CEEB); color: white; font-family: Arial; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; text-align: center; }>>> test.html
    echo         .title { font-size: 72px; margin-bottom: 20px; text-shadow: 3px 3px 6px rgba(0,0,0,0.8); }>>> test.html
    echo         .subtitle { font-size: 36px; margin-bottom: 40px; }>>> test.html
    echo         .clock { font-size: 48px; margin: 20px 0; text-shadow: 0 0 20px white; }>>> test.html
    echo         .counter { font-size: 96px; color: #FFD700; text-shadow: 0 0 30px #FFD700; }>>> test.html
    echo         .stats { position: fixed; top: 20px; left: 20px; background: rgba(0,0,0,0.8); padding: 15px; border-radius: 10px; font-size: 18px; }>>> test.html
    echo     ^</style^>>> test.html
    echo ^</head^>>> test.html
    echo ^<body^>>> test.html
    echo     ^<div class="stats"^>>> test.html
    echo         ^<div id="live-time"^>Live: 0s^</div^>>> test.html
    echo         ^<div id="live-frames"^>Frames: 0^</div^>>> test.html
    echo         ^<div^>Windows Direct Render^</div^>>> test.html
    echo     ^</div^>>> test.html
    echo     ^<div class="title"^>🪟 WINDOWS DIRECT^</div^>>> test.html
    echo     ^<div class="subtitle"^>HTML → Native Screen^</div^>>> test.html
    echo     ^<div class="clock" id="clock"^>00:00:00^</div^>>> test.html
    echo     ^<div class="counter"^>^<span class="live-counter"^>0^</span^>^</div^>>> test.html
    echo     ^<script^>>> test.html
    echo         function updateClock() {>>> test.html
    echo             const now = new Date();>>> test.html
    echo             document.getElementById('clock').textContent = now.toLocaleTimeString();>>> test.html
    echo         }>>> test.html
    echo         setInterval(updateClock, 1000);>>> test.html
    echo         updateClock();>>> test.html
    echo     ^</script^>>> test.html
    echo ^</body^>>> test.html
    echo ^</html^>>> test.html
    
    echo ✅ Created test.html
)

echo.
echo 🚀 Ready to test! Run:
echo   node windows_direct_renderer.js test.html
echo.
pause
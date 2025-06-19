@echo off
REM Windows Direct Screen Renderer Setup
echo.
echo 🪟 Windows Direct Screen Renderer Setup
echo =======================================
echo.

REM Check for Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install it: https://nodejs.org/
    pause
    exit /b 1
)
echo ✅ Node.js found

REM Check for npm
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm not found. Please install Node.js with npm.
    pause
    exit /b 1
)
echo ✅ npm found

REM Create package.json
if not exist package.json (
    echo 📦 Creating Node.js environment...
    (
    echo {
    echo   "name": "windows-direct-renderer",
    echo   "version": "1.0.0",
    echo   "description": "Direct Windows screen renderer for HTML",
    echo   "dependencies": {
    echo     "puppeteer": "^21.0.0"
    echo   }
    echo }
    ) > package.json
)

REM Install dependencies
echo 📦 Installing dependencies...
call npm install

REM Create test.html
if not exist test.html (
    echo 📄 Creating test HTML...
    (
    echo ^<!DOCTYPE html^>
    echo ^<html^>
    echo ^<head^>
    echo ^<title^>Windows Direct Test^</title^>
    echo ^<style^>
    echo body { margin:0; background:linear-gradient(45deg,#000080,#4169E1,#87CEEB); color:white; font-family:Arial; display:flex; flex-direction:column; justify-content:center; align-items:center; height:100vh; text-align:center; }
    echo .title { font-size:72px; margin-bottom:20px; text-shadow:3px 3px 6px rgba(0,0,0,0.8); }
    echo .subtitle { font-size:36px; margin-bottom:40px; }
    echo .clock { font-size:48px; margin:20px 0; text-shadow:0 0 20px white; }
    echo .counter { font-size:96px; color:#FFD700; text-shadow:0 0 30px #FFD700; }
    echo .stats { position:fixed; top:20px; left:20px; background:rgba(0,0,0,0.8); padding:15px; border-radius:10px; font-size:18px; }
    echo ^</style^>
    echo ^</head^>
    echo ^<body^>
    echo ^<div class="stats"^>
    echo ^<div id="live-time"^>Live: 0s^</div^>
    echo ^<div id="live-frames"^>Frames: 0^</div^>
    echo ^<div^>Windows Direct Render^</div^>
    echo ^</div^>
    echo ^<div class="title"^>🪟 WINDOWS DIRECT^</div^>
    echo ^<div class="subtitle"^>HTML → Native Screen^</div^>
    echo ^<div class="clock" id="clock"^>00:00:00^</div^>
    echo ^<div class="counter"^>^<span class="live-counter"^>0^</span^>^</div^>
    echo ^<script^>
    echo function updateClock() {
    echo   const now = new Date();
    echo   document.getElementById('clock').textContent = now.toLocaleTimeString();
    echo }
    echo setInterval(updateClock, 1000);
    echo updateClock();
    echo ^</script^>
    echo ^</body^>
    echo ^</html^>
    ) > test.html
    echo ✅ Created test.html
)

REM Create windows_direct_renderer.js
if not exist windows_direct_renderer.js (
    echo 🧠 Creating windows_direct_renderer.js...
    (
    echo const puppeteer = require("puppeteer");
    echo const fs = require("fs");
    echo const path = require("path");
    echo.
    echo const args = process.argv.slice(2);
    echo const file = args[0];
    echo const fps = parseInt(args[1]) || 1;
    echo const delay = 1000 / fps;
    echo.
    echo if (!file || !fs.existsSync(file)) {
    echo     console.error("❌ HTML file not found:", file);
    echo     process.exit(1);
    echo }
    echo.
    echo (async () => {
    echo     const browser = await puppeteer.launch({
    echo         headless: false,
    echo         args: [
    echo             "--start-fullscreen",
    echo             "--disable-infobars",
    echo             "--kiosk",
    echo             "--no-sandbox"
    echo         ]
    echo     });
    echo.
    echo     const page = await browser.newPage();
    echo     await page.goto("file://" + path.resolve(file));
    echo.
    echo     let frames = 0;
    echo     const start = Date.now();
    echo.
    echo     setInterval(async () => {
    echo         frames++;
    echo         await page.evaluate((frames, start) => {
    echo             const elapsed = Math.floor((Date.now() - start) / 1000);
    echo             document.querySelector("#live-time").textContent = `Live: ${elapsed}s`;
    echo             document.querySelector("#live-frames").textContent = `Frames: ${frames}`;
    echo             document.querySelector(".live-counter").textContent = frames;
    echo         }, frames, start);
    echo     }, delay);
    echo })();
    ) > windows_direct_renderer.js
    echo ✅ Created windows_direct_renderer.js
)

echo.
echo 🚀 Ready to test!
echo Run:
echo   node windows_direct_renderer.js test.html 3
echo.
pause

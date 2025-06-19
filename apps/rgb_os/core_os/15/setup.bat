@echo off
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

REM Install Puppeteer if not yet installed
if not exist node_modules (
    echo 📦 Installing Puppeteer...
    npm install puppeteer
)

REM Create test.html if needed
if not exist test.html (
    echo Creating test.html...
    echo ^<html^>^<body^>Hello HTML^</body^>^</html^> > test.html
)

REM Create JS if needed (placeholder)
if not exist windows_direct_renderer.js (
    echo ⚠️ windows_direct_renderer.js missing!
    echo Please paste the full JS logic here.
    pause
    exit /b 1
)

echo.
echo 🚀 Launching live render now...
node windows_direct_renderer.js test.html 2
pause

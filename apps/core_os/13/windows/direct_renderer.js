// windows_direct_renderer.js - HTML → Direct Windows Screen Rendering
const puppeteer = require('puppeteer');
const fs = require('fs');
const { spawn, exec } = require('child_process');
const path = require('path');

class WindowsDirectRenderer {
    constructor() {
        this.browser = null;
        this.page = null;
        this.screenWidth = 1920;
        this.screenHeight = 1080;
        this.isRunning = false;
        this.frameCount = 0;
        this.startTime = Date.now();
        this.tempDir = process.env.TEMP || 'C:\\temp';
    }

    async initialize() {
        console.log('🖥️  Initializing Windows Direct Screen Renderer...');
        
        // Detect screen resolution
        await this.detectScreenResolution();
        
        // Launch headless browser
        this.browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-dev-shm-usage'
            ]
        });

        this.page = await this.browser.newPage();
        
        await this.page.setViewport({
            width: this.screenWidth,
            height: this.screenHeight,
            deviceScaleFactor: 1
        });

        // Ensure temp directory exists
        if (!fs.existsSync(this.tempDir)) {
            fs.mkdirSync(this.tempDir, { recursive: true });
        }

        console.log(`✅ Windows renderer ready - ${this.screenWidth}x${this.screenHeight}`);
    }

    async detectScreenResolution() {
        return new Promise((resolve) => {
            // Use PowerShell to get screen resolution
            exec('powershell "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen.Bounds"', 
                (error, stdout, stderr) => {
                    if (!error && stdout) {
                        const lines = stdout.trim().split('\n');
                        for (const line of lines) {
                            if (line.includes('Width')) {
                                this.screenWidth = parseInt(line.split(':')[1].trim()) || 1920;
                            }
                            if (line.includes('Height')) {
                                this.screenHeight = parseInt(line.split(':')[1].trim()) || 1080;
                            }
                        }
                    }
                    console.log(`📺 Detected screen: ${this.screenWidth}x${this.screenHeight}`);
                    resolve();
                });
        });
    }

    async startDirectRendering(htmlFile, fps = 2) {
        console.log(`🎬 Starting direct Windows rendering of ${htmlFile} at ${fps}fps...`);
        
        const htmlPath = `file:///${path.resolve(htmlFile).replace(/\\/g, '/')}`;
        await this.page.goto(htmlPath, { waitUntil: 'networkidle0' });
        
        this.isRunning = true;
        const frameInterval = 1000 / fps;
        
        // Inject live update capability
        await this.page.evaluate(() => {
            if (!window.windowsLiveData) {
                window.windowsLiveData = {
                    startTime: Date.now(),
                    frameCount: 0
                };
                
                setInterval(() => {
                    const timeEl = document.getElementById('live-time');
                    if (timeEl) {
                        const elapsed = Math.floor((Date.now() - window.windowsLiveData.startTime) / 1000);
                        timeEl.textContent = `Live: ${elapsed}s`;
                    }
                    
                    const frameEl = document.getElementById('live-frames');
                    if (frameEl) {
                        frameEl.textContent = `Frames: ${window.windowsLiveData.frameCount}`;
                    }
                    
                    const counters = document.querySelectorAll('.live-counter');
                    counters.forEach(counter => {
                        const current = parseInt(counter.textContent) || 0;
                        counter.textContent = current + 1;
                    });
                }, 1000);
            }
        });
        
        console.log('🚀 Starting Windows direct screen rendering...');
        console.log('⚠️  Note: This will take over your entire screen!');
        console.log('⌨️  Press Ctrl+C to stop and restore desktop');
        
        // Start rendering loop
        while (this.isRunning) {
            const frameStart = Date.now();
            
            try {
                await this.page.evaluate((count) => {
                    if (window.windowsLiveData) {
                        window.windowsLiveData.frameCount = count;
                    }
                }, this.frameCount);
                
                await this.renderToScreen();
                this.frameCount++;
                
                if (this.frameCount % 10 === 0) {
                    const elapsed = (Date.now() - this.startTime) / 1000;
                    const actualFPS = this.frameCount / elapsed;
                    console.log(`📊 Frame ${this.frameCount}, ${actualFPS.toFixed(1)} fps`);
                }
                
            } catch (error) {
                console.error(`⚠️ Frame ${this.frameCount} error:`, error.message);
            }
            
            const frameTime = Date.now() - frameStart;
            const delay = Math.max(0, frameInterval - frameTime);
            
            if (delay > 0) {
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }

    async renderToScreen() {
        // Capture screenshot
        const screenshot = await this.page.screenshot({
            type: 'png',
            fullPage: false,
            clip: {
                x: 0,
                y: 0,
                width: this.screenWidth,
                height: this.screenHeight
            }
        });

        // Save to temp file
        const tempImage = path.join(this.tempDir, 'screen_frame.png');
        fs.writeFileSync(tempImage, screenshot);
        
        // Set as wallpaper using Windows API
        await this.setAsWallpaper(tempImage);
    }

    async setAsWallpaper(imagePath) {
        return new Promise((resolve, reject) => {
            // Use PowerShell to set wallpaper
            const psScript = `
                Add-Type -TypeDefinition @"
                using System;
                using System.Runtime.InteropServices;
                public class Wallpaper {
                    [DllImport("user32.dll", CharSet = CharSet.Auto)]
                    public static extern int SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);
                }
"@
                [Wallpaper]::SystemParametersInfo(20, 0, "${imagePath.replace(/\\/g, '\\\\')}", 3)
            `;
            
            exec(`powershell -Command "${psScript}"`, (error, stdout, stderr) => {
                if (error) {
                    // Fallback: try alternative method
                    this.setWallpaperFallback(imagePath).then(resolve).catch(reject);
                } else {
                    resolve();
                }
            });
        });
    }

    async setWallpaperFallback(imagePath) {
        // Alternative method using reg command
        return new Promise((resolve, reject) => {
            const commands = [
                `reg add "HKCU\\Control Panel\\Desktop" /v Wallpaper /t REG_SZ /d "${imagePath}" /f`,
                'RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters'
            ];
            
            let completed = 0;
            commands.forEach(cmd => {
                exec(cmd, (error) => {
                    completed++;
                    if (completed === commands.length) {
                        resolve();
                    }
                });
            });
        });
    }

    async createFullscreenWindow(imagePath) {
        // Alternative: Create a borderless fullscreen window
        const psScript = `
            Add-Type -AssemblyName System.Windows.Forms
            Add-Type -AssemblyName System.Drawing
            
            $form = New-Object System.Windows.Forms.Form
            $form.WindowState = 'Maximized'
            $form.FormBorderStyle = 'None'
            $form.TopMost = $true
            $form.BackgroundImage = [System.Drawing.Image]::FromFile("${imagePath}")
            $form.BackgroundImageLayout = 'Stretch'
            
            $form.Show()
            Start-Sleep -Milliseconds 100
            $form.Close()
        `;
        
        return new Promise((resolve) => {
            exec(`powershell -Command "${psScript}"`, () => resolve());
        });
    }

    async stop() {
        console.log('🛑 Stopping Windows direct renderer...');
        this.isRunning = false;
        
        // Restore desktop
        await this.restoreDesktop();
        
        if (this.browser) {
            await this.browser.close();
        }
        
        // Clean up temp files
        try {
            const tempImage = path.join(this.tempDir, 'screen_frame.png');
            if (fs.existsSync(tempImage)) {
                fs.unlinkSync(tempImage);
            }
        } catch (e) {
            // Ignore cleanup errors
        }
        
        console.log('✅ Windows renderer stopped, desktop restored');
    }

    async restoreDesktop() {
        // Restore original wallpaper or set to solid color
        const psScript = `
            Add-Type -TypeDefinition @"
            using System;
            using System.Runtime.InteropServices;
            public class Wallpaper {
                [DllImport("user32.dll", CharSet = CharSet.Auto)]
                public static extern int SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);
            }
"@
            [Wallpaper]::SystemParametersInfo(20, 0, "", 3)
        `;
        
        return new Promise((resolve) => {
            exec(`powershell -Command "${psScript}"`, () => {
                console.log('🖥️  Desktop wallpaper restored');
                resolve();
            });
        });
    }
}

// Main execution
async function main() {
    const htmlFile = process.argv[2];
    const fps = parseFloat(process.argv[3]) || 2;
    
    if (!htmlFile) {
        console.log('Windows Direct Screen Renderer');
        console.log('Usage: node windows_direct_renderer.js <html_file> [fps]');
        console.log('Example: node windows_direct_renderer.js test.html 3');
        console.log('');
        console.log('⚠️  WARNING: This will take over your entire screen!');
        console.log('⌨️  Press Ctrl+C to stop and restore desktop');
        process.exit(1);
    }

    if (!fs.existsSync(htmlFile)) {
        console.error(`❌ HTML file not found: ${htmlFile}`);
        process.exit(1);
    }

    const renderer = new WindowsDirectRenderer();
    
    // Handle graceful shutdown
    process.on('SIGINT', async () => {
        console.log('\n⚡ Shutting down and restoring desktop...');
        await renderer.stop();
        process.exit(0);
    });
    
    process.on('SIGTERM', async () => {
        await renderer.stop();
        process.exit(0);
    });
    
    try {
        await renderer.initialize();
        await renderer.startDirectRendering(htmlFile, fps);
    } catch (error) {
        console.error(`💥 Error: ${error.message}`);
        await renderer.stop();
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}
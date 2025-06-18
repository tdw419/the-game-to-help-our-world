// html_to_framebuffer.js - Minimal HTML → Framebuffer Pipeline
const puppeteer = require('puppeteer');
const fs = require('fs');
const { spawn } = require('child_process');

class HTMLFramebufferRenderer {
    constructor() {
        this.browser = null;
        this.page = null;
        this.fbWidth = 1024;
        this.fbHeight = 768;
    }

    async initialize() {
        console.log('🖥️  Initializing HTML → Framebuffer renderer...');
        
        // Launch headless browser
        this.browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security'
            ]
        });

        this.page = await this.browser.newPage();
        
        // Set viewport to framebuffer resolution
        await this.page.setViewport({
            width: this.fbWidth,
            height: this.fbHeight,
            deviceScaleFactor: 1
        });

        console.log(`✅ Browser ready - ${this.fbWidth}x${this.fbHeight}`);
    }

    async renderHTMLToFramebuffer(htmlFile) {
        console.log(`🎨 Rendering ${htmlFile} to framebuffer...`);
        
        // Load HTML file
        const htmlPath = `file://${process.cwd()}/${htmlFile}`;
        await this.page.goto(htmlPath, { waitUntil: 'networkidle0' });
        
        // Screenshot to PNG
        const pngBuffer = await this.page.screenshot({
            type: 'png',
            fullPage: false,
            clip: {
                x: 0,
                y: 0,
                width: this.fbWidth,
                height: this.fbHeight
            }
        });

        // Save PNG temporarily
        fs.writeFileSync('/tmp/framebuffer_output.png', pngBuffer);
        
        // Convert PNG to raw RGB
        await this.convertPNGToRaw('/tmp/framebuffer_output.png', '/tmp/framebuffer_output.raw');
        
        // Write to framebuffer
        await this.writeRawToFramebuffer('/tmp/framebuffer_output.raw');
        
        console.log('✅ HTML rendered to framebuffer!');
    }

    convertPNGToRaw(pngFile, rawFile) {
        return new Promise((resolve, reject) => {
            const convert = spawn('convert', [
                pngFile,
                '-depth', '8',
                '-resize', `${this.fbWidth}x${this.fbHeight}!`,
                `rgb:${rawFile}`
            ]);

            convert.on('close', (code) => {
                if (code === 0) {
                    console.log('🔄 PNG converted to raw RGB');
                    resolve();
                } else {
                    reject(new Error(`ImageMagick convert failed with code ${code}`));
                }
            });

            convert.on('error', (err) => {
                reject(new Error(`ImageMagick not found: ${err.message}`));
            });
        });
    }

    writeRawToFramebuffer(rawFile) {
        return new Promise((resolve, reject) => {
            const dd = spawn('sudo', [
                'dd',
                `if=${rawFile}`,
                'of=/dev/fb0',
                'bs=1M'
            ]);

            dd.on('close', (code) => {
                if (code === 0) {
                    console.log('📺 Raw image written to framebuffer');
                    resolve();
                } else {
                    reject(new Error(`dd command failed with code ${code}`));
                }
            });

            dd.on('error', (err) => {
                reject(new Error(`dd command failed: ${err.message}`));
            });
        });
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
        
        // Clean up temp files
        try {
            fs.unlinkSync('/tmp/framebuffer_output.png');
            fs.unlinkSync('/tmp/framebuffer_output.raw');
        } catch (e) {
            // Ignore cleanup errors
        }
    }
}

// Main execution
async function main() {
    const htmlFile = process.argv[2];
    
    if (!htmlFile) {
        console.log('Usage: node html_to_framebuffer.js <html_file>');
        console.log('Example: node html_to_framebuffer.js pxdigest_lab.html');
        process.exit(1);
    }

    if (!fs.existsSync(htmlFile)) {
        console.error(`❌ HTML file not found: ${htmlFile}`);
        process.exit(1);
    }

    const renderer = new HTMLFramebufferRenderer();
    
    try {
        await renderer.initialize();
        await renderer.renderHTMLToFramebuffer(htmlFile);
        console.log('🎯 Success! HTML is now displayed on framebuffer');
    } catch (error) {
        console.error(`💥 Error: ${error.message}`);
    } finally {
        await renderer.cleanup();
    }
}

if (require.main === module) {
    main();
}
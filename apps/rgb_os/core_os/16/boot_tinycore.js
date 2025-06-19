// boot_tinycore.js
// TinyCore Linux Pixel Processor Bootloader
// Usage: node boot_tinycore.js

const fs = require('fs');
const zlib = require('zlib');
const path = require('path');

class PXScreenVM {
  constructor(width = 1024, height = 768) {
    this.width = width;
    this.height = height;
    this.framebuffer = new Array(width * height).fill([0, 0, 0]);
    this.registers = { R0: 0, R1: 0, R2: 0, R3: 0 };
    this.pc = 0; // Program counter
    this.running = false;
    this.bootStage = 'INIT';
  }

  setPixel(x, y, r, g, b) {
    if (x >= 0 && x < this.width && y >= 0 && y < this.height) {
      const index = y * this.width + x;
      this.framebuffer[index] = [r, g, b];
    }
  }

  getPixel(x, y) {
    if (x >= 0 && x < this.width && y >= 0 && y < this.height) {
      const index = y * this.width + x;
      return this.framebuffer[index];
    }
    return [0, 0, 0];
  }

  // PXTalk Opcode Interpreter
  executeOpcode(r, g, b, x, y) {
    const opcode = (r << 16) | (g << 8) | b;
    
    switch(opcode) {
      case 0xFF0000: // HALT
        console.log(`[${x},${y}] HALT`);
        this.running = false;
        break;
        
      case 0x00FF00: // PRINT_HELLO
        console.log(`[${x},${y}] PRINT_HELLO`);
        break;
        
      case 0x0000FF: // SET_PIXEL_GREEN
        this.setPixel(x + 1, y, 0, 255, 0);
        console.log(`[${x},${y}] SET_PIXEL_GREEN at (${x+1},${y})`);
        break;
        
      case 0xFFFF00: // BOOT_INIT
        console.log(`[${x},${y}] BOOT_INIT - Starting TinyCore boot sequence`);
        this.bootStage = 'LOADING_KERNEL';
        break;
        
      case 0xFF00FF: // LOAD_KERNEL
        console.log(`[${x},${y}] LOAD_KERNEL - Loading TinyCore from PXDigest`);
        this.bootStage = 'KERNEL_LOADED';
        break;
        
      case 0x00FFFF: // START_SHELL
        console.log(`[${x},${y}] START_SHELL - TinyCore shell ready`);
        this.bootStage = 'SHELL_READY';
        break;
        
      default:
        // Treat as data/memory
        break;
    }
  }

  // Execute one VM cycle
  tick() {
    if (!this.running) return false;
    
    // Scan a region of framebuffer for opcodes
    const scanY = Math.floor(this.pc / this.width);
    const scanX = this.pc % this.width;
    
    if (scanY < this.height) {
      const [r, g, b] = this.getPixel(scanX, scanY);
      this.executeOpcode(r, g, b, scanX, scanY);
      this.pc++;
    } else {
      this.running = false;
    }
    
    return this.running;
  }

  // Start VM execution
  start() {
    this.running = true;
    this.pc = 0;
    console.log('[PXScreenVM] Starting execution...');
    
    // Execute ticks
    let cycles = 0;
    while (this.running && cycles < 10000) {
      this.tick();
      cycles++;
    }
    
    console.log(`[PXScreenVM] Execution complete after ${cycles} cycles`);
  }
}

class TinyCoreBootloader {
  constructor() {
    this.vm = new PXScreenVM();
    this.pxdigestPath = 'tinycore.pxdigest';
  }

  loadPXDigest() {
    try {
      if (!fs.existsSync(this.pxdigestPath)) {
        console.log('⚠️  tinycore.pxdigest not found. Creating stub...');
        this.createStubDigest();
        return false;
      }

      const data = fs.readFileSync(this.pxdigestPath);
      console.log(`✅ Loaded PXDigest: ${data.length} bytes`);
      
      // Parse PXDigest header
      const headerEnd = data.indexOf(Buffer.from('\0'));
      if (headerEnd === -1) {
        console.log('❌ Invalid PXDigest format');
        return false;
      }
      
      const header = data.slice(0, headerEnd).toString();
      if (!header.startsWith('PXDIGEST')) {
        console.log('❌ Invalid PXDigest header');
        return false;
      }
      
      console.log(`📦 PXDigest header: ${header}`);
      
      // Extract compressed payload (simplified)
      const payloadStart = data.indexOf(Buffer.from('\0\x1f\x8b')) + 1; // Find GZIP magic
      if (payloadStart > 0) {
        const compressed = data.slice(payloadStart);
        console.log(`🗜️  Compressed payload: ${compressed.length} bytes`);
        
        try {
          const decompressed = zlib.gunzipSync(compressed);
          console.log(`📂 Decompressed: ${decompressed.length} bytes`);
          this.loadKernelIntoPixels(decompressed);
          return true;
        } catch (err) {
          console.log('⚠️  Decompression failed, using stub boot sequence');
        }
      }
      
      return false;
    } catch (err) {
      console.log(`❌ Error loading PXDigest: ${err.message}`);
      return false;
    }
  }

  createStubDigest() {
    // Create a minimal stub for testing
    const stubData = Buffer.concat([
      Buffer.from('PXDIGEST\0'),
      Buffer.from('stub_hash\0'),
      Buffer.from('1024\0'),
      zlib.gzipSync(Buffer.from('TinyCore Linux stub kernel'))
    ]);
    
    fs.writeFileSync(this.pxdigestPath, stubData);
    console.log('📝 Created stub tinycore.pxdigest');
  }

  loadKernelIntoPixels(kernelData) {
    console.log('🎨 Loading kernel data into pixel framebuffer...');
    
    // Draw boot signature
    this.vm.setPixel(0, 0, 255, 255, 0);   // BOOT_INIT
    this.vm.setPixel(1, 0, 255, 0, 255);   // LOAD_KERNEL
    this.vm.setPixel(2, 0, 0, 255, 255);   // START_SHELL
    this.vm.setPixel(3, 0, 255, 0, 0);     // HALT
    
    // Load kernel bytes as pixel data (3 bytes per pixel)
    let pixelIndex = 4;
    for (let i = 0; i < kernelData.length; i += 3) {
      const r = kernelData[i] || 0;
      const g = kernelData[i + 1] || 0;
      const b = kernelData[i + 2] || 0;
      
      const x = pixelIndex % this.vm.width;
      const y = Math.floor(pixelIndex / this.vm.width);
      
      this.vm.setPixel(x, y, r, g, b);
      pixelIndex++;
      
      if (pixelIndex >= this.vm.width * this.vm.height) break;
    }
    
    console.log(`🖼️  Loaded ${pixelIndex} pixels from kernel data`);
  }

  boot() {
    console.log('🚀 TinyCore Pixel Processor Boot Sequence Starting...');
    console.log('================================================');
    
    // Load the digest
    const digestLoaded = this.loadPXDigest();
    
    if (!digestLoaded) {
      console.log('⚠️  Using fallback boot sequence');
      // Create a simple boot pattern
      this.vm.setPixel(0, 0, 255, 255, 0);   // BOOT_INIT
      this.vm.setPixel(1, 0, 0, 255, 0);     // PRINT_HELLO  
      this.vm.setPixel(2, 0, 0, 255, 0);     // PRINT_HELLO
      this.vm.setPixel(3, 0, 255, 0, 0);     // HALT
    }
    
    // Start the pixel VM
    console.log('🧠 Starting PXScreenVM...');
    this.vm.start();
    
    console.log('================================================');
    console.log(`✅ Boot complete. Final stage: ${this.vm.bootStage}`);
  }
}

// Main execution
if (require.main === module) {
  const bootloader = new TinyCoreBootloader();
  bootloader.boot();
}

module.exports = { TinyCoreBootloader, PXScreenVM };
// boot_interactive.js
// Interactive TinyCore Pixel Processor with Shell
// Usage: node boot_interactive.js

const fs = require('fs');
const zlib = require('zlib');
const readline = require('readline');

class InteractivePXScreenVM {
  constructor(width = 1024, height = 768) {
    this.width = width;
    this.height = height;
    this.framebuffer = new Array(width * height).fill([0, 0, 0]);
    this.registers = { R0: 0, R1: 0, R2: 0, R3: 0 };
    this.pc = 0;
    this.running = false;
    this.bootStage = 'INIT';
    this.shell = new PXShell(this);
    this.filesystem = new Map();
    this.processes = [];
  }

  setPixel(x, y, r, g, b) {
    if (x >= 0 && x < this.width && y >= 0 && y < this.height) {
      const index = y * this.width + x;
      this.framebuffer[index] = [r, g, b];
      this.displayPixelChange(x, y, r, g, b);
    }
  }

  displayPixelChange(x, y, r, g, b) {
    // Visual representation of pixel changes
    const color = `RGB(${r},${g},${b})`;
    const symbol = this.getPixelSymbol(r, g, b);
    console.log(`📍 Pixel [${x},${y}] = ${color} ${symbol}`);
  }

  getPixelSymbol(r, g, b) {
    if (r === 255 && g === 0 && b === 0) return '🔴 HALT';
    if (r === 0 && g === 255 && b === 0) return '🟢 EXEC';
    if (r === 0 && g === 0 && b === 255) return '🔵 DATA';
    if (r === 255 && g === 255 && b === 0) return '🟡 BOOT';
    if (r === 255 && g === 0 && b === 255) return '🟣 LOAD';
    if (r === 0 && g === 255 && b === 255) return '🟦 SHELL';
    return '⚪ MEM';
  }

  executeOpcode(r, g, b, x, y) {
    const opcode = (r << 16) | (g << 8) | b;
    
    switch(opcode) {
      case 0xFF0000: // HALT
        console.log(`🔴 [${x},${y}] SYSTEM HALT`);
        this.running = false;
        break;
        
      case 0x00FF00: // PRINT_HELLO / EXEC
        console.log(`🟢 [${x},${y}] EXECUTING PROCESS`);
        this.bootStage = 'EXECUTING';
        break;
        
      case 0x0000FF: // SET_PIXEL_BLUE / DATA
        this.setPixel(x + 1, y, 0, 0, 255);
        console.log(`🔵 [${x},${y}] DATA WRITE`);
        break;
        
      case 0xFFFF00: // BOOT_INIT
        console.log(`🟡 [${x},${y}] SYSTEM BOOT INITIALIZED`);
        this.bootStage = 'BOOTING';
        break;
        
      case 0xFF00FF: // LOAD_KERNEL
        console.log(`🟣 [${x},${y}] KERNEL LOADED INTO MEMORY`);
        this.bootStage = 'KERNEL_READY';
        break;
        
      case 0x00FFFF: // START_SHELL
        console.log(`🟦 [${x},${y}] SHELL INTERFACE ACTIVATED`);
        this.bootStage = 'SHELL_READY';
        this.startInteractiveShell();
        break;
        
      case 0x808080: // NOP
        // No operation - just advance
        break;
        
      default:
        // Treat as memory/data
        if (r + g + b > 0) {
          console.log(`⚪ [${x},${y}] MEMORY: ${r},${g},${b}`);
        }
        break;
    }
  }

  startInteractiveShell() {
    console.log('\n' + '='.repeat(60));
    console.log('🖥️  TINYCORE PIXEL SHELL v1.0');
    console.log('='.repeat(60));
    console.log('Available commands: help, ls, ps, echo, reboot, halt');
    console.log('Type "help" for more information');
    console.log('='.repeat(60) + '\n');
    
    this.shell.start();
  }

  tick() {
    if (!this.running) return false;
    
    const scanY = Math.floor(this.pc / this.width);
    const scanX = this.pc % this.width;
    
    if (scanY < this.height) {
      const [r, g, b] = this.framebuffer[scanY * this.width + scanX] || [0, 0, 0];
      this.executeOpcode(r, g, b, scanX, scanY);
      this.pc++;
    } else {
      if (this.bootStage === 'KERNEL_READY') {
        // Start shell after kernel scan complete
        this.setPixel(10, 10, 0, 255, 255); // START_SHELL opcode
        this.executeOpcode(0, 255, 255, 10, 10);
      }
      this.running = false;
    }
    
    return this.running;
  }

  start() {
    this.running = true;
    this.pc = 0;
    console.log('🧠 [PXScreenVM] Interactive mode starting...\n');
    
    let cycles = 0;
    while (this.running && cycles < 100) {
      this.tick();
      cycles++;
    }
    
    console.log(`\n🔄 [PXScreenVM] Boot scan complete: ${cycles} cycles`);
  }
}

class PXShell {
  constructor(vm) {
    this.vm = vm;
    this.rl = null;
    this.currentDir = '/';
    this.fileSystem = {
      '/': ['bin', 'tmp', 'home'],
      '/bin': ['ls', 'echo', 'cat', 'reboot'],
      '/tmp': [],
      '/home': ['user']
    };
  }

  start() {
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      prompt: 'tinycore@pixel:~$ '
    });

    this.rl.prompt();

    this.rl.on('line', (input) => {
      this.processCommand(input.trim());
      this.rl.prompt();
    });

    this.rl.on('close', () => {
      console.log('\n👋 Shell session ended');
      process.exit(0);
    });
  }

  processCommand(cmd) {
    const parts = cmd.split(' ');
    const command = parts[0];
    const args = parts.slice(1);

    // Log command as pixel operation
    console.log(`💻 Command: ${cmd}`);
    
    switch(command) {
      case 'help':
        this.showHelp();
        break;
        
      case 'ls':
        this.listFiles(args[0] || this.currentDir);
        break;
        
      case 'ps':
        this.showProcesses();
        break;
        
      case 'echo':
        this.echo(args.join(' '));
        break;
        
      case 'cat':
        this.catFile(args[0]);
        break;
        
      case 'pixel':
        this.pixelCommand(args);
        break;
        
      case 'framebuffer':
        this.showFramebuffer();
        break;
        
      case 'reboot':
        this.reboot();
        break;
        
      case 'halt':
        this.halt();
        break;
        
      case 'clear':
        console.clear();
        break;
        
      case '':
        // Empty command, just reprompt
        break;
        
      default:
        console.log(`Command not found: ${command}`);
        console.log(`Type 'help' for available commands`);
    }
  }

  showHelp() {
    console.log('\n📚 Available commands:');
    console.log('  help         - Show this help');
    console.log('  ls [dir]     - List files');
    console.log('  ps           - Show processes');
    console.log('  echo <text>  - Print text');
    console.log('  cat <file>   - Display file');
    console.log('  pixel <x> <y> <r> <g> <b> - Set pixel');
    console.log('  framebuffer  - Show pixel memory');
    console.log('  clear        - Clear screen');
    console.log('  reboot       - Restart system');
    console.log('  halt         - Shutdown system\n');
  }

  listFiles(dir = this.currentDir) {
    const files = this.fileSystem[dir];
    if (files) {
      console.log(`📁 Contents of ${dir}:`);
      files.forEach(file => console.log(`  ${file}`));
    } else {
      console.log(`Directory not found: ${dir}`);
    }
  }

  showProcesses() {
    console.log('📊 Active processes:');
    console.log('  PID  NAME           STATUS');
    console.log('  ---  ----           ------');
    console.log('  001  pxkernel       running');
    console.log('  002  pxshell        running');
    console.log('  003  pxscreenvm     running');
  }

  echo(text) {
    console.log(text);
    // Write echo to pixel memory
    if (text.length > 0) {
      this.vm.setPixel(50, 50, text.charCodeAt(0) % 256, 255, 0);
    }
  }

  catFile(filename) {
    if (!filename) {
      console.log('Usage: cat <filename>');
      return;
    }
    
    switch(filename) {
      case 'version':
        console.log('TinyCore Linux Pixel Edition v1.0');
        break;
      case 'cpuinfo':
        console.log('processor: PXScreenVM');
        console.log('cores: 1048576 (1024x768 pixels)');
        console.log('architecture: RGB-based');
        break;
      case 'meminfo':
        console.log(`MemTotal: ${this.vm.width * this.vm.height * 3} bytes`);
        console.log('MemFree: Variable');
        console.log('PixelMemory: Active');
        break;
      default:
        console.log(`File not found: ${filename}`);
    }
  }

  pixelCommand(args) {
    if (args.length !== 5) {
      console.log('Usage: pixel <x> <y> <r> <g> <b>');
      console.log('Example: pixel 100 200 255 0 0');
      return;
    }
    
    const [x, y, r, g, b] = args.map(Number);
    this.vm.setPixel(x, y, r, g, b);
    console.log(`✅ Pixel set at (${x},${y}) to RGB(${r},${g},${b})`);
  }

  showFramebuffer() {
    console.log('🖼️  Framebuffer Status:');
    console.log(`   Resolution: ${this.vm.width}x${this.vm.height}`);
    console.log(`   Total pixels: ${this.vm.width * this.vm.height}`);
    console.log(`   Registers: R0=${this.vm.registers.R0}, R1=${this.vm.registers.R1}`);
    console.log(`   Boot stage: ${this.vm.bootStage}`);
  }

  reboot() {
    console.log('🔄 Rebooting pixel processor...');
    this.rl.close();
    setTimeout(() => {
      const bootloader = new InteractiveTinyCoreBootloader();
      bootloader.boot();
    }, 1000);
  }

  halt() {
    console.log('🛑 Halting system...');
    this.vm.setPixel(0, 0, 255, 0, 0); // HALT opcode
    this.rl.close();
  }
}

class InteractiveTinyCoreBootloader {
  constructor() {
    this.vm = new InteractivePXScreenVM();
    this.pxdigestPath = 'tinycore.pxdigest';
  }

  loadPXDigest() {
    try {
      if (!fs.existsSync(this.pxdigestPath)) {
        console.log('📝 Creating interactive stub...');
        this.createInteractiveStub();
        return true;
      }
      
      const data = fs.readFileSync(this.pxdigestPath);
      console.log(`✅ Loaded PXDigest: ${data.length} bytes`);
      return true;
    } catch (err) {
      console.log(`❌ Error: ${err.message}`);
      return false;
    }
  }

  createInteractiveStub() {
    // Create enhanced boot sequence with shell activation
    this.vm.setPixel(0, 0, 255, 255, 0);   // BOOT_INIT
    this.vm.setPixel(1, 0, 255, 0, 255);   // LOAD_KERNEL  
    this.vm.setPixel(2, 0, 0, 255, 0);     // EXEC (processes)
    this.vm.setPixel(3, 0, 0, 255, 0);     // EXEC (more processes)
    this.vm.setPixel(4, 0, 0, 255, 255);   // START_SHELL
    this.vm.setPixel(5, 0, 255, 0, 0);     // HALT (end of boot)
  }

  boot() {
    console.log('🚀 TinyCore Interactive Pixel Processor Starting...');
    console.log('=' * 50);
    
    this.loadPXDigest();
    
    console.log('🎨 Loading interactive boot sequence...');
    this.createInteractiveStub();
    
    console.log('🧠 Starting interactive PXScreenVM...');
    this.vm.start();
  }
}

// Main execution
if (require.main === module) {
  const bootloader = new InteractiveTinyCoreBootloader();
  bootloader.boot();
}

module.exports = { InteractiveTinyCoreBootloader, InteractivePXScreenVM };
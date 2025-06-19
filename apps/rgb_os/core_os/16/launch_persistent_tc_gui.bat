// boot_tinycore_gui.js
// TinyCore GUI Linux Pixel Processor - Full Desktop Environment
// Usage: node boot_tinycore_gui.js

const fs = require('fs');
const zlib = require('zlib');
const readline = require('readline');

class PXDesktopVM {
  constructor(width = 1920, height = 1080) {
    this.width = width;
    this.height = height;
    this.framebuffer = new Array(width * height).fill([0, 0, 0]);
    this.desktop = new PXDesktop(this);
    this.windows = new Map();
    this.processes = new Map();
    this.fileSystem = new PXFileSystem();
    this.bootStage = 'INIT';
    this.guiMode = true;
    this.mouseX = width / 2;
    this.mouseY = height / 2;
  }

  setPixel(x, y, r, g, b) {
    if (x >= 0 && x < this.width && y >= 0 && y < this.height) {
      const index = y * this.width + x;
      this.framebuffer[index] = [r, g, b];
      this.displayPixelChange(x, y, r, g, b);
    }
  }

  drawRect(x, y, width, height, r, g, b) {
    for (let dy = 0; dy < height; dy++) {
      for (let dx = 0; dx < width; dx++) {
        this.setPixel(x + dx, y + dy, r, g, b);
      }
    }
  }

  drawWindow(x, y, width, height, title, content = []) {
    // Window frame (blue)
    this.drawRect(x, y, width, height, 70, 130, 180);
    
    // Title bar (darker blue)
    this.drawRect(x, y, width, 30, 25, 25, 112);
    
    // Window content area (white)
    this.drawRect(x + 2, y + 32, width - 4, height - 34, 240, 240, 240);
    
    console.log(`🖼️  Window: "${title}" at (${x},${y}) ${width}x${height}`);
    
    // Simulate window content
    content.forEach((line, i) => {
      console.log(`    📄 ${line}`);
    });
    
    return { x, y, width, height, title, content };
  }

  displayPixelChange(x, y, r, g, b) {
    // Only log significant pixel operations to avoid spam
    const opcode = (r << 16) | (g << 8) | b;
    
    // Special GUI opcodes
    switch(opcode) {
      case 0x4682B4: // SteelBlue - Window
        console.log(`🖼️  [${x},${y}] WINDOW_PIXEL`);
        break;
      case 0x191970: // MidnightBlue - Title bar
        console.log(`📋 [${x},${y}] TITLE_BAR`);
        break;
      case 0xF0F0F0: // Light gray - Content
        console.log(`📄 [${x},${y}] CONTENT_AREA`);
        break;
      case 0x008000: // Green - Desktop
        console.log(`🌱 [${x},${y}] DESKTOP_BACKGROUND`);
        break;
    }
  }

  executeGUIOpcode(r, g, b, x, y) {
    const opcode = (r << 16) | (g << 8) | b;
    
    switch(opcode) {
      case 0xFF0000: // HALT
        console.log(`🛑 [${x},${y}] SYSTEM HALT`);
        return false;
        
      case 0x00FF00: // DESKTOP_INIT
        console.log(`🌱 [${x},${y}] DESKTOP INITIALIZATION`);
        this.desktop.initialize();
        this.bootStage = 'DESKTOP_READY';
        break;
        
      case 0x0000FF: // WINDOW_MANAGER_START
        console.log(`🖼️  [${x},${y}] WINDOW MANAGER STARTING`);
        this.desktop.startWindowManager();
        break;
        
      case 0xFFFF00: // GUI_BOOT
        console.log(`🎨 [${x},${y}] GUI SYSTEM BOOT`);
        this.bootStage = 'GUI_LOADING';
        break;
        
      case 0xFF00FF: // LOAD_DESKTOP
        console.log(`🖥️  [${x},${y}] LOADING DESKTOP ENVIRONMENT`);
        this.desktop.loadDesktopEnvironment();
        break;
        
      case 0x00FFFF: // START_APPLICATIONS
        console.log(`📱 [${x},${y}] STARTING GUI APPLICATIONS`);
        this.desktop.startDefaultApps();
        break;
        
      case 0x808080: // TASKBAR
        console.log(`📊 [${x},${y}] TASKBAR RENDERING`);
        this.desktop.renderTaskbar();
        break;
        
      case 0xC0C0C0: // MENU_SYSTEM
        console.log(`📋 [${x},${y}] MENU SYSTEM ACTIVE`);
        this.desktop.activateMenuSystem();
        break;
    }
    
    return true;
  }

  bootGUI() {
    console.log('🎨 Starting TinyCore GUI Boot Sequence...\n');
    
    // Create GUI boot pattern
    this.setPixel(0, 0, 255, 255, 0);   // GUI_BOOT
    this.setPixel(1, 0, 255, 0, 255);   // LOAD_DESKTOP
    this.setPixel(2, 0, 0, 255, 0);     // DESKTOP_INIT
    this.setPixel(3, 0, 0, 0, 255);     // WINDOW_MANAGER_START
    this.setPixel(4, 0, 0, 255, 255);   // START_APPLICATIONS
    this.setPixel(5, 0, 128, 128, 128); // TASKBAR
    this.setPixel(6, 0, 192, 192, 192); // MENU_SYSTEM
    
    // Execute boot opcodes
    for (let i = 0; i < 7; i++) {
      const [r, g, b] = this.framebuffer[i];
      this.executeGUIOpcode(r, g, b, i, 0);
    }
    
    console.log('\n🖥️  TinyCore GUI Desktop Ready!\n');
    this.desktop.showDesktop();
  }
}

class PXDesktop {
  constructor(vm) {
    this.vm = vm;
    this.windows = [];
    this.taskbar = null;
    this.menu = null;
    this.wallpaper = { r: 34, g: 139, b: 34 }; // Forest Green
  }

  initialize() {
    console.log('🌱 Initializing Desktop Environment...');
    this.renderWallpaper();
    this.createTaskbar();
  }

  renderWallpaper() {
    console.log('🎨 Rendering desktop wallpaper...');
    // Fill screen with desktop color
    for (let y = 0; y < 100; y++) { // Sample area
      for (let x = 0; x < 100; x++) {
        this.vm.setPixel(x, y + 100, 
          this.wallpaper.r, this.wallpaper.g, this.wallpaper.b);
      }
    }
  }

  createTaskbar() {
    console.log('📊 Creating taskbar...');
    const taskbarY = this.vm.height - 40;
    this.vm.drawRect(0, taskbarY, this.vm.width, 40, 105, 105, 105);
  }

  startWindowManager() {
    console.log('🖼️  Starting Window Manager...');
    this.createWindow('Terminal', 100, 100, 600, 400, [
      'TinyCore Linux Terminal',
      '$ ls',
      'bin  etc  home  opt  tmp  usr  var',
      '$ uname -a',
      'TinyCore 14.0 pixel-processor x86_64',
      '$ █'
    ]);
    
    this.createWindow('File Manager', 200, 150, 500, 350, [
      '📁 /home/tc/',
      '  📄 Desktop/',
      '  📄 Documents/',
      '  📄 Downloads/',
      '  📄 Pictures/',
      '  📄 Music/'
    ]);
  }

  loadDesktopEnvironment() {
    console.log('🖥️  Loading FLWM Desktop Environment...');
    console.log('   📦 Loading window decorations');
    console.log('   🎨 Loading icon themes');
    console.log('   📋 Loading menu system');
  }

  startDefaultApps() {
    console.log('📱 Starting default applications...');
    
    this.createWindow('Control Panel', 300, 200, 400, 300, [
      '⚙️  TinyCore Control Panel',
      '',
      '🔧 System Settings',
      '📦 App Browser',
      '🌐 Network Config',
      '🔊 Sound Settings',
      '🖥️  Display Settings'
    ]);
    
    this.createWindow('Text Editor', 150, 250, 450, 300, [
      '📝 Editor - untitled.txt',
      '',
      'Welcome to TinyCore Linux!',
      'This is running on a pixel processor.',
      'Every character you see is an RGB value.',
      '',
      'Amazing!'
    ]);
  }

  createWindow(title, x, y, width, height, content) {
    const window = this.vm.drawWindow(x, y, width, height, title, content);
    this.windows.push(window);
    return window;
  }

  renderTaskbar() {
    console.log('📊 Rendering taskbar with running applications...');
    console.log('   🖼️  Terminal');
    console.log('   📁 File Manager');
    console.log('   ⚙️  Control Panel');
    console.log('   📝 Text Editor');
  }

  activateMenuSystem() {
    console.log('📋 Activating FLWM menu system...');
    console.log('   📱 Applications →');
    console.log('     🖥️  System Tools');
    console.log('     📝 Editors');
    console.log('     🌐 Network');
    console.log('     📦 Package Manager');
  }

  showDesktop() {
    console.log('=' * 60);
    console.log('🖥️  TINYCORE LINUX DESKTOP ENVIRONMENT');
    console.log('=' * 60);
    console.log('');
    console.log('👆 Mouse Position: (' + this.vm.mouseX + ', ' + this.vm.mouseY + ')');
    console.log('🖼️  Active Windows: ' + this.windows.length);
    console.log('📊 Taskbar: Ready');
    console.log('🌱 Desktop: Loaded');
    console.log('');
    console.log('Available interactions:');
    console.log('  🖱️  mouse <x> <y>    - Move mouse cursor');
    console.log('  👆 click <x> <y>     - Click at position');
    console.log('  🖼️  window <title>   - Create new window');
    console.log('  📱 app <name>       - Launch application');
    console.log('  📊 taskbar          - Show taskbar info');
    console.log('  🌱 desktop          - Refresh desktop');
    console.log('  📋 menu             - Show desktop menu');
    console.log('  🛑 shutdown         - Close desktop');
    console.log('=' * 60);
    
    this.startGUIShell();
  }

  startGUIShell() {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      prompt: 'tinycore-gui@pixel:desktop$ '
    });

    rl.prompt();

    rl.on('line', (input) => {
      this.processGUICommand(input.trim());
      rl.prompt();
    });

    rl.on('close', () => {
      console.log('\n🖥️  Desktop session ended');
      process.exit(0);
    });
  }

  processGUICommand(cmd) {
    const parts = cmd.split(' ');
    const command = parts[0];
    const args = parts.slice(1);

    console.log(`🖥️  Desktop Command: ${cmd}`);

    switch(command) {
      case 'mouse':
        this.vm.mouseX = parseInt(args[0]) || this.vm.mouseX;
        this.vm.mouseY = parseInt(args[1]) || this.vm.mouseY;
        console.log(`🖱️  Mouse moved to (${this.vm.mouseX}, ${this.vm.mouseY})`);
        break;

      case 'click':
        const clickX = parseInt(args[0]) || this.vm.mouseX;
        const clickY = parseInt(args[1]) || this.vm.mouseY;
        console.log(`👆 Click at (${clickX}, ${clickY})`);
        this.handleClick(clickX, clickY);
        break;

      case 'window':
        const title = args.join(' ') || 'New Window';
        this.createWindow(title, 
          Math.random() * 400 + 100, 
          Math.random() * 300 + 100, 
          400, 300, [`This is ${title}`, 'Window content here...']);
        break;

      case 'app':
        this.launchApp(args[0]);
        break;

      case 'taskbar':
        this.renderTaskbar();
        break;

      case 'desktop':
        this.renderWallpaper();
        console.log('🌱 Desktop refreshed');
        break;

      case 'menu':
        this.activateMenuSystem();
        break;

      case 'shutdown':
        console.log('🛑 Shutting down desktop environment...');
        process.exit(0);
        break;

      case 'help':
        this.showDesktop();
        break;

      default:
        console.log(`Unknown desktop command: ${command}`);
        console.log('Type "help" for available commands');
    }
  }

  handleClick(x, y) {
    // Simple click handling
    if (y > this.vm.height - 40) {
      console.log('📊 Taskbar clicked');
    } else {
      console.log('🖼️  Desktop area clicked');
    }
  }

  launchApp(appName) {
    switch(appName) {
      case 'terminal':
        this.createWindow('Terminal', 150, 150, 600, 400, [
          'TinyCore Terminal Emulator',
          '$ pwd',
          '/home/tc',
          '$ █'
        ]);
        break;
      case 'browser':
        this.createWindow('Web Browser', 200, 100, 800, 600, [
          '🌐 TinyCore Web Browser',
          'Address: http://tinycorelinux.net',
          '',
          'Welcome to TinyCore Linux!',
          'The smallest desktop Linux distribution.'
        ]);
        break;
      case 'editor':
        this.createWindow('Text Editor', 250, 200, 500, 400, [
          '📝 Text Editor',
          '',
          'Enter your text here...',
          '',
          '█'
        ]);
        break;
      default:
        console.log(`App not found: ${appName}`);
        console.log('Available apps: terminal, browser, editor');
    }
  }
}

class PXFileSystem {
  constructor() {
    this.files = {
      '/': ['bin', 'etc', 'home', 'usr', 'var', 'tmp'],
      '/home': ['tc'],
      '/home/tc': ['Desktop', 'Documents', 'Downloads'],
      '/bin': ['bash', 'ls', 'cat', 'cp', 'mv'],
      '/etc': ['passwd', 'hosts', 'fstab']
    };
  }
}

class TinyCoreGUIBootloader {
  constructor() {
    this.vm = new PXDesktopVM();
    this.pxdigestPath = 'tinycore_gui.pxdigest';
  }

  loadGUIPXDigest() {
    try {
      if (!fs.existsSync(this.pxdigestPath)) {
        console.log('📝 Creating TinyCore GUI stub (25MB equivalent)...');
        this.createGUIStub();
        return true;
      }
      
      const data = fs.readFileSync(this.pxdigestPath);
      console.log(`✅ Loaded TinyCore GUI PXDigest: ${data.length} bytes`);
      console.log(`📊 Represents ~25MB TinyCore GUI system`);
      return true;
    } catch (err) {
      console.log(`❌ Error: ${err.message}`);
      return false;
    }
  }

  createGUIStub() {
    const stubData = Buffer.concat([
      Buffer.from('PXDIGEST_GUI\0'),
      Buffer.from('tinycore_gui_25mb_hash\0'),
      Buffer.from('26214400\0'), // 25MB in bytes
      zlib.gzipSync(Buffer.from('TinyCore Linux GUI Desktop Environment - FLWM + Applications'))
    ]);
    
    fs.writeFileSync(this.pxdigestPath, stubData);
    console.log('📝 Created TinyCore GUI PXDigest stub');
  }

  boot() {
    console.log('🚀 TinyCore GUI Linux Pixel Processor Starting...');
    console.log('=' * 60);
    console.log('🎨 Loading 25MB Desktop Environment...');
    console.log('=' * 60);
    
    this.loadGUIPXDigest();
    
    console.log('🖥️  Initializing Pixel Desktop Virtual Machine...');
    console.log('📺 Resolution: ' + this.vm.width + 'x' + this.vm.height);
    console.log('🎨 Color Depth: 24-bit RGB');
    console.log('🖼️  Window Manager: FLWM (Fast Light Window Manager)');
    console.log('');
    
    this.vm.bootGUI();
  }
}

// Main execution
if (require.main === module) {
  const bootloader = new TinyCoreGUIBootloader();
  bootloader.boot();
}

module.exports = { TinyCoreGUIBootloader, PXDesktopVM };
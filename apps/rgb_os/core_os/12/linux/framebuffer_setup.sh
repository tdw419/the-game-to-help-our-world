#!/bin/bash
# Complete HTML → Framebuffer Setup

set -e

echo "🖥️  HTML → Framebuffer Pipeline Setup"
echo "======================================"

# Check dependencies
echo "📋 Checking dependencies..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y nodejs npm
    else
        echo "Please install Node.js manually"
        exit 1
    fi
fi

# Check ImageMagick
if ! command -v convert &> /dev/null; then
    echo "❌ ImageMagick not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y imagemagick
    else
        echo "Please install ImageMagick manually"
        exit 1
    fi
fi

# Check framebuffer
if [ ! -e /dev/fb0 ]; then
    echo "⚠️  Framebuffer /dev/fb0 not found"
    echo "💡 Try: sudo modprobe vfb vfb_enable=1"
    echo "💡 Or boot into console mode"
fi

echo "✅ Dependencies checked"

# Create package.json
echo "📦 Setting up Node.js environment..."
cat > package.json << 'EOF'
{
  "name": "html-framebuffer-renderer",
  "version": "1.0.0",
  "dependencies": {
    "puppeteer": "^21.0.0"
  }
}
EOF

# Install dependencies
npm install

echo "✅ Setup complete!"
echo ""
echo "📋 Usage:"
echo "  node html_to_framebuffer.js your_file.html"
echo ""
echo "📝 Example HTML files you can test:"
echo "  echo '<h1 style=\"color:white;background:black;margin:0;padding:50px;font-size:72px;\">Hello Framebuffer!</h1>' > test.html"
echo "  node html_to_framebuffer.js test.html"
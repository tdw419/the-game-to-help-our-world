// digestmaker.js
// PXDigest generator for any binary file
// Usage: node digestmaker.js input.iso output.pxdigest

const fs = require('fs');
const zlib = require('zlib');
const crypto = require('crypto');
const path = require('path');

function createPXDigest(inputPath, outputPath) {
  try {
    console.log(`📂 Reading input file: ${inputPath}`);
    const inputData = fs.readFileSync(inputPath);
    console.log(`📊 Input size: ${inputData.length} bytes (${(inputData.length / 1024 / 1024).toFixed(2)} MB)`);

    // Generate SHA-256 hash
    const sha256 = crypto.createHash('sha256');
    sha256.update(inputData);
    const digestHex = sha256.digest('hex');
    console.log(`🔐 SHA-256: ${digestHex.substring(0, 16)}...`);

    // Compress with GZIP
    console.log('🗜️  Compressing...');
    const compressed = zlib.gzipSync(inputData, { level: 9 });
    const compressionRatio = ((1 - compressed.length / inputData.length) * 100).toFixed(1);
    console.log(`✅ Compressed: ${compressed.length} bytes (${compressionRatio}% reduction)`);

    // Create PXDigest format:
    // PXDIGEST\0 + SHA256\0 + OriginalSize\0 + CompressedData
    const header = Buffer.from('PXDIGEST\0', 'utf8');
    const hashBuffer = Buffer.from(digestHex + '\0', 'utf8');
    const sizeBuffer = Buffer.from(inputData.length.toString() + '\0', 'utf8');

    const output = Buffer.concat([
      header,
      hashBuffer,
      sizeBuffer,
      compressed
    ]);

    // Write output
    fs.writeFileSync(outputPath, output);
    console.log(`💾 PXDigest written to: ${outputPath}`);
    console.log(`📦 Final size: ${output.length} bytes`);
    
    // Generate optional C++ loader
    const cppPath = outputPath.replace('.pxdigest', '_loader.cpp');
    generateCppLoader(output, cppPath);
    
    return true;
  } catch (err) {
    console.error(`❌ Error: ${err.message}`);
    return false;
  }
}

function generateCppLoader(digestData, outputPath) {
  console.log(`🔧 Generating C++ loader: ${outputPath}`);
  
  let cppCode = `// Auto-generated PXDigest loader
// Compile with: g++ -o loader ${path.basename(outputPath)}

#include <iostream>
#include <vector>
#include <fstream>

const unsigned char pxdigest_data[] = {
`;

  // Convert binary to hex array
  for (let i = 0; i < digestData.length; i++) {
    if (i % 16 === 0) cppCode += '\n  ';
    cppCode += `0x${digestData[i].toString(16).padStart(2, '0')}`;
    if (i < digestData.length - 1) cppCode += ', ';
  }

  cppCode += `
};

const size_t pxdigest_size = ${digestData.length};

int main() {
    std::cout << "PXDigest Loader" << std::endl;
    std::cout << "Data size: " << pxdigest_size << " bytes" << std::endl;
    
    // Write to file for verification
    std::ofstream out("extracted.pxdigest", std::ios::binary);
    out.write(reinterpret_cast<const char*>(pxdigest_data), pxdigest_size);
    out.close();
    
    std::cout << "Extracted to: extracted.pxdigest" << std::endl;
    return 0;
}
`;

  fs.writeFileSync(outputPath, cppCode);
  console.log(`✅ C++ loader generated`);
}

// Command line interface
if (require.main === module) {
  if (process.argv.length < 4) {
    console.log('Usage: node digestmaker.js <input_file> <output_file>');
    console.log('');
    console.log('Examples:');
    console.log('  node digestmaker.js tinycore.iso tinycore.pxdigest');
    console.log('  node digestmaker.js busybox_static busybox.pxdigest');
    console.log('  node digestmaker.js kernel.img kernel.pxdigest');
    process.exit(1);
  }

  const inputPath = process.argv[2];
  const outputPath = process.argv[3];

  if (!fs.existsSync(inputPath)) {
    console.error(`❌ Input file not found: ${inputPath}`);
    process.exit(1);
  }

  console.log('================================================');
  console.log('           PXDigest Generator v1.0');
  console.log('================================================');
  
  const success = createPXDigest(inputPath, outputPath);
  
  if (success) {
    console.log('================================================');
    console.log('✅ PXDigest creation completed successfully!');
    console.log('================================================');
  } else {
    console.log('================================================');
    console.log('❌ PXDigest creation failed');
    console.log('================================================');
    process.exit(1);
  }
}

module.exports = { createPXDigest };
/**
 * PXLDISK File System v1.1
 * Pixel-based file system for PixelNet using PNG canvas storage
 * 
 * Structure:
 * - Row 0: Magic header "PXLDISKv1.1" + metadata
 * - Rows 1-8: Directory entries (filename + row pointer + size)
 * - Rows 9+: File content data
 */

class PXLDiskFS {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.width = 256;
        this.height = 256;
        this.maxFiles = 8;
        this.headerRow = 0;
        this.directoryStart = 1;
        this.contentStart = 9;
        this.maxContentRows = 247; // 256 - 9
        this.magicHeader = "PXLDISKv1.1";
    }

    /**
     * Initialize disk from canvas element
     * @param {HTMLCanvasElement} canvas - Canvas containing the disk image
     * @returns {boolean} Success status
     */
    async initDisk(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        
        // Validate dimensions
        if (canvas.width !== this.width || canvas.height !== this.height) {
            console.error('Invalid disk dimensions. Expected 256x256');
            return false;
        }

        // Check for valid header
        const headerData = this.readRow(this.headerRow);
        const headerText = this.bytesToString(headerData.slice(0, this.magicHeader.length));
        
        if (headerText !== this.magicHeader) {
            console.warn('Invalid or missing PXLDISK header. Initializing new disk...');
            await this.formatDisk();
        }

        console.log('PXLDISK initialized successfully');
        return true;
    }

    /**
     * Format disk with fresh header and empty directory
     */
    async formatDisk() {
        // Write magic header
        const headerBytes = new Uint8Array(this.width);
        const magicBytes = this.stringToBytes(this.magicHeader);
        headerBytes.set(magicBytes, 0);
        headerBytes[magicBytes.length] = 0x01; // Version major
        headerBytes[magicBytes.length + 1] = 0x01; // Version minor
        headerBytes[magicBytes.length + 2] = this.maxFiles; // Max files
        
        this.writeRow(this.headerRow, headerBytes);

        // Clear directory rows
        const emptyRow = new Uint8Array(this.width);
        for (let i = this.directoryStart; i < this.contentStart; i++) {
            this.writeRow(i, emptyRow);
        }

        console.log('Disk formatted with PXLDISK v1.1');
    }

    /**
     * List all files in the directory
     * @returns {Array} Array of file objects {name, size, startRow}
     */
    listFiles() {
        const files = [];
        
        for (let dirRow = this.directoryStart; dirRow < this.contentStart; dirRow++) {
            const dirData = this.readRow(dirRow);
            
            // Check if entry is used (first byte non-zero)
            if (dirData[0] === 0) continue;
            
            // Extract filename (first 32 bytes, null-terminated)
            let nameEnd = 32;
            for (let i = 0; i < 32; i++) {
                if (dirData[i] === 0) {
                    nameEnd = i;
                    break;
                }
            }
            const name = this.bytesToString(dirData.slice(0, nameEnd));
            
            // Extract metadata
            const startRow = (dirData[32] << 8) | dirData[33]; // 2 bytes
            const size = (dirData[34] << 24) | (dirData[35] << 16) | 
                        (dirData[36] << 8) | dirData[37]; // 4 bytes
            
            files.push({ name, size, startRow });
        }
        
        return files;
    }

    /**
     * Write file to disk
     * @param {string} name - Filename (max 31 chars)
     * @param {string|Uint8Array} data - File content
     * @returns {boolean} Success status
     */
    writeFile(name, data) {
        if (name.length > 31) {
            console.error('Filename too long (max 31 characters)');
            return false;
        }

        // Convert data to bytes
        const dataBytes = typeof data === 'string' ? 
            this.stringToBytes(data) : new Uint8Array(data);
        
        const requiredRows = Math.ceil(dataBytes.length / this.width);
        
        if (requiredRows > this.maxContentRows) {
            console.error('File too large for disk');
            return false;
        }

        // Find free directory slot
        let dirSlot = -1;
        for (let i = this.directoryStart; i < this.contentStart; i++) {
            const dirData = this.readRow(i);
            if (dirData[0] === 0) {
                dirSlot = i;
                break;
            }
        }

        if (dirSlot === -1) {
            console.error('Directory full');
            return false;
        }

        // Find free content rows
        const usedRows = new Set();
        const files = this.listFiles();
        
        files.forEach(file => {
            const fileRows = Math.ceil(file.size / this.width);
            for (let i = 0; i < fileRows; i++) {
                usedRows.add(file.startRow + i);
            }
        });

        // Find consecutive free rows
        let startRow = -1;
        let consecutiveFree = 0;
        
        for (let row = this.contentStart; row < this.height; row++) {
            if (usedRows.has(row)) {
                consecutiveFree = 0;
                startRow = -1;
            } else {
                if (startRow === -1) startRow = row;
                consecutiveFree++;
                
                if (consecutiveFree >= requiredRows) {
                    break;
                }
            }
        }

        if (consecutiveFree < requiredRows) {
            console.error('Not enough free space');
            return false;
        }

        // Write file content
        for (let i = 0; i < requiredRows; i++) {
            const rowData = new Uint8Array(this.width);
            const startIdx = i * this.width;
            const endIdx = Math.min(startIdx + this.width, dataBytes.length);
            rowData.set(dataBytes.slice(startIdx, endIdx));
            
            this.writeRow(startRow + i, rowData);
        }

        // Write directory entry
        const dirEntry = new Uint8Array(this.width);
        const nameBytes = this.stringToBytes(name);
        dirEntry.set(nameBytes, 0);
        
        // Metadata: startRow (2 bytes) + size (4 bytes)
        dirEntry[32] = (startRow >> 8) & 0xFF;
        dirEntry[33] = startRow & 0xFF;
        dirEntry[34] = (dataBytes.length >> 24) & 0xFF;
        dirEntry[35] = (dataBytes.length >> 16) & 0xFF;
        dirEntry[36] = (dataBytes.length >> 8) & 0xFF;
        dirEntry[37] = dataBytes.length & 0xFF;
        
        this.writeRow(dirSlot, dirEntry);

        console.log(`File '${name}' written successfully (${dataBytes.length} bytes)`);
        return true;
    }

    /**
     * Read file from disk
     * @param {string} name - Filename
     * @returns {Uint8Array|null} File content or null if not found
     */
    readFile(name) {
        const files = this.listFiles();
        const file = files.find(f => f.name === name);
        
        if (!file) {
            console.error(`File '${name}' not found`);
            return null;
        }

        const requiredRows = Math.ceil(file.size / this.width);
        const data = new Uint8Array(file.size);
        
        for (let i = 0; i < requiredRows; i++) {
            const rowData = this.readRow(file.startRow + i);
            const startIdx = i * this.width;
            const copyLength = Math.min(this.width, file.size - startIdx);
            
            data.set(rowData.slice(0, copyLength), startIdx);
        }

        return data;
    }

    /**
     * Delete file from disk
     * @param {string} name - Filename
     * @returns {boolean} Success status
     */
    deleteFile(name) {
        const files = this.listFiles();
        const fileIndex = files.findIndex(f => f.name === name);
        
        if (fileIndex === -1) {
            console.error(`File '${name}' not found`);
            return false;
        }

        const file = files[fileIndex];
        const requiredRows = Math.ceil(file.size / this.width);

        // Clear content rows
        const emptyRow = new Uint8Array(this.width);
        for (let i = 0; i < requiredRows; i++) {
            this.writeRow(file.startRow + i, emptyRow);
        }

        // Clear directory entry
        const dirRow = this.directoryStart + fileIndex;
        this.writeRow(dirRow, emptyRow);

        console.log(`File '${name}' deleted successfully`);
        return true;
    }

    /**
     * Update existing file
     * @param {string} name - Filename
     * @param {string|Uint8Array} newData - New content
     * @returns {boolean} Success status
     */
    updateFile(name, newData) {
        // Simple implementation: delete and rewrite
        if (this.deleteFile(name)) {
            return this.writeFile(name, newData);
        }
        return false;
    }

    /**
     * Get disk usage statistics
     * @returns {Object} Usage stats
     */
    getDiskStats() {
        const files = this.listFiles();
        let usedBytes = 0;
        let usedRows = 0;

        files.forEach(file => {
            usedBytes += file.size;
            usedRows += Math.ceil(file.size / this.width);
        });

        const totalBytes = this.maxContentRows * this.width;
        const freeBytes = totalBytes - usedBytes;
        const freeRows = this.maxContentRows - usedRows;

        return {
            filesCount: files.length,
            maxFiles: this.maxFiles,
            usedBytes,
            freeBytes,
            totalBytes,
            usedRows,
            freeRows,
            totalRows: this.maxContentRows,
            usagePercent: Math.round((usedBytes / totalBytes) * 100)
        };
    }

    // Utility methods
    readRow(row) {
        const imageData = this.ctx.getImageData(0, row, this.width, 1);
        return imageData.data.filter((_, i) => i % 4 === 0); // Extract R channel only
    }

    writeRow(row, data) {
        const imageData = new ImageData(this.width, 1);
        for (let i = 0; i < this.width; i++) {
            const pixelIndex = i * 4;
            imageData.data[pixelIndex] = data[i] || 0;     // R
            imageData.data[pixelIndex + 1] = 0;             // G
            imageData.data[pixelIndex + 2] = 0;             // B
            imageData.data[pixelIndex + 3] = 255;           // A
        }
        this.ctx.putImageData(imageData, 0, row);
    }

    stringToBytes(str) {
        return new TextEncoder().encode(str);
    }

    bytesToString(bytes) {
        return new TextDecoder().decode(bytes);
    }

    // Export canvas as PNG blob
    async exportDisk() {
        return new Promise(resolve => {
            this.canvas.toBlob(resolve, 'image/png');
        });
    }
}

// Export for use in HTML pages
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PXLDiskFS;
} else {
    window.PXLDiskFS = PXLDiskFS;
}
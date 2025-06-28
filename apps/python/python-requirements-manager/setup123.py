#!/bin/bash
# Ultimate requirements installer - handles all common issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REQUIREMENTS_FILE="${1:-requirements.txt}"
CHUNK_SIZE="${CHUNK_SIZE:-5}"
MAX_RETRIES="${MAX_RETRIES:-3}"
TIMEOUT="${TIMEOUT:-300}"

echo -e "${GREEN}🚀 Ultimate Requirements Installer${NC}"
echo "Requirements file: $REQUIREMENTS_FILE"
echo "Chunk size: $CHUNK_SIZE"
echo "Max retries: $MAX_RETRIES"
echo "Timeout: $TIMEOUT seconds"
echo

# Check if requirements file exists
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${RED}❌ Requirements file not found: $REQUIREMENTS_FILE${NC}"
    exit 1
fi

# Function to install a single package with retries
install_package() {
    local package=$1
    local attempt=1
    
    while [ $attempt -le $MAX_RETRIES ]; do
        echo -e "${YELLOW}Installing $package (attempt $attempt/$MAX_RETRIES)${NC}"
        
        if pip install \
            --prefer-binary \
            --timeout $TIMEOUT \
            --no-cache-dir \
            "$package"; then
            echo -e "${GREEN}✅ $package installed successfully${NC}"
            return 0
        else
            echo -e "${RED}❌ Attempt $attempt failed for $package${NC}"
            attempt=$((attempt + 1))
            sleep 2
        fi
    done
    
    echo -e "${RED}❌ Failed to install $package after $MAX_RETRIES attempts${NC}"
    return 1
}

# Main installation logic
main() {
    echo -e "${YELLOW}🔧 Upgrading pip...${NC}"
    pip install --upgrade pip setuptools wheel
    
    echo -e "${YELLOW}📋 Reading requirements...${NC}"
    # Filter out comments and empty lines
    packages=($(grep -v '^#' "$REQUIREMENTS_FILE" | grep -v '^$' | tr '\n' ' '))
    total_packages=${#packages[@]}
    
    echo "Found $total_packages packages to install"
    echo
    
    # Try installing in chunks first
    echo -e "${YELLOW}📦 Attempting chunk installation...${NC}"
    failed_packages=()
    
    for ((i=0; i<$total_packages; i+=$CHUNK_SIZE)); do
        chunk=("${packages[@]:$i:$CHUNK_SIZE}")
        chunk_num=$((i/$CHUNK_SIZE + 1))
        
        echo -e "${YELLOW}Installing chunk $chunk_num: ${chunk[*]}${NC}"
        
        if pip install \
            --prefer-binary \
            --timeout $TIMEOUT \
            --no-cache-dir \
            "${chunk[@]}"; then
            echo -e "${GREEN}✅ Chunk $chunk_num installed successfully${NC}"
        else
            echo -e "${RED}❌ Chunk $chunk_num failed, will retry individually${NC}"
            failed_packages+=("${chunk[@]}")
        fi
        
        # Small delay between chunks
        sleep 1
    done
    
    # Retry failed packages individually
    if [ ${#failed_packages[@]} -gt 0 ]; then
        echo
        echo -e "${YELLOW}🔄 Retrying ${#failed_packages[@]} failed packages individually...${NC}"
        
        final_failures=()
        for package in "${failed_packages[@]}"; do
            if ! install_package "$package"; then
                final_failures+=("$package")
            fi
        done
        
        # Report final results
        echo
        if [ ${#final_failures[@]} -eq 0 ]; then
            echo -e "${GREEN}🎉 All packages installed successfully!${NC}"
        else
            echo -e "${RED}❌ Failed to install ${#final_failures[@]} packages:${NC}"
            printf '%s\n' "${final_failures[@]}"
            echo
            echo -e "${YELLOW}💡 Try installing these manually:${NC}"
            for package in "${final_failures[@]}"; do
                echo "pip install $package"
            done
            exit 1
        fi
    else
        echo -e "${GREEN}🎉 All packages installed successfully!${NC}"
    fi
    
    # Verify installation
    echo
    echo -e "${YELLOW}🔍 Verifying installation...${NC}"
    pip check && echo -e "${GREEN}✅ All dependencies satisfied${NC}" || echo -e "${RED}⚠️  Dependency conflicts detected${NC}"
}

# Trap errors
trap 'echo -e "${RED}❌ Installation failed!${NC}"; exit 1' ERR

# Run main function
main

echo
echo -e "${GREEN}✅ Installation process complete!${NC}"
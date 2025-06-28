#!/usr/bin/env python3
"""
Robust requirements installer that handles common installation issues
"""
import subprocess
import sys
import time
import os
from pathlib import Path

def run_command(cmd, retries=3, delay=5):
    """Run command with retries"""
    for attempt in range(retries):
        try:
            print(f"Attempt {attempt + 1}/{retries}: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return result
        except subprocess.CalledProcessError as e:
            print(f"Attempt {attempt + 1} failed: {e.stderr}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                raise e

def install_requirements(requirements_file="requirements.txt", chunk_size=10):
    """Install requirements in chunks with error handling"""
    
    # Read requirements
    with open(requirements_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"Installing {len(lines)} packages in chunks of {chunk_size}")
    
    # Upgrade pip first
    print("Upgrading pip...")
    run_command([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
    
    # Install in chunks
    failed_packages = []
    
    for i in range(0, len(lines), chunk_size):
        chunk = lines[i:i + chunk_size]
        print(f"\nInstalling chunk {i//chunk_size + 1}: {chunk}")
        
        try:
            # Try with pre-compiled wheels first
            cmd = [
                sys.executable, '-m', 'pip', 'install',
                '--prefer-binary',  # Use wheels when available
                '--timeout', '300',  # 5 minute timeout
                '--retries', '3',
                '--no-cache-dir',  # Fresh install
            ] + chunk
            
            run_command(cmd)
            print(f"✓ Successfully installed chunk {i//chunk_size + 1}")
            
        except subprocess.CalledProcessError:
            # Try installing packages individually
            print(f"Chunk failed, trying individual packages...")
            for package in chunk:
                try:
                    cmd = [sys.executable, '-m', 'pip', 'install', 
                          '--prefer-binary', '--timeout', '300', package]
                    run_command(cmd)
                    print(f"✓ {package}")
                except subprocess.CalledProcessError as e:
                    print(f"✗ Failed to install {package}: {e}")
                    failed_packages.append(package)
    
    if failed_packages:
        print(f"\n⚠️  Failed packages: {failed_packages}")
        return False
    else:
        print("\n🎉 All packages installed successfully!")
        return True

def setup_environment():
    """Setup optimal environment for installation"""
    # Set environment variables for better installation
    os.environ['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    os.environ['PIP_NO_CACHE_DIR'] = '1'
    os.environ['PIP_TIMEOUT'] = '300'
    
    # Increase wheel cache
    os.environ['PIP_FIND_LINKS'] = 'https://download.pytorch.org/whl/torch_stable.html'

if __name__ == "__main__":
    setup_environment()
    
    # Check if requirements file exists
    req_file = sys.argv[1] if len(sys.argv) > 1 else "requirements.txt"
    
    if not Path(req_file).exists():
        print(f"Requirements file {req_file} not found!")
        sys.exit(1)
    
    success = install_requirements(req_file)
    sys.exit(0 if success else 1)
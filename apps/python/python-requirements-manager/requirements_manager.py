"""
Requirements Manager - Handle dynamic requirements installation and management
"""
import subprocess
import sys
import importlib
import pkg_resources
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RequirementsManager:
    """Manage and install requirements dynamically"""
    
    def __init__(self, requirements_file: str = "requirements.txt"):
        self.requirements_file = Path(requirements_file)
        self.installed_packages = set()
        self.failed_packages = set()
        
    def parse_requirements(self) -> List[str]:
        """Parse requirements file and return list of packages"""
        if not self.requirements_file.exists():
            logger.error(f"Requirements file {self.requirements_file} not found")
            return []
        
        packages = []
        with open(self.requirements_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    packages.append(line)
        
        return packages
    
    def is_package_installed(self, package_spec: str) -> bool:
        """Check if a package is installed"""
        try:
            # Extract package name from specification
            package_name = package_spec.split('==')[0].split('>=')[0].split('<=')[0]
            pkg_resources.get_distribution(package_name)
            return True
        except pkg_resources.DistributionNotFound:
            return False
        except Exception as e:
            logger.warning(f"Error checking {package_spec}: {e}")
            return False
    
    def install_package(self, package: str, retries: int = 3) -> bool:
        """Install a single package with retries"""
        for attempt in range(retries):
            try:
                logger.info(f"Installing {package} (attempt {attempt + 1}/{retries})")
                
                cmd = [
                    sys.executable, '-m', 'pip', 'install',
                    '--prefer-binary',
                    '--timeout', '300',
                    '--retries', '3',
                    package
                ]
                
                result = subprocess.run(
                    cmd, 
                    check=True, 
                    capture_output=True, 
                    text=True
                )
                
                logger.info(f"✓ Successfully installed {package}")
                self.installed_packages.add(package)
                return True
                
            except subprocess.CalledProcessError as e:
                logger.warning(f"Attempt {attempt + 1} failed for {package}: {e.stderr}")
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    logger.error(f"✗ Failed to install {package} after {retries} attempts")
                    self.failed_packages.add(package)
                    return False
        
        return False
    
    def install_requirements(self, chunk_size: int = 5) -> Tuple[List[str], List[str]]:
        """Install all requirements in chunks"""
        packages = self.parse_requirements()
        missing_packages = []
        
        # Check which packages are missing
        for package in packages:
            if not self.is_package_installed(package):
                missing_packages.append(package)
        
        if not missing_packages:
            logger.info("All requirements already satisfied!")
            return [], []
        
        logger.info(f"Found {len(missing_packages)} missing packages")
        
        # Try chunk installation first
        success_chunks = []
        failed_packages = []
        
        for i in range(0, len(missing_packages), chunk_size):
            chunk = missing_packages[i:i + chunk_size]
            logger.info(f"Installing chunk: {chunk}")
            
            try:
                cmd = [
                    sys.executable, '-m', 'pip', 'install',
                    '--prefer-binary',
                    '--timeout', '300',
                ] + chunk
                
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                success_chunks.extend(chunk)
                logger.info(f"✓ Chunk installed successfully")
                
            except subprocess.CalledProcessError:
                logger.warning("Chunk failed, trying individual packages...")
                
                # Try individual packages in the failed chunk
                for package in chunk:
                    if not self.install_package(package):
                        failed_packages.append(package)
        
        return list(self.installed_packages), failed_packages
    
    def verify_imports(self, import_map: Dict[str, str]) -> Dict[str, bool]:
        """Verify that packages can be imported"""
        results = {}
        
        for package_name, import_name in import_map.items():
            try:
                importlib.import_module(import_name)
                results[package_name] = True
                logger.info(f"✓ {package_name} imports successfully")
            except ImportError as e:
                results[package_name] = False
                logger.error(f"✗ {package_name} import failed: {e}")
        
        return results
    
    def get_package_info(self, package_name: str) -> Optional[Dict]:
        """Get information about an installed package"""
        try:
            dist = pkg_resources.get_distribution(package_name)
            return {
                'name': dist.project_name,
                'version': dist.version,
                'location': dist.location,
                'requires': [str(req) for req in dist.requires()]
            }
        except pkg_resources.DistributionNotFound:
            return None

# Global instance
requirements_manager = RequirementsManager()

# Convenience functions
def ensure_requirements(requirements_file: str = "requirements.txt") -> bool:
    """Ensure all requirements are installed"""
    manager = RequirementsManager(requirements_file)
    installed, failed = manager.install_requirements()
    
    if failed:
        logger.error(f"Failed to install: {failed}")
        return False
    
    logger.info("All requirements satisfied!")
    return True

def safe_import(package_name: str, pip_name: str = None):
    """Safely import a package, installing if necessary"""
    try:
        return importlib.import_module(package_name)
    except ImportError:
        if pip_name is None:
            pip_name = package_name
        
        logger.info(f"Package {package_name} not found, installing {pip_name}...")
        
        if requirements_manager.install_package(pip_name):
            return importlib.import_module(package_name)
        else:
            raise ImportError(f"Failed to install and import {package_name}")

def check_critical_packages() -> bool:
    """Check if critical packages are available"""
    critical_imports = {
        'numpy': 'numpy',
        'flask': 'flask', 
        'requests': 'requests',
        'yaml': 'yaml',
        'psutil': 'psutil'
    }
    
    results = requirements_manager.verify_imports(critical_imports)
    missing = [pkg for pkg, status in results.items() if not status]
    
    if missing:
        logger.error(f"Critical packages missing: {missing}")
        return False
    
    return True

# Auto-install decorator
def requires(*packages):
    """Decorator to ensure packages are installed before function execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for package in packages:
                if not requirements_manager.is_package_installed(package):
                    logger.info(f"Installing required package: {package}")
                    requirements_manager.install_package(package)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Example usage in your application
if __name__ == "__main__":
    # Example usage
    
    # 1. Ensure all requirements are installed
    if ensure_requirements():
        print("✅ All requirements satisfied!")
    
    # 2. Safe import with auto-install
    try:
        np = safe_import('numpy')
        flask = safe_import('flask')
        print("✅ Critical packages imported successfully!")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
    
    # 3. Check critical packages
    if check_critical_packages():
        print("✅ All critical packages available!")
    
    # 4. Get package info
    info = requirements_manager.get_package_info('numpy')
    if info:
        print(f"NumPy version: {info['version']}")
    
    # 5. Use decorator for function requirements
    @requires('requests==2.31.0', 'beautifulsoup4')
    def web_scraping_function():
        import requests
        from bs4 import BeautifulSoup
        print("Ready for web scraping!")
    
    web_scraping_function()
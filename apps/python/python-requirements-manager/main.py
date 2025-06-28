#!/usr/bin/env python3
"""
Main Application - Example of using the requirements manager
"""

# Import the requirements manager first
from requirements_manager import (
    ensure_requirements, 
    safe_import, 
    check_critical_packages,
    requires,
    requirements_manager
)

import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def startup_checks():
    """Perform startup checks and requirements installation"""
    logger.info("🚀 Starting application...")
    
    # 1. Ensure all requirements are installed
    logger.info("📦 Checking requirements...")
    if not ensure_requirements():
        logger.error("❌ Failed to install requirements!")
        sys.exit(1)
    
    # 2. Check critical packages
    logger.info("🔍 Verifying critical packages...")
    if not check_critical_packages():
        logger.error("❌ Critical packages missing!")
        sys.exit(1)
    
    logger.info("✅ All requirements satisfied!")

def initialize_components():
    """Initialize application components with safe imports"""
    try:
        # Safe imports - will auto-install if missing
        global np, pd, flask, requests, yaml, psutil
        
        logger.info("📥 Importing core packages...")
        np = safe_import('numpy')
        pd = safe_import('pandas')
        flask = safe_import('flask', 'flask==2.3.3')
        requests = safe_import('requests')
        yaml = safe_import('yaml', 'pyyaml')
        psutil = safe_import('psutil')
        
        logger.info("✅ Core packages imported successfully!")
        
        # Optional packages - won't fail if missing
        try:
            global redis, boto3, sklearn
            redis = safe_import('redis')
            boto3 = safe_import('boto3')
            sklearn = safe_import('sklearn', 'scikit-learn')
            logger.info("✅ Optional packages imported!")
        except ImportError as e:
            logger.warning(f"⚠️  Optional package failed: {e}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Failed to import required packages: {e}")
        return False

# Use decorator for functions with specific requirements
@requires('cryptography==42.0.5', 'authlib==1.3.1')
def setup_security():
    """Setup security components"""
    from cryptography.fernet import Fernet
    from authlib.integrations.flask_client import OAuth
    
    logger.info("🔐 Security components initialized")
    return True

@requires('unicorn==2.0.1', 'capstone==5.0.1')
def setup_emulation():
    """Setup emulation components"""
    import unicorn
    import capstone
    
    logger.info("🖥️  Emulation components initialized")
    return True

@requires('pillow==10.3.0')
def setup_imaging():
    """Setup imaging components"""
    from PIL import Image
    
    logger.info("🖼️  Imaging components initialized")
    return True

class Application:
    """Main application class"""
    
    def __init__(self):
        self.components_initialized = False
        self.flask_app = None
        
    def initialize(self):
        """Initialize the application"""
        try:
            # Startup checks
            startup_checks()
            
            # Initialize components
            if not initialize_components():
                raise RuntimeError("Failed to initialize components")
            
            # Setup optional components
            self.setup_optional_components()
            
            # Create Flask app
            self.flask_app = flask.Flask(__name__)
            self.setup_routes()
            
            self.components_initialized = True
            logger.info("🎉 Application initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Application initialization failed: {e}")
            raise
    
    def setup_optional_components(self):
        """Setup optional components based on what's available"""
        try:
            setup_security()
        except Exception as e:
            logger.warning(f"Security setup failed: {e}")
        
        try:
            setup_emulation()
        except Exception as e:
            logger.warning(f"Emulation setup failed: {e}")
            
        try:
            setup_imaging()
        except Exception as e:
            logger.warning(f"Imaging setup failed: {e}")
    
    def setup_routes(self):
        """Setup Flask routes"""
        @self.flask_app.route('/')
        def home():
            return {
                'status': 'running',
                'components': 'initialized' if self.components_initialized else 'failed'
            }
        
        @self.flask_app.route('/health')
        def health():
            """Health check endpoint"""
            try:
                # Check system resources
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                
                return {
                    'status': 'healthy',
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'packages_status': self.get_package_status()
                }
            except Exception as e:
                return {'status': 'unhealthy', 'error': str(e)}, 500
        
        @self.flask_app.route('/packages')
        def packages():
            """Get package information"""
            return self.get_package_status()
    
    def get_package_status(self):
        """Get status of installed packages"""
        critical_packages = [
            'numpy', 'flask', 'requests', 'pyyaml', 'psutil'
        ]
        
        status = {}
        for package in critical_packages:
            info = requirements_manager.get_package_info(package)
            status[package] = {
                'installed': info is not None,
                'version': info['version'] if info else None
            }
        
        return status
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the application"""
        if not self.components_initialized:
            raise RuntimeError("Application not initialized. Call initialize() first.")
        
        logger.info(f"🌐 Starting server on {host}:{port}")
        self.flask_app.run(host=host, port=port, debug=debug)

# Example usage functions
def example_data_processing():
    """Example function using numpy and pandas"""
    logger.info("📊 Running data processing example...")
    
    # Create sample data
    data = np.random.rand(100, 3)
    df = pd.DataFrame(data, columns=['A', 'B', 'C'])
    
    # Basic operations
    result = {
        'mean': df.mean().to_dict(),
        'std': df.std().to_dict(),
        'shape': df.shape
    }
    
    logger.info(f"Data processing complete: {result}")
    return result

def example_web_request():
    """Example function using requests"""
    logger.info("🌐 Making web request example...")
    
    try:
        response = requests.get('https://httpbin.org/json', timeout=10)
        result = response.json()
        logger.info("Web request successful!")
        return result
    except Exception as e:
        logger.error(f"Web request failed: {e}")
        return None

def main():
    """Main entry point"""
    try:
        # Create and initialize application
        app = Application()
        app.initialize()
        
        # Run some examples
        example_data_processing()
        example_web_request()
        
        # Start the web server
        logger.info("🚀 Starting web server...")
        app.run(debug=True)
        
    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
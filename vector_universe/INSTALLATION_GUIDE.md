# Vector Universe Installation Guide

## 📋 System Requirements

### Minimum Requirements
- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS 11+, Windows 10+
- **Python**: 3.8 or higher
- **Memory**: 4GB RAM (8GB recommended for full features)
- **Storage**: 2GB free disk space
- **Processor**: x86_64 architecture, 2+ cores

### Recommended Requirements
- **Operating System**: Ubuntu 22.04 LTS
- **Python**: 3.9 or 3.10
- **Memory**: 16GB RAM
- **Storage**: 10GB SSD
- **Processor**: x86_64, 4+ cores, AVX2 support

## 🚀 Installation Methods

### Method 1: Quick Start (Recommended)

```bash
# Clone the repository
git clone https://github.com/vector-universe/vector-universe.git
cd vector-universe

# Install dependencies
pip install -r requirements.txt

# Run the system
python self_contained_vector_universe.py
```

### Method 2: Manual Installation

```bash
# Create virtual environment (recommended)
python -m venv vector-env
source vector-env/bin/activate  # Linux/macOS
# vector-env\Scripts\activate  # Windows

# Install core dependencies
pip install numpy chromadb scikit-learn networkx

# Install optional dependencies
pip install weaviate-client qdrant-client

# Run the system
python self_contained_vector_universe.py
```

### Method 3: Docker Installation

```bash
# Build Docker image
docker build -t vector-universe .

# Run container
docker run -it --rm vector-universe
```

## 📦 Dependency Installation

### Core Dependencies

```bash
pip install numpy chromadb scikit-learn networkx
```

### Optional Dependencies

```bash
# For Weaviate support
pip install weaviate-client

# For Qdrant support
pip install qdrant-client

# For advanced features
pip install pandas matplotlib seaborn
```

### Development Dependencies

```bash
pip install pytest black flake8 mypy
```

## 🔧 Configuration

### Basic Configuration

```python
# Minimal configuration
config = {
    'database': {
        'default_collection': 'main_vectors',
        'index_type': 'hnsw'
    },
    'hypervisor': {
        'max_vms': 10,
        'memory_limit_mb': 1024
    },
    'simulator': {
        'hostname': 'vector-linux',
        'kernel_version': '5.15.0-vector'
    }
}

# Initialize with configuration
vector_universe = SelfContainedVectorUniverse(config)
```

### Advanced Configuration

```python
# Comprehensive configuration
advanced_config = {
    'database': {
        'default_collection': 'production_vectors',
        'index_type': 'hnsw',
        'cache_size': 10000,
        'persistence': 'memory_optimized'
    },
    'hypervisor': {
        'max_vms': 20,
        'memory_limit_mb': 2048,
        'cpu_allocation': 'dynamic'
    },
    'simulator': {
        'hostname': 'vector-linux-pro',
        'kernel_version': '5.15.0-vector',
        'services': ['ssh', 'web', 'database'],
        'memory_mb': 2048
    },
    'performance': {
        'monitoring_interval': 60,
        'optimization_frequency': 300,
        'logging_level': 'INFO'
    }
}
```

## 🎯 Platform-Specific Notes

### Linux Installation

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv
pip3 install -r requirements.txt
```

### macOS Installation

```bash
# Install Python
brew install python

# Install dependencies
pip install -r requirements.txt
```

### Windows Installation

```bash
# Install Python from python.org
# Run in PowerShell
python -m pip install -r requirements.txt
```

## 🔍 Troubleshooting

### Common Issues

**Issue: ImportError for chromadb**
```bash
pip install chromadb
```

**Issue: Python version too old**
```bash
# Upgrade Python
sudo apt install python3.9
```

**Issue: Memory errors**
```bash
# Increase memory or reduce workload
export VECTOR_UNIVERSE_MEMORY_LIMIT=2048
```

### Debugging

```bash
# Run with debug logging
python self_contained_vector_universe.py --debug

# Check system requirements
python check_requirements.py
```

## 📊 Performance Tuning

### Memory Optimization

```python
# Configure for memory efficiency
config = {
    'database': {
        'cache_size': 5000,
        'persistence': 'memory_optimized'
    },
    'hypervisor': {
        'memory_limit_mb': 1024
    }
}
```

### Speed Optimization

```python
# Configure for performance
config = {
    'database': {
        'index_type': 'hnsw',
        'optimization_frequency': 60
    },
    'performance': {
        'monitoring_interval': 30,
        'parallel_operations': True
    }
}
```

## 🎓 Verification

### Test Installation

```bash
# Run system tests
python -m pytest tests/ -v

# Check system health
python check_system.py
```

### Validate Configuration

```python
# Test configuration
python validate_config.py --config my_config.json
```

## 🚀 Deployment Options

### Local Deployment

```bash
# Run locally
python self_contained_vector_universe.py

# Run as service
nohup python self_contained_vector_universe.py &
```

### Cloud Deployment

```bash
# AWS EC2
# Use t3.large instance or better
# Install as above

# Google Cloud
# Use e2-medium instance or better
# Install as above
```

### Container Deployment

```bash
# Build and run container
docker build -t vector-universe .
docker run -d -p 8000:8000 vector-universe
```

## 📚 Additional Resources

### Configuration Examples
- `configs/basic.json` - Simple configuration
- `configs/advanced.json` - Full-featured configuration
- `configs/production.json` - Production-ready setup

### Troubleshooting Guides
- `docs/troubleshooting/import_errors.md`
- `docs/troubleshooting/performance_issues.md`
- `docs/troubleshooting/memory_management.md`

### Performance Guides
- `docs/performance/optimization.md`
- `docs/performance/benchmarking.md`
- `docs/performance/scaling.md`

## 🎉 Next Steps

1. **Run the system**: `python self_contained_vector_universe.py`
2. **Explore examples**: Check the `examples/` directory
3. **Review documentation**: Read the complete API reference
4. **Join the community**: Contribute to the project

**Welcome to Vector Universe!** 🚀
# Installation Guide

Complete guide to installing and deploying Santiq in various environments.

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Installation](#quick-installation)
3. [Installation Methods](#installation-methods)
4. [Development Installation](#development-installation)
5. [Production Deployment](#production-deployment)
6. [Docker Deployment](#docker-deployment)
7. [Troubleshooting](#troubleshooting)

## 💻 System Requirements

### Minimum Requirements

- **Python**: 3.11 or higher
- **Memory**: 4 GB RAM
- **Storage**: 1 GB free space
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)

### Recommended Requirements

- **Python**: 3.12 or higher
- **Memory**: 8 GB RAM or more
- **Storage**: 5 GB free space
- **CPU**: Multi-core processor
- **Network**: Internet connection for plugin installation

### Dependencies

Santiq automatically installs these core dependencies:

- **pandas**: Data manipulation and analysis
- **pyarrow**: Efficient data handling
- **pydantic**: Data validation
- **typer**: CLI framework
- **rich**: Rich terminal output
- **pyyaml**: YAML configuration parsing

## ⚡ Quick Installation

### Using pip (Recommended)

```bash
# Install Santiq
pip install santiq

# Verify installation
santiq --version
```

### Using conda

```bash
# Create new environment (optional)
conda create -n santiq python=3.11

# Activate environment
conda activate santiq

# Install Santiq
pip install santiq

# Verify installation
santiq --version
```

## 📦 Installation Methods

### Method 1: PyPI Installation

Install the latest stable release from PyPI:

```bash
# Install latest version
pip install santiq

# Install specific version
pip install santiq==0.1.5

# Upgrade existing installation
pip install --upgrade santiq
```

### Method 2: GitHub Installation

Install directly from the GitHub repository:

```bash
# Install from main branch
pip install git+https://github.com/yourusername/santiq.git

# Install from specific branch
pip install git+https://github.com/yourusername/santiq.git@develop

# Install from specific commit
pip install git+https://github.com/yourusername/santiq.git@commit-hash
```

### Method 3: Local Installation

Install from a local copy of the repository:

```bash
# Clone repository
git clone https://github.com/yourusername/santiq.git
cd santiq

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

## 🛠️ Development Installation

### Prerequisites

```bash
# Install development tools
pip install build twine pytest black isort mypy pre-commit

# Or install all dev dependencies
pip install -e ".[dev]"
```

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/santiq.git
cd santiq

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black .
isort .

# Type checking
mypy santiq/
```

### Development Dependencies

The development installation includes:

- **pytest**: Testing framework
- **black**: Code formatter
- **isort**: Import sorter
- **mypy**: Static type checker
- **pre-commit**: Git hooks
- **coverage**: Test coverage
- **tox**: Multi-environment testing

## 🚀 Production Deployment

### Standard Production Installation

```bash
# Create dedicated user (recommended)
sudo useradd -r -s /bin/false santiq

# Create installation directory
sudo mkdir -p /opt/santiq
sudo chown santiq:santiq /opt/santiq

# Install Santiq
sudo -u santiq pip install --user santiq

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~santiq/.bashrc
```

### System-wide Installation

```bash
# Install system-wide
sudo pip install santiq

# Create configuration directory
sudo mkdir -p /etc/santiq
sudo chown santiq:santiq /etc/santiq

# Create data directories
sudo mkdir -p /var/lib/santiq/{data,logs,plugins}
sudo chown santiq:santiq /var/lib/santiq -R
```

### Environment Configuration

Create environment configuration file:

```bash
# Create environment file
sudo tee /etc/santiq/environment << EOF
SANTIQ_HOME=/opt/santiq
SANTIQ_DATA=/var/lib/santiq/data
SANTIQ_LOGS=/var/lib/santiq/logs
SANTIQ_PLUGINS=/var/lib/santiq/plugins
SANTIQ_CONFIG=/etc/santiq
EOF
```

### Service Configuration

Create systemd service file:

```bash
# Create service file
sudo tee /etc/systemd/system/santiq.service << EOF
[Unit]
Description=Santiq ETL Service
After=network.target

[Service]
Type=simple
User=santiq
Group=santiq
EnvironmentFile=/etc/santiq/environment
ExecStart=/usr/local/bin/santiq run pipeline /etc/santiq/pipeline.yml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable santiq
sudo systemctl start santiq
```

## 🐳 Docker Deployment

### Docker Installation

```bash
# Pull official image
docker pull santiq/santiq:latest

# Run container
docker run -it --rm santiq/santiq:latest --version
```

### Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  santiq:
    image: santiq/santiq:latest
    container_name: santiq
    environment:
      - SANTIQ_DATA=/data
      - SANTIQ_LOGS=/logs
      - SANTIQ_PLUGINS=/plugins
    volumes:
      - ./data:/data
      - ./logs:/logs
      - ./plugins:/plugins
      - ./config:/config
    working_dir: /config
    command: ["santiq", "run", "pipeline", "pipeline.yml"]
    restart: unless-stopped

  santiq-scheduler:
    image: santiq/santiq:latest
    container_name: santiq-scheduler
    environment:
      - SANTIQ_DATA=/data
      - SANTIQ_LOGS=/logs
    volumes:
      - ./data:/data
      - ./logs:/logs
      - ./config:/config
    working_dir: /config
    command: ["santiq", "run", "pipeline", "scheduled-pipeline.yml"]
    restart: unless-stopped
    depends_on:
      - santiq
```

### Custom Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create santiq user
RUN useradd -r -s /bin/false santiq

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Santiq
RUN pip install --no-cache-dir santiq

# Create directories
RUN mkdir -p /data /logs /plugins /config
RUN chown santiq:santiq /data /logs /plugins /config

# Switch to santiq user
USER santiq

# Set environment variables
ENV SANTIQ_DATA=/data
ENV SANTIQ_LOGS=/logs
ENV SANTIQ_PLUGINS=/plugins
ENV SANTIQ_CONFIG=/config

# Expose ports (if needed)
EXPOSE 8000

# Default command
CMD ["santiq", "--help"]
```

## 🔧 Configuration

### Global Configuration

Create global configuration file:

```bash
# Create config directory
mkdir -p ~/.config/santiq

# Create global config
cat > ~/.config/santiq/config.yml << EOF
# Global Santiq configuration
defaults:
  log_level: INFO
  cache_intermediate_results: true
  max_memory_mb: 4000
  parallel_execution: false

paths:
  data: ~/santiq/data
  logs: ~/santiq/logs
  plugins: ~/santiq/plugins
  temp: ~/santiq/temp

plugins:
  registry_url: https://pypi.org/simple/
  local_dirs: []
  auto_update: true

audit:
  enabled: true
  log_path: ~/santiq/logs/audit.log
  retention_days: 30
EOF
```

### Environment Variables

Set important environment variables:

```bash
# Add to ~/.bashrc or ~/.zshrc
export SANTIQ_HOME="$HOME/santiq"
export SANTIQ_DATA="$SANTIQ_HOME/data"
export SANTIQ_LOGS="$SANTIQ_HOME/logs"
export SANTIQ_PLUGINS="$SANTIQ_HOME/plugins"
export SANTIQ_CONFIG="$HOME/.config/santiq"

# Create directories
mkdir -p "$SANTIQ_DATA" "$SANTIQ_LOGS" "$SANTIQ_PLUGINS"
```

## 🔍 Verification

### Installation Verification

```bash
# Check version
santiq --version

# Check help
santiq --help

# List available plugins
santiq plugin list

# Test basic functionality
santiq init test-pipeline
santiq run pipeline test-pipeline.yml --dry-run
```

### System Verification

```bash
# Check Python version
python --version

# Check pip installation
pip show santiq

# Check dependencies
pip list | grep -E "(pandas|pyarrow|pydantic|typer|rich|pyyaml)"

# Check CLI availability
which santiq
```

## 🚨 Troubleshooting

### Common Issues

#### Issue: Command not found

```bash
# Solution: Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall with --user flag
pip install --user santiq
```

#### Issue: Permission denied

```bash
# Solution: Fix permissions
sudo chown -R $USER:$USER ~/.local
chmod +x ~/.local/bin/santiq
```

#### Issue: Import errors

```bash
# Solution: Reinstall dependencies
pip uninstall santiq
pip install santiq --force-reinstall

# Or install in virtual environment
python -m venv santiq-env
source santiq-env/bin/activate
pip install santiq
```

#### Issue: Plugin not found

```bash
# Solution: Check plugin discovery
santiq plugin list --verbose

# Reinstall plugins
santiq plugin update

# Check plugin directory
ls -la ~/santiq/plugins/
```

### Debug Mode

Enable debug logging:

```bash
# Set debug environment variable
export SANTIQ_LOG_LEVEL=DEBUG

# Run with verbose output
santiq run pipeline config.yml --verbose
```

### Log Files

Check log files for errors:

```bash
# Check application logs
tail -f ~/santiq/logs/santiq.log

# Check audit logs
tail -f ~/santiq/logs/audit.log

# Check system logs (if using systemd)
sudo journalctl -u santiq -f
```

### Performance Issues

```bash
# Monitor memory usage
ps aux | grep santiq

# Check disk space
df -h ~/santiq/

# Monitor system resources
htop
```

## 🔄 Upgrading

### Upgrade Santiq

```bash
# Upgrade to latest version
pip install --upgrade santiq

# Upgrade specific version
pip install --upgrade santiq==0.2.0

# Upgrade with dependencies
pip install --upgrade --force-reinstall santiq
```

### Upgrade Plugins

```bash
# Update all plugins
santiq plugin update

# Update specific plugin
santiq plugin update santiq-plugin-postgres

# Check for updates
santiq plugin update --dry-run
```

### Backup Before Upgrade

```bash
# Backup configuration
cp -r ~/.config/santiq ~/.config/santiq.backup

# Backup data
cp -r ~/santiq/data ~/santiq/data.backup

# Backup plugins
cp -r ~/santiq/plugins ~/santiq/plugins.backup
```

## 📚 Additional Resources

- **[Getting Started Guide](getting-started.md)** - Quick start tutorial
- **[User Guide](user-guide.md)** - Comprehensive usage instructions
- **[Configuration Reference](configuration.md)** - Configuration options
- **[CLI Reference](cli-reference.md)** - Command-line interface
- **[API Reference](api-reference.md)** - Core API documentation
- **[Plugin Development](plugin-development.md)** - Create custom plugins

---

**Need help with installation?** Check out the [Getting Started Guide](getting-started.md) for a quick tutorial or the [Troubleshooting](#troubleshooting) section for common issues.

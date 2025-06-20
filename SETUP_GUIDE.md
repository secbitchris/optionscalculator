# Setup Guide - SPY/SPX Options Analysis System

Cross-platform installation guide for Windows, macOS, and Linux.

## 🎯 Quick Setup (All Platforms)

### 🐳 **Docker Deployment (Recommended)**
```bash
# 1. Clone the repository
git clone https://github.com/secbitchris/optionscalculator.git
cd optionscalculator

# 2. Deploy with Docker (includes all dependencies)
docker-compose up --build -d

# 3. Open browser
# Navigate to: http://localhost:5002
# Features: Real market data, 40-point strike filtering, rate limiting
```

### 🐍 **Python Development Setup**
```bash
# 1. Clone the repository
git clone https://github.com/secbitchris/optionscalculator.git
cd optionscalculator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment (optional - for real market data)
cp env_template.txt .env
# Edit .env and add your Polygon.io API key

# 4. Test installation
python test_installation.py

# 5. Start web application
python run_webapp.py --port 5002

# 6. Open browser
# Navigate to: http://localhost:5002
```

## 🖥️ Platform-Specific Instructions

### Windows 10/11

#### Prerequisites
```powershell
# Install Python 3.8+ from python.org or Microsoft Store
# Verify installation
python --version
pip --version
```

#### Setup
```powershell
# Clone repository
git clone https://github.com/secbitchris/optionscalculator.git
cd optionscalculator

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Test installation
python test_installation.py

# Start application
python run_webapp.py --port 5001
```

#### Windows-Specific Notes
- **Port 5000 Issue**: Windows may have services on port 5000, use `--port 5001`
- **Firewall**: Windows Defender may prompt for network access - allow it
- **PowerShell**: Use PowerShell or Command Prompt, both work fine
- **Virtual Environment**: Highly recommended to avoid package conflicts

### macOS 12+ (Monterey/Ventura/Sonoma)

#### Prerequisites
```bash
# Install Python via Homebrew (recommended)
brew install python

# Or use pyenv for version management
brew install pyenv
pyenv install 3.11.0
pyenv global 3.11.0
```

#### Setup
```bash
# Clone repository
git clone https://github.com/secbitchris/optionscalculator.git
cd optionscalculator

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test installation
python test_installation.py

# Start application
python run_webapp.py --port 5001
```

#### macOS-Specific Notes
- **Port 5000 Issue**: macOS Control Center uses port 5000 (AirPlay), use `--port 5001`
- **Xcode Tools**: May need `xcode-select --install` for some packages
- **M1/M2 Macs**: All packages are compatible with Apple Silicon
- **System Python**: Avoid using system Python, use Homebrew or pyenv

### Ubuntu 20.04+ / Debian 11+

#### Prerequisites
```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv git

# Verify installation
python3 --version
pip3 --version
```

#### Setup
```bash
# Clone repository
git clone https://github.com/secbitchris/optionscalculator.git
cd optionscalculator

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test installation
python test_installation.py

# Start application
python run_webapp.py --port 5001
```

#### Linux-Specific Notes
- **System Packages**: Some distributions may need `python3-dev` for compilation
- **Firewall**: May need to configure UFW: `sudo ufw allow 5001`
- **Permissions**: Ensure user has write access to project directory
- **Service**: Can run as systemd service for production

### CentOS 8+ / RHEL 8+ / Fedora 35+

#### Prerequisites
```bash
# Install Python and development tools
sudo dnf install python3 python3-pip python3-devel git

# Or on older systems
sudo yum install python3 python3-pip python3-devel git
```

#### Setup
```bash
# Same as Ubuntu setup above
# Follow Ubuntu instructions - they work identically
```

## 🐍 Python Version Compatibility

### Supported Versions
- ✅ **Python 3.8** - Minimum supported
- ✅ **Python 3.9** - Fully tested
- ✅ **Python 3.10** - Fully tested  
- ✅ **Python 3.11** - Recommended
- ✅ **Python 3.12** - Latest supported

### Version-Specific Notes
- **Python 3.8**: Minimum features, all functionality works
- **Python 3.9+**: Better performance, recommended for production
- **Python 3.11+**: Best performance, latest features
- **Python 3.12**: Cutting edge, fully compatible

## 🔧 Troubleshooting

### Common Issues

#### "Port already in use"
```bash
# Use different port
python run_webapp.py --port 5001

# Or find and kill process using port
# Windows: netstat -ano | findstr :5000
# macOS/Linux: lsof -i :5000
```

#### "Module not found" errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Or force reinstall
pip install --force-reinstall -r requirements.txt
```

#### Permission errors (Linux/macOS)
```bash
# Fix directory permissions
chmod -R 755 .
chown -R $USER:$USER .

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
```

#### Windows path issues
```powershell
# Use forward slashes or raw strings
# Ensure Python is in PATH
# Use virtual environment to avoid conflicts
```

### Performance Optimization

#### For Large Datasets
```bash
# Install optional performance packages
pip install numba  # JIT compilation
pip install cython  # C extensions
```

#### For Production Use
```bash
# Install production WSGI server
pip install gunicorn  # Linux/macOS
pip install waitress  # Windows

# Run with production server
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

## 🌐 Network Configuration

### Local Development
- **Default**: `http://localhost:5001`
- **All interfaces**: `http://0.0.0.0:5001`
- **Specific IP**: `http://192.168.1.100:5001`

### Firewall Configuration

#### Windows
```powershell
# Allow through Windows Firewall
netsh advfirewall firewall add rule name="Options Analysis" dir=in action=allow protocol=TCP localport=5001
```

#### Linux (UFW)
```bash
sudo ufw allow 5001/tcp
sudo ufw reload
```

#### macOS
```bash
# Usually no configuration needed for localhost
# For network access, check System Preferences > Security & Privacy
```

## 📊 Verification

### Test Installation
```bash
# Run comprehensive test
python test_installation.py

# Expected output: "🎉 ALL TESTS PASSED!"
```

### Test Web Interface
1. Start application: `python run_webapp.py --port 5001`
2. Open browser: `http://localhost:5001`
3. Click "Fetch Live Price" - should show current SPY price
4. Click "Analyze Options" - should show results table
5. Try enhanced features (IV Calculator, Price Scenarios, etc.)

### Test Command Line
```bash
# Basic analysis
python option_scenario_calculator.py --current-price 600 --dte 7

# Should output options analysis table
```

## 🚀 Next Steps

After successful installation:

1. **📚 Read Documentation**
   - `README.md` - Main documentation
   - `FRONTEND_README.md` - Web interface guide

2. **🔑 Configure API Keys** (Optional)
   - Create `.env` file for Polygon.io API
   - See documentation for IBKR integration

3. **🎯 Start Trading**
   - Use web interface for analysis
   - Export results for your trading platform
   - Integrate with existing workflows

## 💡 Tips for Success

- **Use Virtual Environments**: Prevents package conflicts
- **Keep Updated**: `git pull` regularly for latest features
- **Test First**: Always run `test_installation.py` after updates
- **Backup Data**: The `data/` directory contains your analysis results
- **Read Logs**: Check terminal output for debugging information

## 🆘 Getting Help

If you encounter issues:

1. **Run Test Script**: `python test_installation.py`
2. **Check Requirements**: Ensure all dependencies are installed
3. **Update System**: Make sure Python and pip are current
4. **Virtual Environment**: Try fresh virtual environment
5. **Platform Specific**: Check platform-specific notes above

**System Requirements Met**: ✅ Python 3.8+, ✅ 2GB RAM, ✅ 100MB disk space 
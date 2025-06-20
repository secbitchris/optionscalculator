# Windows Docker Setup Guide

Complete guide to running the Options Analysis Web Application on Windows using Docker.

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Windows 10/11 (Home, Pro, or Enterprise)
- Administrator access
- 4GB+ available RAM

### Step 1: Install Docker Desktop
1. Download Docker Desktop for Windows from [docker.com](https://www.docker.com/products/docker-desktop/)
2. Run the installer as Administrator
3. Follow the installation wizard (accept defaults)
4. Restart your computer when prompted

### Step 2: Start Docker Desktop
1. Launch Docker Desktop from Start Menu
2. Wait for Docker to start (whale icon in system tray)
3. Accept any license agreements

### Step 3: Deploy the Application
1. Open **PowerShell as Administrator**
2. Navigate to your project folder:
   ```powershell
   cd C:\path\to\your\options_calculation
   ```
3. Run the deployment script:
   ```powershell
   .\docker-deploy.ps1 build
   ```

### Step 4: Access the Application
- Web Interface: http://localhost:5001
- API Documentation: http://localhost:5001/api/docs

## 📋 Detailed Setup Instructions

### Docker Desktop Installation

#### System Requirements
- **Windows 10 64-bit**: Pro, Enterprise, or Education (Build 19041 or higher)
- **Windows 11**: Any edition
- **WSL 2** (Windows Subsystem for Linux) - automatically installed
- **Hardware virtualization** must be enabled in BIOS
- **4GB RAM minimum** (8GB+ recommended)

#### Installation Steps
1. **Download Docker Desktop**
   - Visit https://www.docker.com/products/docker-desktop/
   - Click "Download for Windows"
   - Save the installer file

2. **Run Installation**
   ```powershell
   # Right-click PowerShell and "Run as Administrator"
   # Navigate to Downloads folder
   cd $env:USERPROFILE\Downloads
   
   # Run the installer (replace with actual filename)
   .\Docker Desktop Installer.exe
   ```

3. **Configuration Options**
   - ✅ **Enable WSL 2 integration** (recommended)
   - ✅ **Add Docker to PATH**
   - ✅ **Create desktop shortcut**

4. **Post-Installation**
   - Restart Windows when prompted
   - Launch Docker Desktop
   - Complete the setup tutorial (optional)

### Verify Docker Installation
```powershell
# Check Docker version
docker --version
# Should output: Docker version 24.x.x

# Check Docker Compose
docker-compose --version
# Should output: Docker Compose version 2.x.x

# Test Docker functionality
docker run hello-world
```

## 🛠️ PowerShell Deployment Script

### Using docker-deploy.ps1

The project includes a native PowerShell script for Windows users:

```powershell
# Build and start the application
.\docker-deploy.ps1 build

# Start existing containers
.\docker-deploy.ps1 start

# Stop containers
.\docker-deploy.ps1 stop

# View logs
.\docker-deploy.ps1 logs

# Check status
.\docker-deploy.ps1 status

# Complete cleanup
.\docker-deploy.ps1 clean

# Show help
.\docker-deploy.ps1 help
```

### Manual Docker Commands

If you prefer using Docker commands directly:

```powershell
# Build the image
docker build -t options-analysis .

# Run the container
docker run -d `
  --name options-analysis-app `
  -p 5001:5001 `
  -v ${PWD}/data:/app/data `
  --env-file .env `
  options-analysis

# View logs
docker logs options-analysis-app

# Stop and remove
docker stop options-analysis-app
docker rm options-analysis-app
```

## 🔧 Configuration

### Environment Setup
1. **Copy the environment template**:
   ```powershell
   Copy-Item env_template.txt .env
   ```

2. **Edit the .env file** in your preferred text editor:
   ```powershell
   notepad .env
   ```

3. **Add your API keys** (optional for basic functionality):
   ```
   POLYGON_API_KEY=your_polygon_key_here
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
   ```

### Data Persistence
The application uses Docker volumes to persist data:
- `./data/` folder is mounted to `/app/data` in the container
- Analysis results and cached data are saved locally
- Data survives container restarts

## 🐛 Troubleshooting

### Common Issues

#### 1. "Docker Desktop failed to start"
**Solution:**
```powershell
# Enable Windows features
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform

# Download and install WSL 2 kernel update
# https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi

# Restart computer
```

#### 2. "Port 5001 is already in use"
**Solution:**
```powershell
# Find what's using the port
netstat -ano | findstr :5001

# Kill the process (replace PID with actual process ID)
taskkill /PID 1234 /F

# Or use a different port
.\docker-deploy.ps1 build -p 5002
```

#### 3. "Access denied" or Permission Errors
**Solutions:**
```powershell
# Run PowerShell as Administrator
Start-Process powershell -Verb RunAs

# Add your user to Docker group (restart required)
net localgroup docker-users "yourusername" /add

# Check Docker Desktop is running
Get-Process "Docker Desktop"
```

#### 4. "WSL 2 installation is incomplete"
**Solution:**
```powershell
# Install WSL 2
wsl --install

# Set WSL 2 as default
wsl --set-default-version 2

# Restart computer
```

#### 5. Container Build Fails
**Solutions:**
```powershell
# Clear Docker cache
docker system prune -a

# Check for proxy/firewall issues
docker run --rm alpine ping google.com

# Rebuild with no cache
docker build --no-cache -t options-analysis .
```

### Performance Issues

#### 1. Slow Container Startup
```powershell
# Allocate more memory to Docker Desktop
# Docker Desktop → Settings → Resources → Advanced
# Increase Memory to 4GB+
```

#### 2. File Watching Issues
```powershell
# If hot-reload doesn't work, restart container
docker restart options-analysis-app
```

### Network Troubleshooting
```powershell
# Check if container is running
docker ps

# Test container connectivity
docker exec options-analysis-app curl localhost:5001

# Check Windows Firewall
netsh advfirewall show allprofiles state
```

## 📚 Additional Commands

### Container Management
```powershell
# List all containers
docker ps -a

# View container resource usage
docker stats

# Access container shell
docker exec -it options-analysis-app /bin/bash

# Copy files to/from container
docker cp local-file.txt options-analysis-app:/app/
docker cp options-analysis-app:/app/file.txt ./
```

### Image Management
```powershell
# List images
docker images

# Remove unused images
docker image prune

# Remove specific image
docker rmi options-analysis
```

### Volume Management
```powershell
# List volumes
docker volume ls

# Inspect volume
docker volume inspect options-analysis_data
```

## 🔄 Updates and Maintenance

### Updating the Application
```powershell
# Pull latest code
git pull origin main

# Rebuild and restart
.\docker-deploy.ps1 build
```

### Docker Desktop Updates
- Docker Desktop auto-updates by default
- Manual updates: Docker Desktop → Settings → Software Updates

### Cleanup Commands
```powershell
# Remove all stopped containers
docker container prune

# Remove all unused images
docker image prune -a

# Remove all unused volumes
docker volume prune

# Nuclear option - remove everything
docker system prune -a --volumes
```

## 🎯 Best Practices

### Security
- Don't commit `.env` files with real API keys
- Use strong passwords for any database connections
- Keep Docker Desktop updated
- Don't run containers as root in production

### Performance
- Allocate adequate RAM to Docker Desktop (4GB+)
- Use SSD storage for better I/O performance
- Close unnecessary applications when running containers
- Monitor resource usage with `docker stats`

### Development
- Use volume mounts for active development
- Keep containers lightweight
- Use `.dockerignore` to exclude unnecessary files
- Regular cleanup of unused images and containers

## 📞 Support

### Getting Help
1. **Check logs first**:
   ```powershell
   .\docker-deploy.ps1 logs
   ```

2. **Docker Desktop logs**:
   - Docker Desktop → Troubleshoot → Download logs

3. **System information**:
   ```powershell
   systeminfo | findstr /C:"OS" /C:"Memory"
   docker version
   ```

### Useful Resources
- [Docker Desktop for Windows Documentation](https://docs.docker.com/desktop/windows/)
- [WSL 2 Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [PowerShell Documentation](https://docs.microsoft.com/en-us/powershell/)

---

## 🎉 You're All Set!

Once Docker is running and the container is built, you can access:

- **Web Application**: http://localhost:5001
- **API Documentation**: http://localhost:5001/api/docs
- **Real-time Options Analysis**: Available in the web interface

The application will automatically start when you run the deployment script and will be accessible from any browser on your Windows machine. 
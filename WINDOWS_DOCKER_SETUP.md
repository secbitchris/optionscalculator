# Windows Docker Setup Guide
## SPY/SPX Options Analysis System

Complete step-by-step guide for Windows users to get the Options Analysis web application running using Docker.

## 🎯 **Why Docker?**
- **No Python Setup Required** - Docker handles all dependencies
- **Identical Environment** - Works exactly the same on all systems
- **Easy Cleanup** - Completely remove with one command
- **Professional Deployment** - Same as production systems

## 🛠️ **Prerequisites**

### Step 1: Install Docker Desktop for Windows

1. **Download Docker Desktop**:
   - Go to https://www.docker.com/products/docker-desktop/
   - Click "Download for Windows"
   - Download `Docker Desktop Installer.exe`

2. **Install Docker Desktop**:
   - Run the installer as Administrator
   - Follow the installation wizard
   - **Enable WSL 2** when prompted (recommended)
   - Restart your computer when installation completes

3. **Verify Docker Installation**:
   - Open **Command Prompt** or **PowerShell**
   - Run: `docker --version`
   - You should see something like: `Docker version 24.0.x`

### Step 2: Install Git (if not already installed)

1. **Download Git**:
   - Go to https://git-scm.com/download/win
   - Download and install Git for Windows

2. **Verify Git Installation**:
   - Open **Command Prompt** or **PowerShell**
   - Run: `git --version`

## 🚀 **Quick Start (5 Minutes)**

### Method 1: Using PowerShell (Recommended)

1. **Open PowerShell as Administrator**:
   - Press `Windows + X`
   - Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

2. **Clone and Run**:
   ```powershell
   # Navigate to your desired directory (e.g., Desktop)
   cd $env:USERPROFILE\Desktop
   
   # Clone the repository
   git clone https://github.com/secbitchris/optionscalculator.git
   cd optionscalculator
   
   # Build and start the application
   docker-compose up --build -d
   ```

3. **Access the Application**:
   - Open your web browser
   - Go to: **http://localhost:5002**
   - You should see the Options Analysis interface!

### Method 2: Using the PowerShell Deploy Script

1. **Clone the Repository**:
   ```powershell
   cd $env:USERPROFILE\Desktop
   git clone https://github.com/secbitchris/optionscalculator.git
   cd optionscalculator
   ```

2. **Build and Start Using PowerShell Script**:
   ```powershell
   # Use the Windows PowerShell deployment script
   .\docker-deploy.ps1 build
   .\docker-deploy.ps1 start
   ```

3. **Check Status**:
   ```powershell
   .\docker-deploy.ps1 status
   ```

## 🔧 **Managing the Application**

### Method 1: Using PowerShell Script (Recommended)
```powershell
# From the optionscalculator directory
.\docker-deploy.ps1 start     # Start the application
.\docker-deploy.ps1 stop      # Stop the application
.\docker-deploy.ps1 restart   # Restart the application
.\docker-deploy.ps1 logs      # View logs
.\docker-deploy.ps1 status    # Check status
.\docker-deploy.ps1 help      # Show all commands
```

### Method 2: Using Docker Compose Directly
```powershell
# Starting the Application
docker-compose up -d

# Stopping the Application
docker-compose down

# Viewing Logs
docker-compose logs -f

# Restarting the Application
docker-compose restart

# Check Status
docker-compose ps
```

### Updating the Application
```powershell
# Pull latest changes
git pull

# Method 1: Using PowerShell script
.\docker-deploy.ps1 stop
.\docker-deploy.ps1 build
.\docker-deploy.ps1 start

# Method 2: Using docker-compose
docker-compose down
docker-compose up --build -d
```

## 📊 **Adding Your Polygon.io API Key (Optional)**

To get real market data, you can add your Polygon.io API key:

1. **Create/Edit .env file**:
   - In the `optionscalculator` folder, create a file named `.env`
   - Add your API key:
   ```
   POLYGON_API_KEY=your_api_key_here
   FLASK_ENV=production
   DEBUG=false
   ```

2. **Restart the Application**:
   ```powershell
   docker-compose down
   docker-compose up -d
   ```

## 🔍 **Troubleshooting**

### Docker Desktop Not Starting
- **Enable Virtualization**: Go to BIOS settings and enable Intel VT-x or AMD-V
- **Enable Hyper-V**: In Windows Features, enable Hyper-V
- **WSL 2**: Install Windows Subsystem for Linux 2

### Port 5002 Already in Use
```powershell
# Check what's using the port
netstat -ano | findstr :5002

# Or use a different port
docker-compose down
# Edit docker-compose.yml to change "5002:5001" to "5003:5001"
docker-compose up -d
```

### Application Won't Load
1. **Check Docker is Running**:
   ```powershell
   docker-compose ps
   ```

2. **Check Logs**:
   ```powershell
   docker-compose logs
   ```

3. **Restart Everything**:
   ```powershell
   docker-compose down
   docker-compose up -d
   ```

### Container Build Errors
```powershell
# Clear Docker cache and rebuild
docker system prune -a
docker-compose build --no-cache
```

## 📁 **File Structure After Setup**
```
Desktop/
└── optionscalculator/
    ├── docker-compose.yml     # Docker configuration
    ├── Dockerfile            # Container definition
    ├── .env                  # Your API keys (optional)
    ├── app.py                # Main application
    ├── requirements.txt      # Python dependencies
    └── data/                 # Analysis results saved here
```

## 🎯 **What You Get**
- **Professional Web Interface** at http://localhost:5002
- **Real-time SPY/SPX Analysis** with live market data
- **Options Chain View** with Greeks and probabilities
- **Real Data Only Mode** for verified market data
- **Export Capabilities** for saving analysis results

## 🔄 **Complete Removal**
If you want to completely remove everything:

```powershell
# Stop and remove containers
docker-compose down

# Remove images
docker rmi optionscalculator_options-analyzer

# Remove the folder
cd ..
Remove-Item -Recurse -Force optionscalculator
```

## 🆘 **Need Help?**

### Quick Health Check
```powershell
# Check Docker is working
docker --version

# Check containers are running
docker-compose ps

# Check application logs
docker-compose logs --tail=20
```

### Common Success Indicators
- Docker Desktop shows green "running" status
- `docker-compose ps` shows "Up" status
- http://localhost:5002 loads the web interface
- You can see options analysis data

### If Nothing Works
1. Restart Docker Desktop
2. Restart your computer
3. Try the Quick Start steps again
4. Check Windows Defender isn't blocking Docker

## 🎉 **You're Ready!**
Once you see the Options Analysis interface at http://localhost:5002, you can:
- Analyze SPY/SPX options with real market data
- Use the "Real Data Only" toggle for verified market data
- Export analysis results to CSV/JSON
- Calculate expected moves and Greeks
- Access professional options trading analysis tools

The application runs completely isolated in Docker, so your Windows system stays clean! 
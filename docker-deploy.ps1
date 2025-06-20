# Options Analysis Web Application - Docker Deployment Script (Windows PowerShell)
# Usage: .\docker-deploy.ps1 [build|start|stop|restart|logs|shell|status|help]

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

# Configuration
$APP_NAME = "options-analysis-webapp"
$COMPOSE_FILE = "docker-compose.yml"

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Header {
    Write-Host "================================" -ForegroundColor Blue
    Write-Host " Options Analysis Web App" -ForegroundColor Blue
    Write-Host "================================" -ForegroundColor Blue
}

# Check if Docker is running
function Test-Docker {
    try {
        docker info > $null 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Docker is not running. Please start Docker Desktop first."
            exit 1
        }
    }
    catch {
        Write-Error "Docker is not installed or not accessible. Please install Docker Desktop."
        exit 1
    }
}

# Check if .env file exists
function Test-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Warning ".env file not found. Creating template..."
        @"
# Polygon.io API Key (optional - for live data)
POLYGON_API_KEY=your_api_key_here

# Flask Configuration
FLASK_ENV=production
DEBUG=false
"@ | Out-File -FilePath ".env" -Encoding UTF8
        Write-Warning "Please edit .env file with your Polygon.io API key"
    }
}

# Build the Docker image
function Invoke-Build {
    Write-Header
    Write-Status "Building Docker image..."
    docker-compose -f $COMPOSE_FILE build --no-cache
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Build complete!"
    } else {
        Write-Error "Build failed!"
        exit 1
    }
}

# Start the application
function Invoke-Start {
    Write-Header
    Test-EnvFile
    Write-Status "Starting Options Analysis Web Application..."
    docker-compose -f $COMPOSE_FILE up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Application started successfully!"
        Write-Status "Web interface available at: http://localhost:5002"
        Write-Status "Use '.\docker-deploy.ps1 logs' to view application logs"
    } else {
        Write-Error "Failed to start application!"
        exit 1
    }
}

# Stop the application
function Invoke-Stop {
    Write-Status "Stopping Options Analysis Web Application..."
    docker-compose -f $COMPOSE_FILE down
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Application stopped."
    }
}

# Restart the application
function Invoke-Restart {
    Write-Status "Restarting Options Analysis Web Application..."
    docker-compose -f $COMPOSE_FILE restart
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Application restarted!"
    }
}

# Show logs
function Invoke-Logs {
    Write-Status "Showing application logs (Ctrl+C to exit)..."
    docker-compose -f $COMPOSE_FILE logs -f
}

# Open shell in container
function Invoke-Shell {
    Write-Status "Opening shell in container..."
    docker-compose -f $COMPOSE_FILE exec options-analyzer /bin/bash
}

# Show status
function Invoke-Status {
    Write-Header
    Write-Status "Container status:"
    docker-compose -f $COMPOSE_FILE ps
    
    $running = docker-compose -f $COMPOSE_FILE ps | Select-String "Up"
    if ($running) {
        Write-Status "Application is running at: http://localhost:5002"
    } else {
        Write-Warning "Application is not running. Use '.\docker-deploy.ps1 start' to start it."
    }
}

# Show help
function Show-Help {
    Write-Header
    Write-Host "Usage: .\docker-deploy.ps1 [COMMAND]" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor White
    Write-Host "  build     Build the Docker image" -ForegroundColor Cyan
    Write-Host "  start     Start the application" -ForegroundColor Cyan
    Write-Host "  stop      Stop the application" -ForegroundColor Cyan
    Write-Host "  restart   Restart the application" -ForegroundColor Cyan
    Write-Host "  logs      Show application logs" -ForegroundColor Cyan
    Write-Host "  shell     Open shell in container" -ForegroundColor Cyan
    Write-Host "  status    Show container status" -ForegroundColor Cyan
    Write-Host "  help      Show this help message" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Quick start:" -ForegroundColor Yellow
    Write-Host "  1. .\docker-deploy.ps1 build" -ForegroundColor White
    Write-Host "  2. .\docker-deploy.ps1 start" -ForegroundColor White
    Write-Host "  3. Open http://localhost:5002" -ForegroundColor White
    Write-Host ""
    Write-Host "Windows-specific notes:" -ForegroundColor Yellow
    Write-Host "  - Ensure Docker Desktop is running" -ForegroundColor Gray
    Write-Host "  - Run PowerShell as Administrator if needed" -ForegroundColor Gray
    Write-Host "  - Check Windows Defender if connection issues occur" -ForegroundColor Gray
}

# Main script logic
function Invoke-Main {
    Test-Docker
    
    switch ($Command.ToLower()) {
        "build" {
            Invoke-Build
        }
        "start" {
            Invoke-Start
        }
        "stop" {
            Invoke-Stop
        }
        "restart" {
            Invoke-Restart
        }
        "logs" {
            Invoke-Logs
        }
        "shell" {
            Invoke-Shell
        }
        "status" {
            Invoke-Status
        }
        "help" {
            Show-Help
        }
        default {
            Write-Error "Unknown command: $Command"
            Show-Help
            exit 1
        }
    }
}

# Run main function
Invoke-Main 
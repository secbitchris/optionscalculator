# Options Analysis Docker Deployment Script for Windows
# PowerShell script for easy Docker container management

param(
    [Parameter(Position=0)]
    [ValidateSet("build", "start", "stop", "restart", "logs", "status", "clean", "help")]
    [string]$Action = "help",
    
    [Parameter()]
    [int]$Port = 5001,
    
    [Parameter()]
    [switch]$Follow,
    
    [Parameter()]
    [switch]$Detach = $true
)

# Script configuration
$ImageName = "options-analysis"
$ContainerName = "options-analysis-app"
$DefaultPort = 5001

# Colors for output
$ColorSuccess = "Green"
$ColorWarning = "Yellow"
$ColorError = "Red"
$ColorInfo = "Cyan"
$ColorHeader = "Magenta"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Show-Header {
    Write-ColorOutput "==========================================================" $ColorHeader
    Write-ColorOutput "🚀 Options Analysis Docker Deployment - Windows" $ColorHeader
    Write-ColorOutput "==========================================================" $ColorHeader
}

function Test-DockerInstallation {
    try {
        $dockerVersion = docker --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Docker is installed: $dockerVersion" $ColorSuccess
            return $true
        }
    }
    catch {
        Write-ColorOutput "❌ Docker is not installed or not in PATH" $ColorError
        Write-ColorOutput "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/" $ColorInfo
        return $false
    }
    return $false
}

function Test-DockerRunning {
    try {
        $result = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Docker is running" $ColorSuccess
            return $true
        }
    }
    catch {
        Write-ColorOutput "❌ Docker is not running" $ColorError
        Write-ColorOutput "Please start Docker Desktop" $ColorInfo
        return $false
    }
    return $false
}

function Build-Application {
    Write-ColorOutput "🔨 Building Options Analysis Docker image..." $ColorInfo
    
    # Check if Dockerfile exists
    if (-not (Test-Path "Dockerfile")) {
        Write-ColorOutput "❌ Dockerfile not found in current directory" $ColorError
        return $false
    }
    
    # Check if .env file exists, create from template if not
    if (-not (Test-Path ".env")) {
        if (Test-Path "env_template.txt") {
            Write-ColorOutput "📋 Creating .env file from template..." $ColorWarning
            Copy-Item "env_template.txt" ".env"
            Write-ColorOutput "⚠️  Please edit .env file with your API keys if needed" $ColorWarning
        }
    }
    
    # Stop and remove existing container
    Stop-Application -Silent
    Remove-Container -Silent
    
    # Build the image
    Write-ColorOutput "🔨 Building Docker image: $ImageName" $ColorInfo
    docker build -t $ImageName .
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "✅ Image built successfully" $ColorSuccess
        
        # Start the container
        Start-Application
        return $true
    } else {
        Write-ColorOutput "❌ Failed to build image" $ColorError
        return $false
    }
}

function Start-Application {
    Write-ColorOutput "🚀 Starting Options Analysis application..." $ColorInfo
    
    # Check if container already exists
    $existingContainer = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" 2>$null
    
    if ($existingContainer -eq $ContainerName) {
        Write-ColorOutput "📦 Container exists, starting..." $ColorInfo
        docker start $ContainerName
    } else {
        Write-ColorOutput "📦 Creating new container..." $ColorInfo
        
        # Create data directory if it doesn't exist
        if (-not (Test-Path "data")) {
            New-Item -ItemType Directory -Name "data" | Out-Null
            Write-ColorOutput "📁 Created data directory" $ColorInfo
        }
        
        # Run new container
        $envFile = if (Test-Path ".env") { "--env-file .env" } else { "" }
        
        $dockerCmd = "docker run -d " +
                    "--name $ContainerName " +
                    "-p ${Port}:5001 " +
                    "-v `"${PWD}/data:/app/data`" " +
                    "$envFile " +
                    "$ImageName"
        
        Invoke-Expression $dockerCmd
    }
    
    if ($LASTEXITCODE -eq 0) {
        Start-Sleep -Seconds 3
        Write-ColorOutput "✅ Application started successfully" $ColorSuccess
        Write-ColorOutput "🌐 Web Interface: http://localhost:$Port" $ColorSuccess
        Write-ColorOutput "📚 API Documentation: http://localhost:$Port/api/docs" $ColorSuccess
        Write-ColorOutput "" 
        Write-ColorOutput "💡 Use 'docker-deploy.ps1 logs' to view application logs" $ColorInfo
        Write-ColorOutput "💡 Use 'docker-deploy.ps1 stop' to stop the application" $ColorInfo
    } else {
        Write-ColorOutput "❌ Failed to start application" $ColorError
    }
}

function Stop-Application {
    param([switch]$Silent)
    
    if (-not $Silent) {
        Write-ColorOutput "🛑 Stopping Options Analysis application..." $ColorInfo
    }
    
    $runningContainer = docker ps --filter "name=$ContainerName" --format "{{.Names}}" 2>$null
    
    if ($runningContainer -eq $ContainerName) {
        docker stop $ContainerName | Out-Null
        if ($LASTEXITCODE -eq 0) {
            if (-not $Silent) {
                Write-ColorOutput "✅ Application stopped" $ColorSuccess
            }
        } else {
            if (-not $Silent) {
                Write-ColorOutput "❌ Failed to stop application" $ColorError
            }
        }
    } else {
        if (-not $Silent) {
            Write-ColorOutput "ℹ️  Application is not running" $ColorInfo
        }
    }
}

function Restart-Application {
    Write-ColorOutput "🔄 Restarting Options Analysis application..." $ColorInfo
    Stop-Application -Silent
    Start-Sleep -Seconds 2
    Start-Application
}

function Show-Logs {
    Write-ColorOutput "📋 Showing application logs..." $ColorInfo
    Write-ColorOutput "Press Ctrl+C to exit log view" $ColorWarning
    Write-ColorOutput ""
    
    if ($Follow) {
        docker logs -f $ContainerName
    } else {
        docker logs --tail 50 $ContainerName
    }
}

function Show-Status {
    Write-ColorOutput "📊 Application Status:" $ColorInfo
    Write-ColorOutput ""
    
    # Check if container exists
    $containerExists = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" 2>$null
    
    if ($containerExists -eq $ContainerName) {
        # Get container status
        $containerInfo = docker ps -a --filter "name=$ContainerName" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>$null
        Write-ColorOutput "Container Status:" $ColorInfo
        Write-Host $containerInfo
        
        # Check if it's running
        $isRunning = docker ps --filter "name=$ContainerName" --format "{{.Names}}" 2>$null
        if ($isRunning -eq $ContainerName) {
            Write-ColorOutput ""
            Write-ColorOutput "✅ Application is RUNNING" $ColorSuccess
            Write-ColorOutput "🌐 Access at: http://localhost:$Port" $ColorSuccess
        } else {
            Write-ColorOutput ""
            Write-ColorOutput "⚠️  Application is STOPPED" $ColorWarning
            Write-ColorOutput "💡 Use 'docker-deploy.ps1 start' to start it" $ColorInfo
        }
    } else {
        Write-ColorOutput "❌ Container does not exist" $ColorError
        Write-ColorOutput "💡 Use 'docker-deploy.ps1 build' to create and start it" $ColorInfo
    }
    
    Write-ColorOutput ""
    Write-ColorOutput "Docker System Info:" $ColorInfo
    docker system df 2>$null | Select-Object -Skip 1
}

function Remove-Container {
    param([switch]$Silent)
    
    $existingContainer = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" 2>$null
    
    if ($existingContainer -eq $ContainerName) {
        docker rm $ContainerName | Out-Null
        if (-not $Silent) {
            Write-ColorOutput "🗑️  Removed existing container" $ColorInfo
        }
    }
}

function Clean-Application {
    Write-ColorOutput "🧹 Cleaning up Docker resources..." $ColorWarning
    Write-ColorOutput "This will remove containers, images, and unused resources" $ColorWarning
    
    $confirmation = Read-Host "Are you sure? (y/N)"
    if ($confirmation -eq "y" -or $confirmation -eq "Y") {
        # Stop and remove container
        Stop-Application -Silent
        Remove-Container
        
        # Remove image
        $imageExists = docker images $ImageName -q 2>$null
        if ($imageExists) {
            Write-ColorOutput "🗑️  Removing image: $ImageName" $ColorInfo
            docker rmi $ImageName | Out-Null
        }
        
        # Clean up Docker system
        Write-ColorOutput "🧹 Cleaning up unused Docker resources..." $ColorInfo
        docker system prune -f | Out-Null
        
        Write-ColorOutput "✅ Cleanup completed" $ColorSuccess
    } else {
        Write-ColorOutput "❌ Cleanup cancelled" $ColorInfo
    }
}

function Show-Help {
    Write-ColorOutput ""
    Write-ColorOutput "Options Analysis Docker Deployment Script" $ColorHeader
    Write-ColorOutput ""
    Write-ColorOutput "USAGE:" $ColorInfo
    Write-ColorOutput "  .\docker-deploy.ps1 <command> [options]" 
    Write-ColorOutput ""
    Write-ColorOutput "COMMANDS:" $ColorInfo
    Write-ColorOutput "  build     Build and start the application" 
    Write-ColorOutput "  start     Start the application container" 
    Write-ColorOutput "  stop      Stop the application container" 
    Write-ColorOutput "  restart   Restart the application" 
    Write-ColorOutput "  logs      Show application logs" 
    Write-ColorOutput "  status    Show application status" 
    Write-ColorOutput "  clean     Remove all containers and images" 
    Write-ColorOutput "  help      Show this help message" 
    Write-ColorOutput ""
    Write-ColorOutput "OPTIONS:" $ColorInfo
    Write-ColorOutput "  -Port <number>    Specify port (default: 5001)" 
    Write-ColorOutput "  -Follow           Follow logs in real-time" 
    Write-ColorOutput ""
    Write-ColorOutput "EXAMPLES:" $ColorInfo
    Write-ColorOutput "  .\docker-deploy.ps1 build" 
    Write-ColorOutput "  .\docker-deploy.ps1 start -Port 5002" 
    Write-ColorOutput "  .\docker-deploy.ps1 logs -Follow" 
    Write-ColorOutput "  .\docker-deploy.ps1 status" 
    Write-ColorOutput ""
    Write-ColorOutput "QUICK START:" $ColorSuccess
    Write-ColorOutput "  1. Ensure Docker Desktop is running" 
    Write-ColorOutput "  2. Run: .\docker-deploy.ps1 build" 
    Write-ColorOutput "  3. Access: http://localhost:5001" 
    Write-ColorOutput ""
    Write-ColorOutput "For Windows-specific setup help, see WINDOWS_DOCKER_SETUP.md" $ColorInfo
}

# Main script execution
try {
    Show-Header
    
    # Check Docker installation and status
    if (-not (Test-DockerInstallation)) {
        exit 1
    }
    
    if (-not (Test-DockerRunning)) {
        Write-ColorOutput "Please start Docker Desktop and try again" $ColorError
        exit 1
    }
    
    # Execute the requested action
    switch ($Action.ToLower()) {
        "build" { 
            $success = Build-Application
            if (-not $success) { exit 1 }
        }
        "start" { Start-Application }
        "stop" { Stop-Application }
        "restart" { Restart-Application }
        "logs" { Show-Logs }
        "status" { Show-Status }
        "clean" { Clean-Application }
        "help" { Show-Help }
        default { 
            Write-ColorOutput "❌ Unknown command: $Action" $ColorError
            Show-Help
            exit 1
        }
    }
    
    Write-ColorOutput ""
    Write-ColorOutput "✨ Operation completed!" $ColorSuccess
    
} catch {
    Write-ColorOutput "❌ An error occurred: $($_.Exception.Message)" $ColorError
    exit 1
} 
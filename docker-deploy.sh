#!/bin/bash

# Options Analysis Web Application - Docker Deployment Script
# Usage: ./docker-deploy.sh [build|start|stop|restart|logs|shell]

set -e

# Configuration
APP_NAME="options-analysis-webapp"
COMPOSE_FILE="docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} Options Analysis Web App${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Check if .env file exists
check_env() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating template..."
        cat > .env << EOF
# Polygon.io API Key (optional - for live data)
POLYGON_API_KEY=your_api_key_here

# Flask Configuration
FLASK_ENV=production
DEBUG=false
EOF
        print_warning "Please edit .env file with your Polygon.io API key"
    fi
}

# Build the Docker image
build() {
    print_header
    print_status "Building Docker image..."
    docker-compose -f $COMPOSE_FILE build --no-cache
    print_status "Build complete!"
}

# Start the application
start() {
    print_header
    check_env
    print_status "Starting Options Analysis Web Application..."
    docker-compose -f $COMPOSE_FILE up -d
    print_status "Application started successfully!"
    print_status "Web interface available at: http://localhost:5002"
    print_status "Use 'docker-deploy.sh logs' to view application logs"
}

# Stop the application
stop() {
    print_status "Stopping Options Analysis Web Application..."
    docker-compose -f $COMPOSE_FILE down
    print_status "Application stopped."
}

# Restart the application
restart() {
    print_status "Restarting Options Analysis Web Application..."
    docker-compose -f $COMPOSE_FILE restart
    print_status "Application restarted!"
}

# Show logs
logs() {
    print_status "Showing application logs (Ctrl+C to exit)..."
    docker-compose -f $COMPOSE_FILE logs -f
}

# Open shell in container
shell() {
    print_status "Opening shell in container..."
    docker-compose -f $COMPOSE_FILE exec options-analyzer /bin/bash
}

# Show status
status() {
    print_header
    print_status "Container status:"
    docker-compose -f $COMPOSE_FILE ps
    
    if docker-compose -f $COMPOSE_FILE ps | grep -q "Up"; then
        print_status "Application is running at: http://localhost:5002"
    fi
}

# Show help
help() {
    print_header
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build     Build the Docker image"
    echo "  start     Start the application"
    echo "  stop      Stop the application"
    echo "  restart   Restart the application"
    echo "  logs      Show application logs"
    echo "  shell     Open shell in container"
    echo "  status    Show container status"
    echo "  help      Show this help message"
    echo ""
    echo "Quick start:"
    echo "  1. $0 build"
    echo "  2. $0 start"
    echo "  3. Open http://localhost:5002"
}

# Main script logic
main() {
    check_docker
    
    case "${1:-help}" in
        build)
            build
            ;;
        start)
            start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        logs)
            logs
            ;;
        shell)
            shell
            ;;
        status)
            status
            ;;
        help|--help|-h)
            help
            ;;
        *)
            print_error "Unknown command: $1"
            help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 
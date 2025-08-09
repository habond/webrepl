#!/bin/bash

# WebREPL Control Script
# Usage: ./control [start|stop|restart|status|logs|help]

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Application details
APP_NAME="WebREPL"
APP_URL="http://localhost:8080"

# Docker Compose detection
detect_docker_compose() {
    if docker compose version &> /dev/null 2>&1; then
        echo "docker compose"
    elif command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    else
        echo ""
    fi
}

# Check dependencies
check_dependencies() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi

    DOCKER_COMPOSE=$(detect_docker_compose)
    if [ -z "$DOCKER_COMPOSE" ]; then
        echo -e "${RED}Error: Docker Compose is not installed. Please install Docker Compose first.${NC}"
        exit 1
    fi
}

# Show usage information
show_help() {
    echo -e "${BLUE}WebREPL Control Script${NC}"
    echo ""
    echo "Usage: ./control [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the WebREPL application"
    echo "  stop      Stop the WebREPL application"
    echo "  restart   Restart the WebREPL application (rebuild and start)"
    echo "  status    Show status of running containers"
    echo "  logs      Show application logs (use -f for follow)"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./control start"
    echo "  ./control logs -f"
    echo "  ./control restart"
    echo ""
    echo "Access the application at: $APP_URL"
}

# Start the application
start_app() {
    echo -e "${BLUE}Starting $APP_NAME...${NC}"
    echo ""
    
    check_dependencies
    
    echo "Building and starting services..."
    $DOCKER_COMPOSE up --build -d
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ $APP_NAME is running!${NC}"
        echo ""
        echo -e "${BLUE}📍 Access the application at: $APP_URL${NC}"
        echo ""
        echo "Commands:"
        echo "  ./control stop     - Stop the application"
        echo "  ./control logs -f  - View live logs"
        echo "  ./control status   - Check container status"
    else
        echo ""
        echo -e "${RED}❌ Failed to start the application. Please check the error messages above.${NC}"
        exit 1
    fi
}

# Stop the application
stop_app() {
    echo -e "${BLUE}Stopping $APP_NAME...${NC}"
    
    check_dependencies
    
    $DOCKER_COMPOSE down
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Application stopped successfully.${NC}"
    else
        echo -e "${RED}❌ Failed to stop the application.${NC}"
        exit 1
    fi
}

# Restart the application
restart_app() {
    echo -e "${BLUE}Restarting $APP_NAME...${NC}"
    echo ""
    
    check_dependencies
    
    echo "Stopping services..."
    $DOCKER_COMPOSE down
    
    echo "Building and starting services..."
    $DOCKER_COMPOSE up --build -d
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ $APP_NAME has been restarted!${NC}"
        echo ""
        echo -e "${BLUE}📍 Access the application at: $APP_URL${NC}"
        echo ""
        echo "Commands:"
        echo "  ./control stop     - Stop the application"
        echo "  ./control logs -f  - View live logs"
        echo "  ./control status   - Check container status"
    else
        echo ""
        echo -e "${RED}❌ Failed to restart the application. Please check the error messages above.${NC}"
        exit 1
    fi
}

# Show container status
show_status() {
    check_dependencies
    
    echo -e "${BLUE}$APP_NAME Container Status:${NC}"
    echo ""
    
    # Check if any containers are running
    if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q "webrepl-"; then
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(NAMES|webrepl-)"
        echo ""
        echo -e "${GREEN}Application is running at: $APP_URL${NC}"
    else
        echo -e "${YELLOW}No WebREPL containers are currently running.${NC}"
        echo "Use './control start' to start the application."
    fi
}

# Show logs
show_logs() {
    check_dependencies
    
    # Pass all additional arguments to docker compose logs
    shift # Remove 'logs' from arguments
    $DOCKER_COMPOSE logs "$@"
}

# Main script logic
case "${1:-help}" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
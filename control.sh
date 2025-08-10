#!/bin/bash

# WebREPL Control Script
# Usage: ./control [start|stop|restart|status|logs|help] [service]

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

# Available services
AVAILABLE_SERVICES=(
    "frontend"
    "session-manager" 
    "backend-python"
    "backend-javascript"
    "backend-ruby"
    "backend-php"
    "backend-kotlin"
)

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

# Validate service name
validate_service() {
    local service="$1"
    if [ -n "$service" ]; then
        for valid_service in "${AVAILABLE_SERVICES[@]}"; do
            if [ "$service" = "$valid_service" ]; then
                return 0
            fi
        done
        echo -e "${RED}Error: Invalid service '$service'${NC}"
        echo "Available services: ${AVAILABLE_SERVICES[*]}"
        exit 1
    fi
}

# Show usage information
show_help() {
    echo -e "${BLUE}WebREPL Control Script${NC}"
    echo ""
    echo "Usage: ./control [COMMAND] [SERVICE]"
    echo ""
    echo "Commands:"
    echo "  start     Start the WebREPL application (or specific service)"
    echo "  stop      Stop the WebREPL application (or specific service)"
    echo "  restart   Restart the WebREPL application (rebuild and start)"
    echo "  status    Show status of running containers"
    echo "  logs      Show application logs (use -f for follow)"
    echo "  help      Show this help message"
    echo ""
    echo "Available services:"
    for service in "${AVAILABLE_SERVICES[@]}"; do
        echo "  $service"
    done
    echo ""
    echo "Examples:"
    echo "  ./control start                    # Start all services"
    echo "  ./control start frontend           # Start only frontend"
    echo "  ./control stop backend-python      # Stop only Python backend"
    echo "  ./control restart session-manager  # Restart session manager"
    echo "  ./control logs -f frontend         # Follow frontend logs"
    echo "  ./control status                   # Show all container status"
    echo ""
    echo "Access the application at: $APP_URL"
}

# Start the application
start_app() {
    local service="$1"
    validate_service "$service"
    
    if [ -n "$service" ]; then
        echo -e "${BLUE}Starting service: $service${NC}"
        check_dependencies
        echo "Building and starting $service..."
        $DOCKER_COMPOSE up --build -d "$service"
    else
        echo -e "${BLUE}Starting $APP_NAME...${NC}"
        check_dependencies
        echo "Building and starting all services..."
        $DOCKER_COMPOSE up --build -d
    fi
    
    if [ $? -eq 0 ]; then
        echo ""
        if [ -n "$service" ]; then
            echo -e "${GREEN}✅ Service $service is running!${NC}"
        else
            echo -e "${GREEN}✅ $APP_NAME is running!${NC}"
            echo ""
            echo -e "${BLUE}📍 Access the application at: $APP_URL${NC}"
        fi
        echo ""
        echo "Commands:"
        echo "  ./control stop     - Stop the application"
        echo "  ./control logs -f  - View live logs"
        echo "  ./control status   - Check container status"
    else
        echo ""
        echo -e "${RED}❌ Failed to start. Please check the error messages above.${NC}"
        exit 1
    fi
}

# Stop the application
stop_app() {
    local service="$1"
    validate_service "$service"
    
    check_dependencies
    
    if [ -n "$service" ]; then
        echo -e "${BLUE}Stopping service: $service${NC}"
        $DOCKER_COMPOSE stop "$service"
        $DOCKER_COMPOSE rm -f "$service"
    else
        echo -e "${BLUE}Stopping $APP_NAME...${NC}"
        $DOCKER_COMPOSE down
    fi
    
    if [ $? -eq 0 ]; then
        if [ -n "$service" ]; then
            echo -e "${GREEN}✅ Service $service stopped successfully.${NC}"
        else
            echo -e "${GREEN}✅ Application stopped successfully.${NC}"
        fi
    else
        echo -e "${RED}❌ Failed to stop.${NC}"
        exit 1
    fi
}

# Restart the application
restart_app() {
    local service="$1"
    validate_service "$service"
    
    check_dependencies
    
    if [ -n "$service" ]; then
        echo -e "${BLUE}Restarting service: $service${NC}"
        echo ""
        echo "Stopping $service..."
        $DOCKER_COMPOSE stop "$service"
        $DOCKER_COMPOSE rm -f "$service"
        echo "Building and starting $service..."
        $DOCKER_COMPOSE up --build -d "$service"
        
        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ Service $service has been restarted!${NC}"
        else
            echo ""
            echo -e "${RED}❌ Failed to restart $service. Please check the error messages above.${NC}"
            exit 1
        fi
    else
        echo -e "${BLUE}Restarting $APP_NAME...${NC}"
        echo ""
        echo "Stopping services..."
        $DOCKER_COMPOSE down
        echo "Building and starting services..."
        $DOCKER_COMPOSE up --build -d
        
        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ $APP_NAME has been restarted!${NC}"
            echo ""
            echo -e "${BLUE}📍 Access the application at: $APP_URL${NC}"
        else
            echo ""
            echo -e "${RED}❌ Failed to restart the application. Please check the error messages above.${NC}"
            exit 1
        fi
    fi
    
    echo ""
    echo "Commands:"
    echo "  ./control stop     - Stop the application"
    echo "  ./control logs -f  - View live logs"
    echo "  ./control status   - Check container status"
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
    
    # Parse arguments to extract service name if provided
    local args=()
    local service=""
    
    # Skip 'logs' command
    shift
    
    # Process remaining arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--follow|--tail)
                args+=("$1")
                shift
                ;;
            *)
                # Check if this argument is a valid service name
                for valid_service in "${AVAILABLE_SERVICES[@]}"; do
                    if [ "$1" = "$valid_service" ]; then
                        service="$1"
                        shift
                        continue 2
                    fi
                done
                # If not a service name, treat as regular argument
                args+=("$1")
                shift
                ;;
        esac
    done
    
    if [ -n "$service" ]; then
        validate_service "$service"
        echo -e "${BLUE}Showing logs for service: $service${NC}"
        $DOCKER_COMPOSE logs "${args[@]}" "$service"
    else
        $DOCKER_COMPOSE logs "${args[@]}"
    fi
}

# Main script logic
case "${1:-help}" in
    start)
        start_app "$2"
        ;;
    stop)
        stop_app "$2"
        ;;
    restart)
        restart_app "$2"
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
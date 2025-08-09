#!/bin/bash
# Test runner for all backend services
# This script can test backends either in Docker containers or locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default configuration
USE_DOCKER=${USE_DOCKER:-true}
VERBOSE=${VERBOSE:-false}

print_header() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

test_python_backend() {
    print_header "Testing Python Backend"
    
    if [ "$USE_DOCKER" = true ]; then
        # Test using Docker
        docker exec webrepl-backend-python python test_api.py
    else
        # Test locally
        cd python
        python test_api.py
        cd ..
    fi
}

test_javascript_backend() {
    print_header "Testing JavaScript Backend"
    
    if [ "$USE_DOCKER" = true ]; then
        # Test using Docker
        docker exec webrepl-backend-javascript node test_api.js
    else
        # Test locally
        cd javascript
        node test_api.js
        cd ..
    fi
}

test_ruby_backend() {
    print_header "Testing Ruby Backend"
    
    if [ "$USE_DOCKER" = true ]; then
        # Test using Docker
        docker exec webrepl-backend-ruby ruby test_api.rb
    else
        # Test locally
        cd ruby
        ruby test_api.rb
        cd ..
    fi
}

test_php_backend() {
    print_header "Testing PHP Backend"
    
    if [ "$USE_DOCKER" = true ]; then
        # Test using Docker
        docker exec webrepl-backend-php php test_api.php
    else
        # Test locally
        cd php
        php test_api.php
        cd ..
    fi
}

test_kotlin_backend() {
    print_header "Testing Kotlin Backend"
    
    if [ "$USE_DOCKER" = true ]; then
        # Test using Docker
        docker exec webrepl-backend-kotlin kotlinc -script test_api.kt
    else
        # Test locally
        cd kotlin
        kotlinc -script test_api.kt
        cd ..
    fi
}

run_integration_tests() {
    print_header "Running Integration Tests"
    
    # Generate a test session ID
    TEST_SESSION="test-integration-session"
    
    # Test that all backends are accessible through nginx
    echo "Testing Python through nginx..."
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:8080/api/python/execute/${TEST_SESSION}" \
        -H "Content-Type: application/json" \
        -d '{"code": "print(1)"}')
    if [ "$response" = "200" ]; then
        print_success "Python backend accessible through nginx"
    else
        print_error "Python backend not accessible (HTTP $response)"
        return 1
    fi
    
    echo "Testing JavaScript through nginx..."
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:8080/api/javascript/execute/${TEST_SESSION}" \
        -H "Content-Type: application/json" \
        -d '{"code": "1"}')
    if [ "$response" = "200" ]; then
        print_success "JavaScript backend accessible through nginx"
    else
        print_error "JavaScript backend not accessible (HTTP $response)"
        return 1
    fi
    
    echo "Testing Ruby through nginx..."
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:8080/api/ruby/execute/${TEST_SESSION}" \
        -H "Content-Type: application/json" \
        -d '{"code": "1"}')
    if [ "$response" = "200" ]; then
        print_success "Ruby backend accessible through nginx"
    else
        print_error "Ruby backend not accessible (HTTP $response)"
        return 1
    fi
    
    echo "Testing PHP through nginx..."
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:8080/api/php/execute/${TEST_SESSION}" \
        -H "Content-Type: application/json" \
        -d '{"code": "echo 1;"}')
    if [ "$response" = "200" ]; then
        print_success "PHP backend accessible through nginx"
    else
        print_error "PHP backend not accessible (HTTP $response)"
        return 1
    fi
    
    echo "Testing Kotlin through nginx..."
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:8080/api/kotlin/execute/${TEST_SESSION}" \
        -H "Content-Type: application/json" \
        -d '{"code": "1 + 1"}')
    if [ "$response" = "200" ]; then
        print_success "Kotlin backend accessible through nginx"
    else
        print_error "Kotlin backend not accessible (HTTP $response)"
        return 1
    fi
}

show_usage() {
    echo "Usage: $0 [OPTIONS] [BACKEND]"
    echo ""
    echo "Test all backend services or a specific backend"
    echo ""
    echo "BACKEND:"
    echo "  python      Test only Python backend"
    echo "  javascript  Test only JavaScript backend"
    echo "  ruby        Test only Ruby backend"
    echo "  php         Test only PHP backend"
    echo "  kotlin      Test only Kotlin backend"
    echo "  all         Test all backends (default)"
    echo ""
    echo "OPTIONS:"
    echo "  --local     Run tests against local backends (not Docker)"
    echo "  --docker    Run tests against Docker containers (default)"
    echo "  --verbose   Show detailed output"
    echo "  --help      Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                    # Test all backends in Docker"
    echo "  $0 python             # Test only Python backend"
    echo "  $0 --local javascript # Test JavaScript backend locally"
}

# Parse command line arguments
BACKEND="all"
while [[ $# -gt 0 ]]; do
    case $1 in
        --local)
            USE_DOCKER=false
            shift
            ;;
        --docker)
            USE_DOCKER=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        python|javascript|ruby|php|kotlin|all)
            BACKEND=$1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
print_header "WebREPL Backend Test Suite"

if [ "$USE_DOCKER" = true ]; then
    echo "Testing mode: Docker containers"
    
    # Check if containers are running
    if ! docker ps | grep -q webrepl-backend; then
        print_warning "Backend containers are not running. Starting them..."
        docker compose up -d
        
        # Wait for containers to be ready
        echo "Waiting for containers to start..."
        sleep 5
        
        # Verify they're running now
        if ! docker ps | grep -q webrepl-backend; then
            print_error "Failed to start backend containers"
            exit 1
        fi
        print_success "Backend containers started successfully"
    fi
else
    echo "Testing mode: Local"
    print_warning "Make sure all backends are running locally on their respective ports"
fi

# Track overall success
OVERALL_SUCCESS=true

# Run selected tests
case $BACKEND in
    python)
        test_python_backend || OVERALL_SUCCESS=false
        ;;
    javascript)
        test_javascript_backend || OVERALL_SUCCESS=false
        ;;
    ruby)
        test_ruby_backend || OVERALL_SUCCESS=false
        ;;
    php)
        test_php_backend || OVERALL_SUCCESS=false
        ;;
    kotlin)
        test_kotlin_backend || OVERALL_SUCCESS=false
        ;;
    all)
        test_python_backend || OVERALL_SUCCESS=false
        test_javascript_backend || OVERALL_SUCCESS=false
        test_ruby_backend || OVERALL_SUCCESS=false
        test_php_backend || OVERALL_SUCCESS=false
        test_kotlin_backend || OVERALL_SUCCESS=false
        
        if [ "$USE_DOCKER" = true ]; then
            run_integration_tests || OVERALL_SUCCESS=false
        fi
        ;;
esac

# Final summary
echo ""
if [ "$OVERALL_SUCCESS" = true ]; then
    print_header "All Tests Passed! 🎉"
    exit 0
else
    print_header "Some Tests Failed 😞"
    exit 1
fi
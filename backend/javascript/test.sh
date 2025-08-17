#!/bin/bash

# Test script for JavaScript backend using Docker Compose

set -e

echo "🧪 Starting containerized tests for JavaScript backend..."

# Change to tests directory where docker compose.yml is located
cd "$(dirname "$0")/tests"

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker compose down --remove-orphans

# Build and run tests
echo "🏗️  Building test containers..."
docker compose build

echo "🚀 Running tests..."
# Capture docker compose exit code
if docker compose up --abort-on-container-exit; then
    TEST_RESULT="passed"
else
    TEST_RESULT="failed"
fi

# Clean up
echo "🧹 Cleaning up containers..."
docker compose down --remove-orphans

# Exit with appropriate code
if [ "$TEST_RESULT" = "passed" ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Tests failed!"
    exit 1
fi
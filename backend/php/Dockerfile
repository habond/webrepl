# PHP REPL Backend Dockerfile
FROM php:8.2-cli

# Install required extensions
RUN docker-php-ext-install pcntl

# Set working directory
WORKDIR /app

# Copy PHP server files
COPY server.php ./

# Expose port
EXPOSE 8000

# Install curl for health check
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start PHP server directly (no shell wrapper for faster shutdown)
CMD ["php", "-S", "0.0.0.0:8000", "server.php"]
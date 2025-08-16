FROM python:3.11-slim

# Install coreutils for stdbuf command
RUN apt-get update && apt-get install -y coreutils && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create directory for session working directories
RUN mkdir -p /tmp/bash_sessions

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# PHP Backend Test Runner
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test file
COPY test.py .

# Default command runs the tests
CMD ["pytest", "test.py", "-v", "--tb=short"]
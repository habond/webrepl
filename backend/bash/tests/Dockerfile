FROM python:3.11-slim

WORKDIR /app

# Install any additional testing utilities if needed in the future
# RUN apt-get update && apt-get install -y \
#     <additional-tools> \
#     && rm -rf /var/lib/apt/lists/*

# Copy and install test dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test file
COPY test.py ./

# Default command
CMD ["pytest", "test.py", "-v"]
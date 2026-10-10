FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source tree and tests
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Default entrypoint
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]

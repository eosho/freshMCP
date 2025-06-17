# Dockerfile for Azure Cosmos DB MCP Service
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libicu-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy only requirements first for layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the cosmos directory and its contents
COPY src/cosmos/mcp /app/cosmos_mcp

# Fix permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the FastAPI port
EXPOSE 8001

# Start the Cosmos MCP server
CMD ["python", "-m", "cosmos_mcp.server"]

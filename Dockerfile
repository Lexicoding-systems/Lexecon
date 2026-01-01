# Multi-stage Dockerfile for Lexecon
# Optimized for security and size

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY pyproject.toml .
COPY README.md .

# Install package
RUN pip install --no-cache-dir --user .

# Stage 2: Runtime
FROM python:3.11-slim

# Security: Create non-root user
RUN groupadd -r lexecon && useradd -r -g lexecon lexecon

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/lexecon/.local

# Copy application
COPY --from=builder /build/src ./src
COPY --from=builder /build/pyproject.toml .

# Create data directory
RUN mkdir -p /data/.lexecon && chown -R lexecon:lexecon /data

# Set environment variables
ENV PATH=/home/lexecon/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    LEXECON_DATA_DIR=/data/.lexecon \
    LEXECON_LOG_LEVEL=INFO \
    LEXECON_LOG_FORMAT=json

# Switch to non-root user
USER lexecon

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# Use tini as init system
ENTRYPOINT ["/usr/bin/tini", "--"]

# Run server
CMD ["python", "-m", "uvicorn", "lexecon.api.server:app", "--host", "0.0.0.0", "--port", "8000"]

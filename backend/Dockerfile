# =============================================================================
# CampusPilot AI — Backend Production Dockerfile
# Multi-arch, non-root, security-hardened FastAPI container
# =============================================================================

FROM python:3.11-slim AS runner

# Prevent Python from writing .pyc files and enable unbuffered streaming logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

# Install minimal OS dependencies for healthchecks and runtime networking
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create unprivileged system user and group (security best practice)
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -s /bin/bash -m appuser

# Install Python dependencies first (leverages Docker layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy application source code and migrations
COPY . /app/

# Ensure all files are owned by the unprivileged user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose internal FastAPI port
EXPOSE 8000

# Container healthcheck querying FastAPI /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch Uvicorn with proxy headers enabled for Nginx reverse proxy compatibility
# Single worker recommended for 2 GiB EC2 t3.small instance
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]

# ==============================================================================
# BeanFlow Payroll Backend - Production Dockerfile
# ==============================================================================
# Multi-stage build for FastAPI application with uv package manager
# Target: linux/amd64 (for deployment to Ubuntu server)
# Reference: beancount-LLM/backend/Dockerfile
# ==============================================================================

# ==================== Build Stage ====================
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install production dependencies only
RUN uv sync --no-cache --no-dev

# ==================== Runtime Stage ====================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user FIRST (before COPY --chown)
RUN groupadd -r appuser && useradd -r -m -g appuser appuser

# Install runtime dependencies
# - curl: for healthcheck
# - reportlab dependencies for PDF generation (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager (needed for runtime)
RUN pip install --no-cache-dir uv

# Copy virtual environment from builder stage with correct ownership
# Using --chown avoids creating a separate layer for chown (saves space)
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code with correct ownership
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser config/ ./config/

# Set environment variables for Python to use the virtual environment
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set uv cache directory and prepare cache directory
ENV UV_CACHE_DIR=/home/appuser/.cache/uv
RUN mkdir -p /home/appuser/.cache && chown -R appuser:appuser /home/appuser

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8040

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8040/health || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8040"]

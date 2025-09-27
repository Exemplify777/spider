# SPIDER Dockerfile
# Multi-stage build for production-ready container

# Build stage
FROM python:3.9-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.9-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Install Playwright and browsers
RUN pip install playwright && \
    playwright install chromium && \
    playwright install-deps

# Create non-root user
RUN groupadd -r spider && useradd -r -g spider spider

# Create application directory
WORKDIR /app

# Copy application code
COPY spider/ ./spider/
COPY config/ ./config/
COPY lambda_handler.py .
COPY requirements.txt .

# Create necessary directories
RUN mkdir -p data logs cache && \
    chown -R spider:spider /app

# Switch to non-root user
USER spider

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Default command
CMD ["python", "-m", "spider.main"]

# Development stage
FROM production as development

# Switch back to root for development tools
USER root

# Install development dependencies
RUN pip install pytest pytest-cov black isort flake8 mypy

# Install additional development tools
RUN apt-get update && apt-get install -y \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Switch back to spider user
USER spider

# Override command for development
CMD ["python", "-m", "spider.main", "--config", "config/spider.yaml"]

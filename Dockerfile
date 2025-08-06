# Red Hat Status Checker - Production Container
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY redhat_status/ ./redhat_status/
COPY redhat_status.py .
COPY config.json .
COPY .env .

# Create non-root user for security
RUN groupadd -r redhat && useradd -r -g redhat redhat
RUN chown -R redhat:redhat /app
USER redhat

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 redhat_status.py quick --quiet || exit 1

# Default command
CMD ["python3", "redhat_status.py", "quick"]

# Labels for metadata
LABEL maintainer="Red Hat Status Team"
LABEL version="3.1.0"
LABEL description="Enterprise-grade Red Hat service monitoring platform"

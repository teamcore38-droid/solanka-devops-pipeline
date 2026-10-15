# Multi-stage / Secure Production Dockerfile for Solanka Digital Tourism API
# Adheres to ISO/IEC 27001:2022 ISMS Security Hardening Standards

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PORT=8000

WORKDIR /app

# Install curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app/ ./app

# Create a non-root dedicated service user (ISO 27001 Least Privilege Principle)
RUN useradd -u 1001 -m solanka_user && \
    chown -R solanka_user:solanka_user /app

USER solanka_user

# Expose API port
EXPOSE 8000

# Container Health Check (Used by Docker Engine, Jenkins, and Ansible)
HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch application with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

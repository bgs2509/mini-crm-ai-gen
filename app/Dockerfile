# Multi-stage build for smaller image
FROM python:3.11-slim as builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Copy entrypoint script
COPY --chown=appuser:appuser entrypoint.sh /app/entrypoint.sh

# Make entrypoint executable
USER root
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Add local Python packages to PATH
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

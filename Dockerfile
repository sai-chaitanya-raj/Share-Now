# ============================================================
# NowShare — Production Dockerfile
# Multi-stage optimized build with security best practices
# ============================================================

FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ---- Dependencies stage (cached separately) ----
FROM base AS deps

WORKDIR /app

# Copy only requirements first for layer caching
COPY requirements.txt .

# Install dependencies without cache to minimize image size
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- Application stage ----
FROM base AS runtime

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Copy installed packages from deps stage
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create uploads directory with correct permissions
RUN mkdir -p uploads && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Default port (overridden by Railway/Docker Compose)
ENV PORT=3000

# Expose the port
EXPOSE ${PORT}

# Health check — verifies the app is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')" || exit 1

# Start with gunicorn (shell form for $PORT expansion)
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT} --workers 2 --timeout 120 --access-logfile - --error-logfile -"]

# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies for packages with C extensions (e.g. bcrypt)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from build stage
COPY --from=builder /install /usr/local

# Copy application source and entrypoint
COPY . .
RUN chmod +x entrypoint.sh

# Non-root user for security
RUN useradd --no-create-home --shell /bin/false appuser \
    && chown -R appuser /app
USER appuser

EXPOSE 8000

# entrypoint.sh runs migrations then starts uvicorn.
# Extra CMD args (e.g. --reload) are forwarded to uvicorn.
ENTRYPOINT ["./entrypoint.sh"]

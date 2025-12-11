FROM python:3.12-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=ghcr.io/amacneil/dbmate /usr/local/bin/dbmate /usr/local/bin/dbmate

# Create app directory and set up user
RUN \
    apt-get update && apt-get install -y \
        curl && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir /app && \
    chown 1000:1000 /app

WORKDIR /app

# Copy dependencies as root, then fix ownership
COPY uv.lock pyproject.toml /app/

# Switch to non-root user
USER 1000:1000

# Install dependencies
RUN \
    uv sync \
        --no-cache-dir \
        --no-dev \
        --locked

# Copy application files (these will be owned by 1000:1000 since we're already that user)
COPY --chown=1000:1000 db/migrations /app/migrations
COPY --chown=1000:1000 src /app/src
COPY --chown=1000:1000 scripts/docker-entrypoint.sh /app/scripts/docker-entrypoint.sh

# Make entrypoint executable
RUN chmod +x /app/scripts/docker-entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"
ENV HOST="0.0.0.0"
ENV PORT="8000"

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["/bin/bash", "-c", "uvicorn src.main:app --host $HOST --port $PORT"]

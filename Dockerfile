FROM python:3.12-slim-trixie


COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# https://github.com/amacneil/dbmate
# Pulls down the dbmate binary from its official image
COPY --from=ghcr.io/amacneil/dbmate /usr/local/bin/dbmate /usr/local/bin/dbmate


RUN \
    mkdir /app

WORKDIR /app


# Copy in the dependencies
COPY uv.lock pyproject.toml /app/


# Install the dependencies
RUN \
    uv sync \
        --no-cache-dir \
        --no-dev \
        --locked


# Copy in the application code
COPY src /app/src


ENV PATH="/app/.venv/bin:$PATH"
ENV HOST="0.0.0.0"
ENV PORT="8000"

USER 1000:1000


ENTRYPOINT ["/bin/bash", "-c"]
CMD ["uvicorn src.main:app --host $HOST --port $PORT"]

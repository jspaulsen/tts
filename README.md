# TTS Service

A text-to-speech service using AWS Polly, built with FastAPI.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker and Docker Compose
- AWS credentials configured (for Polly access)

## Installation

Install dependencies using uv:

```bash
uv sync
```

For development dependencies (testing, etc.):

```bash
uv sync --dev
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (e.g., `postgres://user:pass@localhost:5432/dbname`) |
| `ADMIN_API_TOKEN` | Yes | Admin API authentication token |
| `MAXIMUM_CHARACTERS_PER_REQUEST` | No | Max characters per TTS request (default: 2048) |
| `LRU_CACHE_SIZE` | No | Size of the LRU cache (default: 64) |

## AWS Authentication

This service requires AWS credentials with access to Amazon Polly. You can configure credentials using any of the standard AWS methods:

- **Environment variables**: Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optionally `AWS_REGION`
- **Shared credentials file**: Configure `~/.aws/credentials`
- **IAM role**: When running on AWS infrastructure (EC2, ECS, Lambda), use an attached IAM role
- **AWS SSO**: Use `aws sso login` with a configured profile

The IAM policy must include the `polly:SynthesizeSpeech` permission.

## Local Development

### Starting the Database

Start PostgreSQL and run migrations using Docker Compose:

```bash
docker compose -f docker-compose.test.yml up -d
```

If you've added new database migrations, rebuild the containers:

```bash
docker compose -f docker-compose.test.yml up -d --build
```

### Running the Application

```bash
DATABASE_URL="postgres://postgres:postgres@localhost:5432/postgres" \
ADMIN_API_TOKEN="your_token" \
uv run uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Testing

### Running Unit Tests

First, ensure the database is running:

```bash
docker compose -f docker-compose.test.yml up -d
```

Then run the tests:

```bash
uv run pytest
```

### Debugging

For verbose test output:

```bash
uv run pytest -v
```

To run a specific test file:

```bash
uv run pytest tests/routers/test_users.py
```

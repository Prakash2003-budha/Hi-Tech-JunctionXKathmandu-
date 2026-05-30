FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

COPY pyproject.toml .
COPY uv.lock .         
COPY backend/ .
RUN uv pip install --system -r pyproject.toml

COPY . .

CMD ["sh", "-c", "\
    echo 'Waiting for Postgres...' && \
    until python3 -c \"import asyncpg, asyncio; asyncio.run(asyncpg.connect('$DATABASE_URL'))\" 2>/dev/null; do \
        echo 'DB not ready, retrying in 2s...' && sleep 2; \
    done && \
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload \
"]
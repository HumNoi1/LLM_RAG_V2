FROM python:3.12-slim

WORKDIR /app

# System deps needed for pdfplumber, torch, and FlagEmbedding
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev --no-cache

COPY . .

# Place uv-managed venv on PATH so uvicorn is found directly
ENV PATH="/app/.venv/bin:$PATH"

# Dev: hot-reload with uvicorn
# Production (Sprint 4): remove --reload and set workers > 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

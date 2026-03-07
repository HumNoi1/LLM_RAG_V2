FROM python:3.12-slim

WORKDIR /app

# System deps needed for pdfplumber, torch, and FlagEmbedding
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Dev: hot-reload with uvicorn
# Production (Sprint 4): remove --reload and set workers > 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

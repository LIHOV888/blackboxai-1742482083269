# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set environment variables
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME="/opt/poetry" \
    PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock* ./
COPY telegram_uid_scraper ./telegram_uid_scraper
COPY README.md ./

# Install dependencies
RUN poetry install --no-dev --no-root

# Create output directory
RUN mkdir -p /app/output

# Set entrypoint
ENTRYPOINT ["poetry", "run", "telegram-uid-scraper"]

# Default command (can be overridden)
CMD ["--help"]

# Labels
LABEL maintainer="BLACKBOXAI" \
      version="0.1.0" \
      description="A stealth scraper for Telegram group member information"
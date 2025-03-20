# Use Python 3.8 slim image as base
FROM python:3.8-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.5.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

# Add Poetry to PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock* ./
COPY telegram_uid_scraper/ ./telegram_uid_scraper/
COPY dashboard/ ./dashboard/
COPY README.md ./

# Install dependencies
RUN poetry install --no-dev --no-interaction

# Create output directory
RUN mkdir -p output

# Expose port for dashboard
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["poetry", "run", "tg-scraper"]

# Default command (can be overridden)
CMD ["--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/stats || exit 1

# Labels
LABEL maintainer="Your Name <your.email@example.com>" \
    version="2.0.0" \
    description="Advanced Telegram UID scraper with auto-add capability and modern dashboard"
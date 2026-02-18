# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=development

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy requirements files
COPY requirements.in requirements-dev.in ./

# Generate and install dependencies
RUN uv pip compile requirements.in -o requirements.txt && \
    uv pip compile requirements-dev.in -o requirements-dev.txt && \
    uv pip install --system -r requirements-dev.txt

# Copy the rest of the application
COPY . .

# Expose port 8000
EXPOSE 8000

# Start the FastAPI application with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

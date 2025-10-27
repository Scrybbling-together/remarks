# ReMarkable to Markdown Converter - Docker Image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    PyMuPDF \
    pyyaml \
    parsita \
    numpy \
    flask \
    'sentry-sdk[flask]' \
    gunicorn \
    git+https://github.com/scrybbling-together/rmscene.git@main \
    git+https://github.com/scrybbling-together/rmc.git@main

# Create directories for input and output
RUN mkdir -p /input /output

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command shows help
ENTRYPOINT ["python", "-m", "remarks"]
CMD ["--help"]

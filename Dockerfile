# Databricks PowerBI Pipeline Docker Image
FROM python:3.10-slim

LABEL maintainer="Databricks PowerBI Pipeline Team"
LABEL description="Production-ready ETL pipeline for Databricks-Power BI e-commerce analytics"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set Java environment
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir .

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data notebooks/src/config/tests/docs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Default command
CMD ["python", "src/validate_deployment.py"]

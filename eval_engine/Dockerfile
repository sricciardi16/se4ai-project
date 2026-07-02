# Use a slim, standard Python image
FROM python:3.10-slim

# Install build tools (gcc) AND system libraries for image/PDF processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libxcb1 \
    && rm -rf /var/lib/apt/lists/*

# Install pytest and the required plugins for our evaluation metrics
RUN pip install --no-cache-dir \
    pytest \
    pytest-json-report \
    pytest-timeout \
    pytest-cov

# Create the working directories
RUN mkdir -p /app/repo /app/results

# Copy the entrypoint script into the container and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
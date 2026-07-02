# sandbox/Dockerfile
FROM python:3.10-slim

# Install basic system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install tools the LLM will use to test and verify its code
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-timeout \
    flake8 \
    mypy \
    requests # (Useful if the LLM writes integration tests later)

# Set the working directory. 
# We will mount the host's 'workspace' folder to this exact path.
WORKDIR /workspace
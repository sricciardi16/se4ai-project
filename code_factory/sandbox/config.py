# sandbox/config.py

DOCKER_IMAGE_NAME = "llm-coder-sandbox"
DOCKER_TIMEOUT_SECONDS = 60  # Shorter timeout, we don't want the LLM hanging forever

# Resource Limits (The Safety Net)
DOCKER_MEM_LIMIT = "1g"
DOCKER_CPU_LIMIT = "1.0"
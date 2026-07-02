
# Static configuration for the sandbox
DOCKER_IMAGE_NAME = "pytest-sandbox"
DOCKER_CACHE_VOLUME = "pytest-pip-cache"
DOCKER_TIMEOUT_SECONDS = 180

# Resource Limits (The Safety Net)
DOCKER_MEM_LIMIT = "1g"
DOCKER_CPU_LIMIT = "1.0"
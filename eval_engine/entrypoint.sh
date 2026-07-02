#!/bin/bash
# We do NOT use 'set -e' here because we want to manually catch and report errors.

echo "==> 1. Preparing isolated repository..."
cp -r /app/repo /tmp/repo
cd /tmp/repo

echo "==> 2. Attempting to install library..."
# We capture the installation logs. If it fails, we write the flag and exit gracefully.
if ! SETUPTOOLS_SCM_PRETEND_VERSION=1.0.0 pip install --disable-pip-version-check --prefer-binary . > /app/results/install.log 2>&1; then
    echo "INSTALL_FAILED" > /app/results/status.flag
    echo "Installation failed. See install.log for details."
    exit 0
fi


if [ -n "$EXTRA_DEPS" ]; then
    echo "==> 2.5. Installing extra test dependencies: $EXTRA_DEPS"
    # We use >> to append to the existing install.log
    if ! pip install --disable-pip-version-check --prefer-binary $EXTRA_DEPS >> /app/results/install.log 2>&1; then
        echo "INSTALL_FAILED" > /app/results/status.flag
        echo "Extra dependencies installation failed. See install.log."
        exit 0
    fi
fi

# If we reach here, the build succeeded.
echo "BUILT_SUCCESSFULLY" > /app/results/status.flag

cd /app

echo "==> 3. Executing Pytest with Coverage..."
# We run pytest, generate the JSON report, and generate the JSON coverage report.
# The '|| true' ensures the container doesn't crash if tests fail.
pytest test_suite.py \
    --timeout=60 \
    --json-report \
    --json-report-file=/app/results/report.json \
    --cov=${MODULE_NAME} \
    --cov-report=json:/app/results/coverage.json > /app/results/pytest.log 2>&1 || true 

echo "==> 4. Execution complete."
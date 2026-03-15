#!/bin/bash

echo "🤖 Initiating AI Headless Build & Test Sequence..."

# Use the -f flag to point exactly to where your compose file lives
docker compose -f /home/basti/Docker/PixelPilot/docker-compose.yml up debian-trixie-agent-test --build --abort-on-container-exit

# Capture the exit code of the docker container
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ TEST PASSED: The application compiled and ran successfully in headless mode."
    exit 0
else
    echo "❌ TEST FAILED: The application failed to compile or crashed upon startup."
    exit 1
fi

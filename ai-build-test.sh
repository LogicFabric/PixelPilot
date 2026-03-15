#!/bin/bash

echo "🤖 Initiating AI Headless Build & Test Sequence (Arch Native)..."

# We use 'run' instead of 'up' to temporarily override the arch-dev service.
# -e QT_QPA_PLATFORM=offscreen forces headless mode, ignoring your host Wayland.
# We wrap the bash command in single quotes ('') so $! is evaluated inside the container, not on your host.
docker compose -f /home/basti/Docker/PixelPilot/docker-compose.yml run \
    --rm \
    --build \
    -e QT_QPA_PLATFORM=offscreen \
    arch-dev \
    bash -c 'mkdir -p build/arch-dev && cd build/arch-dev && cmake -G Ninja -DCMAKE_BUILD_TYPE=Debug ../.. && ninja && echo "⏳ Running 5-second crash test..." && (./bin/PixelPilotApp & PID=$!; sleep 5; kill -0 $PID && kill $PID || exit 1)'

# Capture the exit code of the docker container
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ TEST PASSED: The application compiled and ran successfully in headless mode."
    exit 0
else
    echo "❌ TEST FAILED: The application failed to compile or crashed upon startup."
    exit 1
fi
#!/bin/bash

# Docker Setup Verification Script
# Run this after restarting your session

echo "=== Docker Setup Verification ==="
echo

echo "1. Checking user groups:"
groups | grep -q docker && echo "✅ User is in docker group" || echo "❌ User NOT in docker group"

echo
echo "2. Testing Docker daemon access:"
if timeout 5 docker ps >/dev/null 2>&1; then
    echo "✅ Docker daemon accessible"
else
    echo "❌ Docker daemon NOT accessible"
fi

echo
echo "3. Testing Docker functionality:"
if timeout 15 docker run --rm hello-world >/dev/null 2>&1; then
    echo "✅ Docker working correctly"
else
    echo "❌ Docker NOT working"
fi

echo
echo "4. Docker version info:"
docker --version

echo
echo "=== Verification Complete ==="
echo
echo "If all tests pass, you can now run:"
echo "  ./test-docker.sh --unit-only"
echo "  python -m pytest tests/test_docker_integration.py -v"

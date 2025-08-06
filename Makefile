# Makefile for Red Hat Status Checker Docker/Podman Testing

.PHONY: help test-docker test-docker-unit test-docker-comprehensive build-test clean-test test-podman

# Default target
help:
	@echo "🐳 Red Hat Status Checker - Container Testing Commands"
	@echo "====================================================="
	@echo ""
	@echo "Available targets:"
	@echo "  test-docker              - Run all tests in Docker container"
	@echo "  test-podman              - Run all tests in Podman container (recommended)"
	@echo "  test-docker-unit         - Run only unit tests in Docker"
	@echo "  test-docker-comprehensive - Run comprehensive tests with docker-compose"
	@echo "  build-test               - Build test container"
	@echo "  clean-test               - Clean up test containers and results"
	@echo "  test-docker-interactive  - Run interactive test container"
	@echo ""
	@echo "Examples:"
	@echo "  make test-podman         # Run all tests with Podman"
	@echo "  make test-docker         # Run all tests with Docker"
	@echo "  make test-docker-unit    # Quick unit tests only"
	@echo "  make clean-test          # Clean up everything"

# Build test container
build-test:
	@echo "🔧 Building test container..."
	docker build -f Dockerfile.test -t redhat-status-test .

# Run comprehensive Podman tests (recommended)
test-podman:
	@echo "🧪 Running comprehensive Podman tests..."
	./test-podman.sh

# Run comprehensive Docker tests
test-docker:
	@echo "🧪 Running comprehensive Docker tests..."
	./test-docker.sh

# Run unit tests only
test-docker-unit:
	@echo "🧪 Running unit tests in Docker..."
	./test-docker.sh --unit-only

# Run comprehensive tests with docker-compose
test-docker-comprehensive:
	@echo "🧪 Running comprehensive tests with docker-compose..."
	./test-docker.sh --comprehensive

# Interactive test container for debugging
test-docker-interactive:
	@echo "🐳 Starting interactive test container..."
	docker run -it --rm \
		-v $(PWD)/redhat_status:/app/redhat_status \
		-v $(PWD)/tests:/app/tests \
		-v $(PWD)/test-results:/app/test-results \
		-e TESTING=1 \
		redhat-status-test bash

# Quick test - build and run unit tests
test-quick:
	@echo "⚡ Quick Docker test (build + unit tests)..."
	$(MAKE) build-test
	docker run --rm \
		-v $(PWD)/test-results:/app/test-results \
		-e TESTING=1 \
		redhat-status-test \
		python3 -m pytest tests/ -v --tb=short --junit-xml=/app/test-results/junit.xml

# Clean up test containers and results
clean-test:
	@echo "🧹 Cleaning up test containers and results..."
	-docker ps -q --filter "name=redhat-status-test" | xargs -r docker stop
	-docker ps -aq --filter "name=redhat-status-test" | xargs -r docker rm
	-docker rmi redhat-status-test 2>/dev/null || true
	-docker-compose -f docker-compose.test.yml down --volumes --remove-orphans 2>/dev/null || true
	-rm -rf test-results coverage-reports performance-results test-results-py39 build.log
	@echo "✅ Cleanup completed"

# Show test results
show-results:
	@echo "📊 Test Results Summary"
	@echo "======================"
	@if [ -f test-results/junit.xml ]; then \
		echo "✅ JUnit results available: test-results/junit.xml"; \
	else \
		echo "❌ No JUnit results found"; \
	fi
	@if [ -d coverage-reports/html ]; then \
		echo "✅ Coverage report available: coverage-reports/html/index.html"; \
	else \
		echo "❌ No coverage report found"; \
	fi
	@if [ -f test-results/docker-test-report.md ]; then \
		echo "✅ Docker test report: test-results/docker-test-report.md"; \
		echo ""; \
		cat test-results/docker-test-report.md; \
	fi

# Continuous testing - rebuild and test on changes
test-watch:
	@echo "👀 Watching for changes and running tests..."
	@while true; do \
		$(MAKE) test-quick; \
		echo "⏰ Waiting for changes... (Press Ctrl+C to stop)"; \
		sleep 10; \
	done

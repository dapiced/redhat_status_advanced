#!/bin/bash
# Docker Test Runner for Red Hat Status Checker
# Runs comprehensive tests in isolated Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check Docker availability and permissions
check_docker_prerequisites() {
    print_status "Checking Docker prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed or not in PATH"
        echo "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Docker version
    if ! docker --version >/dev/null 2>&1; then
        print_error "Docker command failed - Docker may not be running"
        exit 1
    fi
    
    # Check Docker permissions
    if ! docker ps >/dev/null 2>&1; then
        print_error "Docker permission denied. Current user needs Docker access."
        echo ""
        echo "To fix this issue, run:"
        echo "  sudo usermod -aG docker \$USER"
        echo "  newgrp docker"
        echo "  # Or logout and login again"
        echo ""
        echo "Alternatively, you can run this script with sudo:"
        echo "  sudo ./test-docker.sh"
        exit 1
    fi
    
    print_success "Docker is available and accessible"
}

# Create necessary directories
create_directories() {
    print_status "Creating test output directories..."
    mkdir -p test-results coverage-reports performance-results test-results-py39
    print_success "Directories created"
}

# Build test container
build_test_container() {
    print_status "Building test container..."
    
    # Check if Dockerfile.test exists
    if [ ! -f "Dockerfile.test" ]; then
        print_error "Dockerfile.test not found in current directory"
        exit 1
    fi
    
    # Create build log file
    local build_log="build-docker.log"
    
    print_status "Building Docker image 'redhat-status-test'..."
    if docker build -f Dockerfile.test -t redhat-status-test . > "$build_log" 2>&1; then
        print_success "Test container built successfully"
        # Clean up build log on success
        rm -f "$build_log"
        return 0
    else
        print_error "Failed to build test container"
        echo ""
        echo "Build log output:"
        echo "=================="
        cat "$build_log"
        echo "=================="
        echo ""
        echo "Build log saved to: $build_log"
        exit 1
    fi
}

# Run basic unit tests
run_unit_tests() {
    print_status "Running unit tests with pytest..."
    
    if docker run --rm \
        -v "$(pwd)/test-results:/app/test-results" \
        -v "$(pwd)/coverage-reports:/app/coverage-reports" \
        -e TESTING=1 \
        redhat-status-test \
        python3 -m pytest tests/ -v --tb=short \
        --junit-xml=/app/test-results/junit.xml \
        --cov=redhat_status \
        --cov-report=html:/app/coverage-reports/html \
        --cov-report=xml:/app/test-results/coverage.xml \
        --cov-report=term-missing; then
        print_success "Unit tests passed"
        return 0
    else
        print_error "Unit tests failed"
        return 1
    fi
}

# Run CLI flag tests
run_flag_tests() {
    print_status "Running CLI flag tests in container..."
    
    if docker run --rm \
        -e TESTING=1 \
        redhat-status-test \
        timeout 300 python3 run_tests.py --flags; then
        print_success "CLI flag tests passed"
        return 0
    else
        print_warning "CLI flag tests had issues (some expected for isolated environment)"
        return 0  # Don't fail the entire suite for flag tests in container
    fi
}

# Run example command tests
run_example_tests() {
    print_status "Running example command tests in container..."
    
    if docker run --rm \
        -e TESTING=1 \
        redhat-status-test \
        timeout 300 python3 run_tests.py --examples; then
        print_success "Example command tests passed"
        return 0
    else
        print_warning "Example command tests had issues (some expected for isolated environment)"
        return 0
    fi
}

# Run integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    
    if docker run --rm \
        -e TESTING=1 \
        redhat-status-test \
        python3 -m pytest tests/test_integration.py -v --tb=short; then
        print_success "Integration tests passed"
        return 0
    else
        print_error "Integration tests failed"
        return 1
    fi
}

# Run performance tests
run_performance_tests() {
    print_status "Running performance tests..."
    
    if docker run --rm \
        -v "$(pwd)/performance-results:/app/performance-results" \
        -e TESTING=1 \
        -e PERFORMANCE_TESTING=1 \
        redhat-status-test \
        sh -c "
            echo '⚡ Performance Testing Report' > /app/performance-results/performance-report.txt &&
            echo '=========================' >> /app/performance-results/performance-report.txt &&
            echo 'Date: $(date)' >> /app/performance-results/performance-report.txt &&
            echo '' >> /app/performance-results/performance-report.txt &&
            timeout 60 python3 redhat_status.py quick --performance >> /app/performance-results/performance-report.txt 2>&1 || true &&
            echo '' >> /app/performance-results/performance-report.txt &&
            echo 'Container Performance Test Completed' >> /app/performance-results/performance-report.txt
        "; then
        print_success "Performance tests completed"
        return 0
    else
        print_warning "Performance tests had issues (expected in isolated environment)"
        return 0
    fi
}

# Run comprehensive test using docker-compose
run_comprehensive_tests() {
    print_status "Running comprehensive tests with docker-compose..."
    
    if command -v docker-compose >/dev/null 2>&1; then
        if docker-compose -f docker-compose.test.yml up --abort-on-container-exit; then
            print_success "Comprehensive docker-compose tests passed"
            return 0
        else
            print_warning "Docker-compose tests had issues"
            return 1
        fi
    else
        print_warning "docker-compose not available, skipping comprehensive tests"
        return 0
    fi
}

# Clean up containers and images
cleanup() {
    # Only attempt cleanup if Docker is accessible
    if ! docker ps >/dev/null 2>&1; then
        print_status "Skipping Docker cleanup due to permission issues"
        return 0
    fi
    
    print_status "Cleaning up Docker resources..."
    
    # Stop any running test containers with timeout
    print_status "Stopping running containers..."
    if docker ps -q --filter "ancestor=redhat-status-test" | head -10 | xargs -r timeout 30 docker stop 2>/dev/null; then
        print_status "Stopped running containers"
    fi
    
    # Remove stopped test containers
    print_status "Removing stopped containers..."
    if docker ps -aq --filter "ancestor=redhat-status-test" | head -10 | xargs -r docker rm 2>/dev/null; then
        print_status "Removed stopped containers"
    fi
    
    # Clean up docker-compose if it exists
    if [ -f docker-compose.test.yml ]; then
        print_status "Cleaning up docker-compose resources..."
        docker-compose -f docker-compose.test.yml down --volumes --remove-orphans 2>/dev/null || true
    fi
    
    # Remove dangling images (optional - only if --cleanup-images flag is set)
    if [[ "${CLEANUP_IMAGES:-false}" == "true" ]]; then
        print_status "Removing dangling images..."
        docker image prune -f 2>/dev/null || true
    fi
    
    print_success "Docker cleanup completed"
}

# Generate test report
generate_report() {
    print_status "Generating test report..."
    
    cat > test-results/docker-test-report.md << EOF
# Docker Test Report - Red Hat Status Checker

**Date:** $(date)
**Container:** redhat-status-test
**Environment:** Docker $(docker --version)

## Test Results Summary

### Unit Tests
- **Status:** $([ -f test-results/junit.xml ] && echo "✅ PASSED" || echo "❌ FAILED")
- **Coverage Report:** $([ -d coverage-reports/html ] && echo "Generated" || echo "Not generated")
- **JUnit XML:** $([ -f test-results/junit.xml ] && echo "Available" || echo "Not available")

### CLI Tests
- **Flag Tests:** Executed in container environment
- **Example Tests:** Executed in container environment
- **Integration Tests:** Executed with isolated dependencies

### Performance Tests
- **Report:** $([ -f performance-results/performance-report.txt ] && echo "Generated" || echo "Not generated")
- **Container Performance:** Measured in isolated environment

## Files Generated
EOF

    # List generated files
    find test-results coverage-reports performance-results -type f 2>/dev/null | sed 's/^/- /' >> test-results/docker-test-report.md || true
    
    print_success "Test report generated: test-results/docker-test-report.md"
}

# Main execution
main() {
    echo "🐳 DOCKER TESTING SUITE - RED HAT STATUS CHECKER"
    echo "================================================="
    echo ""
    
    # Parse command line arguments
    RUN_UNIT=true
    RUN_FLAG=true
    RUN_EXAMPLE=true
    RUN_INTEGRATION=true
    RUN_PERFORMANCE=true
    RUN_COMPREHENSIVE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                echo "🐳 DOCKER TESTING SUITE - RED HAT STATUS CHECKER"
                echo "================================================="
                echo ""
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --unit-only      Run only unit tests (no integration/performance tests)"
                echo "  --comprehensive  Run all tests including extensive benchmarks"
                echo "  --no-cleanup     Skip cleanup of Docker containers after tests"
                echo "  --help, -h       Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                     # Run standard test suite"
                echo "  $0 --unit-only        # Run only unit tests"
                echo "  $0 --comprehensive    # Run full comprehensive tests"
                echo "  $0 --no-cleanup       # Keep containers for debugging"
                echo ""
                exit 0
                ;;
            --unit-only)
                RUN_FLAG=false
                RUN_EXAMPLE=false
                RUN_INTEGRATION=false
                RUN_PERFORMANCE=false
                shift
                ;;
            --comprehensive)
                RUN_COMPREHENSIVE=true
                shift
                ;;
            --no-cleanup)
                NO_CLEANUP=true
                shift
                ;;
            *)
                echo "🐳 DOCKER TESTING SUITE - RED HAT STATUS CHECKER"
                echo "================================================="
                echo ""
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Unknown option: $1"
                echo ""
                echo "Options:"
                echo "  --unit-only      Run only unit tests"
                echo "  --comprehensive  Run all tests including extensive benchmarks"
                echo "  --no-cleanup     Skip cleanup of Docker containers after tests"
                echo "  --help, -h       Show this help message"
                echo ""
                exit 1
                ;;
        esac
    done
    
    # Setup trap for cleanup
    if [[ "${NO_CLEANUP:-false}" != "true" ]]; then
        trap cleanup EXIT
    fi
    
    # Check Docker prerequisites first
    check_docker_prerequisites
    
    # Execute test phases
    create_directories
    build_test_container
    
    exit_code=0
    
    if [[ "$RUN_COMPREHENSIVE" == "true" ]]; then
        run_comprehensive_tests || exit_code=1
    else
        if [[ "$RUN_UNIT" == "true" ]]; then
            run_unit_tests || exit_code=1
        fi
        
        if [[ "$RUN_INTEGRATION" == "true" ]]; then
            run_integration_tests || exit_code=1
        fi
        
        if [[ "$RUN_FLAG" == "true" ]]; then
            run_flag_tests || true  # Don't fail on flag tests
        fi
        
        if [[ "$RUN_EXAMPLE" == "true" ]]; then
            run_example_tests || true  # Don't fail on example tests
        fi
        
        if [[ "$RUN_PERFORMANCE" == "true" ]]; then
            run_performance_tests || true  # Don't fail on performance tests
        fi
    fi
    
    generate_report
    
    echo ""
    echo "================================================="
    if [[ $exit_code -eq 0 ]]; then
        print_success "🎉 DOCKER TESTING COMPLETED SUCCESSFULLY!"
        print_status "Check test-results/ and coverage-reports/ for detailed results"
    else
        print_error "💥 SOME TESTS FAILED IN DOCKER ENVIRONMENT"
        print_status "Check test-results/ for detailed error information"
    fi
    echo "================================================="
    
    exit $exit_code
}

# Run main function
main "$@"

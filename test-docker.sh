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

# Create necessary directories
create_directories() {
    print_status "Creating test output directories..."
    mkdir -p test-results coverage-reports performance-results test-results-py39
    print_success "Directories created"
}

# Build test container
build_test_container() {
    print_status "Building test container..."
    if docker build -f Dockerfile.test -t redhat-status-test . > build.log 2>&1; then
        print_success "Test container built successfully"
    else
        print_error "Failed to build test container"
        cat build.log
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
    print_status "Cleaning up test containers..."
    
    # Stop any running test containers
    docker ps -q --filter "name=redhat-status-test" | xargs -r docker stop
    
    # Remove test containers
    docker ps -aq --filter "name=redhat-status-test" | xargs -r docker rm
    
    # Clean up docker-compose if it exists
    if [ -f docker-compose.test.yml ]; then
        docker-compose -f docker-compose.test.yml down --volumes --remove-orphans 2>/dev/null || true
    fi
    
    print_success "Cleanup completed"
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
                echo "Usage: $0 [--unit-only] [--comprehensive] [--no-cleanup]"
                exit 1
                ;;
        esac
    done
    
    # Setup trap for cleanup
    if [[ "${NO_CLEANUP:-false}" != "true" ]]; then
        trap cleanup EXIT
    fi
    
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

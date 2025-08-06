#!/bin/bash
# Podman Test Runner for Red Hat Status Checker
# Runs comprehensive tests in isolated Podman containers

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
    if podman build -f Dockerfile.test -t redhat-status-test . > build.log 2>&1; then
        print_success "Test container built successfully"
        return 0
    else
        print_error "Failed to build test container"
        echo "Build log:"
        cat build.log
        return 1
    fi
}

# Run unit tests in container
run_unit_tests() {
    print_status "Running unit tests in container..."
    
    if podman run --rm \
        -v $(pwd)/test-results:/app/test-results \
        -e TESTING=1 \
        redhat-status-test \
        python3 -m pytest tests/ -v --tb=short --junit-xml=/app/test-results/junit.xml --cov=redhat_status --cov-report=html:/app/test-results/coverage > test-results/unit-tests.log 2>&1; then
        print_success "Unit tests passed"
        return 0
    else
        print_warning "Unit tests had issues"
        return 1
    fi
}

# Run CLI flag tests in container
run_cli_tests() {
    print_status "Running CLI flag tests in container..."
    
    if podman run --rm \
        -v $(pwd)/test-results:/app/test-results \
        -e TESTING=1 \
        redhat-status-test \
        python3 run_tests.py --flags > test-results/cli-tests.log 2>&1; then
        print_success "CLI flag tests passed"
        return 0
    else
        print_warning "CLI flag tests had issues"
        return 1
    fi
}

# Run integration tests in container
run_integration_tests() {
    print_status "Running integration tests in container..."
    
    if podman run --rm \
        -v $(pwd)/test-results:/app/test-results \
        -e TESTING=1 \
        redhat-status-test \
        python3 run_tests.py --examples > test-results/integration-tests.log 2>&1; then
        print_success "Integration tests passed"
        return 0
    else
        print_warning "Integration tests had issues"
        return 1
    fi
}

# Run performance tests in container
run_performance_tests() {
    print_status "Running performance tests in container..."
    
    if podman run --rm \
        -v $(pwd)/performance-results:/app/performance-results \
        -e TESTING=1 \
        redhat-status-test \
        python3 run_tests.py --advanced > performance-results/performance-tests.log 2>&1; then
        print_success "Performance tests passed"
        return 0
    else
        print_warning "Performance tests had issues"
        return 1
    fi
}

# Run comprehensive test using podman-compose (if available)
run_comprehensive_tests() {
    print_status "Running comprehensive tests with podman-compose..."
    
    if command -v podman-compose >/dev/null 2>&1; then
        if podman-compose -f docker-compose.test.yml up --abort-on-container-exit; then
            print_success "Comprehensive podman-compose tests passed"
            return 0
        else
            print_warning "Podman-compose tests had issues"
            return 1
        fi
    else
        print_warning "podman-compose not available, skipping comprehensive tests"
        return 1
    fi
}

# Clean up containers and results
cleanup() {
    print_status "Cleaning up test containers..."
    
    # Stop and remove any running test containers
    podman ps -q --filter "name=redhat-status-test" | xargs -r podman stop 2>/dev/null || true
    
    # Remove any stopped test containers
    podman ps -aq --filter "name=redhat-status-test" | xargs -r podman rm 2>/dev/null || true
    
    # Clean up podman-compose if it was used
    if command -v podman-compose >/dev/null 2>&1; then
        podman-compose -f docker-compose.test.yml down --volumes --remove-orphans 2>/dev/null || true
    fi
    
    print_success "Cleanup completed"
}

# Generate test report
generate_report() {
    print_status "Generating test report..."
    
    REPORT_FILE="test-results/podman-test-report.md"
    cat > $REPORT_FILE << EOF
# Podman Test Report

**Generated:** $(date)  
**Test Environment:** Podman Container  
**Python Version:** $(podman run --rm redhat-status-test python3 --version 2>/dev/null || echo "Unknown")  

## Test Results Summary

EOF

    # Check if test results exist and add to report
    local passed=0
    local total=0
    
    if [ -f "test-results/unit-tests.log" ]; then
        total=$((total + 1))
        if grep -q "failed\|error\|FAILED\|ERROR" test-results/unit-tests.log; then
            echo "- ❌ Unit Tests: FAILED" >> $REPORT_FILE
        else
            echo "- ✅ Unit Tests: PASSED" >> $REPORT_FILE
            passed=$((passed + 1))
        fi
    fi
    
    if [ -f "test-results/cli-tests.log" ]; then
        total=$((total + 1))
        if grep -q "failed\|error\|FAILED\|ERROR" test-results/cli-tests.log; then
            echo "- ❌ CLI Flag Tests: FAILED" >> $REPORT_FILE
        else
            echo "- ✅ CLI Flag Tests: PASSED" >> $REPORT_FILE
            passed=$((passed + 1))
        fi
    fi
    
    if [ -f "test-results/integration-tests.log" ]; then
        total=$((total + 1))
        if grep -q "failed\|error\|FAILED\|ERROR" test-results/integration-tests.log; then
            echo "- ❌ Integration Tests: FAILED" >> $REPORT_FILE
        else
            echo "- ✅ Integration Tests: PASSED" >> $REPORT_FILE
            passed=$((passed + 1))
        fi
    fi
    
    if [ -f "performance-results/performance-tests.log" ]; then
        total=$((total + 1))
        if grep -q "failed\|error\|FAILED\|ERROR" performance-results/performance-tests.log; then
            echo "- ❌ Performance Tests: FAILED" >> $REPORT_FILE
        else
            echo "- ✅ Performance Tests: PASSED" >> $REPORT_FILE
            passed=$((passed + 1))
        fi
    fi
    
    cat >> $REPORT_FILE << EOF

**Overall Results:** $passed/$total tests passed

## Test Details

EOF
    
    # Add details from log files
    for log_file in test-results/*.log performance-results/*.log; do
        if [ -f "$log_file" ]; then
            echo "### $(basename $log_file .log | tr '-' ' ' | sed 's/\b\w/\U&/g')" >> $REPORT_FILE
            echo '```' >> $REPORT_FILE
            tail -20 "$log_file" >> $REPORT_FILE
            echo '```' >> $REPORT_FILE
            echo "" >> $REPORT_FILE
        fi
    done
    
    print_success "Test report generated: $REPORT_FILE"
    
    # Display summary
    echo ""
    echo "📊 TEST SUMMARY"
    echo "==============="
    echo "Tests Passed: $passed/$total"
    echo "Success Rate: $(( passed * 100 / total ))%"
    echo "Report: $REPORT_FILE"
}

# Main execution function
main() {
    echo ""
    echo "🐳 PODMAN TESTING SUITE - RED HAT STATUS CHECKER"
    echo "================================================="
    echo ""
    
    local unit_only=false
    local comprehensive=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit-only)
                unit_only=true
                shift
                ;;
            --comprehensive)
                comprehensive=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --unit-only      Run only unit tests"
                echo "  --comprehensive  Run comprehensive tests with podman-compose"
                echo "  --help          Show this help message"
                echo ""
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Set up trap for cleanup on exit
    trap cleanup EXIT
    
    # Create directories
    create_directories
    
    # Build container
    if ! build_test_container; then
        print_error "Failed to build test container"
        exit 1
    fi
    
    # Run tests based on options
    if [ "$unit_only" = true ]; then
        run_unit_tests
    elif [ "$comprehensive" = true ]; then
        run_comprehensive_tests
    else
        # Run all individual tests
        run_unit_tests
        run_cli_tests
        run_integration_tests
        run_performance_tests
    fi
    
    # Generate report
    generate_report
    
    print_success "Podman testing completed!"
}

# Check if podman is available
if ! command -v podman >/dev/null 2>&1; then
    print_error "Podman is not installed or not in PATH"
    print_status "Please install Podman: https://podman.io/getting-started/installation"
    exit 1
fi

# Run main function with all arguments
main "$@"

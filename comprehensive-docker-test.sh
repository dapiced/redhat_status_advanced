#!/bin/bash

# Comprehensive Docker Test Suite for Red Hat Status Checker
# Tests Docker functionality after permission fixes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Test result tracking
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_status "Running: $test_name"
    
    if eval "$test_command" >/dev/null 2>&1; then
        print_success "✅ $test_name"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        print_error "❌ $test_name"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

skip_test() {
    local test_name="$1"
    local reason="$2"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    print_warning "⏭️  SKIPPED: $test_name ($reason)"
}

# Test Docker installation
test_docker_installation() {
    print_header "Docker Installation Tests"
    
    run_test "Docker command available" "command -v docker"
    run_test "Docker version accessible" "docker --version"
    run_test "Docker service status" "systemctl is-active docker"
}

# Test Docker permissions
test_docker_permissions() {
    print_header "Docker Permission Tests"
    
    # Check if user is in docker group
    if groups | grep -q docker; then
        print_success "✅ User is in docker group"
    else
        print_error "❌ User NOT in docker group"
        return 1
    fi
    
    run_test "Docker daemon accessible" "timeout 10 docker ps"
    run_test "Docker info accessible" "timeout 10 docker info"
}

# Test Docker functionality
test_docker_functionality() {
    print_header "Docker Functionality Tests"
    
    # Check if we can access Docker daemon first
    if ! timeout 5 docker ps >/dev/null 2>&1; then
        skip_test "Docker functionality tests" "Docker daemon not accessible"
        return
    fi
    
    run_test "Hello World container" "timeout 30 docker run --rm hello-world"
    run_test "Container listing" "docker ps -a"
    run_test "Image listing" "docker images"
    
    # Test basic container operations
    if run_test "Pull Alpine image" "timeout 60 docker pull alpine:latest"; then
        run_test "Run Alpine container" "timeout 30 docker run --rm alpine:latest echo 'Container test successful'"
        run_test "Remove Alpine image" "docker rmi alpine:latest"
    fi
}

# Test Red Hat Status Checker Docker infrastructure
test_redhat_status_docker_infrastructure() {
    print_header "Red Hat Status Checker Docker Infrastructure"
    
    # Check required files
    run_test "test-docker.sh exists" "test -f ./test-docker.sh"
    run_test "test-docker.sh executable" "test -x ./test-docker.sh"
    run_test "Dockerfile.test exists" "test -f ./Dockerfile.test"
    run_test "docker-compose.test.yml exists" "test -f ./docker-compose.test.yml"
    
    # Test Docker test script help
    if timeout 5 docker ps >/dev/null 2>&1; then
        run_test "test-docker.sh help" "timeout 15 ./test-docker.sh --help"
    else
        skip_test "test-docker.sh help" "Docker daemon not accessible"
    fi
}

# Test pytest integration
test_pytest_integration() {
    print_header "PyTest Docker Integration"
    
    # Check if virtual environment is available
    if [ -d ".venv" ]; then
        print_status "Virtual environment found"
        
        # Activate venv and run tests
        if source .venv/bin/activate; then
            run_test "Docker permission tests" "python -m pytest tests/test_docker_permissions.py::TestDockerPermissionFix::test_docker_installed -v"
            run_test "Docker infrastructure tests" "python -m pytest tests/test_docker_permissions.py::TestDockerTestingInfrastructure::test_docker_test_script_exists -v"
            
            # Only run Docker-dependent tests if Docker is accessible
            if timeout 5 docker ps >/dev/null 2>&1; then
                run_test "Docker integration tests" "python -m pytest tests/test_docker_integration.py::TestDockerScriptFunctionality::test_script_colored_output -v"
            else
                skip_test "Docker integration tests" "Docker daemon not accessible"
            fi
        fi
    else
        skip_test "PyTest tests" "Virtual environment not found"
    fi
}

# Test Docker Compose functionality
test_docker_compose() {
    print_header "Docker Compose Tests"
    
    if command -v docker-compose >/dev/null 2>&1; then
        run_test "Docker Compose version" "docker-compose --version"
        
        if timeout 5 docker ps >/dev/null 2>&1 && [ -f "docker-compose.test.yml" ]; then
            run_test "Docker Compose config validation" "timeout 15 docker-compose -f docker-compose.test.yml config"
        else
            skip_test "Docker Compose config validation" "Docker not accessible or compose file missing"
        fi
    else
        skip_test "Docker Compose tests" "docker-compose not installed"
    fi
}

# Generate test report
generate_test_report() {
    print_header "Test Results Summary"
    
    echo "📊 Test Statistics:"
    echo "   Total Tests: $TOTAL_TESTS"
    echo "   ✅ Passed: $PASSED_TESTS"
    echo "   ❌ Failed: $FAILED_TESTS"
    echo "   ⏭️  Skipped: $SKIPPED_TESTS"
    echo
    
    local success_rate=0
    if [ $TOTAL_TESTS -gt 0 ]; then
        success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    fi
    
    echo "📈 Success Rate: $success_rate%"
    echo
    
    if [ $FAILED_TESTS -eq 0 ]; then
        print_success "🎉 All tests passed! Docker is fully functional."
        echo
        echo "🚀 You can now run:"
        echo "   ./test-docker.sh --unit-only"
        echo "   ./test-docker.sh --comprehensive"
        echo "   python -m pytest tests/test_docker_integration.py -v"
        echo "   python -m pytest tests/test_docker_containers.py -v"
    else
        print_warning "⚠️  Some tests failed. Check the output above for details."
        echo
        echo "💡 If Docker permission tests failed, try:"
        echo "   newgrp docker"
        echo "   # or log out and log back in"
    fi
    
    # Create test report file
    cat > docker-test-results.md << EOF
# Docker Test Results

## Test Summary
- **Date**: $(date)
- **Total Tests**: $TOTAL_TESTS
- **Passed**: $PASSED_TESTS
- **Failed**: $FAILED_TESTS
- **Skipped**: $SKIPPED_TESTS
- **Success Rate**: $success_rate%

## Test Categories
1. Docker Installation Tests
2. Docker Permission Tests
3. Docker Functionality Tests
4. Red Hat Status Checker Docker Infrastructure
5. PyTest Integration Tests
6. Docker Compose Tests

## Status
$(if [ $FAILED_TESTS -eq 0 ]; then echo "✅ **ALL TESTS PASSED** - Docker is fully functional"; else echo "⚠️ **SOME TESTS FAILED** - Check output for details"; fi)

## Next Steps
$(if [ $FAILED_TESTS -eq 0 ]; then 
    echo "- Run: \`./test-docker.sh --unit-only\`"
    echo "- Run: \`python -m pytest tests/test_docker_integration.py -v\`"
    echo "- Run: \`python -m pytest tests/test_docker_containers.py -v\`"
else
    echo "- Fix Docker permission issues if any"
    echo "- Restart session if needed"
    echo "- Re-run this test script"
fi)
EOF
    
    print_success "📝 Test report saved to: docker-test-results.md"
}

# Main execution
main() {
    print_header "Comprehensive Docker Test Suite for Red Hat Status Checker"
    
    # Change to project directory
    cd "$(dirname "$0")"
    
    # Run all test categories
    test_docker_installation
    test_docker_permissions
    test_docker_functionality
    test_redhat_status_docker_infrastructure
    test_pytest_integration
    test_docker_compose
    
    # Generate final report
    generate_test_report
}

# Run main function
main "$@"

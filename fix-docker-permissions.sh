#!/bin/bash

# Docker Permission Fix Script for Red Hat Status Checker
# Fixes Docker permission issues and validates the setup

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

# Check if user is root
check_not_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root"
        print_warning "Please run as a regular user: ./fix-docker-permissions.sh"
        exit 1
    fi
}

# Check if Docker is installed
check_docker_installed() {
    print_header "Checking Docker Installation"
    
    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker is not installed"
        print_status "Please install Docker first:"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install docker.io"
        echo "  or follow: https://docs.docker.com/engine/install/"
        exit 1
    fi
    
    print_success "Docker is installed: $(docker --version)"
}

# Check if docker group exists
check_docker_group() {
    print_header "Checking Docker Group"
    
    if ! getent group docker >/dev/null 2>&1; then
        print_warning "Docker group does not exist, creating it..."
        sudo groupadd docker
        print_success "Docker group created"
    else
        print_success "Docker group exists"
    fi
}

# Add user to docker group
add_user_to_docker_group() {
    print_header "Adding User to Docker Group"
    
    local current_user=$(whoami)
    
    if groups "$current_user" | grep -q '\bdocker\b'; then
        print_success "User '$current_user' is already in docker group"
    else
        print_status "Adding user '$current_user' to docker group..."
        sudo usermod -aG docker "$current_user"
        print_success "User '$current_user' added to docker group"
    fi
}

# Test Docker access
test_docker_access() {
    print_header "Testing Docker Access"
    
    print_status "Testing Docker daemon access..."
    
    # Try to access Docker daemon
    if timeout 10 docker ps >/dev/null 2>&1; then
        print_success "Docker daemon is accessible"
        return 0
    else
        print_warning "Docker daemon not accessible in current session"
        return 1
    fi
}

# Start Docker service if needed
ensure_docker_service() {
    print_header "Checking Docker Service"
    
    if systemctl is-active --quiet docker; then
        print_success "Docker service is running"
    else
        print_status "Starting Docker service..."
        sudo systemctl start docker
        sudo systemctl enable docker
        print_success "Docker service started and enabled"
    fi
}

# Test Docker functionality
test_docker_functionality() {
    print_header "Testing Docker Functionality"
    
    print_status "Testing Docker with hello-world container..."
    
    if timeout 30 docker run --rm hello-world >/dev/null 2>&1; then
        print_success "Docker is working correctly"
        return 0
    else
        print_warning "Docker test failed - may need session restart"
        return 1
    fi
}

# Generate instructions for session restart
generate_restart_instructions() {
    print_header "Session Restart Instructions"
    
    cat << EOF
${YELLOW}IMPORTANT:${NC} Docker group membership requires a new login session.

${BLUE}Choose one of these options:${NC}

1. ${GREEN}Log out and log back in${NC} (Recommended for desktop)
2. ${GREEN}Start a new terminal session${NC}
3. ${GREEN}Use newgrp command${NC}: newgrp docker
4. ${GREEN}Restart your system${NC} (Most reliable)

${BLUE}After restarting your session, verify with:${NC}
  groups
  docker ps
  ./test-docker.sh --help

${BLUE}Then run the Red Hat Status Checker Docker tests:${NC}
  ./test-docker.sh --unit-only
  python -m pytest tests/test_docker_integration.py -v
  python -m pytest tests/test_docker_containers.py -v
EOF
}

# Create a test script to verify after restart
create_verification_script() {
    print_header "Creating Verification Script"
    
    cat > verify-docker-setup.sh << 'EOF'
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
EOF

    chmod +x verify-docker-setup.sh
    print_success "Created verify-docker-setup.sh script"
}

# Main execution
main() {
    print_header "Docker Permission Fix for Red Hat Status Checker"
    
    check_not_root
    check_docker_installed
    ensure_docker_service
    check_docker_group
    add_user_to_docker_group
    
    # Test current session access
    if test_docker_access && test_docker_functionality; then
        print_success "Docker is fully functional in current session!"
        print_status "You can now run Docker tests immediately"
    else
        print_warning "Docker permissions fixed but session restart required"
        generate_restart_instructions
    fi
    
    create_verification_script
    
    print_header "Summary"
    print_success "Docker permissions have been configured"
    print_status "Run './verify-docker-setup.sh' after restarting your session"
    print_status "Then run Docker tests with './test-docker.sh' or pytest"
}

# Run main function
main "$@"

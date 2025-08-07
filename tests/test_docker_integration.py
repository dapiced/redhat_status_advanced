"""
Integration tests for the Docker test script (test-docker.sh)
Tests the complete test automation workflow for Docker containers
"""

import unittest
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
from tests.container_test_utils import (
    ContainerTestUtils, ContainerTestConfig
)


class TestDockerScriptIntegration(unittest.TestCase):
    """Integration tests for the complete Docker testing workflow"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.project_root = Path(__file__).parent.parent
        cls.test_script = cls.project_root / "test-docker.sh"
        cls.runtime = 'docker'
        
        # Check if Docker is available
        if not ContainerTestUtils.is_docker_available():
            raise unittest.SkipTest("Docker not available on this system")
        
        # Check Docker permissions
        try:
            subprocess.run(['docker', 'ps'], capture_output=True, timeout=10, check=True)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            raise unittest.SkipTest("Docker permission issues - cannot run Docker commands")
    
    def setUp(self):
        """Set up for individual tests"""
        self.original_cwd = os.getcwd()
        os.chdir(self.project_root)
    
    def tearDown(self):
        """Clean up after tests"""
        os.chdir(self.original_cwd)
        
        # Clean up any test containers (only if Docker is accessible)
        try:
            ContainerTestUtils.cleanup_containers(
                self.runtime, ContainerTestConfig.CONTAINER_NAME
            )
        except Exception:
            # Ignore cleanup errors in tests
            pass
    
    def test_script_exists_and_executable(self):
        """Test that the test script exists and is executable"""
        self.assertTrue(self.test_script.exists(), 
                       f"Test script not found: {self.test_script}")
        self.assertTrue(os.access(self.test_script, os.X_OK),
                       "Test script is not executable")
    
    def test_script_help_option(self):
        """Test the help option of the test script"""
        result = subprocess.run(
            ['./test-docker.sh', '--help'], 
            capture_output=True, text=True, timeout=30
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Usage:', result.stdout)
        self.assertIn('--unit-only', result.stdout)
        self.assertIn('--comprehensive', result.stdout)
        self.assertIn('--no-cleanup', result.stdout)
    
    def test_script_invalid_option(self):
        """Test script behavior with invalid options"""
        result = subprocess.run(
            ['./test-docker.sh', '--invalid-option'], 
            capture_output=True, text=True, timeout=30
        )
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Usage:', result.stdout + result.stderr)
    
    def test_docker_prerequisite_check(self):
        """Test the Docker prerequisite checking functionality"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Check for prerequisite validation
        self.assertIn('check_docker_prerequisites', script_content)
        self.assertIn('command -v docker', script_content)
        self.assertIn('docker --version', script_content)
        self.assertIn('docker ps', script_content)
    
    def test_container_build_process(self):
        """Test the container build process through the script"""
        # Check if we can at least validate the build would work
        dockerfile_path = self.project_root / "Dockerfile.test"
        self.assertTrue(dockerfile_path.exists(), "Dockerfile.test not found")
        
        # Read dockerfile to validate structure
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()
        
        # Validate dockerfile has required elements
        self.assertIn('FROM python:', dockerfile_content)
        self.assertIn('WORKDIR /app', dockerfile_content)
        self.assertIn('COPY requirements.txt', dockerfile_content)
        self.assertIn('RUN pip install', dockerfile_content)
    
    def test_script_directory_creation(self):
        """Test that the script creates necessary directories"""
        # Remove test directories if they exist
        test_dirs = ['test-results', 'coverage-reports', 'performance-results']
        for dir_name in test_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path)
        
        # The script creates directories as part of normal operation
        # We test this indirectly by checking the script content
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        self.assertIn('create_directories', script_content)
        self.assertIn('mkdir -p', script_content)
    
    def test_docker_compose_integration(self):
        """Test Docker Compose integration"""
        docker_compose_path = self.project_root / "docker-compose.test.yml"
        
        if docker_compose_path.exists():
            with open(docker_compose_path, 'r') as f:
                compose_content = f.read()
            
            self.assertIn('version:', compose_content)
            self.assertIn('services:', compose_content)
            
            # Check script integration
            with open(self.test_script, 'r') as f:
                script_content = f.read()
            
            self.assertIn('docker-compose', script_content)
            self.assertIn('docker-compose.test.yml', script_content)
    
    def test_required_files_present(self):
        """Test that all required files for container testing are present"""
        required_files = [
            'Dockerfile.test',
            'test-docker.sh',
            'docker-compose.test.yml',
            'requirements.txt',
            'redhat_status.py',
            'config.json'
        ]
        
        for filename in required_files:
            file_path = self.project_root / filename
            self.assertTrue(file_path.exists(), f"Required file missing: {filename}")
    
    def test_script_validation_functions(self):
        """Test the validation functions in the script"""
        # Read the script content to validate function presence
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Check for essential functions
        required_functions = [
            'check_docker_prerequisites()',
            'build_test_container()',
            'run_unit_tests()',
            'run_flag_tests()',
            'run_example_tests()',
            'run_integration_tests()',
            'run_performance_tests()',
            'run_comprehensive_tests()',
            'cleanup()',
            'generate_report()',
            'create_directories()'
        ]
        
        for func in required_functions:
            self.assertIn(func, script_content, f"Function missing: {func}")
    
    def test_script_error_handling(self):
        """Test error handling in the script"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Check for proper error handling patterns
        self.assertIn('set -e', script_content, "Script should use 'set -e'")
        self.assertIn('trap cleanup EXIT', script_content, "Script should have cleanup trap")
        
        # Check for Docker-specific error handling
        self.assertIn('Docker permission denied', script_content)
        self.assertIn('sudo usermod -aG docker', script_content)
    
    def test_output_directory_structure(self):
        """Test that the script creates proper output directory structure"""
        # The script should create these directories
        expected_dirs = [
            'test-results',
            'coverage-reports', 
            'performance-results'
        ]
        
        # Check if the script content references these directories
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        for dir_name in expected_dirs:
            self.assertIn(dir_name, script_content, 
                         f"Script should reference {dir_name} directory")
    
    def test_docker_runtime_detection(self):
        """Test that the script properly detects Docker runtime"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Script should check for Docker availability
        self.assertIn('docker', script_content.lower())
        self.assertIn('command -v docker', script_content)
        
        # Should also check permissions
        self.assertIn('docker ps', script_content)
    
    def test_permission_error_handling(self):
        """Test that the script handles Docker permission issues gracefully"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Check for permission-related error messages
        permission_patterns = [
            'permission denied',
            'Docker permission denied',
            'sudo usermod -aG docker',
            'newgrp docker'
        ]
        
        for pattern in permission_patterns:
            self.assertIn(pattern, script_content, 
                         f"Permission handling pattern missing: {pattern}")


class TestDockerScriptFunctionality(unittest.TestCase):
    """Test individual functionality of the Docker script"""
    
    def setUp(self):
        """Set up for functionality tests"""
        self.project_root = Path(__file__).parent.parent
        self.test_script = self.project_root / "test-docker.sh"
        
        if not ContainerTestUtils.is_docker_available():
            self.skipTest("Docker not available")
    
    def test_script_colored_output(self):
        """Test that the script uses colored output"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Check for color definitions
        color_patterns = ['RED=', 'GREEN=', 'YELLOW=', 'BLUE=', 'NC=']
        for pattern in color_patterns:
            self.assertIn(pattern, script_content, f"Color definition missing: {pattern}")
        
        # Check for color usage in print functions
        print_functions = ['print_status', 'print_success', 'print_warning', 'print_error']
        for func in print_functions:
            self.assertIn(func, script_content, f"Print function missing: {func}")
    
    def test_script_timeout_handling(self):
        """Test that the script has appropriate timeout handling"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Look for timeout patterns in Docker commands
        # The script should have reasonable timeouts for long-running operations
        self.assertIn('timeout', script_content.lower())
        
        # Check for specific timeout usage in cleanup
        self.assertIn('timeout 30 docker stop', script_content)
    
    def test_script_logging_capabilities(self):
        """Test that the script has logging capabilities"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Check for log file redirection
        log_patterns = ['.log', '2>&1', '> ', '>>']
        found_patterns = 0
        for pattern in log_patterns:
            if pattern in script_content:
                found_patterns += 1
        
        self.assertGreater(found_patterns, 0, "Script should have some logging patterns")
        
        # Check for specific build log handling
        self.assertIn('build-docker.log', script_content)
    
    def test_script_report_generation(self):
        """Test report generation functionality"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Check for report generation elements
        self.assertIn('generate_report', script_content)
        self.assertIn('.md', script_content, "Script should generate markdown reports")
        self.assertIn('docker-test-report.md', script_content)
    
    def test_script_cleanup_safety(self):
        """Test that cleanup is safe and permission-aware"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Check for safe cleanup patterns
        self.assertIn('docker ps', script_content)  # Check before cleanup
        self.assertIn('Skipping Docker cleanup due to permission issues', script_content)
        
        # Check for proper container filtering
        self.assertIn('ancestor=redhat-status-test', script_content)
    
    def test_script_comprehensive_testing_support(self):
        """Test that the script supports comprehensive testing modes"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Check for comprehensive test mode
        self.assertIn('--comprehensive', script_content)
        self.assertIn('RUN_COMPREHENSIVE', script_content)
        
        # Check for unit-only mode
        self.assertIn('--unit-only', script_content)
        self.assertIn('RUN_UNIT', script_content)
    
    def test_script_build_error_handling(self):
        """Test that the script handles build errors properly"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Check for build-specific error handling
        self.assertIn('Failed to build test container', script_content)
        self.assertIn('Dockerfile.test not found', script_content)
        self.assertIn('Build log output:', script_content)


class TestDockerScriptPermissionHandling(unittest.TestCase):
    """Test Docker permission handling specifically"""
    
    def setUp(self):
        """Set up for permission tests"""
        self.project_root = Path(__file__).parent.parent
        self.test_script = self.project_root / "test-docker.sh"
    
    def test_permission_detection_logic(self):
        """Test the logic for detecting Docker permission issues"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Should check Docker accessibility
        self.assertIn('docker ps >/dev/null 2>&1', script_content)
        
        # Should provide clear error messages
        self.assertIn('Docker permission denied', script_content)
        
        # Should provide solution instructions
        self.assertIn('sudo usermod -aG docker', script_content)
        self.assertIn('newgrp docker', script_content)
    
    def test_graceful_permission_degradation(self):
        """Test that the script degrades gracefully when permissions are missing"""
        # This test simulates what happens when Docker permissions are not available
        result = subprocess.run(
            ['timeout', '10', './test-docker.sh', '--unit-only'],
            capture_output=True, text=True, timeout=15
        )
        
        # The script should exit with an error code but provide helpful information
        self.assertNotEqual(result.returncode, 0, 
                           "Script should exit with error when Docker is not accessible")
        
        output = result.stdout + result.stderr
        
        # Should contain helpful guidance
        permission_indicators = [
            'Docker permission denied',
            'sudo usermod -aG docker',
            'Current user needs Docker access'
        ]
        
        found_indicators = sum(1 for indicator in permission_indicators if indicator in output)
        self.assertGreater(found_indicators, 0, 
                          "Script should provide helpful permission guidance")
    
    def test_alternative_execution_suggestions(self):
        """Test that the script suggests alternative execution methods"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Should suggest running with sudo as alternative
        self.assertIn('sudo ./test-docker.sh', script_content)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)

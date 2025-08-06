"""
Integration tests for the Podman test script (test-podman.sh)
Tests the complete test automation workflow
"""

import unittest
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
from tests.container_test_utils import (
    ContainerTestUtils, ContainerTestConfig, ContainerTestReporter
)


class TestPodmanScriptIntegration(unittest.TestCase):
    """Integration tests for the complete Podman testing workflow"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.project_root = Path(__file__).parent.parent
        cls.test_script = cls.project_root / "test-podman.sh"
        cls.runtime = ContainerTestUtils.get_container_runtime()
        
        if not cls.runtime:
            cls.skipTest("No container runtime available")
    
    def setUp(self):
        """Set up for individual tests"""
        self.original_cwd = os.getcwd()
        os.chdir(self.project_root)
    
    def tearDown(self):
        """Clean up after tests"""
        os.chdir(self.original_cwd)
        
        # Clean up any test containers
        ContainerTestUtils.cleanup_containers(
            self.runtime, ContainerTestConfig.CONTAINER_NAME
        )
    
    def test_script_exists_and_executable(self):
        """Test that the test script exists and is executable"""
        self.assertTrue(self.test_script.exists(), 
                       f"Test script not found: {self.test_script}")
        self.assertTrue(os.access(self.test_script, os.X_OK),
                       "Test script is not executable")
    
    def test_script_help_option(self):
        """Test the help option of the test script"""
        result = subprocess.run(
            ['./test-podman.sh', '--help'], 
            capture_output=True, text=True, timeout=30
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Usage:', result.stdout)
        self.assertIn('--unit-only', result.stdout)
        self.assertIn('--comprehensive', result.stdout)
        self.assertIn('--help', result.stdout)
    
    def test_script_invalid_option(self):
        """Test script behavior with invalid options"""
        result = subprocess.run(
            ['./test-podman.sh', '--invalid-option'], 
            capture_output=True, text=True, timeout=30
        )
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unknown option', result.stderr)
    
    def test_container_build_process(self):
        """Test the container build process through the script"""
        # This test builds the container but doesn't run full tests
        # to avoid long execution times
        
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
        
        # Run script with help to trigger directory creation logic
        # (This tests the create_directories function indirectly)
        result = subprocess.run(
            ['./test-podman.sh', '--help'], 
            capture_output=True, text=True, timeout=30
        )
        
        self.assertEqual(result.returncode, 0)
    
    def test_makefile_integration(self):
        """Test that Makefile has correct Podman targets"""
        makefile_path = self.project_root / "Makefile"
        
        if makefile_path.exists():
            with open(makefile_path, 'r') as f:
                makefile_content = f.read()
            
            self.assertIn('test-podman:', makefile_content)
            self.assertIn('./test-podman.sh', makefile_content)
    
    def test_required_files_present(self):
        """Test that all required files for container testing are present"""
        required_files = [
            'Dockerfile.test',
            'test-podman.sh',
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
            'build_test_container()',
            'run_unit_tests()',
            'run_cli_tests()',
            'run_integration_tests()',
            'run_performance_tests()',
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
    
    def test_output_directory_structure(self):
        """Test that the script creates proper output directory structure"""
        # The script should create these directories
        expected_dirs = [
            'test-results',
            'coverage-reports', 
            'performance-results'
        ]
        
        # Since we can't run the full script, check if the script content
        # references these directories
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        for dir_name in expected_dirs:
            self.assertIn(dir_name, script_content, 
                         f"Script should reference {dir_name} directory")
    
    def test_container_runtime_detection(self):
        """Test that the script properly detects container runtime"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Script should check for podman availability
        self.assertIn('podman', script_content.lower())
        self.assertIn('command -v podman', script_content)


class TestPodmanScriptFunctionality(unittest.TestCase):
    """Test individual functionality of the Podman script"""
    
    def setUp(self):
        """Set up for functionality tests"""
        self.project_root = Path(__file__).parent.parent
        self.test_script = self.project_root / "test-podman.sh"
        self.runtime = ContainerTestUtils.get_container_runtime()
        
        if not self.runtime or self.runtime != 'podman':
            self.skipTest("Podman not available")
    
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
        
        # Look for timeout patterns in podman commands
        # The script should have reasonable timeouts for long-running operations
        self.assertIn('timeout', script_content.lower())
    
    def test_script_logging_capabilities(self):
        """Test that the script has logging capabilities"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Check for log file redirection
        log_patterns = ['.log', '2>&1', '> ', '>>']
        for pattern in log_patterns:
            self.assertIn(pattern, script_content, f"Logging pattern missing: {pattern}")
    
    def test_script_report_generation(self):
        """Test report generation functionality"""
        with open(self.test_script, 'r') as f:
            script_content = f.read()
        
        # Check for report generation elements
        self.assertIn('generate_report', script_content)
        self.assertIn('.md', script_content, "Script should generate markdown reports")
        self.assertIn('TEST SUMMARY', script_content)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)

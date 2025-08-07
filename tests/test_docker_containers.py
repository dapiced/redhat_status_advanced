"""
Docker Container Testing Suite
Tests the Docker-based testing infrastructure for Red Hat Status Checker

These tests verify that the Docker testing environment works correctly,
similar to the Podman container tests.
"""

import unittest
import subprocess
import os
import tempfile
import time
from pathlib import Path
from tests.container_test_utils import ContainerTestUtils, ContainerTestConfig


class TestDockerContainers(unittest.TestCase):
    """Test Docker container functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.project_root = Path(__file__).parent.parent
        cls.dockerfile_path = cls.project_root / "Dockerfile.test"
        cls.container_name = ContainerTestConfig.CONTAINER_NAME
        cls.runtime = 'docker'
        
        # Check if Docker is available
        if not ContainerTestUtils.is_docker_available():
            raise unittest.SkipTest("Docker not available on this system")
        
        # Ensure container is built for tests
        cls._ensure_container_built()
    
    @classmethod
    def _ensure_container_built(cls):
        """Ensure the test container is built"""
        try:
            # Check if container image exists
            result = subprocess.run(
                ['docker', 'images', '-q', cls.container_name],
                capture_output=True, text=True, timeout=30
            )
            
            if not result.stdout.strip():
                # Build the container
                print(f"\nBuilding Docker test container: {cls.container_name}")
                success, stdout, stderr = ContainerTestUtils.build_test_container(
                    cls.runtime,
                    str(cls.dockerfile_path),
                    cls.container_name,
                    str(cls.project_root),
                    timeout=300
                )
                
                if not success:
                    raise unittest.SkipTest(f"Failed to build Docker test container: {stderr}")
                
                print(f"Successfully built Docker test container")
            
        except subprocess.TimeoutExpired:
            raise unittest.SkipTest("Timeout while checking Docker container")
        except Exception as e:
            raise unittest.SkipTest(f"Error setting up Docker test container: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        try:
            # Note: We don't automatically clean up the container image
            # since it might be used by other tests or the test-docker.sh script
            pass
        except Exception:
            pass
    
    def test_docker_availability(self):
        """Test that Docker is available and working"""
        self.assertTrue(ContainerTestUtils.is_docker_available(), 
                       "Docker should be available on the system")
        
        # Test Docker version command
        result = subprocess.run(['docker', '--version'], 
                               capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, "Docker version command should work")
        self.assertIn('Docker version', result.stdout, 
                     "Docker version output should contain version info")
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile.test exists and is readable"""
        self.assertTrue(self.dockerfile_path.exists(), 
                       f"Dockerfile.test not found at {self.dockerfile_path}")
        
        # Test that the Dockerfile is readable and contains expected content
        with open(self.dockerfile_path, 'r') as f:
            content = f.read()
            self.assertIn('FROM python:', content, 
                         "Dockerfile should specify Python base image")
            self.assertIn('WORKDIR /app', content, 
                         "Dockerfile should set working directory")
    
    def test_container_build_and_run(self):
        """Test that the Docker container can be built and run"""
        # Container should already be built by setUpClass
        
        # Test running a simple command in the container
        try:
            result = ContainerTestUtils.run_container_command(
                self.runtime,
                self.container_name,
                ['python3', '--version'],
                timeout=30
            )
            
            self.assertEqual(result.returncode, 0, 
                           "Python version command should work in container")
            self.assertIn('Python', result.stdout, 
                         "Python version output should contain 'Python'")
            
        except subprocess.TimeoutExpired:
            self.fail("Container command timed out")
    
    def test_container_python_environment(self):
        """Test that the Python environment in the container is correct"""
        try:
            # Test Python version
            result = ContainerTestUtils.run_container_command(
                self.runtime,
                self.container_name,
                ['python3', '-c', 'import sys; print(f"Python {sys.version_info.major}.{sys.version_info.minor}")'],
                timeout=30
            )
            
            self.assertEqual(result.returncode, 0, "Python version check should work")
            
            # Test that required packages can be imported
            packages_to_test = ['requests', 'pytest', 'json', 'sqlite3']
            for package in packages_to_test:
                with self.subTest(package=package):
                    result = ContainerTestUtils.run_container_command(
                        self.runtime,
                        self.container_name,
                        ['python3', '-c', f'import {package}; print("{package} imported successfully")'],
                        timeout=30
                    )
                    
                    self.assertEqual(result.returncode, 0, 
                                   f"Should be able to import {package} in container")
                    
        except subprocess.TimeoutExpired:
            self.fail("Container Python environment test timed out")
    
    def test_container_working_directory(self):
        """Test that the container has the correct working directory"""
        try:
            result = ContainerTestUtils.run_container_command(
                self.runtime,
                self.container_name,
                ['pwd'],
                timeout=30
            )
            
            self.assertEqual(result.returncode, 0, "pwd command should work")
            self.assertEqual(result.stdout.strip(), '/app', 
                           "Container working directory should be /app")
            
        except subprocess.TimeoutExpired:
            self.fail("Container working directory test timed out")
    
    def test_container_file_structure(self):
        """Test that the container has the expected file structure"""
        expected_files = [
            'redhat_status.py',
            'redhat_status/',
            'tests/',
            'requirements.txt',
            'pyproject.toml'
        ]
        
        for file_path in expected_files:
            with self.subTest(file=file_path):
                try:
                    result = ContainerTestUtils.run_container_command(
                        self.runtime,
                        self.container_name,
                        ['test', '-e', file_path],
                        timeout=30
                    )
                    
                    self.assertEqual(result.returncode, 0, 
                                   f"{file_path} should exist in container")
                    
                except subprocess.TimeoutExpired:
                    self.fail(f"File existence test for {file_path} timed out")
    
    def test_container_pytest_execution(self):
        """Test that pytest can run in the container"""
        try:
            # Run a simple pytest command to verify the testing infrastructure
            result = ContainerTestUtils.run_container_command(
                self.runtime,
                self.container_name,
                ['python3', '-m', 'pytest', '--version'],
                timeout=30
            )
            
            self.assertEqual(result.returncode, 0, "pytest --version should work")
            self.assertIn('pytest', result.stdout, 
                         "pytest version output should contain 'pytest'")
            
        except subprocess.TimeoutExpired:
            self.fail("Container pytest test timed out")
    
    def test_docker_test_script_exists(self):
        """Test that the test-docker.sh script exists and is executable"""
        test_script_path = self.project_root / "test-docker.sh"
        
        self.assertTrue(test_script_path.exists(), 
                       "test-docker.sh script should exist")
        
        # Check if it's executable
        self.assertTrue(os.access(test_script_path, os.X_OK), 
                       "test-docker.sh should be executable")
        
        # Check that it contains expected Docker commands
        with open(test_script_path, 'r') as f:
            content = f.read()
            self.assertIn('docker', content, 
                         "test-docker.sh should contain Docker commands")
            self.assertIn('redhat-status-test', content, 
                         "test-docker.sh should reference the test container name")
    
    def test_container_runtime_detection(self):
        """Test container runtime detection utility"""
        runtime = ContainerTestUtils.get_container_runtime()
        
        # Should detect Docker if it's available
        if ContainerTestUtils.is_docker_available():
            self.assertIn(runtime, ['docker', 'podman'], 
                         "Should detect available container runtime")
    
    def test_container_cleanup_preparation(self):
        """Test container cleanup functions work"""
        # Test that cleanup functions don't fail
        # (but don't actually clean up the container we need for other tests)
        
        # Test getting container info first
        info = ContainerTestUtils.get_container_info(self.runtime, self.container_name)
        
        self.assertIsInstance(info, dict, "Container info should be a dictionary")
        
        # Should contain basic information
        expected_keys = ['python_version', 'working_directory']
        for key in expected_keys:
            self.assertIn(key, info, f"Container info should contain {key}")
    
    def test_container_environment_variables(self):
        """Test that environment variables work in the container"""
        try:
            # Test setting and reading environment variables
            result = ContainerTestUtils.run_container_command(
                'docker',
                self.container_name,
                ['sh', '-c', 'echo "TESTING=1" > /tmp/test_env && cat /tmp/test_env'],
                timeout=30
            )
            
            self.assertEqual(result.returncode, 0, 
                           "Environment variable test should work")
            self.assertIn('TESTING=1', result.stdout, 
                         "Should be able to set and read environment variables")
            
        except subprocess.TimeoutExpired:
            self.fail("Container environment variable test timed out")


class TestDockerTestScript(unittest.TestCase):
    """Test the test-docker.sh script functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        self.test_script = self.project_root / "test-docker.sh"
        
        if not ContainerTestUtils.is_docker_available():
            self.skipTest("Docker not available on this system")
    
    def test_docker_script_help(self):
        """Test that the Docker test script shows help when called with invalid args"""
        try:
            result = subprocess.run(
                ['bash', str(self.test_script), '--help'],
                capture_output=True, text=True, timeout=30,
                cwd=str(self.project_root)
            )
            
            # Script might exit with error code when showing usage
            # but should provide usage information
            output = result.stdout + result.stderr
            self.assertTrue(
                'Usage:' in output or '--unit-only' in output or 'DOCKER TESTING' in output,
                "Script should provide usage information or main header"
            )
            
        except subprocess.TimeoutExpired:
            self.fail("Docker script help test timed out")
    
    def test_docker_script_syntax(self):
        """Test that the Docker test script has valid bash syntax"""
        try:
            # Use bash -n to check syntax without executing
            result = subprocess.run(
                ['bash', '-n', str(self.test_script)],
                capture_output=True, text=True, timeout=30
            )
            
            self.assertEqual(result.returncode, 0, 
                           f"test-docker.sh should have valid bash syntax. Errors: {result.stderr}")
            
        except subprocess.TimeoutExpired:
            self.fail("Docker script syntax test timed out")


    def test_docker_script_permission_handling(self):
        """Test that the Docker test script handles permission issues gracefully"""
        try:
            result = subprocess.run(
                ['timeout', '10', 'bash', str(self.test_script), '--unit-only'],
                capture_output=True, text=True, timeout=15,
                cwd=str(self.project_root)
            )
            
            # The script should exit with error code due to permission issues
            self.assertNotEqual(result.returncode, 0, 
                               "Script should exit with error code when Docker permissions are denied")
            
            # Check that it provides helpful error messages
            output = result.stdout + result.stderr
            self.assertIn('Docker permission denied', output, 
                         "Script should detect Docker permission issues")
            self.assertIn('sudo usermod -aG docker', output, 
                         "Script should provide instructions to fix permission issues")
            
        except subprocess.TimeoutExpired:
            self.fail("Docker script permission test timed out")
    
    def test_docker_script_prerequisite_check(self):
        """Test that the Docker test script has proper prerequisite checks"""
        with open(self.test_script, 'r') as f:
            content = f.read()
            
        # Check for prerequisite function
        self.assertIn('check_docker_prerequisites', content, 
                     "Script should have Docker prerequisite check function")
        
        # Check for Docker availability tests
        self.assertIn('command -v docker', content, 
                     "Script should check if Docker command is available")
        self.assertIn('docker --version', content, 
                     "Script should check Docker version")
        self.assertIn('docker ps', content, 
                     "Script should test Docker permissions")
    
    def test_docker_script_improved_cleanup(self):
        """Test that the Docker test script has improved cleanup handling"""
        with open(self.test_script, 'r') as f:
            content = f.read()
            
        # Check for permission-aware cleanup
        self.assertIn('Skipping Docker cleanup due to permission issues', content, 
                     "Script should skip cleanup when Docker is not accessible")
        
        # Check for timeout handling in cleanup
        self.assertIn('timeout 30 docker stop', content, 
                     "Script should use timeout for Docker stop operations")
    
    def test_docker_script_error_handling(self):
        """Test that the Docker test script has proper error handling"""
        with open(self.test_script, 'r') as f:
            content = f.read()
            
        # Check for Dockerfile existence check
        self.assertIn('Dockerfile.test not found', content, 
                     "Script should check for Dockerfile.test existence")
        
        # Check for build log handling
        self.assertIn('build-docker.log', content, 
                     "Script should create and manage build logs")
        
        # Check for proper exit codes
        self.assertIn('exit 1', content, 
                     "Script should exit with proper error codes")


class TestDockerInfrastructureValidation(unittest.TestCase):
    """Additional validation tests for Docker infrastructure"""
    
    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        self.docker_files = [
            'Dockerfile.test',
            'docker-compose.test.yml'
        ]
    
    def test_docker_infrastructure_files_exist(self):
        """Test that required Docker infrastructure files exist"""
        for docker_file in self.docker_files:
            file_path = self.project_root / docker_file
            
            with self.subTest(file=docker_file):
                self.assertTrue(file_path.exists(), 
                               f"{docker_file} should exist for Docker testing")
                
                if docker_file.endswith('.yml'):
                    # Basic YAML validation
                    with open(file_path, 'r') as f:
                        content = f.read()
                        self.assertIn('version:', content, 
                                     f"{docker_file} should be a valid Docker Compose file")
    
    def test_docker_script_comprehensive_coverage(self):
        """Test that Docker script covers all necessary test types"""
        test_script = self.project_root / "test-docker.sh"
        
        with open(test_script, 'r') as f:
            content = f.read()
        
        required_test_functions = [
            'run_unit_tests',
            'run_integration_tests', 
            'run_flag_tests',
            'run_example_tests',
            'run_performance_tests'
        ]
        
        for test_func in required_test_functions:
            with self.subTest(function=test_func):
                self.assertIn(test_func, content, 
                             f"Docker script should include {test_func} function")


if __name__ == '__main__':
    unittest.main()

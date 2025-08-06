"""
Unit tests for Podman container functionality
Tests container deployment, module imports, and core functionality within containers
"""

import unittest
import subprocess
import os
import tempfile
import json
from pathlib import Path


class TestPodmanContainerization(unittest.TestCase):
    """Test suite for Podman container deployment and functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment and check if Podman is available"""
        cls.project_root = Path(__file__).parent.parent
        cls.container_name = "redhat-status-test"
        cls.dockerfile_path = cls.project_root / "Dockerfile.test"
        
        # Check if Podman is available
        try:
            result = subprocess.run(['podman', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            cls.podman_available = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            cls.podman_available = False
    
    def setUp(self):
        """Set up for individual tests"""
        if not self.podman_available:
            self.skipTest("Podman is not available")
    
    def test_podman_availability(self):
        """Test that Podman is installed and accessible"""
        result = subprocess.run(['podman', '--version'], 
                              capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('podman version', result.stdout.lower())
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile.test exists and is readable"""
        self.assertTrue(self.dockerfile_path.exists(), 
                       f"Dockerfile.test not found at {self.dockerfile_path}")
        
        with open(self.dockerfile_path, 'r') as f:
            content = f.read()
            self.assertIn('FROM python:', content)
            self.assertIn('WORKDIR /app', content)
    
    def test_container_build(self):
        """Test that the container builds successfully"""
        os.chdir(self.project_root)
        
        # Build container
        build_cmd = [
            'podman', 'build', 
            '-f', 'Dockerfile.test',
            '-t', self.container_name,
            '.'
        ]
        
        result = subprocess.run(build_cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"Build stdout: {result.stdout}")
            print(f"Build stderr: {result.stderr}")
        
        self.assertEqual(result.returncode, 0, 
                        f"Container build failed: {result.stderr}")
    
    def test_container_python_version(self):
        """Test that the container has the correct Python version"""
        os.chdir(self.project_root)
        
        cmd = ['podman', 'run', '--rm', self.container_name, 'python3', '--version']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Python 3.11', result.stdout)
    
    def test_container_module_import(self):
        """Test that Python modules can be imported in the container"""
        os.chdir(self.project_root)
        
        # Test basic module import
        cmd = [
            'podman', 'run', '--rm', self.container_name,
            'python3', '-c', 'import redhat_status; print("SUCCESS: Module imported")'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('SUCCESS: Module imported', result.stdout)
    
    def test_container_basic_functionality(self):
        """Test basic Red Hat status functionality in container"""
        os.chdir(self.project_root)
        
        cmd = [
            'podman', 'run', '--rm', self.container_name,
            'python3', 'redhat_status.py', 'quick', '--quiet'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Global Availability:', result.stdout)
        self.assertIn('Status:', result.stdout)
    
    def test_container_version_command(self):
        """Test version command in container"""
        os.chdir(self.project_root)
        
        cmd = [
            'podman', 'run', '--rm', self.container_name,
            'python3', 'redhat_status.py', '--version'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Red Hat Status Checker v3.1.0', result.stdout)
        self.assertIn('Modular Edition', result.stdout)
    
    def test_container_dependency_availability(self):
        """Test that required dependencies are available in container"""
        os.chdir(self.project_root)
        
        # Test requests library
        cmd = [
            'podman', 'run', '--rm', self.container_name,
            'python3', '-c', 'import requests; print(f"Requests version: {requests.__version__}")'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Requests version:', result.stdout)
        
        # Test pytest
        cmd = [
            'podman', 'run', '--rm', self.container_name,
            'python3', '-c', 'import pytest; print(f"Pytest version: {pytest.__version__}")'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Pytest version:', result.stdout)
    
    def test_container_environment_variables(self):
        """Test that environment variables are set correctly in container"""
        os.chdir(self.project_root)
        
        cmd = [
            'podman', 'run', '--rm', self.container_name,
            'python3', '-c', 
            'import os; print(f"PYTHONPATH={os.environ.get(\"PYTHONPATH\", \"NOT_SET\")}")'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0)
        self.assertIn('PYTHONPATH=/app', result.stdout)
    
    def test_container_working_directory(self):
        """Test that working directory is set correctly in container"""
        os.chdir(self.project_root)
        
        cmd = [
            'podman', 'run', '--rm', self.container_name,
            'pwd'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), '/app')
    
    def test_container_file_structure(self):
        """Test that application files are present in container"""
        os.chdir(self.project_root)
        
        # Check for main application file
        cmd = [
            'podman', 'run', '--rm', self.container_name,
            'ls', '-la', 'redhat_status.py'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0)
        self.assertIn('redhat_status.py', result.stdout)
        
        # Check for module directory
        cmd = [
            'podman', 'run', '--rm', self.container_name,
            'ls', '-la', 'redhat_status/'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0)
        self.assertIn('main.py', result.stdout)
    
    def test_container_simple_mode(self):
        """Test simple mode functionality in container"""
        os.chdir(self.project_root)
        
        cmd = [
            'podman', 'run', '--rm', self.container_name,
            'python3', 'redhat_status.py', 'simple', '--quiet'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('RED HAT MAIN SERVICES', result.stdout)
        self.assertIn('Availability:', result.stdout)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test containers"""
        if cls.podman_available:
            try:
                # Remove test container if it exists
                subprocess.run(['podman', 'rmi', cls.container_name], 
                             capture_output=True, timeout=30)
            except subprocess.TimeoutExpired:
                pass


class TestPodmanTestScript(unittest.TestCase):
    """Test the Podman test script functionality"""
    
    def setUp(self):
        """Set up for test script tests"""
        self.project_root = Path(__file__).parent.parent
        self.test_script = self.project_root / "test-podman.sh"
    
    def test_podman_script_exists(self):
        """Test that the Podman test script exists and is executable"""
        self.assertTrue(self.test_script.exists(), 
                       f"test-podman.sh not found at {self.test_script}")
        
        # Check if script is executable
        self.assertTrue(os.access(self.test_script, os.X_OK),
                       "test-podman.sh is not executable")
    
    def test_podman_script_help(self):
        """Test that the Podman test script shows help"""
        os.chdir(self.project_root)
        
        result = subprocess.run(['./test-podman.sh', '--help'], 
                              capture_output=True, text=True, timeout=30)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Usage:', result.stdout)
        self.assertIn('--unit-only', result.stdout)
        self.assertIn('--comprehensive', result.stdout)
    
    def test_podman_script_structure(self):
        """Test that the Podman test script has correct structure"""
        with open(self.test_script, 'r') as f:
            content = f.read()
        
        # Check for essential functions
        self.assertIn('build_test_container()', content)
        self.assertIn('run_unit_tests()', content)
        self.assertIn('run_cli_tests()', content)
        self.assertIn('run_integration_tests()', content)
        self.assertIn('cleanup()', content)
        
        # Check for proper bash shebang
        self.assertTrue(content.startswith('#!/bin/bash'))


if __name__ == '__main__':
    unittest.main()

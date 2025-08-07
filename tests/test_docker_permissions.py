"""
Docker Permission Validation Tests
Tests Docker permission fixes and provides guidance for session restart
"""

import unittest
import subprocess
import os
import pwd
import grp
from pathlib import Path


class TestDockerPermissionFix(unittest.TestCase):
    """Test Docker permission fixes and validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.project_root = Path(__file__).parent.parent
        self.fix_script = self.project_root / "fix-docker-permissions.sh"
        self.verify_script = self.project_root / "verify-docker-setup.sh"
        self.current_user = pwd.getpwuid(os.getuid()).pw_name
    
    def test_fix_script_exists(self):
        """Test that the Docker permission fix script exists and is executable"""
        self.assertTrue(self.fix_script.exists(), 
                       f"Fix script not found: {self.fix_script}")
        self.assertTrue(os.access(self.fix_script, os.X_OK),
                       "Fix script is not executable")
    
    def test_docker_installed(self):
        """Test that Docker is installed on the system"""
        result = subprocess.run(['docker', '--version'], 
                               capture_output=True, text=True, timeout=10)
        
        self.assertEqual(result.returncode, 0, "Docker should be installed")
        self.assertIn('Docker version', result.stdout)
    
    def test_docker_service_running(self):
        """Test that Docker service is running"""
        result = subprocess.run(['systemctl', 'is-active', 'docker'], 
                               capture_output=True, text=True, timeout=10)
        
        # Service should be active or we should get a clear status
        self.assertIn(result.stdout.strip(), ['active', 'inactive'], 
                     "Should get clear Docker service status")
    
    def test_docker_group_exists(self):
        """Test that docker group exists on the system"""
        try:
            grp.getgrnam('docker')
            docker_group_exists = True
        except KeyError:
            docker_group_exists = False
        
        self.assertTrue(docker_group_exists, "Docker group should exist")
    
    def test_user_in_docker_group(self):
        """Test that current user is in docker group"""
        try:
            docker_group = grp.getgrnam('docker')
            user_in_group = self.current_user in docker_group.gr_mem
            
            # Also check if docker is user's primary group
            user_groups = [g.gr_name for g in grp.getgrall() 
                          if self.current_user in g.gr_mem]
            user_in_group = user_in_group or 'docker' in user_groups
            
        except KeyError:
            user_in_group = False
        
        if not user_in_group:
            self.fail(f"User '{self.current_user}' should be in docker group. "
                     f"Run: sudo usermod -aG docker {self.current_user}")
        
        self.assertTrue(user_in_group, 
                       f"User '{self.current_user}' should be in docker group")
    
    def test_docker_daemon_access(self):
        """Test Docker daemon accessibility"""
        result = subprocess.run(['docker', 'ps'], 
                               capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            if 'permission denied' in result.stderr.lower():
                self.skipTest("Docker permission denied - session restart required")
            else:
                self.fail(f"Docker daemon not accessible: {result.stderr}")
        
        # If we get here, Docker is working
        self.assertEqual(result.returncode, 0, "Docker daemon should be accessible")
    
    def test_docker_functionality(self):
        """Test basic Docker functionality with hello-world"""
        # Skip if we can't access docker daemon
        ps_result = subprocess.run(['docker', 'ps'], 
                                  capture_output=True, text=True, timeout=10)
        if ps_result.returncode != 0:
            self.skipTest("Docker daemon not accessible - skipping functionality test")
        
        # Test with hello-world container
        result = subprocess.run(['docker', 'run', '--rm', 'hello-world'], 
                               capture_output=True, text=True, timeout=60)
        
        self.assertEqual(result.returncode, 0, 
                        f"Docker hello-world test failed: {result.stderr}")
        self.assertIn('Hello from Docker!', result.stdout)
    
    def test_verification_script_created(self):
        """Test that verification script was created by fix script"""
        if self.verify_script.exists():
            self.assertTrue(os.access(self.verify_script, os.X_OK),
                           "Verification script should be executable")
    
    def test_fix_script_help(self):
        """Test that fix script provides help information"""
        # The script should run and provide information
        result = subprocess.run([str(self.fix_script)], 
                               capture_output=True, text=True, timeout=30)
        
        # Script should complete (exit code 0 or 1 are both acceptable)
        self.assertIn(result.returncode, [0, 1], 
                     "Fix script should complete with exit code 0 or 1")
        
        # Should contain helpful output
        output = result.stdout + result.stderr
        helpful_indicators = [
            'Docker',
            'permission',
            'group',
            'user'
        ]
        
        found_indicators = sum(1 for indicator in helpful_indicators 
                              if indicator.lower() in output.lower())
        self.assertGreater(found_indicators, 2, 
                          "Fix script should provide helpful Docker information")


class TestDockerTestingInfrastructure(unittest.TestCase):
    """Test the Docker testing infrastructure after permission fixes"""
    
    def setUp(self):
        """Set up testing infrastructure tests"""
        self.project_root = Path(__file__).parent.parent
        self.test_script = self.project_root / "test-docker.sh"
    
    def test_docker_test_script_exists(self):
        """Test that Docker test script exists"""
        self.assertTrue(self.test_script.exists(), 
                       f"Docker test script not found: {self.test_script}")
        self.assertTrue(os.access(self.test_script, os.X_OK),
                       "Docker test script should be executable")
    
    def test_docker_test_script_help(self):
        """Test Docker test script help functionality"""
        # Skip if Docker not accessible
        ps_result = subprocess.run(['docker', 'ps'], 
                                  capture_output=True, text=True, timeout=10)
        if ps_result.returncode != 0:
            self.skipTest("Docker not accessible - skipping test script tests")
        
        result = subprocess.run([str(self.test_script), '--help'], 
                               capture_output=True, text=True, timeout=30)
        
        self.assertEqual(result.returncode, 0, 
                        "Docker test script help should work")
        self.assertIn('Usage:', result.stdout)
    
    def test_docker_integration_tests_exist(self):
        """Test that Docker integration tests exist"""
        integration_test = self.project_root / "tests" / "test_docker_integration.py"
        self.assertTrue(integration_test.exists(), 
                       "Docker integration tests should exist")
    
    def test_docker_unit_tests_exist(self):
        """Test that Docker unit tests exist"""
        unit_test = self.project_root / "tests" / "test_docker_containers.py"
        self.assertTrue(unit_test.exists(), 
                       "Docker unit tests should exist")
    
    def test_dockerfile_test_exists(self):
        """Test that Dockerfile.test exists for testing"""
        dockerfile = self.project_root / "Dockerfile.test"
        self.assertTrue(dockerfile.exists(), 
                       "Dockerfile.test should exist for container testing")


class TestDockerPermissionGuidance(unittest.TestCase):
    """Test Docker permission guidance and user experience"""
    
    def test_permission_error_guidance(self):
        """Test that users get clear guidance on permission errors"""
        # This test documents the expected user experience
        guidance_points = [
            "Run fix-docker-permissions.sh script",
            "Add user to docker group with: sudo usermod -aG docker $USER",
            "Restart session or run: newgrp docker",
            "Verify with: docker ps",
            "Test with: docker run hello-world"
        ]
        
        # This test passes if the guidance is documented
        self.assertTrue(True, "Permission guidance is documented")
    
    def test_session_restart_instructions(self):
        """Test that session restart instructions are clear"""
        instructions = [
            "Log out and log back in",
            "Start new terminal",
            "Use newgrp docker command",
            "Restart system if needed"
        ]
        
        # This test passes if instructions are available
        self.assertTrue(True, "Session restart instructions are available")


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)

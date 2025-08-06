"""
Container Test Configuration and Utilities
Shared utilities and configuration for container-based testing
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ContainerTestConfig:
    """Configuration for container testing"""
    
    # Container settings
    CONTAINER_NAME = "redhat-status-test"
    DOCKERFILE_TEST = "Dockerfile.test"
    
    # Test timeouts (seconds)
    BUILD_TIMEOUT = 300
    RUN_TIMEOUT = 60
    CLEANUP_TIMEOUT = 30
    
    # Expected outputs
    EXPECTED_PYTHON_VERSION = "Python 3.11"
    EXPECTED_APP_VERSION = "Red Hat Status Checker v3.1.0"
    
    # Test result directories
    TEST_RESULTS_DIR = "test-results"
    PERFORMANCE_RESULTS_DIR = "performance-results"
    COVERAGE_REPORTS_DIR = "coverage-reports"


class ContainerTestUtils:
    """Utility functions for container testing"""
    
    @staticmethod
    def is_podman_available() -> bool:
        """Check if Podman is available on the system"""
        try:
            result = subprocess.run(['podman', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    def is_docker_available() -> bool:
        """Check if Docker is available on the system"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    @staticmethod
    def get_container_runtime() -> Optional[str]:
        """Get available container runtime (podman preferred over docker)"""
        if ContainerTestUtils.is_podman_available():
            return 'podman'
        elif ContainerTestUtils.is_docker_available():
            return 'docker'
        else:
            return None
    
    @staticmethod
    def run_container_command(
        runtime: str,
        container_name: str,
        command: List[str],
        timeout: int = 60,
        capture_output: bool = True,
        cwd: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        """Run a command in a container"""
        cmd = [runtime, 'run', '--rm', container_name] + command
        
        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
    
    @staticmethod
    def build_test_container(
        runtime: str,
        dockerfile: str,
        container_name: str,
        context_dir: str,
        timeout: int = 300
    ) -> Tuple[bool, str, str]:
        """Build test container and return success status with output"""
        build_cmd = [
            runtime, 'build',
            '-f', dockerfile,
            '-t', container_name,
            context_dir
        ]
        
        try:
            result = subprocess.run(
                build_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=context_dir
            )
            
            return (
                result.returncode == 0,
                result.stdout,
                result.stderr
            )
        except subprocess.TimeoutExpired as e:
            return (False, "", f"Build timeout after {timeout} seconds")
    
    @staticmethod
    def cleanup_containers(runtime: str, container_name: str) -> bool:
        """Clean up test containers"""
        try:
            # Stop running containers
            subprocess.run([
                runtime, 'ps', '-q', '--filter', f'name={container_name}'
            ], capture_output=True, timeout=30)
            
            # Remove containers
            subprocess.run([
                runtime, 'ps', '-aq', '--filter', f'name={container_name}'
            ], capture_output=True, timeout=30)
            
            # Remove image
            subprocess.run([
                runtime, 'rmi', container_name
            ], capture_output=True, timeout=30)
            
            return True
        except subprocess.TimeoutExpired:
            return False
    
    @staticmethod
    def wait_for_container_ready(
        runtime: str, 
        container_name: str, 
        max_wait: int = 30
    ) -> bool:
        """Wait for container to be ready"""
        for _ in range(max_wait):
            try:
                result = ContainerTestUtils.run_container_command(
                    runtime, container_name, ['echo', 'ready'], timeout=10
                )
                if result.returncode == 0:
                    return True
            except subprocess.TimeoutExpired:
                pass
            time.sleep(1)
        return False
    
    @staticmethod
    def get_container_info(runtime: str, container_name: str) -> Dict[str, str]:
        """Get container information"""
        info = {}
        
        try:
            # Get Python version
            result = ContainerTestUtils.run_container_command(
                runtime, container_name, ['python3', '--version'], timeout=30
            )
            if result.returncode == 0:
                info['python_version'] = result.stdout.strip()
        except subprocess.TimeoutExpired:
            info['python_version'] = 'Unknown'
        
        try:
            # Get working directory
            result = ContainerTestUtils.run_container_command(
                runtime, container_name, ['pwd'], timeout=30
            )
            if result.returncode == 0:
                info['working_directory'] = result.stdout.strip()
        except subprocess.TimeoutExpired:
            info['working_directory'] = 'Unknown'
        
        try:
            # Get environment variables
            result = ContainerTestUtils.run_container_command(
                runtime, container_name, ['env'], timeout=30
            )
            if result.returncode == 0:
                env_vars = {}
                for line in result.stdout.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
                info['environment'] = env_vars
        except subprocess.TimeoutExpired:
            info['environment'] = {}
        
        return info
    
    @staticmethod
    def validate_container_setup(runtime: str, container_name: str) -> List[str]:
        """Validate container setup and return list of issues"""
        issues = []
        
        # Check Python version
        try:
            result = ContainerTestUtils.run_container_command(
                runtime, container_name, ['python3', '--version'], timeout=30
            )
            if result.returncode != 0:
                issues.append("Python 3 not available in container")
            elif ContainerTestConfig.EXPECTED_PYTHON_VERSION not in result.stdout:
                issues.append(f"Unexpected Python version: {result.stdout.strip()}")
        except subprocess.TimeoutExpired:
            issues.append("Timeout checking Python version")
        
        # Check working directory
        try:
            result = ContainerTestUtils.run_container_command(
                runtime, container_name, ['pwd'], timeout=30
            )
            if result.returncode != 0 or result.stdout.strip() != '/app':
                issues.append("Working directory not set to /app")
        except subprocess.TimeoutExpired:
            issues.append("Timeout checking working directory")
        
        # Check module import
        try:
            result = ContainerTestUtils.run_container_command(
                runtime, container_name, 
                ['python3', '-c', 'import redhat_status'], 
                timeout=30
            )
            if result.returncode != 0:
                issues.append("Cannot import redhat_status module")
        except subprocess.TimeoutExpired:
            issues.append("Timeout checking module import")
        
        # Check main application file
        try:
            result = ContainerTestUtils.run_container_command(
                runtime, container_name, ['ls', 'redhat_status.py'], timeout=30
            )
            if result.returncode != 0:
                issues.append("Main application file not found")
        except subprocess.TimeoutExpired:
            issues.append("Timeout checking application files")
        
        return issues


class ContainerTestReporter:
    """Generate reports for container tests"""
    
    @staticmethod
    def generate_test_report(
        test_results: Dict[str, bool],
        container_info: Dict[str, str],
        issues: List[str],
        output_file: str
    ) -> None:
        """Generate a comprehensive test report"""
        
        report_content = f"""# Container Test Report

**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Container Runtime:** {container_info.get('runtime', 'Unknown')}
**Python Version:** {container_info.get('python_version', 'Unknown')}

## Test Results Summary

"""
        
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            report_content += f"- **{test_name}:** {status}\n"
        
        report_content += f"""
**Overall Results:** {passed_tests}/{total_tests} tests passed
**Success Rate:** {(passed_tests * 100) // total_tests}%

## Container Information

- **Working Directory:** {container_info.get('working_directory', 'Unknown')}
- **Python Version:** {container_info.get('python_version', 'Unknown')}

## Issues Found

"""
        
        if issues:
            for issue in issues:
                report_content += f"- ⚠️ {issue}\n"
        else:
            report_content += "- ✅ No issues found\n"
        
        report_content += f"""

## Environment Variables

"""
        
        env_vars = container_info.get('environment', {})
        for key, value in env_vars.items():
            if key.startswith(('PYTHON', 'PATH', 'TEST')):
                report_content += f"- **{key}:** {value}\n"
        
        with open(output_file, 'w') as f:
            f.write(report_content)


# Test configuration constants
CONTAINER_TESTS_ENABLED = os.environ.get('CONTAINER_TESTS_ENABLED', 'true').lower() == 'true'
SKIP_SLOW_TESTS = os.environ.get('SKIP_SLOW_TESTS', 'false').lower() == 'true'
VERBOSE_OUTPUT = os.environ.get('VERBOSE_OUTPUT', 'false').lower() == 'true'

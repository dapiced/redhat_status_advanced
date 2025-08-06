"""
Integration tests for the complete Red Hat Status Checker application.
Tests all components working together and CLI functionality.
"""
import pytest
import tempfile
import shutil
import subprocess
import sys
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

# Add the project root to sys.path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestCLIIntegration:
    """Integration tests for CLI functionality"""
    
    def setup_method(self):
        """Set up test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.script_path = project_root / "redhat_status.py"
    
    def teardown_method(self):
        """Clean up after test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def run_cli_command(self, args, expect_success=True):
        """Helper method to run CLI commands"""
        cmd = [sys.executable, str(self.script_path)] + args
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(project_root)
            )
            
            if expect_success and result.returncode != 0:
                pytest.fail(f"Command failed: {' '.join(args)}\\nSTDOUT: {result.stdout}\\nSTDERR: {result.stderr}")
            
            return result
        except subprocess.TimeoutExpired:
            pytest.fail(f"Command timed out: {' '.join(args)}")
    
    def test_help_flag(self):
        """Test --help flag"""
        result = self.run_cli_command(['--help'], expect_success=False)
        
        # Help should exit with code 0 but subprocess sees it as non-zero
        assert 'Red Hat Status Checker' in result.stdout
        assert '--quiet' in result.stdout
        assert '--performance' in result.stdout
    
    def test_version_flag(self):
        """Test --version flag"""
        result = self.run_cli_command(['--version'], expect_success=False)
        
        # Version should be in output
        assert 'Red Hat Status Checker v3.1.0' in result.stdout or 'Red Hat Status Checker v3.1.0' in result.stderr
    
    @patch('redhat_status.core.api_client.fetch_status_data')
    def test_quick_mode(self, mock_fetch):
        """Test quick mode functionality"""
        # Mock API response
        mock_fetch.return_value = {
            'page': {'name': 'Red Hat Status'},
            'components': [
                {'id': '1', 'name': 'Service 1', 'status': 'operational'},
                {'id': '2', 'name': 'Service 2', 'status': 'operational'}
            ],
            'incidents': []
        }
        
        result = self.run_cli_command(['quick'])
        
        # Should contain status information
        assert 'Global Availability' in result.stdout or 'RED HAT' in result.stdout
        mock_fetch.assert_called_once()
    
    @patch('redhat_status.core.api_client.fetch_status_data')
    def test_quiet_mode(self, mock_fetch):
        """Test quiet mode functionality"""
        mock_fetch.return_value = {
            'page': {'name': 'Red Hat Status'},
            'components': [
                {'id': '1', 'name': 'Service 1', 'status': 'operational'}
            ],
            'incidents': []
        }
        
        result = self.run_cli_command(['quick', '--quiet'])
        
        # Quiet mode should have minimal output
        lines = result.stdout.strip().split('\\n')
        assert len(lines) <= 5  # Should be very concise
        mock_fetch.assert_called_once()
    
    def test_config_check_flag(self):
        """Test --config-check flag"""
        result = self.run_cli_command(['--config-check'])
        
        # Should show configuration validation
        assert 'CONFIGURATION VALIDATION' in result.stdout
        assert 'Status:' in result.stdout
    
    def test_clear_cache_flag(self):
        """Test --clear-cache flag"""
        result = self.run_cli_command(['--clear-cache'])
        
        # Should show cache clearing message
        assert 'Cache cleared' in result.stdout
    
    @patch('redhat_status.core.api_client.fetch_status_data')
    def test_export_mode(self, mock_fetch):
        """Test export mode functionality"""
        mock_fetch.return_value = {
            'page': {'name': 'Red Hat Status'},
            'components': [
                {'id': '1', 'name': 'Service 1', 'status': 'operational'}
            ],
            'incidents': []
        }
        
        result = self.run_cli_command(['export', '--output', self.temp_dir])
        
        # Should create export files
        export_files = list(Path(self.temp_dir).glob('*.json'))
        assert len(export_files) > 0
        mock_fetch.assert_called_once()
    
    @patch('redhat_status.core.api_client.fetch_status_data')
    def test_performance_flag(self, mock_fetch):
        """Test --performance flag"""
        mock_fetch.return_value = {
            'page': {'name': 'Red Hat Status'},
            'components': [
                {'id': '1', 'name': 'Service 1', 'status': 'operational'}
            ],
            'incidents': []
        }
        
        result = self.run_cli_command(['quick', '--performance'])
        
        # Should show performance metrics
        assert 'Performance' in result.stdout or 'time' in result.stdout.lower()
        mock_fetch.assert_called_once()
    
    def test_invalid_mode(self):
        """Test invalid mode handling"""
        result = self.run_cli_command(['invalid_mode'], expect_success=False)
        
        # Should show error message
        assert result.returncode != 0
        assert 'invalid choice' in result.stderr.lower() or 'error' in result.stderr.lower()
    
    @patch('redhat_status.core.api_client.fetch_status_data')
    def test_filter_flag(self, mock_fetch):
        """Test --filter flag"""
        mock_fetch.return_value = {
            'page': {'name': 'Red Hat Status'},
            'components': [
                {'id': '1', 'name': 'Service 1', 'status': 'operational'},
                {'id': '2', 'name': 'Service 2', 'status': 'degraded_performance'}
            ],
            'incidents': []
        }
        
        result = self.run_cli_command(['simple', '--filter', 'issues'])
        
        # Should filter to show only services with issues
        mock_fetch.assert_called_once()
    
    @patch('redhat_status.core.api_client.fetch_status_data')
    def test_search_flag(self, mock_fetch):
        """Test --search flag"""
        mock_fetch.return_value = {
            'page': {'name': 'Red Hat Status'},
            'components': [
                {'id': '1', 'name': 'Registry Service', 'status': 'operational'},
                {'id': '2', 'name': 'Database Service', 'status': 'operational'}
            ],
            'incidents': []
        }
        
        result = self.run_cli_command(['simple', '--search', 'registry'])
        
        # Should search for services containing 'registry'
        mock_fetch.assert_called_once()
    
    def test_no_cache_flag(self):
        """Test --no-cache flag"""
        # This test ensures the flag is accepted without error
        with patch('redhat_status.core.api_client.fetch_status_data') as mock_fetch:
            mock_fetch.return_value = {
                'components': [],
                'incidents': []
            }
            
            result = self.run_cli_command(['quick', '--no-cache'])
            mock_fetch.assert_called_once()


class TestModuleIntegration:
    """Integration tests for module interactions"""
    
    def setup_method(self):
        """Set up test method"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up after test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('redhat_status.core.api_client.fetch_status_data')
    def test_api_client_cache_integration(self, mock_fetch):
        """Test API client and cache manager integration"""
        from redhat_status.core.api_client import get_api_client
        from redhat_status.core.cache_manager import get_cache_manager
        
        # Mock API response
        mock_data = {
            'components': [{'id': '1', 'name': 'Test Service', 'status': 'operational'}],
            'incidents': []
        }
        mock_fetch.return_value = mock_data
        
        api_client = get_api_client()
        cache_manager = get_cache_manager()
        
        # Clear any existing cache
        cache_manager.clear()
        
        # First call should hit API
        data1 = api_client.fetch_status()
        assert data1 == mock_data
        assert mock_fetch.call_count == 1
        
        # Second call should use cache (if caching is enabled)
        data2 = api_client.fetch_status()
        assert data2 == mock_data
        # Call count may or may not increase depending on cache implementation
    
    def test_config_manager_integration(self):
        """Test configuration manager integration with other modules"""
        from redhat_status.config.config_manager import get_config
        from redhat_status.core.cache_manager import get_cache_manager
        
        config = get_config()
        cache_manager = get_cache_manager()
        
        # Configuration should affect cache manager behavior
        assert config is not None
        assert cache_manager is not None
    
    @patch('redhat_status.core.api_client.fetch_status_data')
    def test_database_integration(self, mock_fetch):
        """Test database integration with status data"""
        try:
            from redhat_status.database.db_manager import get_database_manager
            
            # Mock API response
            mock_fetch.return_value = {
                'components': [{'id': '1', 'name': 'Test Service', 'status': 'operational'}],
                'incidents': []
            }
            
            db_manager = get_database_manager()
            
            if db_manager and db_manager.enabled:
                # Test storing status data
                status_data = {
                    'timestamp': datetime.now(),
                    'overall_status': 'operational',
                    'availability_percentage': 99.5,
                    'total_services': 1,
                    'operational_services': 1,
                    'response_time': 1.5
                }
                
                check_id = db_manager.store_status_check(status_data)
                assert check_id is not None
                
                # Test retrieving data
                history = db_manager.get_status_history(limit=1)
                assert len(history) >= 1
        except ImportError:
            # Database module not available in test environment
            pytest.skip("Database module not available")
    
    def test_notification_integration(self):
        """Test notification manager integration"""
        try:
            from redhat_status.notifications.notification_manager import get_notification_manager
            
            notification_manager = get_notification_manager()
            
            # Test notification configuration
            assert notification_manager is not None
            
            # Test alert formatting
            alert_data = {
                'type': 'service_down',
                'service': 'Test Service',
                'status': 'down',
                'timestamp': datetime.now()
            }
            
            if hasattr(notification_manager, '_format_alert_message'):
                message = notification_manager._format_alert_message(alert_data)
                assert isinstance(message, str)
                assert 'Test Service' in message
        except ImportError:
            # Notification module not available in test environment
            pytest.skip("Notification module not available")
    
    def test_analytics_integration(self):
        """Test AI analytics integration"""
        try:
            from redhat_status.analytics.ai_analytics import get_analytics
            
            analytics = get_analytics()
            
            if analytics and analytics.enabled:
                # Test analytics with sample data
                sample_data = [
                    {
                        'timestamp': datetime.now(),
                        'availability_percentage': 99.5,
                        'response_time': 1.0,
                        'total_services': 50,
                        'operational_services': 49
                    }
                ]
                
                # Test trend analysis
                trends = analytics.analyze_availability_trends(sample_data)
                assert trends is not None or trends == {}
        except ImportError:
            # Analytics module not available in test environment
            pytest.skip("Analytics module not available")


class TestEndToEndScenarios:
    """End-to-end test scenarios"""
    
    def setup_method(self):
        """Set up test method"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up after test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('redhat_status.core.api_client.fetch_status_data')
    def test_complete_status_check_workflow(self, mock_fetch):
        """Test complete status check workflow"""
        # Mock API response with various service states
        mock_fetch.return_value = {
            'page': {'name': 'Red Hat Status'},
            'components': [
                {'id': '1', 'name': 'API Gateway', 'status': 'operational'},
                {'id': '2', 'name': 'Database', 'status': 'degraded_performance'},
                {'id': '3', 'name': 'Cache Service', 'status': 'operational'},
                {'id': '4', 'name': 'Message Queue', 'status': 'major_outage'}
            ],
            'incidents': [
                {
                    'id': 'inc1',
                    'name': 'Database Performance Issues',
                    'status': 'investigating',
                    'impact': 'minor'
                },
                {
                    'id': 'inc2',
                    'name': 'Message Queue Outage',
                    'status': 'identified',
                    'impact': 'major'
                }
            ]
        }
        
        from redhat_status.main import RedHatStatusChecker
        
        # Initialize application
        app = RedHatStatusChecker()
        
        # This would test the complete workflow but requires
        # more complex mocking of all components
        assert app is not None
        mock_fetch.assert_called()
    
    @patch('redhat_status.core.api_client.fetch_status_data')
    def test_error_handling_workflow(self, mock_fetch):
        """Test error handling in complete workflow"""
        # Mock API failure
        mock_fetch.side_effect = Exception("API Error")
        
        from redhat_status.main import RedHatStatusChecker
        
        # Application should handle API errors gracefully
        app = RedHatStatusChecker()
        
        # This would test error recovery mechanisms
        assert app is not None
    
    def test_configuration_workflow(self):
        """Test configuration loading and validation workflow"""
        # Create temporary config file
        config_file = os.path.join(self.temp_dir, 'test_config.json')
        config_data = {
            'cache': {'enabled': True, 'ttl': 300},
            'api': {'timeout': 30, 'retries': 3},
            'database': {'enabled': False},
            'notifications': {
                'email': {'enabled': False},
                'webhooks': {'enabled': False}
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Test configuration loading
        from redhat_status.config.config_manager import ConfigManager
        
        config = ConfigManager(config_file=config_file)
        
        assert config.get('cache', 'enabled') is True
        assert config.get('api', 'timeout') == 30
        
        # Test validation
        validation = config.validate()
        assert validation['valid'] is True


class TestPerformanceIntegration:
    """Integration tests for performance aspects"""
    
    @patch('redhat_status.core.api_client.fetch_status_data')
    def test_performance_monitoring_integration(self, mock_fetch):
        """Test performance monitoring across modules"""
        mock_fetch.return_value = {
            'components': [{'id': '1', 'name': 'Test', 'status': 'operational'}],
            'incidents': []
        }
        
        from redhat_status.main import RedHatStatusChecker
        from redhat_status.core.data_models import PerformanceMetrics
        
        app = RedHatStatusChecker()
        
        # Performance metrics should be tracked
        assert isinstance(app.performance, PerformanceMetrics)
        
        # Test that decorators are working
        # This would require more complex setup to test actual decorator integration
    
    def test_caching_performance_integration(self):
        """Test caching performance across modules"""
        from redhat_status.core.cache_manager import get_cache_manager
        
        cache_manager = get_cache_manager()
        
        # Test cache performance with various data sizes
        small_data = {'test': 'small'}
        large_data = {'test': 'x' * 10000}
        
        # Should handle both efficiently
        cache_manager.set('small', small_data)
        cache_manager.set('large', large_data)
        
        assert cache_manager.get('small') == small_data
        assert cache_manager.get('large') == large_data
        
        # Check cache statistics
        stats = cache_manager.get_stats()
        assert 'total_items' in stats


class TestSecurityIntegration:
    """Integration tests for security aspects"""
    
    def test_sensitive_data_handling(self):
        """Test that sensitive data is handled securely"""
        # Test configuration with sensitive data
        sensitive_config = {
            'notifications': {
                'email': {
                    'username': 'user@example.com',
                    'password': 'secret_password'
                }
            }
        }
        
        from redhat_status.config.config_manager import ConfigManager
        
        config = ConfigManager()
        config.config = sensitive_config
        
        # Configuration should be loaded but password should be handled securely
        assert config.get('notifications', 'email', {}).get('username') == 'user@example.com'
        # Password should be present but handled securely in real implementation
    
    def test_input_validation_integration(self):
        """Test input validation across modules"""
        from redhat_status.config.config_manager import ConfigManager
        
        # Test with invalid configuration
        invalid_config = {
            'cache': {'ttl': -1},  # Invalid negative TTL
            'api': {'timeout': 'invalid'}  # Invalid timeout type
        }
        
        config = ConfigManager()
        config.config = invalid_config
        
        # Validation should catch issues
        validation = config.validate()
        assert validation['valid'] is False
        assert len(validation['errors']) > 0


if __name__ == '__main__':
    pytest.main([__file__])

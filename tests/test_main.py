"""
Test suite for main application functionality and CLI arguments.
"""
import pytest
import sys
import os
import argparse
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

# Add the project root to sys.path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redhat_status.main import RedHatStatusChecker, create_argument_parser, main
from redhat_status.core.data_models import PerformanceMetrics


class TestArgumentParser:
    """Test all command-line arguments and flags"""
    
    def setup_method(self):
        """Set up test method"""
        self.parser = create_argument_parser()
    
    def test_parser_basic_modes(self):
        """Test basic operation modes"""
        # Test each mode
        modes = ['quick', 'simple', 'full', 'export', 'all']
        for mode in modes:
            args = self.parser.parse_args([mode])
            assert args.mode == mode
    
    def test_parser_no_args(self):
        """Test parser with no arguments (interactive mode)"""
        args = self.parser.parse_args([])
        assert args.mode is None
        assert args.quiet is False
        assert args.performance is False
    
    def test_parser_output_flag(self):
        """Test --output/-o flag"""
        args = self.parser.parse_args(['--output', '/tmp/test'])
        assert args.output == '/tmp/test'
        
        args = self.parser.parse_args(['-o', '/tmp/test'])
        assert args.output == '/tmp/test'
    
    def test_parser_quiet_flag(self):
        """Test --quiet/-q flag"""
        args = self.parser.parse_args(['--quiet'])
        assert args.quiet is True
        
        args = self.parser.parse_args(['-q'])
        assert args.quiet is True
    
    def test_parser_performance_flag(self):
        """Test --performance flag"""
        args = self.parser.parse_args(['--performance'])
        assert args.performance is True
    
    def test_parser_clear_cache_flag(self):
        """Test --clear-cache flag"""
        args = self.parser.parse_args(['--clear-cache'])
        assert args.clear_cache is True
    
    def test_parser_config_check_flag(self):
        """Test --config-check flag"""
        args = self.parser.parse_args(['--config-check'])
        assert args.config_check is True
    
    def test_parser_test_notifications_flag(self):
        """Test --test-notifications flag"""
        args = self.parser.parse_args(['--test-notifications'])
        assert args.test_notifications is True
    
    def test_parser_analytics_summary_flag(self):
        """Test --analytics-summary flag"""
        args = self.parser.parse_args(['--analytics-summary'])
        assert args.analytics_summary is True
    
    def test_parser_db_maintenance_flag(self):
        """Test --db-maintenance flag"""
        args = self.parser.parse_args(['--db-maintenance'])
        assert args.db_maintenance is True
    
    def test_parser_ai_insights_flag(self):
        """Test --ai-insights flag"""
        args = self.parser.parse_args(['--ai-insights'])
        assert args.ai_insights is True
    
    def test_parser_anomaly_analysis_flag(self):
        """Test --anomaly-analysis flag"""
        args = self.parser.parse_args(['--anomaly-analysis'])
        assert args.anomaly_analysis is True
    
    def test_parser_health_report_flag(self):
        """Test --health-report flag"""
        args = self.parser.parse_args(['--health-report'])
        assert args.health_report is True
    
    def test_parser_insights_flag(self):
        """Test --insights flag"""
        args = self.parser.parse_args(['--insights'])
        assert args.insights is True
    
    def test_parser_trends_flag(self):
        """Test --trends flag"""
        args = self.parser.parse_args(['--trends'])
        assert args.trends is True
    
    def test_parser_slo_dashboard_flag(self):
        """Test --slo-dashboard flag"""
        args = self.parser.parse_args(['--slo-dashboard'])
        assert args.slo_dashboard is True
    
    def test_parser_export_ai_report_flag(self):
        """Test --export-ai-report flag"""
        args = self.parser.parse_args(['--export-ai-report'])
        assert args.export_ai_report is True
    
    def test_parser_export_history_flag(self):
        """Test --export-history flag"""
        args = self.parser.parse_args(['--export-history'])
        assert args.export_history is True
    
    def test_parser_format_flag(self):
        """Test --format flag with all choices"""
        formats = ['json', 'csv', 'txt']
        for fmt in formats:
            args = self.parser.parse_args(['--format', fmt])
            assert args.format == fmt
    
    def test_parser_filter_flag(self):
        """Test --filter flag with all choices"""
        filters = ['all', 'issues', 'operational', 'degraded']
        for filter_type in filters:
            args = self.parser.parse_args(['--filter', filter_type])
            assert args.filter == filter_type
    
    def test_parser_search_flag(self):
        """Test --search flag"""
        args = self.parser.parse_args(['--search', 'registry'])
        assert args.search == 'registry'
    
    def test_parser_concurrent_check_flag(self):
        """Test --concurrent-check flag"""
        args = self.parser.parse_args(['--concurrent-check'])
        assert args.concurrent_check is True
    
    def test_parser_watch_flag(self):
        """Test --watch flag with interval"""
        args = self.parser.parse_args(['--watch', '30'])
        assert args.watch == 30
    
    def test_parser_notify_flag(self):
        """Test --notify flag"""
        args = self.parser.parse_args(['--notify'])
        assert args.notify is True
    
    def test_parser_benchmark_flag(self):
        """Test --benchmark flag"""
        args = self.parser.parse_args(['--benchmark'])
        assert args.benchmark is True
    
    def test_parser_no_cache_flag(self):
        """Test --no-cache flag"""
        args = self.parser.parse_args(['--no-cache'])
        assert args.no_cache is True
    
    def test_parser_log_level_flag(self):
        """Test --log-level flag with all choices"""
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        for level in levels:
            args = self.parser.parse_args(['--log-level', level])
            assert args.log_level == level
    
    def test_parser_enable_monitoring_flag(self):
        """Test --enable-monitoring flag"""
        args = self.parser.parse_args(['--enable-monitoring'])
        assert args.enable_monitoring is True
    
    def test_parser_setup_flag(self):
        """Test --setup flag"""
        args = self.parser.parse_args(['--setup'])
        assert args.setup is True
    
    def test_parser_version_flag(self):
        """Test --version/-v flag"""
        with pytest.raises(SystemExit):
            self.parser.parse_args(['--version'])
        
        with pytest.raises(SystemExit):
            self.parser.parse_args(['-v'])
    
    def test_parser_combined_flags(self):
        """Test combination of multiple flags"""
        args = self.parser.parse_args([
            'quick', '--quiet', '--performance', '--no-cache',
            '--output', '/tmp', '--format', 'json', '--filter', 'issues'
        ])
        assert args.mode == 'quick'
        assert args.quiet is True
        assert args.performance is True
        assert args.no_cache is True
        assert args.output == '/tmp'
        assert args.format == 'json'
        assert args.filter == 'issues'


class TestRedHatStatusChecker:
    """Test the main application class"""
    
    def setup_method(self):
        """Set up test method"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up after test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('redhat_status.main.get_config')
    @patch('redhat_status.main.get_api_client')
    def test_init_basic(self, mock_api_client, mock_config):
        """Test basic initialization"""
        mock_config.return_value = Mock()
        mock_api_client.return_value = Mock()
        
        app = RedHatStatusChecker()
        
        assert app.config is not None
        assert app.api_client is not None
        assert isinstance(app.performance, PerformanceMetrics)
    
    @patch('redhat_status.main.ENTERPRISE_FEATURES', True)
    @patch('redhat_status.main.get_config')
    @patch('redhat_status.main.get_api_client')
    @patch('redhat_status.main.get_analytics')
    @patch('redhat_status.main.get_database_manager')
    @patch('redhat_status.main.get_notification_manager')
    def test_init_with_enterprise_features(self, mock_notifications, mock_db, 
                                         mock_analytics, mock_api_client, mock_config):
        """Test initialization with enterprise features enabled"""
        # Mock config to enable features
        config_mock = Mock()
        config_mock.get.side_effect = lambda section, key, default=None: {
            ('ai_analytics', 'enabled'): True,
            ('database', 'enabled'): True,
            ('notifications', 'email'): {'enabled': True},
            ('notifications', 'webhooks'): {'enabled': False},
        }.get((section, key), default)
        
        mock_config.return_value = config_mock
        mock_api_client.return_value = Mock()
        mock_analytics.return_value = Mock()
        mock_db.return_value = Mock()
        mock_notifications.return_value = Mock()
        
        app = RedHatStatusChecker()
        
        assert app.analytics is not None
        assert app.db_manager is not None
        assert app.notification_manager is not None
    
    @patch('redhat_status.main.get_config')
    @patch('redhat_status.main.get_api_client')
    def test_present_quick_status_quiet(self, mock_api_client, mock_config):
        """Test quick status presentation in quiet mode"""
        mock_config.return_value = Mock()
        mock_api_client.return_value = Mock()
        
        app = RedHatStatusChecker()
        
        health_metrics = {
            'availability_percentage': 99.5,
            'operational_services': 48,
            'total_services': 50,
            'overall_status': 'Operational'
        }
        
        # Capture print output
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            app._present_quick_status(health_metrics, cached=False, quiet_mode=True)
        
        output = captured_output.getvalue()
        assert '99.5%' in output
        assert '48/50 services' in output
        assert 'Operational' in output
    
    @patch('redhat_status.main.get_config')
    @patch('redhat_status.main.get_api_client')
    def test_present_quick_status_normal(self, mock_api_client, mock_config):
        """Test quick status presentation in normal mode"""
        mock_config.return_value = Mock()
        mock_api_client.return_value = Mock()
        
        app = RedHatStatusChecker()
        
        health_metrics = {
            'availability_percentage': 99.5,
            'operational_services': 48,
            'total_services': 50,
            'overall_status': 'Operational',
            'page_name': 'Red Hat Status',
            'page_url': 'https://status.redhat.com',
            'last_updated': '2023-01-01T12:00:00Z',
            'status_indicator': 'none'
        }
        
        # Capture print output
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            app._present_quick_status(health_metrics, cached=False, quiet_mode=False)
        
        output = captured_output.getvalue()
        assert 'RED HAT GLOBAL STATUS' in output
        assert '=' in output  # Check for formatting
        assert '99.5%' in output


class TestMainFunction:
    """Test the main function and argument handling"""
    
    @patch('redhat_status.main.RedHatStatusChecker')
    @patch('sys.argv', ['main.py', '--clear-cache'])
    def test_main_clear_cache(self, mock_app_class):
        """Test main function with --clear-cache flag"""
        mock_app = Mock()
        mock_app_class.return_value = mock_app
        
        with patch('redhat_status.core.cache_manager.get_cache_manager') as mock_cache_manager:
            cache_manager = Mock()
            cache_manager.clear.return_value = 5
            mock_cache_manager.return_value = cache_manager
            
            with patch('builtins.print') as mock_print:
                main()
                mock_print.assert_called_with("✅ Cache cleared: 5 files removed")
    
    @patch('redhat_status.main.RedHatStatusChecker')
    @patch('sys.argv', ['main.py', '--config-check'])
    def test_main_config_check(self, mock_app_class):
        """Test main function with --config-check flag"""
        mock_app = Mock()
        mock_app_class.return_value = mock_app
        
        with patch('redhat_status.main.get_config') as mock_get_config:
            config = Mock()
            config.validate.return_value = {
                'valid': True,
                'errors': [],
                'warnings': ['Sample warning']
            }
            mock_get_config.return_value = config
            
            with patch('builtins.print') as mock_print:
                main()
                # Check that validation output was printed
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                assert any('CONFIGURATION VALIDATION' in call for call in print_calls)
    
    @patch('redhat_status.main.RedHatStatusChecker')
    @patch('sys.argv', ['main.py', 'quick'])
    def test_main_quick_mode(self, mock_app_class):
        """Test main function with quick mode"""
        mock_app = Mock()
        mock_app_class.return_value = mock_app
        
        # Mock the method that would be called for quick mode
        mock_app.run_quick_check = Mock()
        
        # Since we can't easily test the full main function due to its complexity,
        # we'll test that the app is initialized correctly
        main()
        mock_app_class.assert_called_once()


class TestCLIIntegration:
    """Integration tests for CLI functionality"""
    
    def setup_method(self):
        """Set up test method"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up after test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_help_output(self):
        """Test that help output contains all expected flags"""
        parser = create_argument_parser()
        help_text = parser.format_help()
        
        # Check for major flags
        expected_flags = [
            '--quiet', '--performance', '--clear-cache', '--config-check',
            '--ai-insights', '--health-report', '--export-ai-report',
            '--filter', '--search', '--watch', '--benchmark', '--no-cache'
        ]
        
        for flag in expected_flags:
            assert flag in help_text, f"Flag {flag} not found in help text"
    
    def test_examples_in_help(self):
        """Test that help contains usage examples"""
        parser = create_argument_parser()
        help_text = parser.format_help()
        
        # Check for examples
        assert 'Examples:' in help_text
        assert 'quick' in help_text
        assert 'export' in help_text
        assert 'Advanced Features:' in help_text


if __name__ == '__main__':
    pytest.main([__file__])

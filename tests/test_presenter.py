"""
Tests for the presentation presenter module.
"""
import pytest
from unittest.mock import patch, Mock
import sys
from pathlib import Path
from io import StringIO

# Add the project root to sys.path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redhat_status.presentation.presenter import Presenter


class TestPresenter:
    """Test the Presenter class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.presenter = Presenter()
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_present_quick_status_quiet_mode(self, mock_stdout):
        """Test presenting quick status in quiet mode"""
        health_metrics = {
            'availability_percentage': 99.5,
            'operational_services': 45,
            'total_services': 50,
            'overall_status': 'All Systems Operational'
        }
        
        self.presenter.present_quick_status(health_metrics, cached=False, quiet_mode=True)
        
        output = mock_stdout.getvalue()
        assert "Global Availability: 99.5%" in output
        assert "(45/50 services)" in output
        assert "All Systems Operational" in output
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_present_quick_status_full_output(self, mock_stdout):
        """Test presenting quick status with full output"""
        health_metrics = {
            'availability_percentage': 99.5,
            'operational_services': 45,
            'total_services': 50,
            'overall_status': 'All Systems Operational',
            'page_name': 'Red Hat Status',
            'page_url': 'https://status.redhat.com',
            'last_updated': '2024-01-01T12:00:00Z',
            'status_indicator': 'none'
        }
        
        self.presenter.present_quick_status(health_metrics, cached=True, quiet_mode=False)
        
        output = mock_stdout.getvalue()
        assert "RED HAT GLOBAL STATUS" in output
        assert "Using cached data" in output
        assert "Red Hat Status" in output
        assert "https://status.redhat.com" in output
        assert "🟢 STATUS: All Systems Operational" in output
        assert "99.5%" in output
        assert "EXCELLENT" in output
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_present_quick_status_various_indicators(self, mock_stdout):
        """Test quick status with different status indicators"""
        base_metrics = {
            'availability_percentage': 85.0,
            'operational_services': 40,
            'total_services': 50,
            'overall_status': 'Minor Issues',
            'page_name': 'Red Hat Status',
            'page_url': 'https://status.redhat.com',
            'last_updated': '2024-01-01T12:00:00Z'
        }
        
        # Test minor issues
        metrics = base_metrics.copy()
        metrics['status_indicator'] = 'minor'
        self.presenter.present_quick_status(metrics, cached=False)
        
        output = mock_stdout.getvalue()
        assert "🟡" in output
        assert "Minor Issues" in output
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_present_quick_status_health_levels(self, mock_stdout):
        """Test different health levels in quick status"""
        base_metrics = {
            'operational_services': 40,
            'total_services': 50,
            'overall_status': 'Service Issues',
            'page_name': 'Red Hat Status',
            'page_url': 'https://status.redhat.com',
            'last_updated': '2024-01-01T12:00:00Z',
            'status_indicator': 'major'
        }
        
        # Test different availability percentages
        test_cases = [
            (99.5, "EXCELLENT"),
            (96.0, "GOOD"),
            (92.0, "FAIR"),
            (85.0, "POOR")
        ]
        
        for availability, expected_health in test_cases:
            mock_stdout.truncate(0)
            mock_stdout.seek(0)
            
            metrics = base_metrics.copy()
            metrics['availability_percentage'] = availability
            
            self.presenter.present_quick_status(metrics, cached=False)
            
            output = mock_stdout.getvalue()
            assert expected_health in output
            
    @patch('sys.stdout', new_callable=StringIO)
    def test_present_simple_check(self, mock_stdout):
        """Test presenting simple service check"""
        components = [
            {'name': 'API Gateway', 'status': 'operational', 'group_id': None},
            {'name': 'Database', 'status': 'degraded_performance', 'group_id': None},
            {'name': 'Load Balancer', 'status': 'operational', 'group_id': None},
            {'name': 'Sub Service', 'status': 'operational', 'group_id': 'main-1'}
        ]
        
        self.presenter.present_simple_check(components)
        
        output = mock_stdout.getvalue()
        assert "RED HAT MAIN SERVICES" in output
        assert "Total components in API: 4" in output
        assert "Main services found: 3" in output
        assert "✅ API Gateway" in output
        assert "❌ Database - DEGRADED_PERFORMANCE" in output
        assert "✅ Load Balancer" in output
        assert "2 operational, 1 with issues" in output
        assert "66.7%" in output
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_present_full_check(self, mock_stdout):
        """Test presenting full service hierarchy"""
        components = [
            {'id': 'main-1', 'name': 'API Gateway', 'status': 'operational', 'group_id': None},
            {'id': 'main-2', 'name': 'Database', 'status': 'degraded_performance', 'group_id': None},
            {'id': 'sub-1', 'name': 'Cache Service', 'status': 'operational', 'group_id': 'main-1'},
            {'id': 'sub-2', 'name': 'Auth Service', 'status': 'operational', 'group_id': 'main-1'},
            {'id': 'sub-3', 'name': 'Replica 1', 'status': 'maintenance', 'group_id': 'main-2'}
        ]
        
        self.presenter.present_full_check(components)
        
        output = mock_stdout.getvalue()
        assert "COMPLETE RED HAT STRUCTURE" in output
        assert "Main services: 2" in output
        assert "Sub-service groups: 2" in output
        assert "Total components: 5" in output
        assert "🟢 API Gateway" in output
        assert "🔴 Database - DEGRADED_PERFORMANCE" in output
        assert "Cache Service" in output
        assert "Auth Service" in output
        assert "Replica 1 - MAINTENANCE" in output
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_present_performance_metrics(self, mock_stdout):
        """Test presenting performance metrics"""
        # Mock performance metrics
        performance_metrics = Mock()
        performance_metrics.duration = 1.25
        performance_metrics.api_calls = 3
        performance_metrics.errors = []
        
        # Mock cache info
        cache_info = Mock()
        cache_info.entries_count = 15
        cache_info.size_human = "2.4 MB"
        cache_info.hit_ratio = 85.5
        
        # Mock database stats
        db_stats = {
            'service_snapshots_count': 100,
            'service_metrics_count': 250,
            'system_alerts_count': 5,
            'database_size_bytes': 52428800  # 50 MB
        }
        
        # Mock notification stats
        notif_stats = {
            'notifications_24h': 12,
            'notifications_7d': 85,
            'active_channels': 3
        }
        
        self.presenter.present_performance_metrics(
            performance_metrics, cache_info, db_stats, notif_stats
        )
        
        output = mock_stdout.getvalue()
        assert "PERFORMANCE METRICS" in output
        assert "Session Duration: 1.25s" in output
        assert "API Calls: 3" in output
        assert "Cache Entries: 15" in output
        assert "Cache Size: 2.4 MB" in output
        assert "Cache Hit Ratio: 85.5%" in output
        assert "DATABASE METRICS" in output
        assert "Total Snapshots: 100" in output
        assert "Service Metrics: 250" in output
        assert "Active Alerts: 5" in output
        assert "DB Size: 50.0 MB" in output
        assert "NOTIFICATION METRICS" in output
        assert "Sent (24h): 12" in output
        assert "Sent (7d): 85" in output
        assert "Active Channels: 3" in output
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_present_performance_metrics_with_errors(self, mock_stdout):
        """Test performance metrics with errors"""
        performance_metrics = Mock()
        performance_metrics.duration = 2.5
        performance_metrics.api_calls = 5
        performance_metrics.errors = ['Error 1', 'Error 2']
        
        cache_info = Mock()
        cache_info.entries_count = 10
        cache_info.size_human = "1.2 MB"
        cache_info.hit_ratio = 75.0
        
        self.presenter.present_performance_metrics(performance_metrics, cache_info)
        
        output = mock_stdout.getvalue()
        assert "Errors: 2" in output
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_present_error(self, mock_stdout):
        """Test presenting error message"""
        self.presenter.present_error("Test error message")
        
        output = mock_stdout.getvalue()
        assert "❌ Test error message" in output
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_present_message(self, mock_stdout):
        """Test presenting generic message"""
        self.presenter.present_message("Test message")
        
        output = mock_stdout.getvalue()
        assert "Test message" in output


class TestPresenterEdgeCases:
    """Test edge cases and error handling in Presenter"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.presenter = Presenter()
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_present_simple_check_empty_components(self, mock_stdout):
        """Test simple check with empty components list"""
        self.presenter.present_simple_check([])
        
        output = mock_stdout.getvalue()
        assert "Total components in API: 0" in output
        assert "Main services found: 0" in output
        assert "0 operational, 0 with issues" in output
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_present_full_check_no_sub_services(self, mock_stdout):
        """Test full check with no sub-services"""
        components = [
            {'id': 'main-1', 'name': 'Service 1', 'status': 'operational', 'group_id': None},
            {'id': 'main-2', 'name': 'Service 2', 'status': 'operational', 'group_id': None}
        ]
        
        self.presenter.present_full_check(components)
        
        output = mock_stdout.getvalue()
        assert "Main services: 2" in output
        assert "Sub-service groups: 0" in output
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_present_quick_status_unknown_indicator(self, mock_stdout):
        """Test quick status with unknown status indicator"""
        health_metrics = {
            'availability_percentage': 95.0,
            'operational_services': 38,
            'total_services': 40,
            'overall_status': 'Unknown Status',
            'page_name': 'Red Hat Status',
            'page_url': 'https://status.redhat.com',
            'last_updated': '2024-01-01T12:00:00Z',
            'status_indicator': 'unknown_status'
        }
        
        self.presenter.present_quick_status(health_metrics, cached=False)
        
        output = mock_stdout.getvalue()
        assert "⚪" in output
        assert "Unknown Status (unknown_status)" in output
        
    @patch('sys.stdout', new_callable=StringIO)
    def test_present_performance_metrics_minimal(self, mock_stdout):
        """Test performance metrics with minimal data"""
        performance_metrics = Mock()
        performance_metrics.duration = 0.5
        performance_metrics.api_calls = 1
        # Explicitly set errors to None to test the condition
        del performance_metrics.errors
        
        cache_info = Mock()
        cache_info.entries_count = 0
        cache_info.size_human = "0 B"
        cache_info.hit_ratio = 0.0
        
        self.presenter.present_performance_metrics(performance_metrics, cache_info)
        
        output = mock_stdout.getvalue()
        assert "Session Duration: 0.50s" in output
        assert "API Calls: 1" in output
        assert "Cache Entries: 0" in output
        assert "Cache Hit Ratio: 0.0%" in output
        # Should NOT contain errors since we don't have any
        assert "Errors:" not in output

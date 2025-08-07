"""
Tests for the Prometheus exporter module.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import sys
from pathlib import Path

# Add the project root to sys.path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestPrometheusExporter:
    """Test the Prometheus exporter"""
    
    def test_prometheus_exporter_import(self):
        """Test that Prometheus exporter can be imported"""
        try:
            from redhat_status.exporters.prometheus_exporter import PrometheusExporter
            assert PrometheusExporter is not None
        except ImportError as e:
            pytest.skip(f"Prometheus exporter not available: {e}")
    
    def test_metric_definitions_exist(self):
        """Test that metric definitions are available"""
        try:
            from redhat_status.exporters import prometheus_exporter
            
            # Check that key metrics are defined
            assert hasattr(prometheus_exporter, 'GLOBAL_AVAILABILITY')
            assert hasattr(prometheus_exporter, 'SERVICES_OPERATIONAL')
            assert hasattr(prometheus_exporter, 'SERVICES_WITH_ISSUES')
            assert hasattr(prometheus_exporter, 'SERVICE_STATUS')
            assert hasattr(prometheus_exporter, 'CACHE_HIT_RATIO')
            assert hasattr(prometheus_exporter, 'API_RESPONSE_TIME')
            
        except ImportError as e:
            pytest.skip(f"Prometheus exporter dependencies not available: {e}")
    
    @patch('redhat_status.exporters.prometheus_exporter.start_http_server')
    def test_prometheus_exporter_creation(self, mock_start_server):
        """Test creating a Prometheus exporter instance"""
        try:
            from redhat_status.exporters.prometheus_exporter import PrometheusExporter
            
            exporter = PrometheusExporter(port=9090)
            assert exporter is not None
            assert exporter.port == 9090
            
        except ImportError as e:
            pytest.skip(f"Prometheus exporter not available: {e}")
    
    @patch('redhat_status.exporters.prometheus_exporter.start_http_server')
    def test_start_server(self, mock_start_server):
        """Test starting the Prometheus server"""
        try:
            from redhat_status.exporters.prometheus_exporter import PrometheusExporter
            
            exporter = PrometheusExporter(port=9090)
            exporter.start_server()
            
            mock_start_server.assert_called_once_with(9090)
            
        except ImportError as e:
            pytest.skip(f"Prometheus exporter not available: {e}")
    
    def test_update_metrics_with_data(self):
        """Test updating metrics with status data"""
        try:
            from redhat_status.exporters.prometheus_exporter import PrometheusExporter
            
            exporter = PrometheusExporter()
            
            # Mock status data
            status_data = {
                'availability_percentage': 99.5,
                'operational_services': 45,
                'services_with_issues': 5,
                'components': [
                    {'name': 'API Gateway', 'status': 'operational', 'group': 'core'},
                    {'name': 'Database', 'status': 'degraded_performance', 'group': 'storage'}
                ],
                'response_time': 1.2,
                'cache_hit_ratio': 85.0
            }
            
            # This should not raise an exception
            exporter.update_metrics(status_data)
            
        except ImportError as e:
            pytest.skip(f"Prometheus exporter not available: {e}")
    
    def test_metric_updates(self):
        """Test individual metric updates"""
        try:
            from redhat_status.exporters.prometheus_exporter import (
                GLOBAL_AVAILABILITY, SERVICES_OPERATIONAL, SERVICES_WITH_ISSUES
            )
            
            # Test setting metric values
            GLOBAL_AVAILABILITY.set(99.5)
            SERVICES_OPERATIONAL.set(45)
            SERVICES_WITH_ISSUES.set(5)
            
            # These should complete without errors
            assert True
            
        except ImportError as e:
            pytest.skip(f"Prometheus client not available: {e}")


class TestPrometheusIntegration:
    """Test Prometheus exporter integration"""
    
    @patch('redhat_status.exporters.prometheus_exporter.start_http_server')
    def test_exporter_with_config(self, mock_start_server):
        """Test exporter with configuration"""
        try:
            from redhat_status.exporters.prometheus_exporter import PrometheusExporter
            
            config = {
                'prometheus': {
                    'enabled': True,
                    'port': 9091,
                    'metrics_path': '/metrics'
                }
            }
            
            exporter = PrometheusExporter(config=config)
            exporter.start_server()
            
            # Should use config port
            mock_start_server.assert_called_once_with(9091)
            
        except ImportError as e:
            pytest.skip(f"Prometheus exporter not available: {e}")
    
    def test_disabled_exporter(self):
        """Test exporter behavior when disabled"""
        try:
            from redhat_status.exporters.prometheus_exporter import PrometheusExporter
            
            config = {
                'prometheus': {
                    'enabled': False
                }
            }
            
            exporter = PrometheusExporter(config=config)
            
            # Should handle disabled state gracefully
            assert exporter is not None
            
        except ImportError as e:
            pytest.skip(f"Prometheus exporter not available: {e}")


class TestPrometheusMetrics:
    """Test individual Prometheus metrics"""
    
    def test_service_status_metric(self):
        """Test service status metric with labels"""
        try:
            from redhat_status.exporters.prometheus_exporter import SERVICE_STATUS
            
            # Test setting labeled metrics
            SERVICE_STATUS.labels(
                service_name='API Gateway',
                group_name='core'
            ).set(1)  # operational
            
            SERVICE_STATUS.labels(
                service_name='Database',
                group_name='storage'  
            ).set(0)  # issue
            
            # These should complete without errors
            assert True
            
        except ImportError as e:
            pytest.skip(f"Prometheus client not available: {e}")
    
    def test_all_metrics_can_be_set(self):
        """Test that all defined metrics can be set"""
        try:
            from redhat_status.exporters.prometheus_exporter import (
                GLOBAL_AVAILABILITY,
                SERVICES_OPERATIONAL,
                SERVICES_WITH_ISSUES,
                CACHE_HIT_RATIO,
                API_RESPONSE_TIME
            )
            
            # Test setting all metrics
            GLOBAL_AVAILABILITY.set(99.5)
            SERVICES_OPERATIONAL.set(45)
            SERVICES_WITH_ISSUES.set(5)
            CACHE_HIT_RATIO.set(85.0)
            API_RESPONSE_TIME.set(1.2)
            
            # These should complete without errors
            assert True
            
        except ImportError as e:
            pytest.skip(f"Prometheus client not available: {e}")

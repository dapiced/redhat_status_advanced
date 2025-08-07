"""
Tests for the Flask web application module.
"""
import pytest
from unittest.mock import patch, Mock
import sys
from pathlib import Path

# Add the project root to sys.path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestWebApp:
    """Test the Flask web application"""
    
    def setup_method(self):
        """Set up test method"""
        pass
    
    def test_web_app_import(self):
        """Test that web app can be imported"""
        try:
            from redhat_status.web.app import app
            assert app is not None
            assert app.name == 'redhat_status.web.app'
        except ImportError as e:
            pytest.skip(f"Web module not available: {e}")
    
    @patch('redhat_status.web.app.fetch_status_data')
    @patch('redhat_status.web.app.get_api_client')
    def test_index_route_success(self, mock_get_client, mock_fetch_data):
        """Test successful index route rendering"""
        try:
            from redhat_status.web.app import app
            from redhat_status.core.data_models import APIResponse
            
            # Mock successful API response
            mock_response = APIResponse(
                success=True,
                data={'components': [], 'incidents': []},
                error_message=None,
                response_time=0.5,
                status_code=200
            )
            mock_fetch_data.return_value = mock_response
            
            # Mock API client with health metrics
            mock_client = Mock()
            mock_client.get_service_health_metrics.return_value = {
                'overall_status': 'All Systems Operational',
                'last_updated': '2025-01-01 12:00:00',
                'availability_percentage': 100.0,
                'status_indicator': 'operational',
                'total_services': 10,
                'operational_services': 10,
                'services_with_issues': 0
            }
            mock_get_client.return_value = mock_client
            
            with app.test_client() as client:
                response = client.get('/')
                assert response.status_code == 200
                assert b'Red Hat Service Status' in response.data
                assert b'All Systems Operational' in response.data
                
        except ImportError as e:
            pytest.skip(f"Web module dependencies not available: {e}")
    
    @patch('redhat_status.web.app.fetch_status_data')
    @patch('redhat_status.web.app.get_api_client')
    def test_index_route_error(self, mock_get_client, mock_fetch_data):
        """Test index route with API error"""
        try:
            from redhat_status.web.app import app
            from redhat_status.core.data_models import APIResponse
            
            # Mock failed API response
            mock_response = APIResponse(
                success=False,
                data=None,
                error_message="API Error",
                response_time=2.0,
                status_code=500
            )
            mock_fetch_data.return_value = mock_response
            
            with app.test_client() as client:
                response = client.get('/')
                assert response.status_code == 200
                assert b'Error' in response.data
                assert b'API Error' in response.data
                
        except ImportError as e:
            pytest.skip(f"Web module dependencies not available: {e}")
    
    def test_run_web_server_function(self):
        """Test that run_web_server function exists and is callable"""
        try:
            from redhat_status.web.app import run_web_server
            assert callable(run_web_server)
        except ImportError as e:
            pytest.skip(f"Web module not available: {e}")
    
    def test_get_current_time_function(self):
        """Test get_current_time utility function"""
        try:
            from redhat_status.web.app import get_current_time
            time_str = get_current_time()
            assert isinstance(time_str, str)
            assert len(time_str) == 19  # YYYY-MM-DD HH:MM:SS format
            assert '-' in time_str and ':' in time_str
        except ImportError as e:
            pytest.skip(f"Web module not available: {e}")


class TestWebAppConfiguration:
    """Test web app configuration aspects"""
    
    def test_flask_app_configuration(self):
        """Test Flask app basic configuration"""
        try:
            from redhat_status.web.app import app
            
            # Test basic Flask app properties
            assert app.name == 'redhat_status.web.app'
            assert hasattr(app, 'route')
            assert hasattr(app, 'test_client')
            
        except ImportError as e:
            pytest.skip(f"Web module not available: {e}")
    
    def test_html_template_exists(self):
        """Test that HTML template is defined"""
        try:
            from redhat_status.web.app import HTML_TEMPLATE
            assert isinstance(HTML_TEMPLATE, str)
            assert 'Red Hat Status' in HTML_TEMPLATE
            assert '<html' in HTML_TEMPLATE
            assert '</html>' in HTML_TEMPLATE
        except ImportError as e:
            pytest.skip(f"Web module not available: {e}")


class TestWebAppIntegration:
    """Test web app integration with other modules"""
    
    @patch('redhat_status.core.api_client.get_api_client')
    def test_web_app_api_client_integration(self, mock_get_client):
        """Test web app integration with API client"""
        try:
            from redhat_status.web.app import app
            
            # Test that the app can get an API client
            mock_client = Mock()
            mock_get_client.return_value = mock_client
            
            with app.app_context():
                from redhat_status.web.app import get_api_client
                client = get_api_client()
                assert client is not None
                
        except ImportError as e:
            pytest.skip(f"Web module dependencies not available: {e}")

"""
Red Hat Status Checker - API Client

This module handles all communication with the Red Hat Status API,
including data fetching, error handling, and response processing.

Author: Red Hat Status Checker v3.1.0 - Modular Edition
"""

import requests
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from redhat_status.core.data_models import APIResponse
from redhat_status.utils.decorators import performance_monitor, retry_on_failure
from redhat_status.config.config_manager import get_config


class RedHatAPIClient:
    """Client for Red Hat Status API communication"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize API client with configuration"""
        if config:
            self.config = config
        else:
            self.config = get_config()
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create configured requests session with retries"""
        session = requests.Session()
        
        # Configure retry strategy
        max_retries = self._get_config_value('api', 'max_retries', 3)
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'User-Agent': 'RedHat-Status-Checker/3.1.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        })
        
        return session
    
    def _get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """Helper to get configuration values from either dict or ConfigManager"""
        if hasattr(self.config, 'get') and hasattr(self.config.get, '__code__') and self.config.get.__code__.co_argcount > 2:
            # It's a ConfigManager with get(section, key, default) method
            return self.config.get(section, key, default)
        else:
            # It's a dictionary, use simple key lookup for test compatibility
            if isinstance(self.config, dict):
                # For API tests, look for direct keys
                key_mapping = {
                    'url': 'base_url',
                    'base_url': 'base_url',  # Allow both keys
                    'timeout': 'timeout', 
                    'max_retries': 'retries'
                }
                mapped_key = key_mapping.get(key, key)
                return self.config.get(mapped_key, default)
            return default
    
    @performance_monitor
    def fetch_status_data(self, use_cache: bool = True) -> APIResponse:
        """Fetch status data from Red Hat API
        
        Args:
            use_cache: Whether to use cached data if available
            
        Returns:
            APIResponse object with data and metadata
        """
        # Check cache first if enabled
        if use_cache:
            cached_response = self._get_cached_response()
            if cached_response:
                return cached_response
        
        # Fetch fresh data from API
        return self._fetch_fresh_data()
    
    def _get_cached_response(self) -> Optional[APIResponse]:
        """Get cached response if available and valid"""
        try:
            from redhat_status.core.cache_manager import get_cache_manager
            cache_manager = get_cache_manager()
            
            if cache_manager.is_enabled():
                cached_data = cache_manager.get("summary_data")
                if cached_data:
                    logging.info("Using cached data")
                    return APIResponse(
                        success=True,
                        data=cached_data,
                        error_message=None,
                        response_time=0.0,
                        status_code=200,
                        timestamp=datetime.now()
                    )
        except Exception as e:
            logging.warning(f"Failed to load from cache: {e}")
        
        return None
    
    def _fetch_fresh_data(self) -> APIResponse:
        """Fetch fresh data from API with retry logic"""
        start_time = time.time()
        
        max_retries = self._get_config_value('api', 'max_retries', 3)
        api_url = self._get_config_value('api', 'url', 'https://status.redhat.com/api/v2/summary.json')  
        api_timeout = self._get_config_value('api', 'timeout', 30)
        retry_delay = self._get_config_value('api', 'retry_delay', 1)
        
        for attempt in range(max_retries + 1):
            try:
                logging.info(f"Fetching Red Hat Status data (attempt {attempt + 1}/{max_retries + 1})")
                
                response = self.session.get(
                    api_url,
                    timeout=api_timeout
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Cache the successful response (with original data)
                    self._cache_response(data)
                    
                    # Store in database if enabled
                    self._store_in_database(data)
                    
                    logging.info(f"Data fetched successfully in {response_time:.2f}s")
                    
                    return APIResponse(
                        success=True,
                        data=data,
                        error_message=None,
                        response_time=response_time,
                        status_code=response.status_code,
                        timestamp=datetime.now()
                    )
                
                else:
                    error_msg = f"HTTP {response.status_code}: {response.reason}"
                    logging.warning(error_msg)
                    
                    if attempt < max_retries:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    
                    return APIResponse(
                        success=False,
                        data=None,
                        error_message=error_msg,
                        response_time=time.time() - start_time,
                        status_code=response.status_code,
                        timestamp=datetime.now()
                    )
                    
            except requests.exceptions.Timeout:
                error_msg = f"Request timeout after {api_timeout}s"
                logging.warning(f"{error_msg} (attempt {attempt + 1})")
                
                if attempt < max_retries:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                
                return APIResponse(
                    success=False,
                    data=None,
                    error_message=error_msg,
                    response_time=time.time() - start_time,
                    status_code=408,  # Request Timeout
                    timestamp=datetime.now()
                )
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Network error: {str(e)}"
                logging.warning(f"{error_msg} (attempt {attempt + 1})")
                
                if attempt < max_retries:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                
                return APIResponse(
                    success=False,
                    data=None,
                    error_message=error_msg,
                    response_time=time.time() - start_time,
                    status_code=0,  # Connection error
                    timestamp=datetime.now()
                )
            
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                logging.error(error_msg)
                
                return APIResponse(
                    success=False,
                    data=None,
                    error_message=error_msg,
                    response_time=time.time() - start_time,
                    status_code=500,  # Internal error
                    timestamp=datetime.now()
                )
        
        # Should not reach here, but just in case
        return APIResponse(
            success=False,
            data=None,
            error_message="Max retries exceeded",
            response_time=time.time() - start_time,
            status_code=503,
            timestamp=datetime.now()
        )
    
    def fetch_status(self, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Legacy method name for backward compatibility with tests
        
        Args:
            use_cache: Whether to use cached data if available
            
        Returns:
            Status data dictionary or None on error
        """
        response = self.fetch_status_data(use_cache)
        return response.data if response.success else None
    
    def fetch_component_details(self, component_id: str) -> Optional[Dict[str, Any]]:
        """Fetch details for a specific component
        
        Args:
            component_id: ID of the component to fetch
            
        Returns:
            Component details dictionary or None on error
        """
        # For now, return mock data since Red Hat doesn't have component-specific endpoints
        if self.fetch_status():
            return {
                "id": component_id,
                "name": f"Component {component_id}",
                "status": "operational",
                "updated_at": datetime.now().isoformat()
            }
        return None
    
    def fetch_incidents(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch current incidents
        
        Returns:
            List of incidents or None on error
        """
        status_data = self.fetch_status()
        if status_data and 'incidents' in status_data:
            return status_data['incidents']
        return []
    
    def _build_url(self, endpoint: str = "", params: Optional[Dict[str, Any]] = None) -> str:
        """Build API URL with optional endpoint and parameters
        
        Args:
            endpoint: API endpoint to append
            params: URL parameters
            
        Returns:
            Complete URL string
        """
        # Get the full URL from config
        full_url = self._get_config_value('api', 'url', 'https://status.redhat.com/api/v2/summary.json')
        
        # Extract base URL (scheme + netloc)
        if endpoint:
            from urllib.parse import urlparse
            parsed = urlparse(full_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        else:
            url = full_url
        
        if params:
            param_strings = [f"{k}={v}" for k, v in params.items()]
            url += "?" + "&".join(param_strings)
            
        return url
    
    @property
    def base_url(self) -> str:
        """Get base URL for API requests"""
        full_url = self._get_config_value('api', 'url', 'https://status.redhat.com/api/v2/summary.json')
        if full_url and '://' in full_url:
            from urllib.parse import urlparse
            parsed = urlparse(full_url)
            return f"{parsed.scheme}://{parsed.netloc}"
        return self._get_config_value('api', 'base_url', 'https://status.redhat.com')
    
    @property
    def timeout(self) -> int:
        """Get request timeout"""
        return self._get_config_value('api', 'timeout', 10)
    
    @property
    def retries(self) -> int:
        """Get max retries"""
        return self._get_config_value('api', 'max_retries', 3)
    
    def _cache_response(self, data: Dict[str, Any]) -> None:
        """Cache successful response"""
        try:
            from redhat_status.core.cache_manager import get_cache_manager
            cache_manager = get_cache_manager()
            
            if cache_manager.is_enabled():
                cache_manager.set("summary_data", data)
                logging.debug("Response cached successfully")
        except Exception as e:
            logging.warning(f"Failed to cache response: {e}")
    
    def _store_in_database(self, data: Dict[str, Any]) -> None:
        """Store response in database for analysis"""
        try:
            from redhat_status.database.db_manager import get_database_manager
            db_manager = get_database_manager()
            
            if db_manager and db_manager.is_enabled():
                db_manager.store_status_history(data)
                logging.debug("Response stored in database")
        except Exception as e:
            logging.warning(f"Failed to store in database: {e}")
    
    def get_service_health_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract service health metrics from API response
        
        Args:
            data: API response data
            
        Returns:
            Dictionary with health metrics
        """
        if not data or 'components' not in data:
            return {}
        
        components = data['components']
        total_services = len(components)
        operational_services = sum(1 for comp in components if comp.get('status') == 'operational')
        
        # Calculate availability percentage
        availability_percentage = (operational_services / total_services * 100) if total_services > 0 else 0.0
        
        # Get overall status
        page_info = data.get('page', {})
        status_info = data.get('status', {})
        
        # Service breakdown by status
        status_breakdown = {}
        for component in components:
            status = component.get('status', 'unknown')
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        return {
            'availability_percentage': availability_percentage,
            'total_services': total_services,
            'operational_services': operational_services,
            'services_with_issues': total_services - operational_services,
            'status_breakdown': status_breakdown,
            'overall_status': status_info.get('description', 'Unknown'),
            'status_indicator': status_info.get('indicator', 'unknown'),
            'last_updated': page_info.get('updated_at', ''),
            'page_name': page_info.get('name', ''),
            'page_url': page_info.get('url', '')
        }
    
    def validate_response(self, data: Dict[str, Any]) -> bool:
        """Validate API response structure
        
        Args:
            data: API response data
            
        Returns:
            True if response is valid, False otherwise
        """
        required_fields = ['page', 'status', 'components']
        return all(field in data for field in required_fields)
    
    def close(self) -> None:
        """Close the HTTP session"""
        if self.session:
            self.session.close()


# Global API client instance
_api_client: Optional[RedHatAPIClient] = None


def get_api_client() -> RedHatAPIClient:
    """Get global API client instance"""
    global _api_client
    if _api_client is None:
        _api_client = RedHatAPIClient()
    return _api_client


def fetch_status_data(use_cache: bool = True) -> APIResponse:
    """Convenience function to fetch status data
    
    Args:
        use_cache: Whether to use cached data if available
        
    Returns:
        APIResponse object with data and metadata
    """
    client = get_api_client()
    return client.fetch_status_data(use_cache)


def get_service_health_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to extract health metrics
    
    Args:
        data: API response data
        
    Returns:
        Dictionary with health metrics
    """
    client = get_api_client()
    return client.get_service_health_metrics(data)

"""
Red Hat Status Checker - Modular Edition

A enterprise-grade Python monitoring solution for Red Hat services with 
advanced analytics, performance optimization, and professional monitoring capabilities.

This modular version provides:
- Improved code organization and maintainability
- Better separation of concerns
- Enhanced testing capabilities
- Cleaner API interfaces

Author: Red Hat Status Checker v3.1.0 - Modular Edition
Version: 3.1.0
"""

__version__ = "3.1.0"
__author__ = "Red Hat Status Checker Team"

# Import main components for easy access
from redhat_status.config.config_manager import get_config
from redhat_status.core.api_client import get_api_client, fetch_status_data
from redhat_status.core.data_models import (
    PerformanceMetrics, 
    ServiceHealthMetrics, 
    SystemAlert, 
    HealthReport
)

__all__ = [
    'get_config',
    'get_api_client', 
    'fetch_status_data',
    'PerformanceMetrics',
    'ServiceHealthMetrics', 
    'SystemAlert',
    'HealthReport'
]

"""
Red Hat Status Checker - Prometheus Exporter

This module provides a Prometheus exporter to expose health and
performance metrics for monitoring with a Prometheus-compatible stack.
"""

import threading
import time
from typing import Dict, Any, List

from prometheus_client import start_http_server, Gauge

# --- Metric Definitions ---

# It's a good practice to define metrics globally.
# This ensures they are registered only once.

GLOBAL_AVAILABILITY = Gauge(
    'redhat_status_global_availability_percentage',
    'Overall availability percentage of all Red Hat services'
)

SERVICES_OPERATIONAL = Gauge(
    'redhat_status_services_operational_total',
    'Total number of operational services'
)

SERVICES_WITH_ISSUES = Gauge(
    'redhat_status_services_with_issues_total',
    'Total number of services with issues (non-operational)'
)

SERVICE_STATUS = Gauge(
    'redhat_status_service_status',
    'Status of an individual Red Hat service (1=operational, 0=issue)',
    ['service_name', 'group_name']
)

CACHE_HIT_RATIO = Gauge(
    'redhat_status_cache_hit_ratio_percentage',
    'Cache hit ratio for the API client'
)

API_RESPONSE_TIME = Gauge(
    'redhat_status_api_response_time_seconds',
    'Response time for the Red Hat Status API'
)


def update_metrics(health_metrics: Dict[str, Any], components: List[Dict[str, Any]], perf_metrics: Dict[str, Any]) -> None:
    """
    Update the Prometheus gauges with the latest metrics.

    Args:
        health_metrics: A dictionary of global health metrics from the API client.
        components: A list of all service components from the API.
        perf_metrics: A dictionary of performance metrics.
    """
    GLOBAL_AVAILABILITY.set(health_metrics.get('availability_percentage', 0))
    SERVICES_OPERATIONAL.set(health_metrics.get('operational_services', 0))
    SERVICES_WITH_ISSUES.set(health_metrics.get('services_with_issues', 0))

    # Create a map of group IDs to names for easier lookup
    groups = {comp['id']: comp['name'] for comp in components if comp.get('group_id') is None}
    groups[None] = "Main Services" # For services without a group

    for component in components:
        service_name = component.get('name', 'Unknown')
        group_id = component.get('group_id')
        group_name = groups.get(group_id, "Unknown Group")

        status = 1 if component.get('status') == 'operational' else 0
        SERVICE_STATUS.labels(service_name=service_name, group_name=group_name).set(status)

    if perf_metrics:
        # Check for cache info in performance metrics
        cache_info = perf_metrics.get('cache_info')
        if cache_info:
            CACHE_HIT_RATIO.set(cache_info.get('hit_ratio', 0))

        # Check for API response time
        api_response_time = perf_metrics.get('api_response_time')
        if api_response_time:
            API_RESPONSE_TIME.set(api_response_time)


def start_exporter_http_server(port: int = 8000) -> None:
    """
    Starts the Prometheus metrics HTTP server in a daemon thread.
    This allows the main application to continue its execution.

    Args:
        port: The port to expose the /metrics endpoint on.
    """
    def run_server():
        # This function will run in the background
        start_http_server(port)
        # Keep the thread alive
        while True:
            time.sleep(1)

    # Start the server in a daemon thread so it doesn't block the main app
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    print(f"📈 Prometheus exporter started on http://localhost:{port}")

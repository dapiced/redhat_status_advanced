import pytest
from datetime import datetime, timedelta
from redhat_status.core.data_models import PerformanceMetrics

def test_performance_metrics_initialization():
    """Test that PerformanceMetrics initializes with correct default values."""
    start_time = datetime.now()
    metrics = PerformanceMetrics(start_time=start_time)

    assert metrics.start_time == start_time
    assert metrics.end_time is None
    assert metrics.api_calls == 0
    assert metrics.cache_hits == 0
    assert metrics.cache_misses == 0
    assert metrics.response_time == 0.0
    assert metrics.data_size == 0
    assert metrics.errors == []

def test_performance_metrics_duration():
    """Test the duration property calculates time correctly."""
    start_time = datetime.now() - timedelta(seconds=5)
    metrics = PerformanceMetrics(start_time=start_time)
    metrics.end_time = start_time + timedelta(seconds=5)

    assert metrics.duration == pytest.approx(5.0)

def test_performance_metrics_cache_hit_ratio():
    """Test the cache_hit_ratio property."""
    metrics = PerformanceMetrics(start_time=datetime.now())

    # Test with no cache activity
    assert metrics.cache_hit_ratio == 0.0

    # Test with some hits and misses
    metrics.cache_hits = 10
    metrics.cache_misses = 10
    assert metrics.cache_hit_ratio == 50.0

    # Test with only hits
    metrics.cache_hits = 20
    metrics.cache_misses = 0
    assert metrics.cache_hit_ratio == 100.0

    # Test with only misses
    metrics.cache_hits = 0
    metrics.cache_misses = 20
    assert metrics.cache_hit_ratio == 0.0

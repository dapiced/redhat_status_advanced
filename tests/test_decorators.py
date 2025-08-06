import pytest
import time
import tempfile
import os
import logging
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

# Add the project root to sys.path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redhat_status.utils.decorators import (
    performance_monitor, Timer, cache_result, retry_on_failure,
    log_execution, validate_input, singleton, deprecated
)


class TestPerformanceMonitor:
    """Test the performance_monitor decorator"""
    
    def test_performance_monitor_basic(self):
        """Test basic performance monitoring"""
        @performance_monitor
        def sample_function():
            time.sleep(0.1)  # Simulate some work
            return "result"
        
        result = sample_function()
        
        assert result == "result"
        # The decorator should work without errors
        assert callable(sample_function)
    
    def test_performance_monitor_with_exception(self):
        """Test performance monitoring when function raises exception"""
        @performance_monitor
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        # Function should still be callable
        assert callable(failing_function)
    
    def test_performance_monitor_multiple_calls(self):
        """Test performance monitoring across multiple calls"""
        @performance_monitor
        def multi_call_function(delay=0.01):
            time.sleep(delay)
            return "done"
        
        # Make multiple calls
        results = []
        for i in range(5):
            results.append(multi_call_function(0.01))
        
        assert all(r == "done" for r in results)
        assert callable(multi_call_function)
    
    def test_performance_monitor_with_arguments(self):
        """Test performance monitoring with function arguments"""
        @performance_monitor
        def function_with_args(x, y, keyword=None):
            return x + y + (keyword or 0)
        
        result = function_with_args(1, 2, keyword=3)
        
        assert result == 6
        assert callable(function_with_args)


class TestTimer:
    """Test the Timer class"""
    
    def test_timer_basic_usage(self):
        """Test basic timer usage"""
        with Timer() as timer:
            time.sleep(0.1)
        
        assert timer.duration > 0.09  # Should be at least 0.1 seconds
        assert timer.duration < 0.2   # Should be less than 0.2 seconds
    
    def test_timer_with_name(self):
        """Test timer with custom name"""
        with Timer("test_operation") as timer:
            time.sleep(0.05)
        
        assert timer.name == "test_operation"
        assert timer.duration > 0.04
    
    def test_timer_as_decorator(self):
        """Test timer used as decorator"""
        timer_instance = Timer("decorated_function")
        
        @timer_instance
        def timed_function():
            time.sleep(0.05)
            return "result"
        
        result = timed_function()
        
        assert result == "result"
        # The decorator should work correctly
    
    def test_timer_duration_property(self):
        """Test timer duration property"""
        timer = Timer()
        
        with timer:
            time.sleep(0.05)
        
        assert timer.duration > 0.04
        assert timer.duration < 0.1


class TestCacheResult:
    """Test the cache_result decorator"""
    
    def setup_method(self):
        """Set up test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.call_count = 0
    
    def test_cache_result_basic(self):
        """Test basic result caching"""
        @cache_result(ttl=60)
        def expensive_function(x):
            self.call_count += 1
            return x * 2
        
        # First call
        result1 = expensive_function(5)
        assert result1 == 10
        assert self.call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert self.call_count == 1  # Should not increment
    
    def test_cache_result_different_args(self):
        """Test caching with different arguments"""
        @cache_result(ttl=60)
        def cached_function(x, y=None):
            self.call_count += 1
            return x + (y or 0)
        
        # Different arguments should not use cached result
        result1 = cached_function(1, y=2)
        result2 = cached_function(1, y=3)
        result3 = cached_function(1, y=2)  # Same as first, should use cache
        
        assert result1 == 3
        assert result2 == 4
        assert result3 == 3
        assert self.call_count == 2  # Only two unique calls
    
    def test_cache_result_expiration(self):
        """Test cache expiration"""
        @cache_result(ttl=0.1)  # Very short TTL
        def short_cache_function(x):
            self.call_count += 1
            return x * 3
        
        # First call
        result1 = short_cache_function(2)
        assert result1 == 6
        assert self.call_count == 1
        
        # Wait for cache to expire
        time.sleep(0.2)
        
        # Second call should not use cache
        result2 = short_cache_function(2)
        assert result2 == 6
        assert self.call_count == 2
    
    def test_cache_result_disabled(self):
        """Test caching functionality - note: the actual decorator doesn't have 'enabled' parameter"""
        @cache_result(ttl=1)  # Very short TTL to test expiration
        def short_ttl_function(x):
            self.call_count += 1
            return x * 4
        
        # First call
        result1 = short_ttl_function(1)
        assert result1 == 4
        assert self.call_count == 1
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        # Second call should not use cache anymore
        result2 = short_ttl_function(1)
        assert result2 == 4
        assert self.call_count == 2


class TestRetryOnFailure:
    """Test the retry_on_failure decorator"""
    
    def setup_method(self):
        """Set up test method"""
        self.attempt_count = 0
    
    def test_retry_success_first_attempt(self):
        """Test successful function on first attempt"""
        @retry_on_failure(max_retries=3)
        def successful_function():
            self.attempt_count += 1
            return "success"
        
        result = successful_function()
        
        assert result == "success"
        assert self.attempt_count == 1
    
    def test_retry_success_after_failures(self):
        """Test successful function after some failures"""
        @retry_on_failure(max_retries=3)
        def eventually_successful_function():
            self.attempt_count += 1
            if self.attempt_count < 3:
                raise RuntimeError("Temporary failure")
            return "success"
        
        result = eventually_successful_function()
        
        assert result == "success"
        assert self.attempt_count == 3
    
    def test_retry_max_retries_exceeded(self):
        """Test when max retries are exceeded"""
        @retry_on_failure(max_retries=2)
        def always_failing_function():
            self.attempt_count += 1
            raise RuntimeError("Always fails")
        
        with pytest.raises(RuntimeError):
            always_failing_function()
        
        assert self.attempt_count == 3  # Initial + 2 retries
    
    def test_retry_with_delay(self):
        """Test retry with delay between attempts"""
        start_time = time.time()
        
        @retry_on_failure(max_retries=2, delay=0.1)
        def delayed_retry_function():
            self.attempt_count += 1
            if self.attempt_count < 3:
                raise RuntimeError("Temporary failure")
            return "success"
        
        result = delayed_retry_function()
        elapsed = time.time() - start_time
        
        assert result == "success"
        assert elapsed >= 0.2  # At least 2 * 0.1 seconds delay
    
    def test_retry_specific_exceptions(self):
        """Test retry functionality - note: actual decorator retries all exceptions"""
        @retry_on_failure(max_retries=2)
        def specific_exception_function():
            self.attempt_count += 1
            if self.attempt_count == 1:
                raise ValueError("Retryable error")
            elif self.attempt_count == 2:
                raise RuntimeError("Another error")
            return "success"
        
        result = specific_exception_function()
        assert result == "success"
        assert self.attempt_count == 3  # Should retry both exceptions


class TestValidateInput:
    """Test the validate_input decorator"""
    
    def test_validate_input_types(self):
        """Test input type validation"""
        def is_int(value):
            try:
                int(value)
                return True
            except (ValueError, TypeError):
                return False
        
        def is_str(value):
            return isinstance(value, str)
        
        @validate_input(x=is_int, y=is_str)
        def typed_function(x, y):
            return f"{x}_{y}"
        
        # Valid inputs
        result = typed_function(42, "hello")
        assert result == "42_hello"
        
        # Invalid type should raise error
        with pytest.raises(ValueError):
            typed_function("not_int", "hello")
    
    def test_validate_input_custom_validator(self):
        """Test custom input validation"""
        def positive_validator(value):
            return value > 0
        
        @validate_input(x=positive_validator)
        def positive_function(x):
            return x * 2
        
        # Valid input
        result = positive_function(5)
        assert result == 10
        
        # Invalid input
        with pytest.raises(ValueError):
            positive_function(-1)
    
    def test_validate_input_optional_parameters(self):
        """Test validation with optional parameters"""
        @validate_input(x=int, y=str)
        def optional_param_function(x, y="default"):
            return f"{x}_{y}"
        
        # Should work with default parameter
        result = optional_param_function(42)
        assert result == "42_default"
        
        # Should work with provided parameter
        result = optional_param_function(42, "custom")
        assert result == "42_custom"


class TestSingleton:
    """Test the singleton decorator"""
    
    def test_singleton_behavior(self):
        """Test that singleton ensures single instance"""
        @singleton
        class TestSingletonClass:
            def __init__(self):
                self.value = "test"
        
        instance1 = TestSingletonClass()
        instance2 = TestSingletonClass()
        
        assert instance1 is instance2
        assert instance1.value == instance2.value


class TestDeprecated:
    """Test the deprecated decorator"""
    
    def test_deprecated_warning(self):
        """Test that deprecated decorator issues warning"""
        @deprecated("This function is old")
        def old_function():
            return "result"
        
        with pytest.warns(DeprecationWarning):
            result = old_function()
        
        assert result == "result"


class TestDecoratorIntegration:
    """Test combinations of decorators"""
    
    def setup_method(self):
        """Set up test method"""
        self.call_count = 0
    
    def test_multiple_decorators(self):
        """Test function with multiple decorators"""
        @performance_monitor
        @cache_result(ttl=60)
        @retry_on_failure(max_retries=2)
        def multi_decorated_function(x):
            self.call_count += 1
            if self.call_count == 1 and x == 1:
                raise RuntimeError("First attempt fails")
            return x * 2
        
        # Should retry and then cache the result
        result1 = multi_decorated_function(1)
        result2 = multi_decorated_function(1)  # Should use cache
        
        assert result1 == 2
        assert result2 == 2
        assert self.call_count == 2  # One failure + one success


if __name__ == '__main__':
    pytest.main([__file__])

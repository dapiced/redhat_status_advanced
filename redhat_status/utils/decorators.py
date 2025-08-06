"""
Red Hat Status Checker - Performance Decorators and Utilities

This module provides decorators and utility functions for performance
monitoring, timing, and system optimization.

Author: Red Hat Status Checker v3.1.0 - Modular Edition
"""

import time
import logging
from functools import wraps
from contextlib import contextmanager
from typing import Any, Callable, Optional


def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance and track metrics
    
    Args:
        func: Function to monitor
        
    Returns:
        Wrapped function with performance monitoring
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Import here to avoid circular imports
        from redhat_status.config.config_manager import get_config
        from redhat_status.core.data_models import PerformanceMetrics
        
        config = get_config()
        if not config.get('performance', 'enable_metrics', True):
            return func(*args, **kwargs)
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            # Track successful API calls
            if hasattr(wrapper, '_performance_tracker'):
                wrapper._performance_tracker.api_calls += 1
            return result
        except Exception as e:
            # Track errors
            if hasattr(wrapper, '_performance_tracker'):
                wrapper._performance_tracker.errors.append(f"{func.__name__}: {str(e)}")
            raise
        finally:
            if config.get('performance', 'detailed_timing', False):
                duration = time.time() - start_time
                logging.debug(f"{func.__name__} executed in {duration:.3f}s")
    
    return wrapper


@contextmanager
def performance_context(operation_name: str):
    """Context manager for performance tracking of code blocks
    
    Args:
        operation_name: Name of the operation being tracked
        
    Example:
        with performance_context("API request"):
            response = requests.get(url)
    """
    start_time = time.time()
    try:
        yield
    finally:
        from redhat_status.config.config_manager import get_config
        config = get_config()
        if config.get('performance', 'detailed_timing', False):
            duration = time.time() - start_time
            logging.info(f"{operation_name} completed in {duration:.3f}s")


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, exponential_backoff: bool = True):
    """Decorator to retry function on failure with configurable parameters
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        exponential_backoff: Whether to use exponential backoff
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                        time.sleep(current_delay)
                        if exponential_backoff:
                            current_delay *= 2
                    else:
                        logging.error(f"{func.__name__} failed after {max_retries + 1} attempts")
            
            raise last_exception
        
        return wrapper
    return decorator


def cache_result(ttl: int = 300):
    """Simple function result caching decorator
    
    Args:
        ttl: Time to live in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_times = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            current_time = time.time()
            
            # Check if we have a valid cached result
            if (cache_key in cache and 
                cache_key in cache_times and 
                current_time - cache_times[cache_key] < ttl):
                return cache[cache_key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = result
            cache_times[cache_key] = current_time
            
            return result
        
        # Add cache management methods
        wrapper.clear_cache = lambda: cache.clear() or cache_times.clear()
        wrapper.cache_info = lambda: {
            'size': len(cache),
            'keys': list(cache.keys())
        }
        
        return wrapper
    return decorator


def log_execution(level: int = logging.INFO, include_args: bool = False):
    """Decorator to log function execution
    
    Args:
        level: Logging level to use
        include_args: Whether to include function arguments in log
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if include_args:
                logging.log(level, f"Executing {func.__name__} with args={args}, kwargs={kwargs}")
            else:
                logging.log(level, f"Executing {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                logging.log(level, f"Successfully executed {func.__name__}")
                return result
            except Exception as e:
                logging.error(f"Error in {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator


def validate_input(**validators):
    """Decorator to validate function input parameters
    
    Args:
        **validators: Mapping of parameter names to validation functions
        
    Returns:
        Decorator function
        
    Example:
        @validate_input(url=lambda x: x.startswith('https://'))
        def fetch_data(url):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature for parameter mapping
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each parameter
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(f"Invalid value for parameter '{param_name}': {value}")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def singleton(cls):
    """Decorator to create singleton classes
    
    Args:
        cls: Class to make singleton
        
    Returns:
        Singleton class
    """
    instances = {}
    
    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


def deprecated(reason: str = "This function is deprecated"):
    """Decorator to mark functions as deprecated
    
    Args:
        reason: Reason for deprecation
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import warnings
            warnings.warn(
                f"{func.__name__} is deprecated: {reason}",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class Timer:
    """Context manager and decorator for timing operations"""
    
    def __init__(self, name: str = "Operation", log_result: bool = True):
        self.name = name
        self.log_result = log_result
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        if self.log_result:
            duration = self.duration
            logging.info(f"{self.name} completed in {duration:.3f}s")
    
    @property
    def duration(self) -> float:
        """Get operation duration in seconds"""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time
    
    def __call__(self, func: Callable) -> Callable:
        """Use as decorator"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            with Timer(f"{self.name or func.__name__}", self.log_result):
                return func(*args, **kwargs)
        return wrapper


def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 2.0, initial_delay: float = 1.0):
    """Decorator to retry function on failure with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for delay between retries
        initial_delay: Initial delay in seconds
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = initial_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logging.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            # If we get here, all retries failed
            raise last_exception
        return wrapper
    return decorator

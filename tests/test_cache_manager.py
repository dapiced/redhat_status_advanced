"""
Test suite for cache manager module.
"""
import pytest
import tempfile
import json
import os
import shutil
import time
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add the project root to sys.path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redhat_status.core.cache_manager import CacheManager, get_cache_manager


class TestCacheManager:
    """Test the CacheManager class"""
    
    def setup_method(self):
        """Set up test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, 'cache')
        self.config = {
            'enabled': True,
            'ttl': 300,  # 5 minutes
            'cache_dir': self.cache_dir,
            'max_size': 100,
            'compression': True
        }
        self.cache_manager = CacheManager(self.config)
    
    def teardown_method(self):
        """Clean up after test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_creates_cache_directory(self):
        """Test that initialization creates cache directory"""
        assert os.path.exists(self.cache_dir)
    
    def test_init_disabled_cache(self):
        """Test initialization with disabled cache"""
        config = {'enabled': False}
        cache_manager = CacheManager(config)
        
        assert cache_manager.enabled is False
    
    def test_set_and_get_cache_item(self):
        """Test setting and getting a cache item"""
        key = 'test_key'
        data = {'test': 'data', 'number': 123}
        
        # Set cache item
        self.cache_manager.set(key, data)
        
        # Get cache item
        retrieved_data = self.cache_manager.get(key)
        
        assert retrieved_data == data
    
    def test_get_nonexistent_item(self):
        """Test getting a non-existent cache item"""
        result = self.cache_manager.get('nonexistent_key')
        
        assert result is None
    
    def test_cache_expiration(self):
        """Test cache item expiration"""
        key = 'expiring_key'
        data = {'test': 'data'}
        
        # Set cache with short TTL
        short_ttl_config = self.config.copy()
        short_ttl_config['ttl'] = 1  # 1 second
        cache_manager = CacheManager(short_ttl_config)
        
        cache_manager.set(key, data)
        
        # Should be available immediately
        assert cache_manager.get(key) == data
        
        # Wait for expiration
        time.sleep(2)
        
        # Should be expired
        assert cache_manager.get(key) is None
    
    def test_has_valid_cache(self):
        """Test checking for valid cache"""
        key = 'valid_key'
        data = {'test': 'data'}
        
        # No cache initially
        assert self.cache_manager.has_valid_cache(key) is False
        
        # Set cache
        self.cache_manager.set(key, data)
        
        # Should have valid cache
        assert self.cache_manager.has_valid_cache(key) is True
    
    def test_delete_cache_item(self):
        """Test deleting a cache item"""
        key = 'delete_key'
        data = {'test': 'data'}
        
        # Set cache
        self.cache_manager.set(key, data)
        assert self.cache_manager.get(key) == data
        
        # Delete cache
        self.cache_manager.delete(key)
        assert self.cache_manager.get(key) is None
    
    def test_clear_all_cache(self):
        """Test clearing all cache"""
        # Set multiple cache items
        self.cache_manager.set('key1', {'data': 1})
        self.cache_manager.set('key2', {'data': 2})
        self.cache_manager.set('key3', {'data': 3})
        
        # Verify they exist
        assert self.cache_manager.get('key1') is not None
        assert self.cache_manager.get('key2') is not None
        assert self.cache_manager.get('key3') is not None
        
        # Clear all cache
        cleared_count = self.cache_manager.clear()
        
        # Verify they are gone
        assert self.cache_manager.get('key1') is None
        assert self.cache_manager.get('key2') is None
        assert self.cache_manager.get('key3') is None
        assert cleared_count == 3
    
    def test_cache_size_limit(self):
        """Test cache size limiting"""
        # Set config with small max size
        small_config = self.config.copy()
        small_config['max_size'] = 2
        cache_manager = CacheManager(small_config)
        
        # Add items beyond limit
        cache_manager.set('key1', {'data': 1})
        cache_manager.set('key2', {'data': 2})
        cache_manager.set('key3', {'data': 3})  # Should evict oldest
        
        # First item should be evicted
        assert cache_manager.get('key1') is None
        assert cache_manager.get('key2') is not None
        assert cache_manager.get('key3') is not None
    
    def test_compression(self):
        """Test data compression"""
        key = 'compression_key'
        large_data = {'large_text': 'x' * 1000}  # Large data to compress
        
        self.cache_manager.set(key, large_data)
        retrieved_data = self.cache_manager.get(key)
        
        assert retrieved_data == large_data
        
        # Check that file is smaller than uncompressed JSON
        cache_file = os.path.join(self.cache_dir, f"{key}.cache")
        assert os.path.exists(cache_file)
        
        # File should be smaller due to compression
        file_size = os.path.getsize(cache_file)
        uncompressed_size = len(json.dumps(large_data))
        assert file_size < uncompressed_size
    
    def test_disabled_cache_operations(self):
        """Test operations when cache is disabled"""
        config = {'enabled': False}
        cache_manager = CacheManager(config)
        
        # All operations should be no-ops
        cache_manager.set('key', {'data': 'test'})
        assert cache_manager.get('key') is None
        assert cache_manager.has_valid_cache('key') is False
        assert cache_manager.clear() == 0
    
    def test_get_cache_stats(self):
        """Test getting cache statistics"""
        # Set some cache items
        self.cache_manager.set('key1', {'data': 1})
        self.cache_manager.set('key2', {'data': 2})
        
        # Get some items (cache hits)
        self.cache_manager.get('key1')
        self.cache_manager.get('key1')  # Another hit
        self.cache_manager.get('nonexistent')  # Cache miss
        
        stats = self.cache_manager.get_stats()
        
        assert 'total_items' in stats
        assert 'cache_hits' in stats
        assert 'cache_misses' in stats
        assert stats['total_items'] == 2
        assert stats['cache_hits'] == 2
        assert stats['cache_misses'] == 1
    
    def test_cache_key_sanitization(self):
        """Test that cache keys are properly sanitized"""
        # Test with key containing invalid characters
        key = 'key/with\\special:characters?'
        data = {'test': 'data'}
        
        self.cache_manager.set(key, data)
        retrieved_data = self.cache_manager.get(key)
        
        assert retrieved_data == data
    
    def test_corrupted_cache_file_handling(self):
        """Test handling of corrupted cache files"""
        key = 'corrupted_key'
        
        # Create a corrupted cache file
        cache_file = os.path.join(self.cache_dir, f"{key}.cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        with open(cache_file, 'wb') as f:
            f.write(b'corrupted data that is not valid')
        
        # Should return None for corrupted cache
        result = self.cache_manager.get(key)
        assert result is None
    
    def test_cleanup_expired_items(self):
        """Test cleanup of expired cache items"""
        # Set items with different expiration times
        short_config = self.config.copy()
        short_config['ttl'] = 1  # 1 second
        cache_manager = CacheManager(short_config)
        
        cache_manager.set('key1', {'data': 1})
        time.sleep(0.5)  # Wait half the TTL
        cache_manager.set('key2', {'data': 2})
        
        # Wait for first item to expire
        time.sleep(1)
        
        # Cleanup expired items
        cache_manager._cleanup_expired()
        
        # First item should be gone, second should remain
        assert cache_manager.get('key1') is None
        assert cache_manager.get('key2') is not None
    
    def test_cache_file_permissions(self):
        """Test that cache files have correct permissions"""
        key = 'permissions_key'
        data = {'test': 'data'}
        
        self.cache_manager.set(key, data)
        
        cache_file = os.path.join(self.cache_dir, f"{key}.cache")
        file_stat = os.stat(cache_file)
        
        # Check that file is readable and writable by owner
        assert file_stat.st_mode & 0o600


class TestGetCacheManagerFunction:
    """Test the get_cache_manager function"""
    
    def test_get_cache_manager_singleton(self):
        """Test that get_cache_manager returns the same instance"""
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        
        assert manager1 is manager2
    
    @patch('redhat_status.core.cache_manager.CacheManager')
    def test_get_cache_manager_creates_instance(self, mock_cache_manager):
        """Test that get_cache_manager creates a CacheManager instance"""
        mock_instance = Mock()
        mock_cache_manager.return_value = mock_instance
        
        # Clear any existing singleton
        import redhat_status.core.cache_manager as cache_module
        cache_module._cache_manager_instance = None
        
        result = get_cache_manager()
        
        mock_cache_manager.assert_called_once()
        assert result == mock_instance


class TestCacheManagerConfiguration:
    """Test cache manager configuration handling"""
    
    def setup_method(self):
        """Set up test method"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up after test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_default_configuration(self):
        """Test default configuration values"""
        cache_manager = CacheManager()
        
        assert cache_manager.enabled is True
        assert cache_manager.ttl > 0
        assert cache_manager.max_size > 0
        assert cache_manager.compression is True
    
    def test_custom_configuration(self):
        """Test custom configuration values"""
        config = {
            'enabled': False,
            'ttl': 600,
            'max_size': 50,
            'compression': False,
            'cache_dir': self.temp_dir
        }
        
        cache_manager = CacheManager(config)
        
        assert cache_manager.enabled is False
        assert cache_manager.ttl == 600
        assert cache_manager.max_size == 50
        assert cache_manager.compression is False
    
    def test_invalid_configuration_fallback(self):
        """Test that invalid configuration falls back to defaults"""
        config = {
            'ttl': 'invalid',
            'max_size': 'invalid'
        }
        
        cache_manager = CacheManager(config)
        
        # Should use defaults for invalid values
        assert isinstance(cache_manager.ttl, int)
        assert isinstance(cache_manager.max_size, int)


class TestCacheManagerPerformance:
    """Test cache manager performance aspects"""
    
    def setup_method(self):
        """Set up test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'enabled': True,
            'ttl': 300,
            'cache_dir': os.path.join(self.temp_dir, 'cache'),
            'max_size': 1000
        }
        self.cache_manager = CacheManager(self.config)
    
    def teardown_method(self):
        """Clean up after test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_large_data_caching(self):
        """Test caching of large data structures"""
        key = 'large_data'
        large_data = {
            'items': [{'id': i, 'data': f'item_{i}' * 100} for i in range(1000)]
        }
        
        # Measure time to set and get
        start_time = time.time()
        self.cache_manager.set(key, large_data)
        set_time = time.time() - start_time
        
        start_time = time.time()
        retrieved_data = self.cache_manager.get(key)
        get_time = time.time() - start_time
        
        assert retrieved_data == large_data
        # Operations should be reasonably fast
        assert set_time < 1.0  # Less than 1 second
        assert get_time < 1.0  # Less than 1 second
    
    def test_concurrent_access(self):
        """Test concurrent access to cache"""
        import threading
        
        def cache_operations(thread_id):
            for i in range(10):
                key = f'thread_{thread_id}_item_{i}'
                data = {'thread': thread_id, 'item': i}
                self.cache_manager.set(key, data)
                retrieved = self.cache_manager.get(key)
                assert retrieved == data
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_operations, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify cache contains items from all threads
        stats = self.cache_manager.get_stats()
        assert stats['total_items'] == 50  # 5 threads * 10 items each


if __name__ == '__main__':
    pytest.main([__file__])

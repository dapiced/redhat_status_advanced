"""
Red Hat Status Checker - Cache Manager

This module handles all caching operations including:
- File-based caching with compression
- Cache validation and expiration
- Automatic cleanup and size management
- Performance optimization

Author: Red Hat Status Checker v3.1.0 - Modular Edition
"""

import json
import gzip
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from functools import lru_cache

from redhat_status.config.config_manager import get_config
from redhat_status.core.data_models import CacheInfo


class CacheManager:
    """Manages file-based caching with compression and cleanup"""
    
    def __init__(self):
        """Initialize cache manager with configuration"""
        self.config = get_config()
        self._setup_cache_directory()
    
    def _setup_cache_directory(self) -> None:
        """Create cache directory if it doesn't exist"""
        cache_dir = Path(self.config.get('cache', 'directory', '.cache'))
        cache_dir.mkdir(parents=True, exist_ok=True)
    
    def is_enabled(self) -> bool:
        """Check if caching is enabled"""
        return self.config.get('cache', 'enabled', True)
    
    def get_cache_file(self, cache_key: str) -> Path:
        """Get cache file path for a given key
        
        Args:
            cache_key: Unique cache key
            
        Returns:
            Path to cache file
        """
        cache_dir = Path(self.config.get('cache', 'directory', '.cache'))
        
        # Create safe filename from cache key
        safe_key = hashlib.md5(cache_key.encode()).hexdigest()
        extension = '.json.gz' if self.config.get('cache', 'compression', True) else '.json'
        
        return cache_dir / f"{safe_key}{extension}"
    
    def is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file is valid and not expired
        
        Args:
            cache_file: Path to cache file
            
        Returns:
            True if cache is valid, False otherwise
        """
        if not cache_file.exists():
            return False
        
        try:
            file_age = datetime.now().timestamp() - cache_file.stat().st_mtime
            ttl = self.config.get('cache', 'ttl', 300)
            return file_age < ttl
        except Exception as e:
            logging.warning(f"Cache validation error: {e}")
            return False
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache
        
        Args:
            cache_key: Unique cache key
            
        Returns:
            Cached data or None if not available/expired
        """
        if not self.is_enabled():
            return None
        
        cache_file = self.get_cache_file(cache_key)
        
        if not self.is_cache_valid(cache_file):
            return None
        
        try:
            if cache_file.suffix == '.gz':
                with gzip.open(cache_file, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with cache_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Add cache metadata
            data['_metadata'] = data.get('_metadata', {})
            data['_metadata']['cached'] = True
            data['_metadata']['cache_file'] = str(cache_file)
            
            logging.debug(f"Cache hit for key: {cache_key}")
            return data
            
        except Exception as e:
            logging.warning(f"Failed to load from cache: {e}")
            # Remove corrupted cache file
            try:
                cache_file.unlink()
            except:
                pass
            return None
    
    def set(self, cache_key: str, data: Dict[str, Any]) -> bool:
        """Save data to cache
        
        Args:
            cache_key: Unique cache key
            data: Data to cache
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False
        
        cache_file = self.get_cache_file(cache_key)
        
        try:
            # Ensure directory exists
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Remove cache metadata before saving
            save_data = data.copy()
            if '_metadata' in save_data:
                metadata = save_data['_metadata'].copy()
                metadata.pop('cached', None)
                metadata.pop('cache_file', None)
                save_data['_metadata'] = metadata
            
            if self.config.get('cache', 'compression', True):
                with gzip.open(cache_file, 'wt', encoding='utf-8') as f:
                    json.dump(save_data, f, separators=(',', ':'))
            else:
                with cache_file.open('w', encoding='utf-8') as f:
                    json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            logging.debug(f"Data cached for key: {cache_key}")
            
            # Perform cleanup if needed
            self._check_and_cleanup()
            
            return True
            
        except Exception as e:
            logging.warning(f"Failed to save to cache: {e}")
            return False
    
    def delete(self, cache_key: str) -> bool:
        """Delete cache entry
        
        Args:
            cache_key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        cache_file = self.get_cache_file(cache_key)
        
        try:
            if cache_file.exists():
                cache_file.unlink()
                logging.debug(f"Cache entry deleted: {cache_key}")
                return True
            return False
        except Exception as e:
            logging.warning(f"Failed to delete cache entry: {e}")
            return False
    
    def clear(self) -> int:
        """Clear all cache entries
        
        Returns:
            Number of files deleted
        """
        cache_dir = Path(self.config.get('cache', 'directory', '.cache'))
        
        if not cache_dir.exists():
            return 0
        
        deleted_count = 0
        
        try:
            for cache_file in cache_dir.rglob("*.json*"):
                cache_file.unlink()
                deleted_count += 1
            
            logging.info(f"Cache cleared: {deleted_count} files deleted")
            return deleted_count
            
        except Exception as e:
            logging.error(f"Failed to clear cache: {e}")
            return deleted_count
    
    def get_cache_info(self) -> CacheInfo:
        """Get cache information and statistics
        
        Returns:
            CacheInfo object with cache statistics
        """
        cache_dir = Path(self.config.get('cache', 'directory', '.cache'))
        
        if not cache_dir.exists():
            return CacheInfo(
                enabled=self.is_enabled(),
                size_bytes=0,
                hit_ratio=0.0,
                entries_count=0,
                ttl_seconds=self.config.get('cache', 'ttl', 300),
                compression_enabled=self.config.get('cache', 'compression', True),
                last_cleanup=datetime.now()
            )
        
        # Calculate cache statistics
        total_size = 0
        entries_count = 0
        
        try:
            for cache_file in cache_dir.rglob("*.json*"):
                total_size += cache_file.stat().st_size
                entries_count += 1
        except Exception as e:
            logging.warning(f"Failed to calculate cache stats: {e}")
        
        return CacheInfo(
            enabled=self.is_enabled(),
            size_bytes=total_size,
            hit_ratio=0.0,  # Would need tracking to calculate
            entries_count=entries_count,
            ttl_seconds=self.config.get('cache', 'ttl', 300),
            compression_enabled=self.config.get('cache', 'compression', True),
            last_cleanup=datetime.now()
        )
    
    def _check_and_cleanup(self) -> None:
        """Check cache size and perform cleanup if needed"""
        try:
            cache_info = self.get_cache_info()
            max_size_mb = self.config.get('cache', 'max_size_mb', 100)
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if cache_info.size_bytes <= max_size_bytes:
                return
            
            # Perform cleanup
            self._cleanup_old_entries()
            
        except Exception as e:
            logging.warning(f"Cache cleanup check failed: {e}")
    
    def _cleanup_old_entries(self) -> None:
        """Remove old cache entries to free space"""
        try:
            cache_dir = Path(self.config.get('cache', 'directory', '.cache'))
            cache_files = list(cache_dir.rglob("*.json*"))
            
            # Sort by modification time (oldest first)
            cache_files.sort(key=lambda x: x.stat().st_mtime)
            
            max_size_mb = self.config.get('cache', 'max_size_mb', 100)
            max_size_bytes = max_size_mb * 1024 * 1024
            
            current_size = sum(f.stat().st_size for f in cache_files)
            removed_count = 0
            
            for cache_file in cache_files:
                if current_size <= max_size_bytes:
                    break
                
                file_size = cache_file.stat().st_size
                cache_file.unlink()
                current_size -= file_size
                removed_count += 1
            
            if removed_count > 0:
                logging.info(f"Cache cleanup: removed {removed_count} old entries")
                
        except Exception as e:
            logging.warning(f"Cache cleanup failed: {e}")
    
    def cleanup_expired(self) -> int:
        """Remove expired cache entries
        
        Returns:
            Number of expired entries removed
        """
        cache_dir = Path(self.config.get('cache', 'directory', '.cache'))
        
        if not cache_dir.exists():
            return 0
        
        removed_count = 0
        ttl = self.config.get('cache', 'ttl', 300)
        current_time = datetime.now().timestamp()
        
        try:
            for cache_file in cache_dir.rglob("*.json*"):
                file_age = current_time - cache_file.stat().st_mtime
                if file_age > ttl:
                    cache_file.unlink()
                    removed_count += 1
            
            if removed_count > 0:
                logging.info(f"Removed {removed_count} expired cache entries")
            
            return removed_count
            
        except Exception as e:
            logging.error(f"Failed to cleanup expired cache: {e}")
            return removed_count


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


# Convenience functions
def cache_get(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get data from cache (convenience function)"""
    return get_cache_manager().get(cache_key)


def cache_set(cache_key: str, data: Dict[str, Any]) -> bool:
    """Save data to cache (convenience function)"""
    return get_cache_manager().set(cache_key, data)


def cache_delete(cache_key: str) -> bool:
    """Delete cache entry (convenience function)"""
    return get_cache_manager().delete(cache_key)


def cache_clear() -> int:
    """Clear all cache (convenience function)"""
    return get_cache_manager().clear()


@lru_cache(maxsize=32)
def get_service_health_score(status: str, last_update: str) -> float:
    """Calculate service health score based on status and update time
    
    Args:
        status: Service status string
        last_update: Last update timestamp
        
    Returns:
        Health score (0-100)
    """
    base_scores = {
        'operational': 100.0,
        'degraded_performance': 75.0,
        'partial_outage': 50.0,
        'major_outage': 25.0,
        'maintenance': 90.0
    }
    
    score = base_scores.get(status, 0.0)
    
    # Adjust based on last update time
    try:
        last_update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
        time_diff = datetime.now() - last_update_time.replace(tzinfo=None)
        hours_old = time_diff.total_seconds() / 3600
        
        # Reduce score if data is stale
        if hours_old > 24:
            score *= 0.8
        elif hours_old > 12:
            score *= 0.9
            
    except Exception:
        # If we can't parse time, apply penalty
        score *= 0.85
    
    return score

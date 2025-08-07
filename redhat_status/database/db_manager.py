"""
Red Hat Status Checker - Database Management Module

This module provides database operations for storing and retrieving
Red Hat service monitoring data, analytics results, and system insights.

Contains:
- DatabaseManager class for SQLite operations
- Data persistence and retrieval
- Database optimization and maintenance
- Backup and restore functionality
- Performance monitoring

Author: Red Hat Status Checker v3.1.0 - Modular Edition
"""

import json
import logging
import sqlite3
import threading
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import asdict
from typing import Dict, List, Optional, Any, Tuple

# Configure SQLite datetime adapters to avoid Python 3.12 deprecation warning
def _adapt_datetime_iso(val):
    """Adapt datetime to ISO format for SQLite storage"""
    return val.isoformat()

def _convert_datetime(val):
    """Convert ISO format string back to datetime"""
    return datetime.fromisoformat(val.decode())

# Register the adapters
sqlite3.register_adapter(datetime, _adapt_datetime_iso)
sqlite3.register_converter("datetime", _convert_datetime)

from ..core.data_models import (
    PerformanceMetrics, ServiceHealthMetrics, SystemAlert,
    AnomalyDetection, PredictiveInsight, AlertSeverity
)
from ..config.config_manager import get_config
from ..utils.decorators import performance_monitor, retry_with_backoff


# Convenience functions for easy access
_db_manager_instance = None

def get_database_manager() -> 'DatabaseManager':
    """Get singleton database manager instance"""
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager()
    return _db_manager_instance


class DatabaseManager:
    """
    Advanced Database Manager for Red Hat Status Checker
    
    Provides thread-safe database operations, data persistence,
    and optimization for SQLite-based storage.
    """
    
    def __init__(self, db_path: Optional[Union[str, Dict[str, Any]]] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize database manager
        
        Args:
            db_path: Database file path (string) or configuration dict for backward compatibility
            config: Optional configuration dictionary
        """
        self.config = config or get_config()
        
        # Handle both string path and config dict for backward compatibility with tests
        if isinstance(db_path, dict):
            # If db_path is actually a config dict, use it
            self.config = db_path
            self.db_path = db_path.get('path', self._get_config_value('database', 'path', 'redhat_status.db'))
        elif isinstance(db_path, str):
            self.db_path = db_path
        else:
            self.db_path = self._get_config_value('database', 'path', 'redhat_status.db')
            
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # Database configuration
        self.connection_timeout = self._get_config_value('database', 'connection_timeout', 30)
        self.journal_mode = self._get_config_value('database', 'journal_mode', 'WAL')
        self.synchronous = self._get_config_value('database', 'synchronous', 'NORMAL')
        self.cache_size = self._get_config_value('database', 'cache_size', 2000)
        
        # Performance metrics
        self._operation_count = 0
        self._total_execution_time = 0.0
        self._last_vacuum = None
        self._last_analyze = None
        
        # Initialize database
        try:
            self._init_database()
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            # Database will be considered disabled via is_enabled() method

    def _get_config_value(self, section: str, key: str, default: Any = None) -> Any:
        """Helper to get configuration values from either dict or ConfigManager"""
        if hasattr(self.config, 'get') and hasattr(self.config.get, '__code__') and self.config.get.__code__.co_argcount > 2:
            # It's a ConfigManager with get(section, key, default) method
            return self.config.get(section, key, default)
        else:
            # It's a dictionary, use direct key access
            if isinstance(self.config, dict):
                return self.config.get(key, default)
            return default
        self._init_database()
        
    def is_enabled(self) -> bool:
        """Check if database operations are enabled"""
        try:
            return (
                self._get_config_value('database', 'enabled', True) and 
                Path(self.db_path).parent.exists()
            )
        except Exception:
            return False
        
    def _init_database(self) -> None:
        """Initialize SQLite database with optimized settings"""
        try:
            # Ensure directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            with self._get_connection() as conn:
                # Configure SQLite for performance
                conn.execute(f'PRAGMA journal_mode = {self.journal_mode}')
                conn.execute(f'PRAGMA synchronous = {self.synchronous}')
                conn.execute(f'PRAGMA cache_size = -{self.cache_size}')
                conn.execute('PRAGMA foreign_keys = ON')
                conn.execute('PRAGMA temp_store = MEMORY')
                conn.execute('PRAGMA mmap_size = 268435456')  # 256MB
                
                # Create tables
                self._create_tables(conn)
                
                # Create indexes for performance
                self._create_indexes(conn)
                
            self.logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            # Let the database be disabled naturally through is_enabled() check
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with timeout and configuration"""
        conn = sqlite3.Connection(
            self.db_path,
            timeout=self.connection_timeout,
            check_same_thread=False
        )
        
        # Enable row factory for easier data access
        conn.row_factory = sqlite3.Row
        
        return conn
    
    def _create_tables(self, conn: sqlite3.Connection) -> None:
        """Create all necessary database tables"""
        conn.executescript('''
            -- Legacy tables for backward compatibility with tests
            CREATE TABLE IF NOT EXISTS status_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                overall_status TEXT NOT NULL,
                availability_percentage REAL DEFAULT 0.0,
                total_services INTEGER DEFAULT 0,
                operational_services INTEGER DEFAULT 0,
                response_time REAL DEFAULT 0.0,
                details TEXT
            );
            
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                description TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                impact TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME,
                description TEXT
            );
            
            -- Service status snapshots
            CREATE TABLE IF NOT EXISTS service_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                page_name TEXT NOT NULL,
                page_url TEXT,
                overall_status TEXT NOT NULL,
                status_indicator TEXT,
                last_updated DATETIME,
                total_services INTEGER DEFAULT 0,
                operational_services INTEGER DEFAULT 0,
                availability_percentage REAL DEFAULT 0.0,
                metadata TEXT,
                UNIQUE(timestamp, page_name)
            );
            
            -- Individual service metrics
            CREATE TABLE IF NOT EXISTS service_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                service_name TEXT NOT NULL,
                service_id TEXT,
                group_id TEXT,
                status TEXT NOT NULL,
                response_time REAL,
                availability_score REAL,
                performance_score REAL,
                is_main_service BOOLEAN DEFAULT 0,
                metadata TEXT,
                FOREIGN KEY (snapshot_id) REFERENCES service_snapshots(id) ON DELETE CASCADE
            );
            
            -- System alerts and notifications
            CREATE TABLE IF NOT EXISTS system_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT,
                source_service TEXT,
                acknowledged BOOLEAN DEFAULT 0,
                acknowledged_by TEXT,
                acknowledged_at DATETIME,
                resolved_at DATETIME,
                metadata TEXT
            );
            
            -- Performance metrics tracking
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                api_calls INTEGER DEFAULT 0,
                cache_hits INTEGER DEFAULT 0,
                cache_misses INTEGER DEFAULT 0,
                response_time REAL,
                data_size INTEGER,
                metadata TEXT
            );
            
            -- API response caching
            CREATE TABLE IF NOT EXISTS api_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                response_data TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                content_hash TEXT,
                size_bytes INTEGER DEFAULT 0,
                access_count INTEGER DEFAULT 1,
                last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Configuration history
            CREATE TABLE IF NOT EXISTS config_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                config_section TEXT NOT NULL,
                config_key TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_by TEXT,
                reason TEXT
            );
            
            -- Database maintenance log
            CREATE TABLE IF NOT EXISTS maintenance_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                operation_type TEXT NOT NULL,
                details TEXT,
                duration_seconds REAL,
                records_affected INTEGER DEFAULT 0,
                status TEXT DEFAULT 'completed'
            );
        ''')
    
    def _create_indexes(self, conn: sqlite3.Connection) -> None:
        """Create indexes for better query performance"""
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_service_snapshots_timestamp ON service_snapshots(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_service_snapshots_status ON service_snapshots(overall_status)',
            'CREATE INDEX IF NOT EXISTS idx_service_metrics_timestamp ON service_metrics(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_service_metrics_name ON service_metrics(service_name)',
            'CREATE INDEX IF NOT EXISTS idx_service_metrics_status ON service_metrics(status)',
            'CREATE INDEX IF NOT EXISTS idx_service_metrics_snapshot_id ON service_metrics(snapshot_id)',
            'CREATE INDEX IF NOT EXISTS idx_system_alerts_timestamp ON system_alerts(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_system_alerts_severity ON system_alerts(severity)',
            'CREATE INDEX IF NOT EXISTS idx_system_alerts_resolved ON system_alerts(resolved_at)',
            'CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_performance_metrics_operation ON performance_metrics(operation_type)',
            'CREATE INDEX IF NOT EXISTS idx_api_cache_key ON api_cache(cache_key)',
            'CREATE INDEX IF NOT EXISTS idx_api_cache_expires ON api_cache(expires_at)',
            'CREATE INDEX IF NOT EXISTS idx_config_history_timestamp ON config_history(timestamp)',
            'CREATE INDEX IF NOT EXISTS idx_maintenance_log_timestamp ON maintenance_log(timestamp)'
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(index_sql)
            except sqlite3.OperationalError as e:
                # Skip indexes for columns that don't exist (legacy compatibility)
                if "no such column" in str(e):
                    self.logger.debug(f"Skipping index due to missing column: {index_sql}")
                    continue
                else:
                    raise
    
    @performance_monitor
    def save_service_snapshot(self, health_metrics: Dict, service_data: List[Dict]) -> int:
        """Save complete service status snapshot"""
        try:
            with self.lock:
                with self._get_connection() as conn:
                    # Insert snapshot record
                    cursor = conn.execute('''
                        INSERT INTO service_snapshots 
                        (page_name, page_url, overall_status, status_indicator, 
                         last_updated, total_services, operational_services, 
                         availability_percentage, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        health_metrics.get('page_name', 'Red Hat'),
                        health_metrics.get('page_url', 'https://status.redhat.com'),
                        health_metrics.get('overall_status', 'unknown'),
                        health_metrics.get('status_indicator', 'unknown'),
                        health_metrics.get('last_updated'),
                        health_metrics.get('total_services', 0),
                        health_metrics.get('operational_services', 0),
                        health_metrics.get('availability_percentage', 0.0),
                        json.dumps(health_metrics)
                    ))
                    
                    snapshot_id = cursor.lastrowid
                    
                    # Insert individual service statuses
                    for service in service_data:
                        conn.execute('''
                            INSERT INTO service_statuses 
                            (snapshot_id, service_name, status, created_at,
                             updated_at, description, metadata)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            snapshot_id,
                            service.get('name', ''),
                            service.get('status', 'unknown'),
                            service.get('created_at'),
                            service.get('updated_at'),
                            service.get('description', ''),
                            json.dumps(service)
                        ))
                    
                    conn.commit()
                    self.logger.info(f"Saved service snapshot with {len(service_data)} services")
                    return snapshot_id
                    
        except Exception as e:
            self.logger.error(f"Error saving service snapshot: {e}")
            return 0
    
    def store_status_history(self, data: Dict[str, Any]) -> bool:
        """Store status data in history (alias for save_service_snapshot for backward compatibility)
        
        Args:
            data: Status data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract health metrics and service data from the status data
            health_metrics = {
                'page_name': data.get('page', {}).get('name', 'Red Hat'),
                'page_url': data.get('page', {}).get('url', 'https://status.redhat.com'),
                'overall_status': data.get('status', {}).get('description', 'unknown'),
                'status_indicator': data.get('status', {}).get('indicator', 'unknown'),
                'last_updated': data.get('page', {}).get('updated_at'),
                'total_services': len(data.get('components', [])),
                'operational_services': sum(1 for c in data.get('components', []) if c.get('status') == 'operational'),
                'availability_percentage': 0.0
            }
            
            # Calculate availability percentage
            if health_metrics['total_services'] > 0:
                health_metrics['availability_percentage'] = (
                    health_metrics['operational_services'] / health_metrics['total_services'] * 100
                )
            
            service_data = data.get('components', [])
            snapshot_id = self.save_service_snapshot(health_metrics, service_data)
            return snapshot_id > 0
            
        except Exception as e:
            self.logger.error(f"Error storing status history: {e}")
            return False

    @performance_monitor
    def get_service_history(
        self, 
        service_name: str, 
        hours_back: int = 24,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get historical data for a specific service"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            with self._get_connection() as conn:
                cursor = conn.execute('''
                    SELECT sm.timestamp, sm.service_name, sm.status, 
                           sm.availability_score, sm.performance_score,
                           ss.overall_status, ss.availability_percentage
                    FROM service_metrics sm
                    JOIN service_snapshots ss ON sm.snapshot_id = ss.id
                    WHERE sm.service_name = ? AND sm.timestamp >= ?
                    ORDER BY sm.timestamp DESC
                    LIMIT ?
                ''', (service_name, cutoff_time.isoformat(), limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'timestamp': row['timestamp'],
                        'service_name': row['service_name'],
                        'status': row['status'],
                        'availability_score': row['availability_score'],
                        'performance_score': row['performance_score'],
                        'overall_status': row['overall_status'],
                        'global_availability': row['availability_percentage']
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to get service history for {service_name}: {e}")
            return []
    
    @performance_monitor
    def get_availability_trends(self, days_back: int = 7) -> Dict[str, Any]:
        """Get availability trends over time"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days_back)
            
            with self._get_connection() as conn:
                # Global availability trend
                cursor = conn.execute('''
                    SELECT DATE(timestamp) as date,
                           AVG(availability_percentage) as avg_availability,
                           MIN(availability_percentage) as min_availability,
                           MAX(availability_percentage) as max_availability,
                           COUNT(*) as sample_count
                    FROM service_snapshots
                    WHERE timestamp >= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                ''', (cutoff_time.isoformat(),))
                
                global_trends = [dict(row) for row in cursor.fetchall()]
                
                # Service-specific trends
                cursor = conn.execute('''
                    SELECT service_name,
                           AVG(CASE WHEN status = 'operational' THEN 100.0 ELSE 0.0 END) as availability_percentage,
                           COUNT(*) as total_measurements,
                           SUM(CASE WHEN status = 'operational' THEN 1 ELSE 0 END) as operational_count
                    FROM service_metrics
                    WHERE timestamp >= ? AND is_main_service = 1
                    GROUP BY service_name
                    ORDER BY availability_percentage DESC
                ''', (cutoff_time.isoformat(),))
                
                service_trends = [dict(row) for row in cursor.fetchall()]
                
                return {
                    'global_trends': global_trends,
                    'service_trends': service_trends,
                    'period_days': days_back,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get availability trends: {e}")
            return {}
    
    @performance_monitor
    def save_performance_metrics(self, metrics: PerformanceMetrics) -> None:
        """Save performance metrics to database"""
        try:
            with self.lock:
                with self._get_connection() as conn:
                    conn.execute('''
                        INSERT INTO performance_metrics
                        (operation_type, duration_seconds, api_calls, cache_hits,
                         cache_misses, memory_usage_mb, cpu_usage_percent, errors_count, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        metrics.operation_type,
                        metrics.duration,
                        metrics.api_calls,
                        metrics.cache_hits,
                        metrics.cache_misses,
                        metrics.memory_usage_mb,
                        metrics.cpu_usage_percent,
                        len(metrics.errors) if metrics.errors else 0,
                        json.dumps(asdict(metrics))
                    ))
                    
        except Exception as e:
            self.logger.error(f"Failed to save performance metrics: {e}")
    
    @performance_monitor
    def save_system_alert(self, alert: SystemAlert) -> int:
        """Save system alert to database"""
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cursor = conn.execute('''
                        INSERT INTO system_alerts
                        (alert_type, severity, title, message, source_service, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        alert.alert_type,
                        alert.severity.value,
                        alert.title,
                        alert.message,
                        alert.source_service,
                        json.dumps(asdict(alert))
                    ))
                    
                    return cursor.lastrowid
                    
        except Exception as e:
            self.logger.error(f"Failed to save system alert: {e}")
            return 0
    
    @performance_monitor
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Dict[str, Any]]:
        """Get active (unresolved) alerts"""
        try:
            with self._get_connection() as conn:
                query = '''
                    SELECT id, timestamp, alert_type, severity, title, message,
                           source_service, acknowledged, acknowledged_by
                    FROM system_alerts
                    WHERE resolved_at IS NULL
                '''
                params = []
                
                if severity:
                    query += ' AND severity = ?'
                    params.append(severity.value)
                
                query += ' ORDER BY timestamp DESC'
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get active alerts: {e}")
            return []
    
    @performance_monitor
    def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cursor = conn.execute('''
                        UPDATE system_alerts
                        SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND acknowledged = 0
                    ''', (acknowledged_by, alert_id))
                    
                    return cursor.rowcount > 0
                    
        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False
    
    @performance_monitor
    def resolve_alert(self, alert_id: int) -> bool:
        """Mark an alert as resolved"""
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cursor = conn.execute('''
                        UPDATE system_alerts
                        SET resolved_at = CURRENT_TIMESTAMP
                        WHERE id = ? AND resolved_at IS NULL
                    ''', (alert_id,))
                    
                    return cursor.rowcount > 0
                    
        except Exception as e:
            self.logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False
    
    @performance_monitor
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            with self._get_connection() as conn:
                stats = {}
                
                # Table row counts
                tables = ['service_snapshots', 'service_metrics', 'system_alerts', 
                         'performance_metrics', 'api_cache', 'config_history', 'maintenance_log']
                
                for table in tables:
                    cursor = conn.execute(f'SELECT COUNT(*) FROM {table}')
                    stats[f'{table}_count'] = cursor.fetchone()[0]
                
                # Database size
                cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                stats['database_size_bytes'] = cursor.fetchone()[0]
                
                # Oldest and newest records
                cursor = conn.execute('SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest FROM service_snapshots')
                row = cursor.fetchone()
                stats['data_range'] = {
                    'oldest': row[0],
                    'newest': row[1]
                }
                
                # Recent activity (last 24 hours)
                cutoff = datetime.now() - timedelta(hours=24)
                cursor = conn.execute('SELECT COUNT(*) FROM service_snapshots WHERE timestamp >= ?', (cutoff.isoformat(),))
                stats['snapshots_last_24h'] = cursor.fetchone()[0]
                
                # Cache efficiency
                cursor = conn.execute('''
                    SELECT AVG(access_count) as avg_access,
                           SUM(size_bytes) as total_cache_size,
                           COUNT(*) as cache_entries
                    FROM api_cache
                    WHERE expires_at > CURRENT_TIMESTAMP
                ''')
                cache_row = cursor.fetchone()
                stats['cache_stats'] = {
                    'avg_access_count': cache_row[0] or 0,
                    'total_size_bytes': cache_row[1] or 0,
                    'active_entries': cache_row[2] or 0
                }
                
                # Performance metrics
                stats['operation_count'] = self._operation_count
                stats['avg_operation_time'] = (
                    self._total_execution_time / self._operation_count 
                    if self._operation_count > 0 else 0
                )
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}
    
    @performance_monitor
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old data from database"""
        cleanup_results = {}
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with self.lock:
                with self._get_connection() as conn:
                    # Log cleanup operation
                    conn.execute('''
                        INSERT INTO maintenance_log (operation_type, details)
                        VALUES ('cleanup', ?)
                    ''', (f'Cleaning data older than {cutoff_date.isoformat()}',))
                    
                    # Clean service snapshots (cascades to metrics)
                    cursor = conn.execute('''
                        DELETE FROM service_snapshots WHERE timestamp < ?
                    ''', (cutoff_date.isoformat(),))
                    cleanup_results['service_snapshots'] = cursor.rowcount
                    
                    # Clean old status checks
                    cursor = conn.execute('''
                        DELETE FROM status_checks WHERE timestamp < ?
                    ''', (cutoff_date.isoformat(),))
                    cleanup_results['status_checks'] = cursor.rowcount
                    
                    # Clean system alerts
                    cursor = conn.execute('''
                        DELETE FROM system_alerts 
                        WHERE timestamp < ? AND resolved_at IS NOT NULL
                    ''', (cutoff_date.isoformat(),))
                    cleanup_results['system_alerts'] = cursor.rowcount
                    
                    # Clean performance metrics
                    cursor = conn.execute('''
                        DELETE FROM performance_metrics WHERE timestamp < ?
                    ''', (cutoff_date.isoformat(),))
                    cleanup_results['performance_metrics'] = cursor.rowcount
                    
                    # Clean expired cache entries
                    cursor = conn.execute('''
                        DELETE FROM api_cache WHERE expires_at < CURRENT_TIMESTAMP
                    ''', ())
                    cleanup_results['api_cache'] = cursor.rowcount
                    
                    # Clean old config history
                    old_config_cutoff = datetime.now() - timedelta(days=days_to_keep * 2)
                    cursor = conn.execute('''
                        DELETE FROM config_history WHERE timestamp < ?
                    ''', (old_config_cutoff.isoformat(),))
                    cleanup_results['config_history'] = cursor.rowcount
                    
                    # Update maintenance log
                    conn.execute('''
                        UPDATE maintenance_log 
                        SET status = 'completed', records_affected = ?
                        WHERE id = (SELECT MAX(id) FROM maintenance_log WHERE operation_type = 'cleanup')
                    ''', (sum(cleanup_results.values()),))
                    
            self.logger.info(f"Cleanup completed: {cleanup_results}")
            return sum(cleanup_results.values())
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return 0
    
    @performance_monitor
    def vacuum_database(self) -> bool:
        """Vacuum database to reclaim space and optimize"""
        try:
            with self.lock:
                # Log vacuum operation first (in a separate transaction)
                start_time = datetime.now()
                with self._get_connection() as conn:
                    conn.execute('''
                        INSERT INTO maintenance_log (operation_type, details)
                        VALUES ('vacuum', 'Database optimization and space reclamation')
                    ''')
                
                # Perform vacuum outside of transaction context
                # SQLite VACUUM cannot be run within a transaction
                conn = sqlite3.connect(self.db_path)
                conn.execute('VACUUM')
                conn.close()
                
                # Update maintenance log (in another separate transaction)
                duration = (datetime.now() - start_time).total_seconds()
                with self._get_connection() as conn:
                    conn.execute('''
                        UPDATE maintenance_log 
                        SET status = 'completed', duration_seconds = ?
                        WHERE id = (SELECT MAX(id) FROM maintenance_log WHERE operation_type = 'vacuum')
                    ''', (duration,))
                
                self._last_vacuum = datetime.now()
                self.logger.info(f"Database vacuum completed in {duration:.2f}s")
                return True
                    
        except Exception as e:
            self.logger.error(f"Failed to vacuum database: {e}")
            return False
    
    @performance_monitor
    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """Create database backup"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"{self.db_path}.backup_{timestamp}"
            
            # Ensure backup directory exists
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            
            with self.lock:
                # Use shutil for atomic copy
                shutil.copy2(self.db_path, backup_path)
                
                # Log backup operation
                with self._get_connection() as conn:
                    conn.execute('''
                        INSERT INTO maintenance_log (operation_type, details, status)
                        VALUES ('backup', ?, 'completed')
                    ''', (f'Database backed up to {backup_path}',))
                
            self.logger.info(f"Database backed up to: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to backup database: {e}")
            return False
    
    @performance_monitor
    def analyze_database(self) -> bool:
        """Analyze database to update query planner statistics"""
        try:
            with self.lock:
                with self._get_connection() as conn:
                    # Log analyze operation
                    start_time = datetime.now()
                    conn.execute('''
                        INSERT INTO maintenance_log (operation_type, details)
                        VALUES ('analyze', 'Update query planner statistics')
                    ''')
                    
                    # Perform analyze
                    conn.execute('ANALYZE')
                    
                    # Update maintenance log
                    duration = (datetime.now() - start_time).total_seconds()
                    conn.execute('''
                        UPDATE maintenance_log 
                        SET status = 'completed', duration_seconds = ?
                        WHERE id = (SELECT MAX(id) FROM maintenance_log WHERE operation_type = 'analyze')
                    ''', (duration,))
                    
                    self._last_analyze = datetime.now()
                    self.logger.info(f"Database analysis completed in {duration:.2f}s")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to analyze database: {e}")
            return False
    
    def close(self) -> None:
        """Close database connections and cleanup"""
        try:
            # Perform final maintenance if needed
            if self._last_vacuum is None or (datetime.now() - self._last_vacuum).days > 7:
                self.vacuum_database()
            
            self.logger.info("Database manager closed")
            
        except Exception as e:
            self.logger.error(f"Error during database cleanup: {e}")

    def export_historical_data(self, days: int = 30) -> Dict[str, Any]:
        """Export historical data for the specified number of days"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            with self._get_connection() as conn:
                export_data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'days_included': days,
                    'data': {}
                }
                
                # Export service snapshots
                cursor = conn.execute('''
                    SELECT * FROM service_snapshots 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp DESC
                ''', (cutoff.isoformat(),))
                
                export_data['data']['service_snapshots'] = [
                    {
                        'id': row[0],
                        'timestamp': row[1],
                        'service_name': row[2],
                        'status': row[3],
                        'availability_percentage': row[4],
                        'response_time_ms': row[5],
                        'metadata': json.loads(row[6]) if row[6] else {}
                    }
                    for row in cursor.fetchall()
                ]
                
                # Export system alerts
                cursor = conn.execute('''
                    SELECT * FROM system_alerts 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp DESC
                ''', (cutoff.isoformat(),))
                
                export_data['data']['system_alerts'] = [
                    {
                        'id': row[0],
                        'timestamp': row[1],
                        'source': row[2],
                        'title': row[3],
                        'message': row[4],
                        'severity': row[5],
                        'resolved': bool(row[6]),
                        'metadata': json.loads(row[7]) if row[7] else {}
                    }
                    for row in cursor.fetchall()
                ]
                
                # Export performance metrics
                cursor = conn.execute('''
                    SELECT * FROM performance_metrics 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp DESC
                ''', (cutoff.isoformat(),))
                
                export_data['data']['performance_metrics'] = [
                    {
                        'id': row[0],
                        'timestamp': row[1],
                        'metric_name': row[2],
                        'value': row[3],
                        'unit': row[4],
                        'metadata': json.loads(row[5]) if row[5] else {}
                    }
                    for row in cursor.fetchall()
                ]
                
                return export_data
                
        except Exception as e:
            self.logger.error(f"Failed to export historical data: {e}")
            return {
                'export_timestamp': datetime.now().isoformat(),
                'error': str(e),
                'data': {}
            }

    # Legacy methods for backward compatibility with tests
    @property
    def enabled(self) -> bool:
        """Legacy property for test compatibility"""
        return self.is_enabled()

    @property
    def connection(self) -> Optional[sqlite3.Connection]:
        """Legacy property for test compatibility - returns None for disabled DB"""
        if not self.is_enabled():
            return None
        # For compatibility, we don't expose active connections since we use context managers
        return None

    def store_status_check(self, status_data: Dict[str, Any]) -> Optional[int]:
        """Store status check data in legacy format
        
        Args:
            status_data: Dictionary with status information
            
        Returns:
            Status check ID if successful, None otherwise
        """
        if not self.is_enabled():
            return None
            
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cursor = conn.execute('''
                        INSERT INTO status_checks (
                            timestamp, overall_status, availability_percentage, 
                            total_services, operational_services, response_time, details
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        status_data.get('timestamp', datetime.now()).isoformat(),
                        status_data.get('overall_status', 'unknown'),
                        status_data.get('availability_percentage', 0.0),
                        status_data.get('total_services', 0),
                        status_data.get('operational_services', 0),
                        status_data.get('response_time', 0.0),
                        json.dumps({k: v for k, v in status_data.items() 
                                  if k not in ['timestamp', 'overall_status', 'availability_percentage', 
                                             'total_services', 'operational_services', 'response_time']})
                    ))
                    return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Failed to store status check: {e}")
            return None

    def store_component_status(self, component_data: Dict[str, Any]) -> bool:
        """Store component status data in legacy format
        
        Args:
            component_data: Dictionary with component information
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False
            
        try:
            with self.lock:
                with self._get_connection() as conn:
                    conn.execute('''
                        INSERT INTO components (
                            component_id, name, status, description, last_updated
                        ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        component_data.get('component_id', 'unknown'),
                        component_data.get('name', 'unknown'),
                        component_data.get('status', 'unknown'),
                        component_data.get('description', '')
                    ))
                    return True
        except Exception as e:
            self.logger.error(f"Failed to store component status: {e}")
            return False

    def store_incident(self, incident_data: Dict[str, Any]) -> bool:
        """Store incident data in legacy format
        
        Args:
            incident_data: Dictionary with incident information
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False
            
        try:
            with self.lock:
                with self._get_connection() as conn:
                    conn.execute('''
                        INSERT OR REPLACE INTO incidents (
                            incident_id, name, status, impact, created_at, resolved_at, description
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        incident_data.get('incident_id', 'unknown'),
                        incident_data.get('name', 'Unknown Incident'),
                        incident_data.get('status', 'unknown'),
                        incident_data.get('impact', 'unknown'),
                        incident_data.get('created_at', datetime.now()).isoformat(),
                        incident_data.get('resolved_at', None),
                        incident_data.get('description', '')
                    ))
                    return True
        except Exception as e:
            self.logger.error(f"Failed to store incident: {e}")
            return False

    def store_performance_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """Store performance metrics using test-expected schema
        
        Args:
            metrics_data: Dictionary with metrics information
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled():
            return False
            
        try:
            with self.lock:
                with self._get_connection() as conn:
                    conn.execute('''
                        INSERT INTO performance_metrics 
                        (api_calls, cache_hits, cache_misses, response_time, data_size, metadata) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        metrics_data.get('api_calls', 0),
                        metrics_data.get('cache_hits', 0),
                        metrics_data.get('cache_misses', 0),
                        metrics_data.get('response_time'),
                        metrics_data.get('data_size'),
                        json.dumps(metrics_data.get('metadata', {}))
                    ))
                    return True
        except Exception as e:
            self.logger.error(f"Failed to store performance metrics: {e}")
            return False

    def get_status_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get status check history
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of status check records
        """
        if not self.is_enabled():
            return []
            
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cursor = conn.execute('''
                        SELECT id, timestamp, overall_status, availability_percentage,
                               total_services, operational_services, response_time, details 
                        FROM status_checks 
                        ORDER BY timestamp ASC 
                        LIMIT ?
                    ''', (limit,))
                    
                    return [
                        {
                            'id': row[0],
                            'timestamp': row[1],
                            'overall_status': row[2],
                            'availability_percentage': row[3],
                            'total_services': row[4],
                            'operational_services': row[5],
                            'response_time': row[6],
                            'details': json.loads(row[7]) if row[7] else {}
                        }
                        for row in cursor.fetchall()
                    ]
        except Exception as e:
            self.logger.error(f"Failed to get status history: {e}")
            return []

    def get_component_history(self, component_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get component status history
        
        Args:
            component_name: Name or ID of the component
            limit: Maximum number of records to return
            
        Returns:
            List of component status records
        """
        if not self.is_enabled():
            return []
            
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cursor = conn.execute('''
                        SELECT id, component_id, name, status, description, last_updated 
                        FROM components 
                        WHERE component_id = ? OR name = ?
                        ORDER BY last_updated DESC 
                        LIMIT ?
                    ''', (component_name, component_name, limit))
                    
                    return [
                        {
                            'id': row[0],
                            'component_id': row[1],
                            'name': row[2],
                            'status': row[3],
                            'description': row[4],
                            'last_updated': row[5]
                        }
                        for row in cursor.fetchall()
                    ]
        except Exception as e:
            self.logger.error(f"Failed to get component history: {e}")
            return []

    def get_incidents_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get incidents by status
        
        Args:
            status: Status to filter by
            
        Returns:
            List of incident records
        """
        if not self.is_enabled():
            return []
            
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cursor = conn.execute('''
                        SELECT id, incident_id, name, status, impact, created_at, resolved_at, description 
                        FROM incidents 
                        WHERE status = ?
                        ORDER BY created_at DESC
                    ''', (status,))
                    
                    return [
                        {
                            'id': row[0],
                            'incident_id': row[1],
                            'name': row[2],
                            'status': row[3],
                            'impact': row[4],
                            'created_at': row[5],
                            'resolved_at': row[6],
                            'description': row[7]
                        }
                        for row in cursor.fetchall()
                    ]
        except Exception as e:
            self.logger.error(f"Failed to get incidents by status: {e}")
            return []

    def get_performance_metrics(self, metric_name: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get performance metrics
        
        Args:
            metric_name: Optional metric name to filter by (not used with new schema)
            limit: Maximum number of records to return
            
        Returns:
            List of performance metric records
        """
        if not self.is_enabled():
            return []
            
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cursor = conn.execute('''
                        SELECT id, timestamp, api_calls, cache_hits, cache_misses, 
                               response_time, data_size, metadata 
                        FROM performance_metrics 
                        ORDER BY timestamp DESC 
                        LIMIT ?
                    ''', (limit,))
                    
                    return [
                        {
                            'id': row[0],
                            'timestamp': row[1],
                            'api_calls': row[2],
                            'cache_hits': row[3],
                            'cache_misses': row[4],
                            'response_time': row[5],
                            'data_size': row[6],
                            'metadata': json.loads(row[7]) if row[7] else {}
                        }
                        for row in cursor.fetchall()
                    ]
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            return []

    def get_availability_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get availability trends over specified days
        
        Args:
            days: Number of days to analyze
            
        Returns:
            List of dictionaries with date and availability data
        """
        if not self.is_enabled():
            return []
            
        try:
            with self.lock:
                with self._get_connection() as conn:
                    cutoff_date = datetime.now() - timedelta(days=days)
                    cursor = conn.execute('''
                        SELECT DATE(timestamp) as date, 
                               AVG(CASE WHEN overall_status = 'operational' THEN 100.0 ELSE 0.0 END) as availability
                        FROM status_checks 
                        WHERE timestamp >= ?
                        GROUP BY DATE(timestamp)
                        ORDER BY date
                    ''', (cutoff_date.isoformat(),))
                    
                    results = cursor.fetchall()
                    return [
                        {'date': row[0], 'availability': row[1]}
                        for row in results
                    ]
        except Exception as e:
            self.logger.error(f"Failed to get availability trends: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count records in each table
                tables = ['status_checks', 'components', 'incidents']
                for table in tables:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cursor.fetchone()[0]
                    stats[f'total_{table}'] = count
                
                # Database file size
                import os
                if os.path.exists(self.db_path):
                    stats['database_size'] = os.path.getsize(self.db_path)
                else:
                    stats['database_size'] = 0
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}



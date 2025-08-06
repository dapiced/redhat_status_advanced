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
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager"""
        self.config = get_config()
        self.db_path = db_path or self.config.get('database', 'path', 'redhat_status.db')
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # Database configuration
        self.connection_timeout = self.config.get('database', 'connection_timeout', 30)
        self.journal_mode = self.config.get('database', 'journal_mode', 'WAL')
        self.synchronous = self.config.get('database', 'synchronous', 'NORMAL')
        self.cache_size = self.config.get('database', 'cache_size', 2000)
        
        # Performance metrics
        self._operation_count = 0
        self._total_execution_time = 0.0
        self._last_vacuum = None
        self._last_analyze = None
        
        # Initialize database
        self._init_database()
        
    def is_enabled(self) -> bool:
        """Check if database operations are enabled"""
        try:
            return (
                self.config.get('database', 'enabled', True) and 
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
            raise
    
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
                operation_type TEXT NOT NULL,
                duration_seconds REAL NOT NULL,
                api_calls INTEGER DEFAULT 0,
                cache_hits INTEGER DEFAULT 0,
                cache_misses INTEGER DEFAULT 0,
                memory_usage_mb REAL,
                cpu_usage_percent REAL,
                errors_count INTEGER DEFAULT 0,
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
            conn.execute(index_sql)
    
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
                        health_metrics.get('page_name', ''),
                        health_metrics.get('page_url', ''),
                        health_metrics.get('overall_status', ''),
                        health_metrics.get('status_indicator', ''),
                        health_metrics.get('last_updated', ''),
                        health_metrics.get('total_services', 0),
                        health_metrics.get('operational_services', 0),
                        health_metrics.get('availability_percentage', 0.0),
                        json.dumps(health_metrics)
                    ))
                    
                    snapshot_id = cursor.lastrowid
                    
                    # Insert service metrics
                    for service in service_data:
                        conn.execute('''
                            INSERT INTO service_metrics
                            (snapshot_id, service_name, service_id, group_id, status,
                             availability_score, performance_score, is_main_service, metadata)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            snapshot_id,
                            service.get('name', ''),
                            service.get('id', ''),
                            service.get('group_id'),
                            service.get('status', 'unknown'),
                            service.get('availability_score', 0.0),
                            service.get('performance_score', 0.0),
                            service.get('group_id') is None,  # Main service if no group
                            json.dumps(service)
                        ))
                    
                    self._operation_count += 1
                    self.logger.debug(f"Saved snapshot {snapshot_id} with {len(service_data)} services")
                    
                    return snapshot_id
                    
        except Exception as e:
            self.logger.error(f"Failed to save service snapshot: {e}")
            raise
    
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
    def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
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
            return cleanup_results
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return {}
    
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



"""
Test suite for database manager module.
"""
import pytest
import tempfile
import sqlite3
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add the project root to sys.path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redhat_status.database.db_manager import DatabaseManager, get_database_manager


class TestDatabaseManager:
    """Test the DatabaseManager class"""
    
    def setup_method(self):
        """Set up test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.config = {
            'enabled': True,
            'path': self.db_path,
            'cleanup_days': 30
        }
        self.db_manager = DatabaseManager(self.config)
    
    def teardown_method(self):
        """Clean up after test"""
        if hasattr(self, 'db_manager'):
            self.db_manager.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_creates_database(self):
        """Test that initialization creates database and tables"""
        assert os.path.exists(self.db_path)
        
        # Check that tables exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check for main tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['status_checks', 'components', 'incidents', 'performance_metrics']
        for table in expected_tables:
            assert table in tables
        
        conn.close()
    
    def test_init_disabled_database(self):
        """Test initialization with disabled database"""
        config = {'enabled': False}
        db_manager = DatabaseManager(config)
        
        assert db_manager.enabled is False
        assert db_manager.connection is None
    
    def test_store_status_check(self):
        """Test storing status check data"""
        status_data = {
            'timestamp': datetime.now(),
            'overall_status': 'operational',
            'availability_percentage': 99.5,
            'total_services': 50,
            'operational_services': 48,
            'response_time': 1.5
        }
        
        check_id = self.db_manager.store_status_check(status_data)
        
        assert check_id is not None
        assert isinstance(check_id, int)
        
        # Verify data was stored
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM status_checks WHERE id = ?", (check_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[2] == 'operational'  # overall_status
        assert row[3] == 99.5  # availability_percentage
        conn.close()
    
    def test_store_component_status(self):
        """Test storing component status data"""
        component_data = {
            'component_id': 'test-component',
            'name': 'Test Component',
            'status': 'operational',
            'description': 'Test description',
            'timestamp': datetime.now()
        }
        
        self.db_manager.store_component_status(component_data)
        
        # Verify data was stored
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM components WHERE component_id = ?", 
                      (component_data['component_id'],))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[1] == 'test-component'  # component_id
        assert row[2] == 'Test Component'  # name
        assert row[3] == 'operational'  # status
        conn.close()
    
    def test_store_incident(self):
        """Test storing incident data"""
        incident_data = {
            'incident_id': 'test-incident',
            'name': 'Test Incident',
            'status': 'resolved',
            'impact': 'minor',
            'created_at': datetime.now(),
            'resolved_at': datetime.now()
        }
        
        self.db_manager.store_incident(incident_data)
        
        # Verify data was stored
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incidents WHERE incident_id = ?", 
                      (incident_data['incident_id'],))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[1] == 'test-incident'  # incident_id
        assert row[2] == 'Test Incident'  # name
        assert row[3] == 'resolved'  # status
        conn.close()
    
    def test_store_performance_metrics(self):
        """Test storing performance metrics"""
        metrics_data = {
            'timestamp': datetime.now(),
            'api_calls': 5,
            'cache_hits': 3,
            'cache_misses': 2,
            'response_time': 1.5,
            'data_size': 1024
        }
        
        self.db_manager.store_performance_metrics(metrics_data)
        
        # Verify data was stored
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM performance_metrics ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        
        assert row is not None
        assert row[2] == 5  # api_calls
        assert row[3] == 3  # cache_hits
        assert row[4] == 2  # cache_misses
        conn.close()
    
    def test_get_status_history(self):
        """Test getting status history"""
        # Store some test data
        for i in range(5):
            status_data = {
                'timestamp': datetime.now() - timedelta(hours=i),
                'overall_status': 'operational',
                'availability_percentage': 99.0 + i * 0.1,
                'total_services': 50,
                'operational_services': 48 + i,
                'response_time': 1.0 + i * 0.1
            }
            self.db_manager.store_status_check(status_data)
        
        # Get history
        history = self.db_manager.get_status_history(limit=3)
        
        assert len(history) == 3
        # Should be ordered by timestamp descending (most recent first)
        assert history[0]['availability_percentage'] == 99.4
        assert history[1]['availability_percentage'] == 99.3
        assert history[2]['availability_percentage'] == 99.2
    
    def test_get_component_history(self):
        """Test getting component history"""
        component_id = 'test-component'
        
        # Store some test data
        for i in range(3):
            component_data = {
                'component_id': component_id,
                'name': 'Test Component',
                'status': 'operational' if i % 2 == 0 else 'degraded_performance',
                'description': f'Status {i}',
                'timestamp': datetime.now() - timedelta(hours=i)
            }
            self.db_manager.store_component_status(component_data)
        
        # Get history
        history = self.db_manager.get_component_history(component_id)
        
        assert len(history) == 3
        assert history[0]['status'] == 'operational'
        assert history[1]['status'] == 'degraded_performance'
    
    def test_get_incidents_by_status(self):
        """Test getting incidents by status"""
        # Store test incidents
        incident_statuses = ['investigating', 'resolved', 'investigating']
        for i, status in enumerate(incident_statuses):
            incident_data = {
                'incident_id': f'incident-{i}',
                'name': f'Test Incident {i}',
                'status': status,
                'impact': 'minor',
                'created_at': datetime.now() - timedelta(hours=i)
            }
            self.db_manager.store_incident(incident_data)
        
        # Get investigating incidents
        investigating = self.db_manager.get_incidents_by_status('investigating')
        assert len(investigating) == 2
        
        # Get resolved incidents
        resolved = self.db_manager.get_incidents_by_status('resolved')
        assert len(resolved) == 1
    
    def test_get_performance_metrics(self):
        """Test getting performance metrics"""
        # Store test metrics
        for i in range(5):
            metrics_data = {
                'timestamp': datetime.now() - timedelta(minutes=i * 10),
                'api_calls': 10 + i,
                'cache_hits': 5 + i,
                'cache_misses': 3 + i,
                'response_time': 1.0 + i * 0.1,
                'data_size': 1000 + i * 100
            }
            self.db_manager.store_performance_metrics(metrics_data)
        
        # Get metrics
        metrics = self.db_manager.get_performance_metrics(limit=3)
        
        assert len(metrics) == 3
        # Should be ordered by timestamp descending
        assert metrics[0]['api_calls'] == 14
        assert metrics[1]['api_calls'] == 13
        assert metrics[2]['api_calls'] == 12
    
    def test_cleanup_old_data(self):
        """Test cleanup of old data"""
        # Store old data
        old_timestamp = datetime.now() - timedelta(days=40)
        recent_timestamp = datetime.now() - timedelta(days=10)
        
        # Store old status check
        old_status = {
            'timestamp': old_timestamp,
            'overall_status': 'operational',
            'availability_percentage': 99.0,
            'total_services': 50,
            'operational_services': 48,
            'response_time': 1.0
        }
        self.db_manager.store_status_check(old_status)
        
        # Store recent status check
        recent_status = {
            'timestamp': recent_timestamp,
            'overall_status': 'operational',
            'availability_percentage': 99.5,
            'total_services': 50,
            'operational_services': 49,
            'response_time': 1.2
        }
        self.db_manager.store_status_check(recent_status)
        
        # Run cleanup (30 days retention)
        cleaned_count = self.db_manager.cleanup_old_data()
        
        assert cleaned_count > 0
        
        # Verify old data is gone but recent data remains
        history = self.db_manager.get_status_history()
        assert len(history) == 1
        assert history[0]['availability_percentage'] == 99.5
    
    def test_get_availability_trends(self):
        """Test getting availability trends"""
        # Store trend data
        for i in range(7):
            status_data = {
                'timestamp': datetime.now() - timedelta(days=i),
                'overall_status': 'operational',
                'availability_percentage': 99.0 + (i % 3) * 0.2,
                'total_services': 50,
                'operational_services': 48,
                'response_time': 1.0
            }
            self.db_manager.store_status_check(status_data)
        
        # Get trends
        trends = self.db_manager.get_availability_trends(days=7)
        
        assert len(trends) <= 7  # Should have up to 7 days of data
        assert all('date' in trend and 'availability' in trend for trend in trends)
    
    def test_get_database_stats(self):
        """Test getting database statistics"""
        # Store some test data
        self.db_manager.store_status_check({
            'timestamp': datetime.now(),
            'overall_status': 'operational',
            'availability_percentage': 99.0,
            'total_services': 50,
            'operational_services': 48,
            'response_time': 1.0
        })
        
        stats = self.db_manager.get_stats()
        
        assert 'total_status_checks' in stats
        assert 'total_components' in stats
        assert 'total_incidents' in stats
        assert 'database_size' in stats
        assert stats['total_status_checks'] >= 1
    
    def test_disabled_database_operations(self):
        """Test operations when database is disabled"""
        config = {'enabled': False}
        db_manager = DatabaseManager(config)
        
        # All operations should be no-ops and return None/empty
        result = db_manager.store_status_check({})
        assert result is None
        
        history = db_manager.get_status_history()
        assert history == []
        
        cleanup_count = db_manager.cleanup_old_data()
        assert cleanup_count == 0
    
    def test_database_connection_error_handling(self):
        """Test handling of database connection errors"""
        # Use invalid database path
        config = {
            'enabled': True,
            'path': '/invalid/path/database.db'
        }
        
        # Should handle the error gracefully
        db_manager = DatabaseManager(config)
        assert db_manager.connection is None
    
    def test_transaction_rollback_on_error(self):
        """Test transaction rollback on error"""
        # This would be tested with a scenario that causes a database error
        # For now, we'll test that invalid data doesn't break the database
        
        invalid_data = {
            'timestamp': 'invalid_timestamp',  # Should be datetime
            'overall_status': 'operational',
            'availability_percentage': 'invalid',  # Should be float
            'total_services': 50,
            'operational_services': 48,
            'response_time': 1.0
        }
        
        # Should handle the error and return None
        result = self.db_manager.store_status_check(invalid_data)
        assert result is None
    
    def test_concurrent_database_access(self):
        """Test concurrent access to database"""
        import threading
        
        def database_operations(thread_id):
            for i in range(5):
                status_data = {
                    'timestamp': datetime.now(),
                    'overall_status': 'operational',
                    'availability_percentage': 99.0,
                    'total_services': 50,
                    'operational_services': 48,
                    'response_time': 1.0
                }
                self.db_manager.store_status_check(status_data)
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=database_operations, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all data was stored
        history = self.db_manager.get_status_history()
        assert len(history) == 15  # 3 threads * 5 operations each


class TestGetDatabaseManagerFunction:
    """Test the get_database_manager function"""
    
    def test_get_database_manager_singleton(self):
        """Test that get_database_manager returns the same instance"""
        manager1 = get_database_manager()
        manager2 = get_database_manager()
        
        assert manager1 is manager2
    
    @patch('redhat_status.database.db_manager.DatabaseManager')
    def test_get_database_manager_creates_instance(self, mock_db_manager):
        """Test that get_database_manager creates a DatabaseManager instance"""
        mock_instance = Mock()
        mock_db_manager.return_value = mock_instance
        
        # Clear any existing singleton
        import redhat_status.database.db_manager as db_module
        db_module._db_manager_instance = None
        
        result = get_database_manager()
        
        mock_db_manager.assert_called_once()
        assert result == mock_instance


class TestDatabaseSchema:
    """Test database schema and migrations"""
    
    def setup_method(self):
        """Set up test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'schema_test.db')
    
    def teardown_method(self):
        """Clean up after test"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_tables_schema(self):
        """Test that tables are created with correct schema"""
        config = {'enabled': True, 'path': self.db_path}
        db_manager = DatabaseManager(config)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check status_checks table schema
        cursor.execute("PRAGMA table_info(status_checks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        expected_columns = ['id', 'timestamp', 'overall_status', 
                          'availability_percentage', 'total_services', 
                          'operational_services', 'response_time']
        for col in expected_columns:
            assert col in columns
        
        conn.close()
        db_manager.close()
    
    def test_database_indexes(self):
        """Test that proper indexes are created"""
        config = {'enabled': True, 'path': self.db_path}
        db_manager = DatabaseManager(config)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check for indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        # Should have indexes on timestamp columns for performance
        timestamp_indexes = [idx for idx in indexes if 'timestamp' in idx.lower()]
        assert len(timestamp_indexes) > 0
        
        conn.close()
        db_manager.close()


if __name__ == '__main__':
    pytest.main([__file__])

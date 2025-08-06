"""
Red Hat Status Checker - Analytics and AI Module

This module provides advanced analytics and AI-powered insights
for Red Hat service monitoring and alerting.

Contains:
- AIAnalytics class for intelligent monitoring
- Anomaly detection algorithms
- Predictive analytics
- Performance optimization insights
- Smart alerting with machine learning

Author: Red Hat Status Checker v3.1.0 - Modular Edition
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import asdict

from ..core.data_models import (
    PerformanceMetrics, ServiceHealthMetrics, SystemAlert,
    AnomalyDetection, PredictiveInsight, AnomalyType, AlertSeverity, InsightType
)
from ..config.config_manager import get_config
from ..utils.decorators import performance_monitor, retry_with_backoff


class AIAnalytics:
    """
    Advanced AI Analytics Engine for Red Hat Services
    
    Provides intelligent monitoring, anomaly detection, and predictive insights
    using machine learning algorithms and statistical analysis.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize AI Analytics with database connection"""
        self.config = get_config()
        self.db_path = db_path or self.config.get('analytics', 'database_path', 'redhat_analytics.db')
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # AI Configuration
        self.anomaly_threshold = self.config.get('analytics', 'anomaly_threshold', 2.0)
        self.learning_window = self.config.get('analytics', 'learning_window_days', 30)
        self.min_samples = self.config.get('analytics', 'min_samples_for_learning', 10)
        
        # Initialize database
        self._init_database()
        
        # Cache for performance
        self._service_baselines = {}
        self._recent_anomalies = []
        
    def _init_database(self) -> None:
        """Initialize SQLite database for analytics data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript('''
                    CREATE TABLE IF NOT EXISTS service_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        service_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        response_time REAL,
                        availability_score REAL,
                        performance_score REAL,
                        metadata TEXT
                    );
                    
                    CREATE TABLE IF NOT EXISTS anomalies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        service_name TEXT NOT NULL,
                        anomaly_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        description TEXT,
                        confidence_score REAL,
                        resolved_at DATETIME,
                        metadata TEXT
                    );
                    
                    CREATE TABLE IF NOT EXISTS predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        service_name TEXT NOT NULL,
                        prediction_type TEXT NOT NULL,
                        prediction_value REAL,
                        confidence_score REAL,
                        time_horizon_hours INTEGER,
                        metadata TEXT
                    );
                    
                    CREATE TABLE IF NOT EXISTS system_insights (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        insight_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        confidence_score REAL,
                        impact_score REAL,
                        actionable BOOLEAN DEFAULT 0,
                        metadata TEXT
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_service_metrics_timestamp 
                    ON service_metrics(timestamp);
                    
                    CREATE INDEX IF NOT EXISTS idx_service_metrics_name 
                    ON service_metrics(service_name);
                    
                    CREATE INDEX IF NOT EXISTS idx_anomalies_timestamp 
                    ON anomalies(timestamp);
                    
                    CREATE INDEX IF NOT EXISTS idx_predictions_timestamp 
                    ON predictions(timestamp);
                ''')
                
            self.logger.info(f"Analytics database initialized: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize analytics database: {e}")
            raise
    
    @performance_monitor
    def record_service_metrics(self, metrics: ServiceHealthMetrics) -> None:
        """Record service metrics for analytics"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        INSERT INTO service_metrics 
                        (service_name, status, response_time, availability_score, 
                         performance_score, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        metrics.service_name,
                        metrics.status,
                        metrics.response_time,
                        metrics.availability_score,
                        metrics.performance_score,
                        json.dumps(asdict(metrics))
                    ))
                    
        except Exception as e:
            self.logger.error(f"Failed to record service metrics: {e}")
    
    @performance_monitor
    def detect_anomalies(self, current_metrics: ServiceHealthMetrics) -> List[AnomalyDetection]:
        """Detect anomalies using statistical analysis and ML algorithms"""
        anomalies = []
        
        try:
            service_name = current_metrics.service_name
            
            # Get historical data for baseline
            baseline = self._get_service_baseline(service_name)
            if not baseline:
                self.logger.debug(f"Insufficient data for anomaly detection: {service_name}")
                return anomalies
            
            # Detect different types of anomalies
            anomalies.extend(self._detect_availability_anomalies(current_metrics, baseline))
            anomalies.extend(self._detect_performance_anomalies(current_metrics, baseline))
            anomalies.extend(self._detect_status_anomalies(current_metrics, baseline))
            
            # Record detected anomalies
            for anomaly in anomalies:
                self._record_anomaly(anomaly)
                
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
            return []
    
    def _get_service_baseline(self, service_name: str) -> Optional[Dict[str, float]]:
        """Calculate baseline metrics for a service"""
        try:
            if service_name in self._service_baselines:
                return self._service_baselines[service_name]
            
            cutoff_date = datetime.now() - timedelta(days=self.learning_window)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT availability_score, performance_score, response_time
                    FROM service_metrics
                    WHERE service_name = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                    LIMIT 1000
                ''', (service_name, cutoff_date.isoformat()))
                
                rows = cursor.fetchall()
                
            if len(rows) < self.min_samples:
                return None
            
            # Calculate statistical baseline
            availability_scores = [row[0] for row in rows if row[0] is not None]
            performance_scores = [row[1] for row in rows if row[1] is not None]
            response_times = [row[2] for row in rows if row[2] is not None]
            
            baseline = {
                'availability_mean': sum(availability_scores) / len(availability_scores) if availability_scores else 0,
                'availability_std': self._calculate_std(availability_scores),
                'performance_mean': sum(performance_scores) / len(performance_scores) if performance_scores else 0,
                'performance_std': self._calculate_std(performance_scores),
                'response_time_mean': sum(response_times) / len(response_times) if response_times else 0,
                'response_time_std': self._calculate_std(response_times),
                'sample_count': len(rows)
            }
            
            # Cache baseline
            self._service_baselines[service_name] = baseline
            return baseline
            
        except Exception as e:
            self.logger.error(f"Failed to calculate baseline for {service_name}: {e}")
            return None
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def _detect_availability_anomalies(
        self, 
        metrics: ServiceHealthMetrics, 
        baseline: Dict[str, float]
    ) -> List[AnomalyDetection]:
        """Detect availability anomalies"""
        anomalies = []
        
        try:
            current_availability = metrics.availability_score
            baseline_mean = baseline['availability_mean']
            baseline_std = baseline['availability_std']
            
            if baseline_std == 0:
                return anomalies
            
            # Z-score based anomaly detection
            z_score = abs(current_availability - baseline_mean) / baseline_std
            
            if z_score > self.anomaly_threshold:
                severity = AlertSeverity.CRITICAL if z_score > 3 else AlertSeverity.WARNING
                
                anomaly = AnomalyDetection(
                    timestamp=datetime.now(),
                    service_name=metrics.service_name,
                    anomaly_type=AnomalyType.AVAILABILITY_DROP if current_availability < baseline_mean else AnomalyType.UNUSUAL_BEHAVIOR,
                    severity=severity,
                    description=f"Availability anomaly detected: {current_availability:.1f}% (baseline: {baseline_mean:.1f}%, z-score: {z_score:.2f})",
                    confidence_score=min(z_score / 3 * 100, 100),
                    affected_metrics={'availability_score': current_availability, 'z_score': z_score}
                )
                
                anomalies.append(anomaly)
                
        except Exception as e:
            self.logger.error(f"Availability anomaly detection failed: {e}")
        
        return anomalies
    
    def _detect_performance_anomalies(
        self, 
        metrics: ServiceHealthMetrics, 
        baseline: Dict[str, float]
    ) -> List[AnomalyDetection]:
        """Detect performance anomalies"""
        anomalies = []
        
        try:
            current_performance = metrics.performance_score
            baseline_mean = baseline['performance_mean']
            baseline_std = baseline['performance_std']
            
            if baseline_std == 0:
                return anomalies
            
            z_score = abs(current_performance - baseline_mean) / baseline_std
            
            if z_score > self.anomaly_threshold:
                severity = AlertSeverity.CRITICAL if z_score > 3 else AlertSeverity.WARNING
                
                anomaly = AnomalyDetection(
                    timestamp=datetime.now(),
                    service_name=metrics.service_name,
                    anomaly_type=AnomalyType.PERFORMANCE_DEGRADATION if current_performance < baseline_mean else AnomalyType.UNUSUAL_BEHAVIOR,
                    severity=severity,
                    description=f"Performance anomaly detected: {current_performance:.1f} (baseline: {baseline_mean:.1f}, z-score: {z_score:.2f})",
                    confidence_score=min(z_score / 3 * 100, 100),
                    affected_metrics={'performance_score': current_performance, 'z_score': z_score}
                )
                
                anomalies.append(anomaly)
                
        except Exception as e:
            self.logger.error(f"Performance anomaly detection failed: {e}")
        
        return anomalies
    
    def _detect_status_anomalies(
        self, 
        metrics: ServiceHealthMetrics, 
        baseline: Dict[str, float]
    ) -> List[AnomalyDetection]:
        """Detect status change anomalies"""
        anomalies = []
        
        try:
            # Check for recent status changes
            cutoff_time = datetime.now() - timedelta(hours=1)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT status, timestamp FROM service_metrics
                    WHERE service_name = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''', (metrics.service_name, cutoff_time.isoformat()))
                
                recent_statuses = cursor.fetchall()
            
            if len(recent_statuses) < 2:
                return anomalies
            
            # Detect frequent status changes (flapping)
            unique_statuses = set(row[0] for row in recent_statuses)
            
            if len(unique_statuses) > 2:  # More than 2 different statuses in an hour
                anomaly = AnomalyDetection(
                    timestamp=datetime.now(),
                    service_name=metrics.service_name,
                    anomaly_type=AnomalyType.SERVICE_FLAPPING,
                    severity=AlertSeverity.WARNING,
                    description=f"Service status flapping detected: {len(unique_statuses)} different statuses in the last hour",
                    confidence_score=75.0,
                    affected_metrics={'status_changes': len(unique_statuses), 'current_status': metrics.status}
                )
                
                anomalies.append(anomaly)
                
        except Exception as e:
            self.logger.error(f"Status anomaly detection failed: {e}")
        
        return anomalies
    
    def _record_anomaly(self, anomaly: AnomalyDetection) -> None:
        """Record detected anomaly in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO anomalies 
                    (service_name, anomaly_type, severity, description, 
                     confidence_score, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    anomaly.service_name,
                    anomaly.anomaly_type.value,
                    anomaly.severity.value,
                    anomaly.description,
                    anomaly.confidence_score,
                    json.dumps(anomaly.affected_metrics)
                ))
                
        except Exception as e:
            self.logger.error(f"Failed to record anomaly: {e}")
    
    @performance_monitor
    def generate_predictions(self, service_name: str, hours_ahead: int = 24) -> List[PredictiveInsight]:
        """Generate predictive insights for service health"""
        predictions = []
        
        try:
            # Get historical data for prediction
            cutoff_date = datetime.now() - timedelta(days=self.learning_window)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT timestamp, availability_score, performance_score, response_time
                    FROM service_metrics
                    WHERE service_name = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                ''', (service_name, cutoff_date.isoformat()))
                
                data = cursor.fetchall()
            
            if len(data) < 20:  # Need enough data for prediction
                return predictions
            
            # Simple trend-based predictions
            predictions.extend(self._predict_availability_trend(service_name, data, hours_ahead))
            predictions.extend(self._predict_performance_trend(service_name, data, hours_ahead))
            
            # Record predictions
            for prediction in predictions:
                self._record_prediction(prediction, hours_ahead)
                
            return predictions
            
        except Exception as e:
            self.logger.error(f"Prediction generation failed: {e}")
            return []
    
    def _predict_availability_trend(
        self, 
        service_name: str, 
        data: List[Tuple], 
        hours_ahead: int
    ) -> List[PredictiveInsight]:
        """Predict availability trends using simple linear regression"""
        predictions = []
        
        try:
            # Extract availability data
            availability_data = [(i, row[1]) for i, row in enumerate(data) if row[1] is not None]
            
            if len(availability_data) < 10:
                return predictions
            
            # Simple linear trend calculation
            n = len(availability_data)
            sum_x = sum(point[0] for point in availability_data)
            sum_y = sum(point[1] for point in availability_data)
            sum_xy = sum(point[0] * point[1] for point in availability_data)
            sum_x2 = sum(point[0] ** 2 for point in availability_data)
            
            # Linear regression coefficients
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            intercept = (sum_y - slope * sum_x) / n
            
            # Predict future value
            future_x = n + (hours_ahead / 24 * 7)  # Approximate future data point
            predicted_availability = slope * future_x + intercept
            
            # Calculate confidence based on recent trend stability
            recent_values = [point[1] for point in availability_data[-10:]]
            recent_std = self._calculate_std(recent_values)
            confidence = max(20, 100 - (recent_std * 10))  # Lower confidence for higher volatility
            
            # Determine insight type based on trend
            if slope < -0.1:  # Declining trend
                insight_type = InsightType.PERFORMANCE_DEGRADATION
                description = f"Availability trend declining. Predicted: {predicted_availability:.1f}% in {hours_ahead}h"
            elif slope > 0.1:  # Improving trend
                insight_type = InsightType.PERFORMANCE_OPTIMIZATION
                description = f"Availability trend improving. Predicted: {predicted_availability:.1f}% in {hours_ahead}h"
            else:  # Stable
                insight_type = InsightType.CAPACITY_PLANNING
                description = f"Availability stable. Predicted: {predicted_availability:.1f}% in {hours_ahead}h"
            
            prediction = PredictiveInsight(
                timestamp=datetime.now(),
                service_name=service_name,
                insight_type=insight_type,
                description=description,
                confidence_score=confidence,
                time_horizon_hours=hours_ahead,
                predicted_values={'availability': predicted_availability, 'trend_slope': slope}
            )
            
            predictions.append(prediction)
            
        except Exception as e:
            self.logger.error(f"Availability prediction failed: {e}")
        
        return predictions
    
    def _predict_performance_trend(
        self, 
        service_name: str, 
        data: List[Tuple], 
        hours_ahead: int
    ) -> List[PredictiveInsight]:
        """Predict performance trends"""
        predictions = []
        
        try:
            # Similar to availability prediction but for performance
            performance_data = [(i, row[2]) for i, row in enumerate(data) if row[2] is not None]
            
            if len(performance_data) < 10:
                return predictions
            
            # Calculate trend
            n = len(performance_data)
            sum_x = sum(point[0] for point in performance_data)
            sum_y = sum(point[1] for point in performance_data)
            sum_xy = sum(point[0] * point[1] for point in performance_data)
            sum_x2 = sum(point[0] ** 2 for point in performance_data)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            intercept = (sum_y - slope * sum_x) / n
            
            future_x = n + (hours_ahead / 24 * 7)
            predicted_performance = slope * future_x + intercept
            
            recent_values = [point[1] for point in performance_data[-10:]]
            recent_std = self._calculate_std(recent_values)
            confidence = max(20, 100 - (recent_std * 5))
            
            if slope < -0.05:
                insight_type = InsightType.PERFORMANCE_DEGRADATION
                description = f"Performance declining. Predicted score: {predicted_performance:.1f} in {hours_ahead}h"
            elif slope > 0.05:
                insight_type = InsightType.PERFORMANCE_OPTIMIZATION
                description = f"Performance improving. Predicted score: {predicted_performance:.1f} in {hours_ahead}h"
            else:
                insight_type = InsightType.CAPACITY_PLANNING
                description = f"Performance stable. Predicted score: {predicted_performance:.1f} in {hours_ahead}h"
            
            prediction = PredictiveInsight(
                timestamp=datetime.now(),
                service_name=service_name,
                insight_type=insight_type,
                description=description,
                confidence_score=confidence,
                time_horizon_hours=hours_ahead,
                predicted_values={'performance': predicted_performance, 'trend_slope': slope}
            )
            
            predictions.append(prediction)
            
        except Exception as e:
            self.logger.error(f"Performance prediction failed: {e}")
        
        return predictions
    
    def _record_prediction(self, prediction: PredictiveInsight, hours_ahead: int) -> None:
        """Record prediction in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO predictions 
                    (service_name, prediction_type, prediction_value, 
                     confidence_score, time_horizon_hours, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    prediction.service_name,
                    prediction.insight_type.value,
                    list(prediction.predicted_values.values())[0] if prediction.predicted_values else 0,
                    prediction.confidence_score,
                    hours_ahead,
                    json.dumps(prediction.predicted_values)
                ))
                
        except Exception as e:
            self.logger.error(f"Failed to record prediction: {e}")
    
    @performance_monitor
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Recent anomalies
                cursor = conn.execute('''
                    SELECT COUNT(*) as count, severity 
                    FROM anomalies 
                    WHERE timestamp >= datetime('now', '-24 hours')
                    GROUP BY severity
                ''')
                anomaly_counts = {row[1]: row[0] for row in cursor.fetchall()}
                
                # Service health scores
                cursor = conn.execute('''
                    SELECT service_name, AVG(availability_score) as avg_availability,
                           AVG(performance_score) as avg_performance
                    FROM service_metrics
                    WHERE timestamp >= datetime('now', '-24 hours')
                    GROUP BY service_name
                    ORDER BY avg_availability DESC
                ''')
                service_health = cursor.fetchall()
                
                # Recent predictions
                cursor = conn.execute('''
                    SELECT COUNT(*) as count, prediction_type
                    FROM predictions
                    WHERE timestamp >= datetime('now', '-24 hours')
                    GROUP BY prediction_type
                ''')
                prediction_counts = {row[1]: row[0] for row in cursor.fetchall()}
                
                # Data quality metrics
                cursor = conn.execute('''
                    SELECT COUNT(*) as total_metrics,
                           COUNT(DISTINCT service_name) as unique_services,
                           MIN(timestamp) as oldest_data,
                           MAX(timestamp) as newest_data
                    FROM service_metrics
                ''')
                data_quality = cursor.fetchone()
                
            return {
                'anomaly_counts': anomaly_counts,
                'service_health': [
                    {
                        'service_name': row[0],
                        'avg_availability': row[1],
                        'avg_performance': row[2]
                    }
                    for row in service_health
                ],
                'prediction_counts': prediction_counts,
                'data_quality': {
                    'total_metrics': data_quality[0],
                    'unique_services': data_quality[1],
                    'oldest_data': data_quality[2],
                    'newest_data': data_quality[3]
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate analytics summary: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """Clean up old analytics data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_path) as conn:
                # Count records to be deleted
                cursor = conn.execute('''
                    SELECT COUNT(*) FROM service_metrics WHERE timestamp < ?
                ''', (cutoff_date.isoformat(),))
                
                deleted_count = cursor.fetchone()[0]
                
                # Delete old records
                conn.execute('DELETE FROM service_metrics WHERE timestamp < ?', 
                           (cutoff_date.isoformat(),))
                conn.execute('DELETE FROM anomalies WHERE timestamp < ?', 
                           (cutoff_date.isoformat(),))
                conn.execute('DELETE FROM predictions WHERE timestamp < ?', 
                           (cutoff_date.isoformat(),))
                
                # Vacuum database to reclaim space
                conn.execute('VACUUM')
                
            self.logger.info(f"Cleaned up {deleted_count} old analytics records")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup analytics data: {e}")
            return 0


# Convenience functions for easy access
_analytics_instance = None

def get_analytics() -> AIAnalytics:
    """Get singleton analytics instance"""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = AIAnalytics()
    return _analytics_instance

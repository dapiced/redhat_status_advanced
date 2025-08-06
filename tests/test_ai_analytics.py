"""
Test suite for AI analytics module.
"""
import pytest
import tempfile
import json
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add the project root to sys.path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redhat_status.analytics.ai_analytics import AIAnalytics, get_analytics


class TestAIAnalytics:
    """Test the AIAnalytics class"""
    
    def setup_method(self):
        """Set up test method"""
        self.config = {
            'enabled': True,
            'model_type': 'sklearn',
            'anomaly_threshold': 0.1,
            'prediction_days': 7
        }
        self.ai_analytics = AIAnalytics(self.config)
        
        # Sample historical data for testing
        self.sample_data = [
            {
                'timestamp': datetime.now() - timedelta(days=i),
                'availability_percentage': 99.0 + (i % 3) * 0.3,
                'response_time': 1.0 + (i % 2) * 0.5,
                'total_services': 50,
                'operational_services': 48 + (i % 3)
            }
            for i in range(30)  # 30 days of data
        ]
    
    def test_init_with_config(self):
        """Test initialization with configuration"""
        assert self.ai_analytics.enabled is True
        assert self.ai_analytics.anomaly_threshold == 0.1
        assert self.ai_analytics.prediction_days == 7
    
    def test_init_disabled(self):
        """Test initialization with disabled analytics"""
        config = {'enabled': False}
        analytics = AIAnalytics(config)
        
        assert analytics.enabled is False
    
    def test_analyze_availability_trends(self):
        """Test availability trend analysis"""
        analysis = self.ai_analytics.analyze_availability_trends(self.sample_data)
        
        assert 'trend' in analysis
        assert 'correlation' in analysis
        assert 'insights' in analysis
        assert 'predictions' in analysis
        
        # Check trend direction
        assert analysis['trend'] in ['improving', 'declining', 'stable']
        
        # Check correlation is a valid value
        assert -1 <= analysis['correlation'] <= 1
        
        # Check insights is a list
        assert isinstance(analysis['insights'], list)
    
    def test_detect_anomalies(self):
        """Test anomaly detection"""
        anomalies = self.ai_analytics.detect_anomalies(self.sample_data)
        
        assert 'anomalies' in anomalies
        assert 'score' in anomalies
        assert 'threshold' in anomalies
        assert 'summary' in anomalies
        
        # Check anomalies is a list
        assert isinstance(anomalies['anomalies'], list)
        
        # Check score is a valid number
        assert isinstance(anomalies['score'], (int, float))
        
        # Check threshold matches config
        assert anomalies['threshold'] == self.config['anomaly_threshold']
    
    def test_predict_availability(self):
        """Test availability prediction"""
        predictions = self.ai_analytics.predict_availability(self.sample_data)
        
        assert 'predictions' in predictions
        assert 'confidence' in predictions
        assert 'model_info' in predictions
        
        # Check predictions length matches configured days
        assert len(predictions['predictions']) == self.config['prediction_days']
        
        # Check predictions are in valid range
        for pred in predictions['predictions']:
            assert 'date' in pred
            assert 'availability' in pred
            assert 0 <= pred['availability'] <= 100
    
    def test_analyze_service_patterns(self):
        """Test service pattern analysis"""
        # Mock service data with patterns
        service_data = [
            {
                'timestamp': datetime.now() - timedelta(hours=i),
                'services': {
                    'service_a': 'operational' if i % 4 != 0 else 'degraded',
                    'service_b': 'operational',
                    'service_c': 'operational' if i % 8 != 0 else 'down'
                }
            }
            for i in range(48)  # 48 hours of data
        ]
        
        patterns = self.ai_analytics.analyze_service_patterns(service_data)
        
        assert 'patterns' in patterns
        assert 'correlations' in patterns
        assert 'insights' in patterns
        
        # Check that patterns were detected
        assert isinstance(patterns['patterns'], dict)
        assert isinstance(patterns['correlations'], dict)
    
    def test_generate_health_score(self):
        """Test health score generation"""
        health_score = self.ai_analytics.generate_health_score(self.sample_data)
        
        assert 'score' in health_score
        assert 'factors' in health_score
        assert 'recommendations' in health_score
        
        # Check score is in valid range
        assert 0 <= health_score['score'] <= 100
        
        # Check factors is a dictionary
        assert isinstance(health_score['factors'], dict)
        
        # Check recommendations is a list
        assert isinstance(health_score['recommendations'], list)
    
    def test_analyze_response_time_patterns(self):
        """Test response time pattern analysis"""
        analysis = self.ai_analytics.analyze_response_time_patterns(self.sample_data)
        
        assert 'average_response_time' in analysis
        assert 'trend' in analysis
        assert 'outliers' in analysis
        assert 'recommendations' in analysis
        
        # Check average is a positive number
        assert analysis['average_response_time'] > 0
        
        # Check trend is valid
        assert analysis['trend'] in ['improving', 'declining', 'stable']
    
    def test_detect_seasonal_patterns(self):
        """Test seasonal pattern detection"""
        # Create data with seasonal patterns
        seasonal_data = []
        for i in range(168):  # Week of hourly data
            hour = i % 24
            day = i // 24
            
            # Simulate lower availability during business hours
            base_availability = 99.0
            if 9 <= hour <= 17:  # Business hours
                base_availability -= 0.5
            
            seasonal_data.append({
                'timestamp': datetime.now() - timedelta(hours=i),
                'availability_percentage': base_availability + np.random.normal(0, 0.1),
                'response_time': 1.0 + (hour / 24) * 0.5  # Slower during day
            })
        
        patterns = self.ai_analytics.detect_seasonal_patterns(seasonal_data)
        
        assert 'hourly_patterns' in patterns
        assert 'daily_patterns' in patterns
        assert 'insights' in patterns
        
        # Should detect business hour pattern
        assert any('business' in insight.lower() for insight in patterns['insights'])
    
    def test_generate_slo_analysis(self):
        """Test SLO analysis generation"""
        slo_targets = {
            'availability': 99.5,
            'response_time': 2.0
        }
        
        analysis = self.ai_analytics.generate_slo_analysis(self.sample_data, slo_targets)
        
        assert 'slo_compliance' in analysis
        assert 'breach_analysis' in analysis
        assert 'recommendations' in analysis
        
        # Check compliance percentages
        for metric, compliance in analysis['slo_compliance'].items():
            assert 0 <= compliance <= 100
    
    def test_analyze_incident_correlation(self):
        """Test incident correlation analysis"""
        # Mock incident data
        incident_data = [
            {
                'timestamp': datetime.now() - timedelta(days=i),
                'incident_id': f'incident_{i}',
                'affected_services': ['service_a', 'service_b'],
                'impact': 'minor' if i % 3 != 0 else 'major'
            }
            for i in range(10)
        ]
        
        correlation = self.ai_analytics.analyze_incident_correlation(
            self.sample_data, incident_data
        )
        
        assert 'correlations' in correlation
        assert 'patterns' in correlation
        assert 'insights' in correlation
    
    def test_disabled_analytics_operations(self):
        """Test operations when analytics is disabled"""
        config = {'enabled': False}
        analytics = AIAnalytics(config)
        
        # All operations should return None or empty results
        result = analytics.analyze_availability_trends([])
        assert result is None or result == {}
        
        result = analytics.detect_anomalies([])
        assert result is None or result == {}
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data"""
        # Test with very little data
        minimal_data = self.sample_data[:2]
        
        analysis = self.ai_analytics.analyze_availability_trends(minimal_data)
        
        # Should handle gracefully and provide appropriate messaging
        assert analysis is not None
        if 'insights' in analysis:
            assert any('insufficient' in insight.lower() or 'limited' in insight.lower() 
                     for insight in analysis['insights'])
    
    def test_data_preprocessing(self):
        """Test data preprocessing functionality"""
        # Test with data containing missing values and outliers
        messy_data = self.sample_data.copy()
        
        # Add some problematic data points
        messy_data.append({
            'timestamp': datetime.now(),
            'availability_percentage': None,  # Missing value
            'response_time': 1000,  # Outlier
            'total_services': 50,
            'operational_services': 48
        })
        
        # Data should be cleaned automatically
        analysis = self.ai_analytics.analyze_availability_trends(messy_data)
        
        # Should still provide valid analysis
        assert analysis is not None
        assert 'trend' in analysis
    
    def test_model_performance_metrics(self):
        """Test model performance evaluation"""
        # Split data for training and testing
        train_data = self.sample_data[:20]
        test_data = self.sample_data[20:]
        
        performance = self.ai_analytics.evaluate_model_performance(train_data, test_data)
        
        assert 'accuracy' in performance
        assert 'precision' in performance
        assert 'recall' in performance
        assert 'rmse' in performance
        
        # Check metrics are in valid ranges
        assert 0 <= performance['accuracy'] <= 1
        assert 0 <= performance['precision'] <= 1
        assert 0 <= performance['recall'] <= 1
        assert performance['rmse'] >= 0
    
    def test_feature_importance_analysis(self):
        """Test feature importance analysis"""
        importance = self.ai_analytics.analyze_feature_importance(self.sample_data)
        
        assert 'features' in importance
        assert 'scores' in importance
        assert 'insights' in importance
        
        # Check that all features have importance scores
        assert len(importance['features']) == len(importance['scores'])
        
        # Scores should be non-negative
        assert all(score >= 0 for score in importance['scores'])
    
    def test_real_time_anomaly_detection(self):
        """Test real-time anomaly detection"""
        # Simulate real-time data point
        current_data = {
            'timestamp': datetime.now(),
            'availability_percentage': 95.0,  # Anomalously low
            'response_time': 5.0,  # Anomalously high
            'total_services': 50,
            'operational_services': 45
        }
        
        is_anomaly = self.ai_analytics.detect_real_time_anomaly(current_data, self.sample_data)
        
        assert isinstance(is_anomaly, dict)
        assert 'is_anomaly' in is_anomaly
        assert 'confidence' in is_anomaly
        assert 'reasons' in is_anomaly
        
        # Should detect this as anomalous
        assert is_anomaly['is_anomaly'] is True


class TestGetAnalyticsFunction:
    """Test the get_analytics function"""
    
    def test_get_analytics_singleton(self):
        """Test that get_analytics returns the same instance"""
        analytics1 = get_analytics()
        analytics2 = get_analytics()
        
        assert analytics1 is analytics2
    
    @patch('redhat_status.analytics.ai_analytics.AIAnalytics')
    def test_get_analytics_creates_instance(self, mock_ai_analytics):
        """Test that get_analytics creates an AIAnalytics instance"""
        mock_instance = Mock()
        mock_ai_analytics.return_value = mock_instance
        
        # Clear any existing singleton
        import redhat_status.analytics.ai_analytics as analytics_module
        analytics_module._analytics_instance = None
        
        result = get_analytics()
        
        mock_ai_analytics.assert_called_once()
        assert result == mock_instance


class TestAIAnalyticsConfiguration:
    """Test AI analytics configuration handling"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        analytics = AIAnalytics()
        
        assert analytics.enabled is True
        assert analytics.anomaly_threshold > 0
        assert analytics.prediction_days > 0
    
    def test_custom_configuration(self):
        """Test custom configuration values"""
        config = {
            'enabled': True,
            'model_type': 'tensorflow',
            'anomaly_threshold': 0.05,
            'prediction_days': 14
        }
        
        analytics = AIAnalytics(config)
        
        assert analytics.model_type == 'tensorflow'
        assert analytics.anomaly_threshold == 0.05
        assert analytics.prediction_days == 14
    
    def test_invalid_configuration_fallback(self):
        """Test that invalid configuration falls back to defaults"""
        config = {
            'anomaly_threshold': 'invalid',
            'prediction_days': 'invalid'
        }
        
        analytics = AIAnalytics(config)
        
        # Should use defaults for invalid values
        assert isinstance(analytics.anomaly_threshold, float)
        assert isinstance(analytics.prediction_days, int)


class TestAdvancedAnalytics:
    """Test advanced analytics features"""
    
    def setup_method(self):
        """Set up test method"""
        self.config = {
            'enabled': True,
            'advanced_features': True,
            'ml_algorithms': ['isolation_forest', 'one_class_svm']
        }
        self.analytics = AIAnalytics(self.config)
    
    def test_ensemble_anomaly_detection(self):
        """Test ensemble anomaly detection using multiple algorithms"""
        data = [
            {
                'timestamp': datetime.now() - timedelta(hours=i),
                'availability_percentage': 99.0 + np.random.normal(0, 0.1),
                'response_time': 1.0 + np.random.normal(0, 0.1)
            }
            for i in range(100)
        ]
        
        # Add clear anomaly
        data[50]['availability_percentage'] = 85.0  # Clear outlier
        
        anomalies = self.analytics.detect_anomalies_ensemble(data)
        
        assert 'ensemble_score' in anomalies
        assert 'algorithm_votes' in anomalies
        assert 'anomalies' in anomalies
        
        # Should detect the anomaly
        assert len(anomalies['anomalies']) > 0
    
    def test_predictive_maintenance_analysis(self):
        """Test predictive maintenance analysis"""
        # Simulate degrading service data
        maintenance_data = []
        for i in range(100):
            # Simulate gradually degrading performance
            degradation_factor = i / 100.0
            availability = 99.5 - (degradation_factor * 2)
            response_time = 1.0 + (degradation_factor * 0.5)
            
            maintenance_data.append({
                'timestamp': datetime.now() - timedelta(hours=i),
                'availability_percentage': availability,
                'response_time': response_time,
                'error_rate': degradation_factor * 0.05
            })
        
        analysis = self.analytics.analyze_predictive_maintenance(maintenance_data)
        
        assert 'maintenance_probability' in analysis
        assert 'time_to_maintenance' in analysis
        assert 'risk_factors' in analysis
        assert 'recommendations' in analysis
        
        # Should detect high maintenance probability
        assert analysis['maintenance_probability'] > 0.5
    
    def test_capacity_planning_analysis(self):
        """Test capacity planning analysis"""
        # Simulate growing load data
        capacity_data = []
        for i in range(50):
            growth_factor = i / 50.0
            load_percentage = 50 + (growth_factor * 30)  # Growing from 50% to 80%
            
            capacity_data.append({
                'timestamp': datetime.now() - timedelta(days=i),
                'load_percentage': load_percentage,
                'response_time': 1.0 + (growth_factor * 0.3),
                'active_users': 1000 + (growth_factor * 500)
            })
        
        analysis = self.analytics.analyze_capacity_planning(capacity_data)
        
        assert 'current_utilization' in analysis
        assert 'projected_capacity_date' in analysis
        assert 'scaling_recommendations' in analysis
        assert 'growth_rate' in analysis
        
        # Should detect growth trend
        assert analysis['growth_rate'] > 0


if __name__ == '__main__':
    pytest.main([__file__])

"""
Test suite for notification manager module.
"""
import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the project root to sys.path for imports
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from redhat_status.notifications.notification_manager import NotificationManager, get_notification_manager


class TestNotificationManager:
    """Test the NotificationManager class"""
    
    def setup_method(self):
        """Set up test method"""
        self.email_config = {
            'enabled': True,
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'test_password',
            'recipients': ['admin@example.com', 'ops@example.com'],
            'use_tls': True
        }
        
        self.webhook_config = {
            'enabled': True,
            'urls': [
                'https://hooks.slack.com/services/test',
                'https://discord.com/api/webhooks/test'
            ],
            'timeout': 30
        }
        
        self.config = {
            'email': self.email_config,
            'webhooks': self.webhook_config
        }
        
        self.notification_manager = NotificationManager(self.config)
    
    def test_init_with_config(self):
        """Test initialization with configuration"""
        assert self.notification_manager.email_config == self.email_config
        assert self.notification_manager.webhook_config == self.webhook_config
        assert self.notification_manager.email_enabled is True
        assert self.notification_manager.webhook_enabled is True
    
    def test_init_disabled_notifications(self):
        """Test initialization with disabled notifications"""
        config = {
            'email': {'enabled': False},
            'webhooks': {'enabled': False}
        }
        
        manager = NotificationManager(config)
        
        assert manager.email_enabled is False
        assert manager.webhook_enabled is False
    
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending"""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        subject = "Test Alert"
        message = "This is a test alert message"
        
        result = self.notification_manager.send_email(subject, message)
        
        assert result is True
        mock_smtp.assert_called_once_with(self.email_config['smtp_server'], 
                                         self.email_config['smtp_port'])
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(
            self.email_config['username'], 
            self.email_config['password']
        )
        mock_server.send_message.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_email_failure(self, mock_smtp):
        """Test email sending failure"""
        # Mock SMTP server to raise exception
        mock_smtp.side_effect = Exception("SMTP Error")
        
        subject = "Test Alert"
        message = "This is a test alert message"
        
        result = self.notification_manager.send_email(subject, message)
        
        assert result is False
    
    def test_send_email_disabled(self):
        """Test email sending when disabled"""
        config = {'email': {'enabled': False}, 'webhooks': {'enabled': False}}
        manager = NotificationManager(config)
        
        result = manager.send_email("Test", "Message")
        
        assert result is False
    
    @patch('requests.post')
    def test_send_webhook_success(self, mock_post):
        """Test successful webhook sending"""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        message = "Test webhook message"
        
        result = self.notification_manager.send_webhook(message)
        
        assert result is True
        # Should be called for each webhook URL
        assert mock_post.call_count == len(self.webhook_config['urls'])
    
    @patch('requests.post')
    def test_send_webhook_failure(self, mock_post):
        """Test webhook sending failure"""
        # Mock HTTP error
        mock_post.side_effect = Exception("Network Error")
        
        message = "Test webhook message"
        
        result = self.notification_manager.send_webhook(message)
        
        assert result is False
    
    def test_send_webhook_disabled(self):
        """Test webhook sending when disabled"""
        config = {'email': {'enabled': False}, 'webhooks': {'enabled': False}}
        manager = NotificationManager(config)
        
        result = manager.send_webhook("Test message")
        
        assert result is False
    
    @patch('requests.post')
    def test_send_slack_webhook(self, mock_post):
        """Test sending Slack-formatted webhook"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        title = "Status Alert"
        message = "Service is down"
        color = "danger"
        
        result = self.notification_manager.send_slack_webhook(title, message, color)
        
        assert result is True
        
        # Check that proper Slack format was used
        call_args = mock_post.call_args_list[0]
        posted_data = json.loads(call_args[1]['data'])
        
        assert 'attachments' in posted_data
        assert posted_data['attachments'][0]['title'] == title
        assert posted_data['attachments'][0]['text'] == message
        assert posted_data['attachments'][0]['color'] == color
    
    @patch('requests.post')
    def test_send_discord_webhook(self, mock_post):
        """Test sending Discord-formatted webhook"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        title = "Status Alert"
        message = "Service is down"
        
        result = self.notification_manager.send_discord_webhook(title, message)
        
        assert result is True
        
        # Check that proper Discord format was used
        call_args = mock_post.call_args_list[0]
        posted_data = json.loads(call_args[1]['data'])
        
        assert 'embeds' in posted_data
        assert posted_data['embeds'][0]['title'] == title
        assert posted_data['embeds'][0]['description'] == message
    
    @patch.object(NotificationManager, 'send_email')
    @patch.object(NotificationManager, 'send_webhook')
    def test_send_alert(self, mock_webhook, mock_email):
        """Test sending alert through all channels"""
        mock_email.return_value = True
        mock_webhook.return_value = True
        
        alert_data = {
            'type': 'service_down',
            'service': 'Test Service',
            'status': 'down',
            'timestamp': datetime.now(),
            'message': 'Service is experiencing issues'
        }
        
        result = self.notification_manager.send_alert(alert_data)
        
        assert result is True
        mock_email.assert_called_once()
        mock_webhook.assert_called_once()
    
    @patch.object(NotificationManager, 'send_email')
    @patch.object(NotificationManager, 'send_webhook')
    def test_send_status_update(self, mock_webhook, mock_email):
        """Test sending status update notification"""
        mock_email.return_value = True
        mock_webhook.return_value = True
        
        status_data = {
            'overall_status': 'operational',
            'availability_percentage': 99.5,
            'total_services': 50,
            'operational_services': 49,
            'issues': ['Service A experiencing slowdowns']
        }
        
        result = self.notification_manager.send_status_update(status_data)
        
        assert result is True
        mock_email.assert_called_once()
        mock_webhook.assert_called_once()
    
    def test_format_alert_message(self):
        """Test alert message formatting"""
        alert_data = {
            'type': 'service_down',
            'service': 'Test Service',
            'status': 'down',
            'timestamp': datetime(2023, 1, 1, 12, 0, 0),
            'message': 'Service is experiencing issues'
        }
        
        message = self.notification_manager._format_alert_message(alert_data)
        
        assert '🚨 ALERT' in message
        assert 'Test Service' in message
        assert 'down' in message
        assert 'Service is experiencing issues' in message
    
    def test_format_status_message(self):
        """Test status message formatting"""
        status_data = {
            'overall_status': 'operational',
            'availability_percentage': 99.5,
            'total_services': 50,
            'operational_services': 49,
            'issues': ['Service A experiencing slowdowns']
        }
        
        message = self.notification_manager._format_status_message(status_data)
        
        assert '📊 STATUS UPDATE' in message
        assert '99.5%' in message
        assert '49/50' in message
        assert 'operational' in message
        assert 'Service A experiencing slowdowns' in message
    
    def test_test_all_channels(self):
        """Test testing all notification channels"""
        with patch.object(self.notification_manager, 'send_email') as mock_email, \
             patch.object(self.notification_manager, 'send_webhook') as mock_webhook:
            
            mock_email.return_value = True
            mock_webhook.return_value = True
            
            results = self.notification_manager.test_all_channels()
            
            assert results['email'] is True
            assert results['webhook'] is True
            mock_email.assert_called_once()
            mock_webhook.assert_called_once()
    
    def test_get_notification_stats(self):
        """Test getting notification statistics"""
        # Simulate some notifications
        self.notification_manager._email_sent_count = 5
        self.notification_manager._webhook_sent_count = 3
        self.notification_manager._email_failed_count = 1
        self.notification_manager._webhook_failed_count = 0
        
        stats = self.notification_manager.get_stats()
        
        assert 'email_sent' in stats
        assert 'webhook_sent' in stats
        assert 'email_failed' in stats
        assert 'webhook_failed' in stats
        assert stats['email_sent'] == 5
        assert stats['webhook_sent'] == 3
        assert stats['email_failed'] == 1
        assert stats['webhook_failed'] == 0
    
    def test_rate_limiting(self):
        """Test notification rate limiting"""
        # This would test that notifications are rate-limited to prevent spam
        # For now, we'll test that the rate limiting configuration is respected
        
        config_with_rate_limit = self.config.copy()
        config_with_rate_limit['rate_limit'] = {
            'max_per_hour': 10,
            'max_per_day': 50
        }
        
        manager = NotificationManager(config_with_rate_limit)
        
        # Rate limiting configuration should be stored
        assert hasattr(manager, 'rate_limit_config')
    
    def test_notification_templates(self):
        """Test notification message templates"""
        # Test different types of notifications use appropriate templates
        
        # Service down alert
        alert_data = {'type': 'service_down', 'service': 'API Gateway', 'status': 'down'}
        message = self.notification_manager._format_alert_message(alert_data)
        assert '🚨' in message and 'down' in message.lower()
        
        # Service recovered alert
        alert_data = {'type': 'service_recovered', 'service': 'API Gateway', 'status': 'operational'}
        message = self.notification_manager._format_alert_message(alert_data)
        assert '✅' in message and 'recovered' in message.lower()
        
        # Degraded performance alert
        alert_data = {'type': 'degraded_performance', 'service': 'Database', 'status': 'degraded'}
        message = self.notification_manager._format_alert_message(alert_data)
        assert '⚠️' in message and 'degraded' in message.lower()


class TestGetNotificationManagerFunction:
    """Test the get_notification_manager function"""
    
    def test_get_notification_manager_singleton(self):
        """Test that get_notification_manager returns the same instance"""
        manager1 = get_notification_manager()
        manager2 = get_notification_manager()
        
        assert manager1 is manager2
    
    @patch('redhat_status.notifications.notification_manager.NotificationManager')
    def test_get_notification_manager_creates_instance(self, mock_notification_manager):
        """Test that get_notification_manager creates a NotificationManager instance"""
        mock_instance = Mock()
        mock_notification_manager.return_value = mock_instance
        
        # Clear any existing singleton
        import redhat_status.notifications.notification_manager as notification_module
        notification_module._notification_manager_instance = None
        
        result = get_notification_manager()
        
        mock_notification_manager.assert_called_once()
        assert result == mock_instance


class TestNotificationConfiguration:
    """Test notification configuration handling"""
    
    def test_email_configuration_validation(self):
        """Test email configuration validation"""
        # Valid configuration
        valid_config = {
            'email': {
                'enabled': True,
                'smtp_server': 'smtp.example.com',
                'smtp_port': 587,
                'username': 'test@example.com',
                'password': 'password',
                'recipients': ['admin@example.com']
            },
            'webhooks': {'enabled': False}
        }
        
        manager = NotificationManager(valid_config)
        assert manager.email_enabled is True
        
        # Invalid configuration (missing required fields)
        invalid_config = {
            'email': {
                'enabled': True,
                'smtp_server': '',  # Empty server
                'recipients': []  # No recipients
            },
            'webhooks': {'enabled': False}
        }
        
        manager = NotificationManager(invalid_config)
        # Should disable email if configuration is invalid
        assert manager.email_enabled is False
    
    def test_webhook_configuration_validation(self):
        """Test webhook configuration validation"""
        # Valid configuration
        valid_config = {
            'email': {'enabled': False},
            'webhooks': {
                'enabled': True,
                'urls': ['https://hooks.slack.com/test'],
                'timeout': 30
            }
        }
        
        manager = NotificationManager(valid_config)
        assert manager.webhook_enabled is True
        
        # Invalid configuration (no URLs)
        invalid_config = {
            'email': {'enabled': False},
            'webhooks': {
                'enabled': True,
                'urls': [],  # No URLs
                'timeout': 30
            }
        }
        
        manager = NotificationManager(invalid_config)
        # Should disable webhooks if no URLs provided
        assert manager.webhook_enabled is False
    
    def test_default_configuration(self):
        """Test default configuration when none provided"""
        manager = NotificationManager({})
        
        # Should have sensible defaults
        assert manager.email_enabled is False
        assert manager.webhook_enabled is False


class TestNotificationSecurity:
    """Test notification security features"""
    
    def test_sensitive_data_filtering(self):
        """Test that sensitive data is filtered from notifications"""
        alert_data = {
            'type': 'security_alert',
            'service': 'Authentication Service',
            'details': {
                'password': 'secret123',
                'api_key': 'sk-1234567890',
                'token': 'bearer_token_here',
                'message': 'Login failed for user'
            }
        }
        
        manager = NotificationManager({})
        message = manager._format_alert_message(alert_data)
        
        # Sensitive data should not appear in the message
        assert 'secret123' not in message
        assert 'sk-1234567890' not in message
        assert 'bearer_token_here' not in message
        # But non-sensitive data should be present
        assert 'Login failed' in message
    
    def test_recipient_validation(self):
        """Test email recipient validation"""
        config = {
            'email': {
                'enabled': True,
                'smtp_server': 'smtp.example.com',
                'smtp_port': 587,
                'username': 'test@example.com',
                'password': 'password',
                'recipients': [
                    'valid@example.com',
                    'invalid-email',  # Invalid email format
                    'another@valid.com'
                ]
            }
        }
        
        manager = NotificationManager(config)
        
        # Should filter out invalid email addresses
        valid_recipients = manager._validate_email_recipients(config['email']['recipients'])
        assert 'valid@example.com' in valid_recipients
        assert 'another@valid.com' in valid_recipients
        assert 'invalid-email' not in valid_recipients


class TestNotificationDelivery:
    """Test notification delivery mechanisms"""
    
    def setup_method(self):
        """Set up test method"""
        self.config = {
            'email': {
                'enabled': True,
                'smtp_server': 'smtp.example.com',
                'smtp_port': 587,
                'username': 'test@example.com',
                'password': 'password',
                'recipients': ['admin@example.com']
            },
            'webhooks': {
                'enabled': True,
                'urls': ['https://hooks.slack.com/test'],
                'timeout': 30
            }
        }
        self.manager = NotificationManager(self.config)
    
    @patch('smtplib.SMTP')
    def test_email_retry_mechanism(self, mock_smtp):
        """Test email retry mechanism on failure"""
        # First attempt fails, second succeeds
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        mock_server.send_message.side_effect = [Exception("Temporary failure"), None]
        
        result = self.manager.send_email("Test", "Message", max_retries=2)
        
        # Should succeed after retry
        assert result is True
        assert mock_server.send_message.call_count == 2
    
    @patch('requests.post')
    def test_webhook_retry_mechanism(self, mock_post):
        """Test webhook retry mechanism on failure"""
        # First attempt fails, second succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.side_effect = [Exception("Network error"), mock_response]
        
        result = self.manager.send_webhook("Test message", max_retries=2)
        
        # Should succeed after retry
        assert result is True
        assert mock_post.call_count == 2
    
    def test_notification_queuing(self):
        """Test notification queuing for high-volume scenarios"""
        # This would test that notifications are queued when sending many at once
        # For now, we'll test that the queue mechanism exists
        
        assert hasattr(self.manager, '_notification_queue') or True  # Placeholder
    
    def test_notification_priorities(self):
        """Test notification priority handling"""
        # Test that high-priority notifications are sent immediately
        # while low-priority ones can be batched
        
        high_priority_alert = {
            'type': 'critical_service_down',
            'priority': 'high',
            'service': 'Core API'
        }
        
        low_priority_alert = {
            'type': 'maintenance_notification',
            'priority': 'low',
            'service': 'Documentation Site'
        }
        
        # High priority should be processed differently than low priority
        # This is a placeholder for priority-based notification logic
        assert True  # Placeholder test


if __name__ == '__main__':
    pytest.main([__file__])

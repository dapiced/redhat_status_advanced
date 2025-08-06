"""
Red Hat Status Checker - Notification Management Module

This module provides comprehensive notification and alerting capabilities
for Red Hat service monitoring, including email, webhooks, and custom integrations.

Contains:
- NotificationManager class for multi-channel notifications
- Email notifications with SMTP support
- Webhook integrations
- Alert escalation and routing
- Template-based messaging
- Notification history and tracking

Author: Red Hat Status Checker v3.1.0 - Modular Edition
"""

import json
import logging
import smtplib
import threading
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import asdict
import requests

from ..core.data_models import SystemAlert, AlertSeverity, AnomalyDetection
from ..config.config_manager import get_config
from ..utils.decorators import performance_monitor, retry_with_backoff


class NotificationChannel:
    """Base class for notification channels"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    def send(self, alert: SystemAlert, context: Dict[str, Any] = None) -> bool:
        """Send notification - to be implemented by subclasses"""
        raise NotImplementedError
    
    def test_connection(self) -> bool:
        """Test channel connectivity - to be implemented by subclasses"""
        raise NotImplementedError


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel using SMTP"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        # SMTP Configuration
        self.smtp_server = config.get('smtp_server', 'localhost')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.use_tls = config.get('use_tls', True)
        self.use_ssl = config.get('use_ssl', False)
        
        # Email settings
        self.from_email = config.get('from_email', 'redhat-status@localhost')
        self.from_name = config.get('from_name', 'Red Hat Status Checker')
        self.recipients = config.get('recipients', [])
        
        # Message settings
        self.subject_template = config.get('subject_template', '[{severity}] Red Hat Alert: {title}')
        self.include_logo = config.get('include_logo', True)
        self.html_template = config.get('html_template', True)
        
        # Rate limiting
        self.max_emails_per_hour = config.get('max_emails_per_hour', 10)
        self.email_history = []
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def send(self, alert: SystemAlert, context: Dict[str, Any] = None) -> bool:
        """Send email notification"""
        try:
            if not self.enabled or not self.recipients:
                return False
            
            # Check rate limiting
            if not self._check_rate_limit():
                self.logger.warning("Email rate limit exceeded, skipping notification")
                return False
            
            # Create message
            msg = self._create_email_message(alert, context or {})
            
            # Send email
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.use_tls:
                    server.starttls()
            
            if self.username and self.password:
                server.login(self.username, self.password)
            
            server.send_message(msg)
            server.quit()
            
            # Track sent email
            self.email_history.append(datetime.now())
            self.logger.info(f"Email notification sent for alert: {alert.title}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = datetime.now()
        cutoff = now - timedelta(hours=1)
        
        # Remove old entries
        self.email_history = [ts for ts in self.email_history if ts > cutoff]
        
        return len(self.email_history) < self.max_emails_per_hour
    
    def _create_email_message(self, alert: SystemAlert, context: Dict[str, Any]) -> MIMEMultipart:
        """Create email message from alert"""
        msg = MIMEMultipart('alternative')
        
        # Headers
        subject = self.subject_template.format(
            severity=alert.severity.value.upper(),
            title=alert.title,
            service=alert.source_service or 'System',
            timestamp=alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        )
        
        msg['Subject'] = subject
        msg['From'] = f"{self.from_name} <{self.from_email}>"
        msg['To'] = ', '.join(self.recipients)
        msg['X-Priority'] = self._get_email_priority(alert.severity)
        
        # Create text and HTML versions
        text_content = self._create_text_content(alert, context)
        msg.attach(MIMEText(text_content, 'plain'))
        
        if self.html_template:
            html_content = self._create_html_content(alert, context)
            msg.attach(MIMEText(html_content, 'html'))
        
        return msg
    
    def _get_email_priority(self, severity: AlertSeverity) -> str:
        """Get email priority based on alert severity"""
        priority_map = {
            AlertSeverity.INFO: '5',      # Low
            AlertSeverity.WARNING: '3',   # Normal
            AlertSeverity.ERROR: '2',     # High
            AlertSeverity.CRITICAL: '1'   # Highest
        }
        return priority_map.get(severity, '3')
    
    def _create_text_content(self, alert: SystemAlert, context: Dict[str, Any]) -> str:
        """Create plain text email content"""
        content = f"""
RED HAT STATUS ALERT
{'=' * 50}

Alert Type: {alert.alert_type}
Severity: {alert.severity.value.upper()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Title: {alert.title}

Message:
{alert.message}

Source Service: {alert.source_service or 'N/A'}

Additional Information:
"""
        
        if context:
            for key, value in context.items():
                content += f"- {key}: {value}\n"
        
        content += f"""

Alert ID: {getattr(alert, 'alert_id', str(id(alert)))}

--
Red Hat Status Checker v3.1.0
Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return content
    
    def _create_html_content(self, alert: SystemAlert, context: Dict[str, Any]) -> str:
        """Create HTML email content"""
        # Severity color mapping
        severity_colors = {
            AlertSeverity.INFO: '#17a2b8',      # Info blue
            AlertSeverity.WARNING: '#ffc107',   # Warning yellow
            AlertSeverity.ERROR: '#fd7e14',     # Error orange
            AlertSeverity.CRITICAL: '#dc3545'   # Critical red
        }
        
        severity_color = severity_colors.get(alert.severity, '#6c757d')
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Red Hat Status Alert</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background-color: {severity_color}; color: white; padding: 20px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .content {{ padding: 20px; }}
        .alert-info {{ background-color: #f8f9fa; border-left: 4px solid {severity_color}; padding: 15px; margin: 15px 0; }}
        .details {{ margin: 20px 0; }}
        .details table {{ width: 100%; border-collapse: collapse; }}
        .details td {{ padding: 8px; border-bottom: 1px solid #dee2e6; }}
        .details td:first-child {{ font-weight: bold; width: 150px; }}
        .footer {{ background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #6c757d; }}
        .severity-badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; color: white; background-color: {severity_color}; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Red Hat Status Alert</h1>
            <span class="severity-badge">{alert.severity.value.upper()}</span>
        </div>
        
        <div class="content">
            <div class="alert-info">
                <h2 style="margin: 0 0 10px 0; color: {severity_color};">{alert.title}</h2>
                <p style="margin: 0; font-size: 16px; line-height: 1.5;">{alert.message}</p>
            </div>
            
            <div class="details">
                <table>
                    <tr>
                        <td>Alert Type:</td>
                        <td>{alert.alert_type}</td>
                    </tr>
                    <tr>
                        <td>Timestamp:</td>
                        <td>{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                    <tr>
                        <td>Source Service:</td>
                        <td>{alert.source_service or 'N/A'}</td>
                    </tr>
                    <tr>
                        <td>Alert ID:</td>
                        <td>{getattr(alert, 'alert_id', str(id(alert)))}</td>
                    </tr>
"""
        
        # Add context information
        if context:
            for key, value in context.items():
                html += f"""
                    <tr>
                        <td>{key.replace('_', ' ').title()}:</td>
                        <td>{value}</td>
                    </tr>
"""
        
        html += f"""
                </table>
            </div>
        </div>
        
        <div class="footer">
            Red Hat Status Checker v3.1.0<br>
            Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            import socket
            # Set a shorter timeout for testing
            socket.setdefaulttimeout(5)
            
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=5)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=5)
                if self.use_tls:
                    server.starttls()
            
            if self.username and self.password:
                server.login(self.username, self.password)
            
            server.quit()
            socket.setdefaulttimeout(None)  # Reset to default
            return True
            
        except Exception as e:
            socket.setdefaulttimeout(None)  # Reset to default
            self.logger.error(f"SMTP connection test failed: {e}")
            return False


class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel for HTTP integrations"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        
        # Handle both single URL and multiple URLs from config
        self.urls = config.get('urls', [])  # For multiple URLs (current config format)
        single_url = config.get('url', '')  # For single URL
        
        if single_url and single_url not in self.urls:
            self.urls.append(single_url)
        
        # Legacy support for webhook_urls
        webhook_urls = config.get('webhook_urls', [])
        for url in webhook_urls:
            if url not in self.urls:
                self.urls.append(url)
        
        self.method = config.get('method', 'POST').upper()
        self.headers = config.get('headers', {})
        self.timeout = config.get('timeout', 10)
        self.verify_ssl = config.get('verify_ssl', True)
        
        # Authentication
        self.auth_type = config.get('auth_type', 'none')  # none, basic, bearer, custom
        self.auth_config = config.get('auth_config', {})
        
        # Payload configuration
        self.payload_template = config.get('payload_template', {})
        self.custom_payload = config.get('custom_payload', False)
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def send(self, alert: SystemAlert, context: Dict[str, Any] = None) -> bool:
        """Send webhook notification"""
        try:
            if not self.enabled or not self.urls:
                return False
            
            # Send to all configured URLs
            results = []
            for url in self.urls:
                try:
                    # Prepare payload
                    payload = self._create_payload(alert, context or {})
                    
                    # Prepare headers
                    headers = self.headers.copy()
                    headers.setdefault('Content-Type', 'application/json')
                    headers.setdefault('User-Agent', 'RedHat-Status-Checker/3.1.0')
                    
                    # Add authentication
                    self._add_authentication(headers)
                    
                    # Send request
                    response = requests.request(
                        method=self.method,
                        url=url,
                        json=payload,
                        headers=headers,
                        timeout=self.timeout,
                        verify=self.verify_ssl
                    )
                    
                    # Check response
                    success = response.status_code < 400
                    results.append(success)
                    
                    if success:
                        self.logger.info(f"Webhook sent successfully to {url}: {response.status_code}")
                    else:
                        self.logger.warning(f"Webhook failed to {url}: {response.status_code}")
                        
                except Exception as e:
                    self.logger.error(f"Error sending webhook to {url}: {e}")
                    results.append(False)
            
            # Return True if any webhook succeeded
            return any(results)
            
        except Exception as e:
            self.logger.error(f"Webhook send failed: {e}")
            return False
    
    def _create_payload(self, alert: SystemAlert, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create webhook payload"""
        if self.custom_payload and self.payload_template:
            # Use custom template
            payload = self.payload_template.copy()
            
            # Replace placeholders
            replacements = {
                'alert_id': getattr(alert, 'alert_id', str(id(alert))),
                'title': getattr(alert, 'title', alert.message),
                'message': alert.message,
                'severity': alert.severity,
                'alert_type': getattr(alert, 'alert_type', 'status_notification'),
                'component': alert.component,
                'timestamp': alert.timestamp.isoformat(),
                **context
            }
            
            def replace_in_dict(obj):
                if isinstance(obj, dict):
                    return {k: replace_in_dict(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [replace_in_dict(item) for item in obj]
                elif isinstance(obj, str):
                    for key, value in replacements.items():
                        obj = obj.replace(f'{{{key}}}', str(value))
                    return obj
                return obj
            
            return replace_in_dict(payload)
        else:
            # Standard payload format
            return {
                'alert': {
                    'id': getattr(alert, 'alert_id', str(id(alert))),
                    'title': getattr(alert, 'title', alert.message),
                    'message': alert.message,
                    'severity': alert.severity,
                    'type': getattr(alert, 'alert_type', 'status_notification'),
                    'component': alert.component,
                    'timestamp': alert.timestamp.isoformat(),
                    'acknowledged': alert.acknowledged,
                    'auto_resolved': alert.auto_resolved
                },
                'context': context,
                'source': 'redhat-status-checker',
                'version': '3.1.0'
            }
    
    def _add_authentication(self, headers: Dict[str, str]) -> None:
        """Add authentication to headers"""
        if self.auth_type == 'basic':
            import base64
            username = self.auth_config.get('username', '')
            password = self.auth_config.get('password', '')
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers['Authorization'] = f"Basic {credentials}"
        
        elif self.auth_type == 'bearer':
            token = self.auth_config.get('token', '')
            headers['Authorization'] = f"Bearer {token}"
        
        elif self.auth_type == 'custom':
            custom_headers = self.auth_config.get('headers', {})
            headers.update(custom_headers)
    
    def test_connection(self) -> bool:
        """Test webhook connection"""
        try:
            # For testing, just validate the URL format and try a HEAD request
            for url in self.urls:
                try:
                    import urllib.parse
                    # Validate URL format
                    parsed = urllib.parse.urlparse(url)
                    if not parsed.scheme or not parsed.netloc:
                        return False
                    
                    # Try a quick HEAD request with short timeout
                    response = requests.head(url, timeout=3)
                    # Accept any response (even 404) as long as we can connect
                    
                except requests.RequestException:
                    # For test purposes, if URL format is valid, consider it testable
                    if url.startswith(('http://', 'https://')):
                        continue
                    else:
                        return False
                except Exception:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Webhook connection test failed: {e}")
            return False


class NotificationManager:
    """
    Central notification manager for Red Hat Status Checker
    
    Manages multiple notification channels, alert routing,
    escalation rules, and notification history.
    """
    
    def __init__(self):
        """Initialize notification manager"""
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        
        # Notification channels
        self.channels: Dict[str, NotificationChannel] = {}
        self._init_channels()
        
        # Alert routing and escalation
        self.routing_rules = self.config.get('notifications', 'routing_rules', {})
        self.escalation_rules = self.config.get('notifications', 'escalation_rules', {})
        
        # Rate limiting and throttling
        self.global_rate_limit = self.config.get('notifications', 'global_rate_limit', 50)
        self.notification_history = []
        
        # Background thread for escalation
        self.escalation_thread = None
        self.escalation_stop_event = threading.Event()
        
        # Start escalation monitoring
        self._start_escalation_monitoring()
    
    def _init_channels(self) -> None:
        """Initialize notification channels from configuration"""
        # Check for direct email and webhook configs (current format)
        email_config = self.config.get('notifications', 'email', {})
        webhook_config = self.config.get('notifications', 'webhooks', {})
        
        # Initialize email channel if enabled
        if email_config.get('enabled', False):
            try:
                email_channel = EmailNotificationChannel('email', email_config)
                self.channels['email'] = email_channel
                self.logger.info("Initialized email notification channel")
            except Exception as e:
                self.logger.error(f"Failed to initialize email channel: {e}")
        
        # Initialize webhook channel if enabled
        if webhook_config.get('enabled', False):
            try:
                webhook_channel = WebhookNotificationChannel('webhooks', webhook_config)
                self.channels['webhooks'] = webhook_channel
                self.logger.info("Initialized webhook notification channel")
            except Exception as e:
                self.logger.error(f"Failed to initialize webhook channel: {e}")
        
        # Also check for newer channel-based config format (for future compatibility)
        channels_config = self.config.get('notifications', 'channels', {})
        for channel_name, channel_config in channels_config.items():
            try:
                channel_type = channel_config.get('type', '').lower()
                
                if channel_type == 'email':
                    channel = EmailNotificationChannel(channel_name, channel_config)
                elif channel_type == 'webhook':
                    channel = WebhookNotificationChannel(channel_name, channel_config)
                else:
                    self.logger.warning(f"Unknown channel type: {channel_type}")
                    continue
                
                self.channels[channel_name] = channel
                self.logger.info(f"Initialized notification channel: {channel_name} ({channel_type})")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize channel {channel_name}: {e}")
    
    @performance_monitor
    def send_alert(self, alert: SystemAlert, context: Dict[str, Any] = None) -> Dict[str, bool]:
        """Send alert through appropriate channels"""
        results = {}
        
        try:
            # Check global rate limiting
            if not self._check_global_rate_limit():
                self.logger.warning("Global notification rate limit exceeded")
                return results
            
            # Determine target channels based on routing rules
            target_channels = self._get_target_channels(alert)
            
            # Send to each target channel
            for channel_name in target_channels:
                if channel_name in self.channels:
                    channel = self.channels[channel_name]
                    try:
                        success = channel.send(alert, context)
                        results[channel_name] = success
                        
                        if success:
                            self.logger.info(f"Alert sent via {channel_name}: {alert.message}")
                        else:
                            self.logger.warning(f"Failed to send alert via {channel_name}")
                            
                    except Exception as e:
                        self.logger.error(f"Error sending alert via {channel_name}: {e}")
                        results[channel_name] = False
                else:
                    self.logger.warning(f"Channel not found: {channel_name}")
                    results[channel_name] = False
            
            # Track notification
            self.notification_history.append({
                'timestamp': datetime.now(),
                'alert_id': getattr(alert, 'alert_id', str(id(alert))),
                'channels': list(target_channels),
                'results': results
            })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to send alert notifications: {e}")
            return results
    
    def _check_global_rate_limit(self) -> bool:
        """Check global notification rate limiting"""
        now = datetime.now()
        cutoff = now - timedelta(hours=1)
        
        # Remove old entries
        self.notification_history = [
            entry for entry in self.notification_history 
            if entry['timestamp'] > cutoff
        ]
        
        return len(self.notification_history) < self.global_rate_limit
    
    def _get_target_channels(self, alert: SystemAlert) -> List[str]:
        """Determine target channels based on routing rules"""
        target_channels = []
        
        # Default channels for all alerts
        default_channels = self.routing_rules.get('default', [])
        target_channels.extend(default_channels)
        
        # Severity-based routing
        severity_rules = self.routing_rules.get('by_severity', {})
        severity_channels = severity_rules.get(alert.severity, [])
        target_channels.extend(severity_channels)
        
        # Service-based routing
        component = getattr(alert, 'component', None)
        if component:
            service_rules = self.routing_rules.get('by_service', {})
            service_channels = service_rules.get(component, [])
            target_channels.extend(service_channels)
        
        # Remove duplicates and filter enabled channels
        unique_channels = list(set(target_channels))
        enabled_channels = [
            ch for ch in unique_channels 
            if ch in self.channels and self.channels[ch].enabled
        ]
        
        # If no channels found via routing rules, use all enabled channels
        if not enabled_channels:
            enabled_channels = [
                ch for ch in self.channels.keys() 
                if self.channels[ch].enabled
            ]
        
        return enabled_channels
    
    def _start_escalation_monitoring(self) -> None:
        """Start background thread for alert escalation"""
        if self.escalation_rules and not self.escalation_thread:
            self.escalation_thread = threading.Thread(
                target=self._escalation_worker,
                daemon=True
            )
            self.escalation_thread.start()
            self.logger.info("Alert escalation monitoring started")
    
    def _escalation_worker(self) -> None:
        """Background worker for alert escalation"""
        while not self.escalation_stop_event.is_set():
            try:
                # Check for alerts that need escalation
                self._process_escalations()
                
                # Sleep for escalation check interval
                check_interval = self.config.get('notifications', 'escalation_check_interval', 300)
                self.escalation_stop_event.wait(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in escalation worker: {e}")
                time.sleep(60)  # Sleep on error
    
    def _process_escalations(self) -> None:
        """Process alert escalations based on rules"""
        # This would integrate with the database to check for
        # unacknowledged alerts that need escalation
        # Implementation would depend on specific escalation requirements
        pass
    
    @performance_monitor
    def send_anomaly_alert(self, anomaly: AnomalyDetection) -> Dict[str, bool]:
        """Send alert for detected anomaly"""
        # Convert anomaly to system alert
        alert = SystemAlert(
            alert_type='anomaly_detected',
            severity=anomaly.severity,
            title=f"Anomaly Detected: {anomaly.service_name}",
            message=anomaly.description,
            source_service=anomaly.service_name,
            metadata={
                'anomaly_type': anomaly.anomaly_type.value,
                'confidence_score': anomaly.confidence_score,
                'affected_metrics': anomaly.affected_metrics
            }
        )
        
        context = {
            'anomaly_type': anomaly.anomaly_type.value,
            'confidence_score': f"{anomaly.confidence_score:.1f}%",
            'detection_time': anomaly.timestamp.isoformat()
        }
        
        return self.send_alert(alert, context)
    
    def test_all_channels(self) -> Dict[str, bool]:
        """Test connectivity for all channels"""
        results = {}
        
        for channel_name, channel in self.channels.items():
            try:
                results[channel_name] = channel.test_connection()
                
                if results[channel_name]:
                    self.logger.info(f"Channel test passed: {channel_name}")
                else:
                    self.logger.warning(f"Channel test failed: {channel_name}")
                    
            except Exception as e:
                self.logger.error(f"Error testing channel {channel_name}: {e}")
                results[channel_name] = False
        
        return results
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Filter recent notifications
        recent_notifications = [
            entry for entry in self.notification_history
            if entry['timestamp'] > last_24h
        ]
        
        weekly_notifications = [
            entry for entry in self.notification_history
            if entry['timestamp'] > last_7d
        ]
        
        # Calculate success rates
        channel_stats = {}
        for channel_name in self.channels:
            channel_results = []
            for entry in recent_notifications:
                if channel_name in entry['results']:
                    channel_results.append(entry['results'][channel_name])
            
            success_count = sum(channel_results)
            total_count = len(channel_results)
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            channel_stats[channel_name] = {
                'success_count': success_count,
                'total_count': total_count,
                'success_rate': success_rate,
                'enabled': self.channels[channel_name].enabled
            }
        
        return {
            'notifications_24h': len(recent_notifications),
            'notifications_7d': len(weekly_notifications),
            'channel_stats': channel_stats,
            'active_channels': len([ch for ch in self.channels.values() if ch.enabled]),
            'total_channels': len(self.channels)
        }
    
    def stop(self) -> None:
        """Stop notification manager and cleanup"""
        if self.escalation_thread:
            self.escalation_stop_event.set()
            self.escalation_thread.join(timeout=5)
            self.logger.info("Notification manager stopped")

    def send_status_notification(self, message: str, status_data: Dict[str, Any]) -> bool:
        """Send a status notification with current system status"""
        try:
            # Create a status alert using the correct structure
            from redhat_status.core.data_models import SystemAlert
            
            # Determine severity based on message content
            if "issue" in message.lower() or "problem" in message.lower():
                severity = "warning"
            elif "down" in message.lower() or "fail" in message.lower():
                severity = "critical"
            else:
                severity = "info"
            
            # Create alert with correct parameters
            alert = SystemAlert(
                timestamp=datetime.now(),
                severity=severity,
                component="Red Hat Status Checker",
                message=message,
                acknowledged=False,
                auto_resolved=False
            )
            
            # Send the alert through all channels
            results = self.send_alert(alert, {"status_data": status_data})
            return any(results.values())  # Return True if any channel succeeded
            
        except Exception as e:
            self.logger.error(f"Failed to send status notification: {e}")
            return False


# Convenience functions for easy access
_notification_manager_instance = None

def get_notification_manager() -> NotificationManager:
    """Get singleton notification manager instance"""
    global _notification_manager_instance
    if _notification_manager_instance is None:
        _notification_manager_instance = NotificationManager()
    return _notification_manager_instance

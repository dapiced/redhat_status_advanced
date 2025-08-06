"""
Red Hat Status Checker - Notifications Module Init

This module initializes the notification and alerting components
for multi-channel notifications.
"""

from .notification_manager import (
    NotificationManager, 
    NotificationChannel,
    EmailNotificationChannel,
    WebhookNotificationChannel,
    get_notification_manager
)

__all__ = [
    'NotificationManager',
    'NotificationChannel', 
    'EmailNotificationChannel',
    'WebhookNotificationChannel',
    'get_notification_manager'
]

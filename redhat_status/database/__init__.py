"""
Red Hat Status Checker - Database Module Init

This module initializes the database management components
for data persistence and retrieval.
"""

from .db_manager import DatabaseManager, get_database_manager

__all__ = ['DatabaseManager', 'get_database_manager']

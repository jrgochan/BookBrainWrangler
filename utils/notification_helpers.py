"""
Helper functions for working with notifications.
"""

from typing import Dict, List, Any

def count_unread_notifications(notifications: List[Any]) -> int:
    """
    Count the number of unread notifications.
    
    Args:
        notifications: List of notification objects
        
    Returns:
        Number of unread notifications
    """
    if not notifications:
        return 0
        
    return len([n for n in notifications if not n.read and not n.dismissed])
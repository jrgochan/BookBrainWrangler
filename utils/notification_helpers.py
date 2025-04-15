"""
Helper functions for working with notifications.
"""

from typing import List, Dict, Any

def count_unread_notifications(notifications: List[Dict[str, Any]]) -> int:
    """
    Count the number of unread notifications.
    
    Args:
        notifications: List of notification dictionaries
        
    Returns:
        Number of unread notifications
    """
    return sum(1 for n in notifications if not n.get("read", False))
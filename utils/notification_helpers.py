"""
Helper functions for working with notifications.
"""

from typing import Dict, List, Any

def count_unread_notifications(notifications: List[Dict[str, Any]]) -> int:
    """
    Count the number of unread notifications.
    
    Args:
        notifications: List of notification dictionaries
        
    Returns:
        Number of unread notifications
    """
    if not notifications:
        return 0
        
    return len([n for n in notifications if not n.get("read", False) and not n.get("dismissed", False)])
"""
Notification system for BookBrainWrangler
"""

import streamlit as st
from enum import Enum
import time
import json
import os
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

class NotificationLevel(Enum):
    """Notification severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

class NotificationType(Enum):
    """Types of notifications"""
    BOOK_CONTENT_MISSING = "book_content_missing"
    FILE_NOT_FOUND = "file_not_found"
    PROCESSING_ERROR = "processing_error"
    KNOWLEDGE_BASE_ERROR = "knowledge_base_error"
    ARCHIVE_DOWNLOAD_ERROR = "archive_download_error"
    GENERAL = "general"

class Notification:
    """Notification data structure"""
    
    def __init__(
        self,
        message: str,
        level: NotificationLevel,
        notification_type: NotificationType,
        title: Optional[str] = None,
        details: Optional[str] = None,
        book_id: Optional[int] = None,
        book_title: Optional[str] = None,
        timestamp: Optional[float] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        id: Optional[str] = None,
        read: bool = False,
        dismissed: bool = False,
    ):
        self.id = id or f"{int(time.time() * 1000)}"
        self.message = message
        self.level = level
        self.notification_type = notification_type
        self.title = title or self._generate_title()
        self.details = details
        self.book_id = book_id
        self.book_title = book_title
        self.timestamp = timestamp or time.time()
        self.actions = actions or []
        self.read = read
        self.dismissed = dismissed
    
    def _generate_title(self) -> str:
        """Generate a title based on notification type and level"""
        if self.notification_type == NotificationType.BOOK_CONTENT_MISSING:
            return "Book Content Missing"
        elif self.notification_type == NotificationType.FILE_NOT_FOUND:
            return "File Not Found"
        elif self.notification_type == NotificationType.PROCESSING_ERROR:
            return "Processing Error"
        elif self.notification_type == NotificationType.KNOWLEDGE_BASE_ERROR:
            return "Knowledge Base Error"
        elif self.notification_type == NotificationType.ARCHIVE_DOWNLOAD_ERROR:
            return "Archive.org Download Error"
        else:
            # Default titles based on level
            if self.level == NotificationLevel.ERROR:
                return "Error"
            elif self.level == NotificationLevel.WARNING:
                return "Warning"
            elif self.level == NotificationLevel.SUCCESS:
                return "Success"
            else:
                return "Information"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary for serialization"""
        return {
            "id": self.id,
            "message": self.message,
            "level": self.level.value,
            "notification_type": self.notification_type.value,
            "title": self.title,
            "details": self.details,
            "book_id": self.book_id,
            "book_title": self.book_title,
            "timestamp": self.timestamp,
            "actions": self.actions,
            "read": self.read,
            "dismissed": self.dismissed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        """Create notification from dictionary"""
        return cls(
            message=data["message"],
            level=NotificationLevel(data["level"]),
            notification_type=NotificationType(data["notification_type"]),
            title=data.get("title"),
            details=data.get("details"),
            book_id=data.get("book_id"),
            book_title=data.get("book_title"),
            timestamp=data.get("timestamp"),
            actions=data.get("actions", []),
            id=data.get("id"),
            read=data.get("read", False),
            dismissed=data.get("dismissed", False)
        )

class NotificationManager:
    """
    Manages system notifications and persists them between sessions.
    Handles displaying notifications in the UI and tracking their status.
    """
    
    STORAGE_FILE = "notifications.json"
    MAX_NOTIFICATIONS = 100  # Maximum number to store
    
    def __init__(self, storage_dir: str = "data"):
        """
        Initialize the notification manager
        
        Args:
            storage_dir: Directory to store notifications file
        """
        self.storage_dir = storage_dir
        self.storage_path = os.path.join(storage_dir, self.STORAGE_FILE)
        self._notifications = []
        self._load_notifications()
    
    def _load_notifications(self) -> None:
        """Load notifications from storage file"""
        try:
            if not os.path.exists(self.storage_dir):
                os.makedirs(self.storage_dir, exist_ok=True)
                
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self._notifications = [Notification.from_dict(item) for item in data]
                    logger.debug(f"Loaded {len(self._notifications)} notifications from storage")
            else:
                logger.debug("No notification storage file found, starting with empty list")
                self._notifications = []
        except Exception as e:
            logger.error(f"Error loading notifications: {str(e)}")
            self._notifications = []
    
    def _save_notifications(self) -> None:
        """Save notifications to storage file"""
        try:
            if not os.path.exists(self.storage_dir):
                os.makedirs(self.storage_dir, exist_ok=True)
                
            # Limit to max notifications, keeping most recent
            if len(self._notifications) > self.MAX_NOTIFICATIONS:
                self._notifications = sorted(
                    self._notifications, 
                    key=lambda n: n.timestamp, 
                    reverse=True
                )[:self.MAX_NOTIFICATIONS]
                
            data = [n.to_dict() for n in self._notifications]
            with open(self.storage_path, 'w') as f:
                json.dump(data, f)
                
            logger.debug(f"Saved {len(data)} notifications to storage")
        except Exception as e:
            logger.error(f"Error saving notifications: {str(e)}")
    
    def add_notification(self, notification: Notification) -> str:
        """
        Add a new notification
        
        Args:
            notification: The notification to add
            
        Returns:
            Notification ID
        """
        self._notifications.append(notification)
        logger.info(f"Added notification: {notification.title} ({notification.level.value})")
        
        # Check for similar existing notifications and mark them as dismissed
        if notification.book_id is not None:
            for n in self._notifications:
                if (n.id != notification.id and 
                    n.book_id == notification.book_id and 
                    n.notification_type == notification.notification_type and
                    not n.dismissed):
                    n.dismissed = True
                    logger.debug(f"Marked similar notification {n.id} as dismissed")
        
        self._save_notifications()
        return notification.id
    
    def create_notification(
        self,
        message: str,
        level: NotificationLevel,
        notification_type: NotificationType,
        title: Optional[str] = None,
        details: Optional[str] = None,
        book_id: Optional[int] = None,
        book_title: Optional[str] = None,
        actions: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Create and add a new notification
        
        Args:
            message: Main notification message
            level: Notification severity level
            notification_type: Type of notification
            title: Optional title, generated if not provided
            details: Optional detailed message
            book_id: Optional associated book ID
            book_title: Optional associated book title
            actions: Optional list of actions
            
        Returns:
            Notification ID
        """
        notification = Notification(
            message=message,
            level=level,
            notification_type=notification_type,
            title=title,
            details=details,
            book_id=book_id,
            book_title=book_title,
            actions=actions
        )
        return self.add_notification(notification)
    
    def mark_as_read(self, notification_id: str) -> None:
        """Mark a notification as read"""
        for notification in self._notifications:
            if notification.id == notification_id:
                notification.read = True
                self._save_notifications()
                return
    
    def mark_as_dismissed(self, notification_id: str) -> None:
        """Mark a notification as dismissed"""
        for notification in self._notifications:
            if notification.id == notification_id:
                notification.dismissed = True
                self._save_notifications()
                return
    
    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Get a specific notification by ID"""
        for notification in self._notifications:
            if notification.id == notification_id:
                return notification
        return None
    
    def get_all_notifications(self) -> List[Notification]:
        """Get all notifications"""
        return sorted(self._notifications, key=lambda n: n.timestamp, reverse=True)
    
    def get_active_notifications(self) -> List[Notification]:
        """Get active (not dismissed) notifications"""
        return sorted(
            [n for n in self._notifications if not n.dismissed],
            key=lambda n: n.timestamp,
            reverse=True
        )
    
    def get_notifications_by_level(self, level: NotificationLevel) -> List[Notification]:
        """Get notifications by severity level"""
        return sorted(
            [n for n in self._notifications if n.level == level and not n.dismissed],
            key=lambda n: n.timestamp,
            reverse=True
        )
    
    def get_notifications_for_book(self, book_id: int) -> List[Notification]:
        """Get notifications for a specific book"""
        return sorted(
            [n for n in self._notifications if n.book_id == book_id and not n.dismissed],
            key=lambda n: n.timestamp,
            reverse=True
        )
    
    def count_unread(self) -> int:
        """Count unread notifications"""
        return len([n for n in self._notifications if not n.read and not n.dismissed])
    
    def clear_all(self) -> None:
        """Clear all notifications"""
        self._notifications = []
        self._save_notifications()
    
    def has_error_for_book(self, book_id: int, notification_type: NotificationType = None) -> bool:
        """
        Check if there's an active error notification for a specific book
        
        Args:
            book_id: Book ID to check
            notification_type: Optional specific notification type to check
            
        Returns:
            True if there is an active error for the book
        """
        for notification in self._notifications:
            if notification.book_id == book_id and notification.level == NotificationLevel.ERROR and not notification.dismissed:
                if notification_type is None or notification.notification_type == notification_type:
                    return True
        return False
    
    def display_toast(self, notification: Union[Notification, str]) -> None:
        """
        Display a toast notification in Streamlit UI
        
        Args:
            notification: Notification object or notification ID
        """
        if isinstance(notification, str):
            notification = self.get_notification(notification)
            
        if not notification:
            return
            
        if notification.level == NotificationLevel.ERROR:
            st.error(notification.message, icon="🚨")
        elif notification.level == NotificationLevel.WARNING:
            st.warning(notification.message, icon="⚠️")
        elif notification.level == NotificationLevel.SUCCESS:
            st.success(notification.message, icon="✅")
        else:
            st.info(notification.message, icon="ℹ️")
            
        # Mark as read after displaying
        self.mark_as_read(notification.id)
    
    def render_notification_indicator(self) -> None:
        """Render notification indicator in the UI"""
        unread_count = self.count_unread()
        
        if unread_count > 0:
            st.markdown(
                f"""
                <div style="position: fixed; top: 60px; right: 20px; 
                           background-color: red; color: white; 
                           border-radius: 50%; width: 24px; height: 24px; 
                           display: flex; justify-content: center; align-items: center;
                           font-size: 14px; font-weight: bold; z-index: 1000;">
                  {min(unread_count, 9) if unread_count < 10 else "9+"}
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    # Helper methods for common notification types
    def notify_missing_content(self, book_id: int, book_title: str) -> str:
        """Notification for book with missing content"""
        return self.create_notification(
            message=f"Book '{book_title}' has no content and cannot be added to the Knowledge Base.",
            level=NotificationLevel.ERROR,
            notification_type=NotificationType.BOOK_CONTENT_MISSING,
            book_id=book_id,
            book_title=book_title,
            details="The book is in the database but has no text content. This may happen if the file upload or processing was interrupted.",
            actions=[
                {"label": "Process Again", "action": "process_book", "book_id": book_id},
                {"label": "Remove Book", "action": "delete_book", "book_id": book_id}
            ]
        )
    
    def notify_file_not_found(self, book_id: int, book_title: str, file_path: str) -> str:
        """Notification for book with missing file"""
        return self.create_notification(
            message=f"File for book '{book_title}' was not found at the expected location.",
            level=NotificationLevel.ERROR,
            notification_type=NotificationType.FILE_NOT_FOUND,
            book_id=book_id,
            book_title=book_title,
            details=f"The file was expected at: {file_path}\n\nThe file may have been moved, deleted, or the upload was interrupted.",
            actions=[
                {"label": "Upload Again", "action": "upload_book"},
                {"label": "Remove Book", "action": "delete_book", "book_id": book_id}
            ]
        )
    
    def notify_processing_error(self, book_id: int, book_title: str, error_message: str) -> str:
        """Notification for book processing error"""
        return self.create_notification(
            message=f"Error processing book '{book_title}'.",
            level=NotificationLevel.ERROR,
            notification_type=NotificationType.PROCESSING_ERROR,
            book_id=book_id,
            book_title=book_title,
            details=f"Error details: {error_message}",
            actions=[
                {"label": "Retry Processing", "action": "process_book", "book_id": book_id},
                {"label": "Remove Book", "action": "delete_book", "book_id": book_id}
            ]
        )
    
    def notify_knowledge_base_error(self, book_id: int, book_title: str, error_message: str) -> str:
        """Notification for knowledge base error"""
        return self.create_notification(
            message=f"Could not add book '{book_title}' to Knowledge Base.",
            level=NotificationLevel.ERROR,
            notification_type=NotificationType.KNOWLEDGE_BASE_ERROR,
            book_id=book_id,
            book_title=book_title,
            details=f"Error details: {error_message}",
            actions=[
                {"label": "Retry Adding", "action": "add_to_kb", "book_id": book_id},
                {"label": "Check Book", "action": "view_book", "book_id": book_id}
            ]
        )
    
    def notify_archive_download_error(self, identifier: str, error_message: str) -> str:
        """Notification for archive.org download error"""
        return self.create_notification(
            message=f"Error downloading from Archive.org: {identifier}",
            level=NotificationLevel.ERROR,
            notification_type=NotificationType.ARCHIVE_DOWNLOAD_ERROR,
            details=f"Error details: {error_message}",
            actions=[
                {"label": "Retry Download", "action": "retry_download", "identifier": identifier},
                {"label": "View in Archive.org", "action": "view_archive", "identifier": identifier}
            ]
        )

# Initialize global notification manager instance
_notification_manager = None

def get_notification_manager(storage_dir: str = "data") -> NotificationManager:
    """
    Get or create the global notification manager instance
    
    Args:
        storage_dir: Directory to store notifications
        
    Returns:
        NotificationManager instance
    """
    global _notification_manager
    
    if _notification_manager is None:
        _notification_manager = NotificationManager(storage_dir)
    
    return _notification_manager

# Streamlit component for notification center
def render_notification_center():
    """Render the notification center in the Streamlit UI"""
    nm = get_notification_manager()
    
    # Get active notifications
    notifications = nm.get_active_notifications()
    
    # Count by level
    error_count = len([n for n in notifications if n.level == NotificationLevel.ERROR])
    warning_count = len([n for n in notifications if n.level == NotificationLevel.WARNING])
    info_count = len([n for n in notifications if n.level == NotificationLevel.INFO])
    
    # Create tabs for different notification types
    if not notifications:
        st.info("No notifications", icon="🔔")
        return
    
    tabs = ["All", f"Errors ({error_count})", f"Warnings ({warning_count})", f"Info ({info_count})"]
    active_tab = st.tabs(tabs)
    
    with active_tab[0]:
        _render_notification_list(notifications)
    
    with active_tab[1]:
        error_notifications = [n for n in notifications if n.level == NotificationLevel.ERROR]
        if error_notifications:
            _render_notification_list(error_notifications)
        else:
            st.info("No error notifications", icon="✅")
    
    with active_tab[2]:
        warning_notifications = [n for n in notifications if n.level == NotificationLevel.WARNING]
        if warning_notifications:
            _render_notification_list(warning_notifications)
        else:
            st.info("No warning notifications", icon="✅")
    
    with active_tab[3]:
        info_notifications = [n for n in notifications if n.level == NotificationLevel.INFO]
        if info_notifications:
            _render_notification_list(info_notifications)
        else:
            st.info("No info notifications", icon="ℹ️")

def _render_notification_list(notifications):
    """Render a list of notifications"""
    for notification in notifications:
        _render_notification_card(notification)

def _render_notification_card(notification):
    """Render a single notification card"""
    # Determine icon and color based on level
    if notification.level == NotificationLevel.ERROR:
        icon = "🚨"
        border_color = "red"
    elif notification.level == NotificationLevel.WARNING:
        icon = "⚠️"
        border_color = "orange"
    elif notification.level == NotificationLevel.SUCCESS:
        icon = "✅"
        border_color = "green"
    else:
        icon = "ℹ️"
        border_color = "blue"
    
    # Create card with appropriate styling
    with st.container(border=True):
        col1, col2 = st.columns([0.9, 0.1])
        
        with col1:
            # Header with title and timestamp
            st.markdown(f"### {icon} {notification.title}")
            timestamp_str = datetime.fromtimestamp(notification.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            st.caption(f"**Time:** {timestamp_str}")
            
            # Book info if available
            if notification.book_title:
                st.markdown(f"**Book:** {notification.book_title}")
            
            # Main message
            st.markdown(notification.message)
            
            # Expandable details
            if notification.details:
                with st.expander("Details"):
                    st.markdown(notification.details)
            
            # Action buttons
            if notification.actions:
                st.markdown("**Actions:**")
                cols = st.columns(len(notification.actions))
                
                for i, action in enumerate(notification.actions):
                    with cols[i]:
                        if st.button(action["label"], key=f"action_{notification.id}_{i}"):
                            # The action handling would be implemented elsewhere
                            # Here we just mark the notification as read when an action is taken
                            nm = get_notification_manager()
                            nm.mark_as_read(notification.id)
                            
                            # Set session state to indicate action was taken
                            if "notification_actions" not in st.session_state:
                                st.session_state.notification_actions = []
                            
                            st.session_state.notification_actions.append({
                                "action": action["action"],
                                "parameters": {k: v for k, v in action.items() if k != "action" and k != "label"},
                                "notification_id": notification.id,
                                "timestamp": time.time()
                            })
                            
                            # Force rerun to update UI
                            st.rerun()
        
        # Dismiss button
        with col2:
            if st.button("✕", key=f"dismiss_{notification.id}"):
                nm = get_notification_manager()
                nm.mark_as_dismissed(notification.id)
                st.rerun()

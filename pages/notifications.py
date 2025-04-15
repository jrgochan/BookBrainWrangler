"""
Notifications page for the application.
Displays all system notifications and allows users to manage them.
"""

import streamlit as st
from utils.notifications import get_notification_manager, render_notification_center, NotificationLevel

def render_notifications_page():
    """
    Render the Notifications page.
    """
    st.title("Notifications")
    
    # Get notification manager
    notification_manager = get_notification_manager()
    
    # Create tabs for filtering notifications
    notifications = notification_manager.get_active_notifications()
    
    # Count by level
    error_count = len([n for n in notifications if n.level == NotificationLevel.ERROR])
    warning_count = len([n for n in notifications if n.level == NotificationLevel.WARNING])
    info_count = len([n for n in notifications if n.level == NotificationLevel.INFO])
    success_count = len([n for n in notifications if n.level == NotificationLevel.SUCCESS])
    
    # Create a header with notification counts
    st.markdown(f"""
    ### Notification Summary
    - 🚨 **Errors**: {error_count}
    - ⚠️ **Warnings**: {warning_count}
    - ℹ️ **Info**: {info_count}
    - ✅ **Success**: {success_count}
    - 📋 **Total**: {len(notifications)}
    """)
    
    # Add management actions
    col1, col2 = st.columns(2)
    with col1:
        # Mark all as read
        if st.button("Mark All as Read", key="mark_all_read", use_container_width=True):
            for notification in notifications:
                notification_manager.mark_as_read(notification.id)
            st.success("All notifications marked as read")
            st.rerun()
            
    with col2:
        # Clear all notifications 
        if st.button("Clear All Notifications", key="clear_all", type="primary", use_container_width=True):
            # Add confirmation
            if "confirm_clear" not in st.session_state:
                st.session_state.confirm_clear = False
                
            if st.session_state.confirm_clear:
                notification_manager.clear_all()
                st.success("All notifications cleared")
                st.session_state.confirm_clear = False
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("Are you sure you want to clear all notifications? Click 'Clear All Notifications' again to confirm.")
                st.rerun()
                
    # Display divider
    st.divider()
    
    # Render notification center
    if notifications:
        render_notification_center()
    else:
        st.info("No active notifications", icon="🔔")
        
        # Display some examples of what notifications look like
        with st.expander("Notification Examples"):
            st.markdown("""
            ### Examples of Notifications You Might See
            
            #### Error Notifications
            - 🚨 **Missing Content**: Shown when a book is in the database but has no text content
            - 🚨 **Processing Error**: Displayed when there's an error processing a book file
            - 🚨 **Download Error**: Appears when a file can't be downloaded from Archive.org
            
            #### Warning Notifications
            - ⚠️ **Large File**: Shown when a book file is unusually large
            - ⚠️ **Low OCR Quality**: Displayed when OCR quality is below threshold
            
            #### Info Notifications
            - ℹ️ **Knowledge Base Updates**: Shown when books are removed from the Knowledge Base
            - ℹ️ **System Status**: General system information
            
            #### Success Notifications
            - ✅ **Download Complete**: Appears when a book is successfully downloaded
            - ✅ **Processing Complete**: Shown when a book is successfully processed
            """)

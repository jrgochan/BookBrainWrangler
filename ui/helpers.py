"""
UI helper functions for the application.
Contains common UI utilities used across multiple pages.
"""

import streamlit as st
import time
from typing import Union, Callable, Optional, Dict, Any, Literal

from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

def set_page_config(title: str, icon: str, layout: str, initial_sidebar_state: str):
    """
    Set the page configuration for Streamlit.
    
    Args:
        title: The page title
        icon: The page icon (emoji or URL)
        layout: Page layout ("wide" or "centered")
        initial_sidebar_state: Initial sidebar state ("expanded" or "collapsed")
    """
    try:
        st.set_page_config(
            page_title=title,
            page_icon=icon,
            layout=layout,
            initial_sidebar_state=initial_sidebar_state,
            menu_items={
                'About': f"""
                # {title}
                An interactive document management and knowledge extraction application.
                """
            }
        )
        logger.debug(f"Page config set: title='{title}', layout='{layout}', sidebar='{initial_sidebar_state}'")
    except Exception as e:
        # This might happen if set_page_config is called twice
        logger.debug(f"Could not set page config: {str(e)}")

def show_progress_bar(message: str, progress_func: Callable, complete_message: str = "Complete!"):
    """
    Show a progress bar with a message and completion message.
    
    Args:
        message: Message to display during progress
        progress_func: Function that performs the work and yields progress (0.0 to 1.0)
        complete_message: Message to display when complete
    """
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Display initial message
    status_text.text(message)
    
    try:
        # Call the progress function and update the progress bar
        for progress in progress_func():
            # Ensure progress is between 0 and 1
            progress = max(0, min(1, progress))
            progress_bar.progress(progress)
            
            # Update status text with percentage
            percentage = int(progress * 100)
            status_text.text(f"{message} ({percentage}%)")
            
            # Small delay for visual effect
            time.sleep(0.01)
        
        # Complete
        progress_bar.progress(1.0)
        status_text.text(complete_message)
        
    except Exception as e:
        # Error
        status_text.text(f"Error: {str(e)}")
        logger.error(f"Progress bar error: {str(e)}")
        raise

def create_download_link(data: bytes, filename: str, link_text: str = "Download") -> str:
    """
    Create a download link for file data.
    
    Args:
        data: File data as bytes
        filename: Name of the file to download
        link_text: Text to display for the link
        
    Returns:
        HTML string with download link
    """
    import base64
    
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def render_file_upload_area(label: str, file_types: Optional[list] = None, accept_multiple_files: bool = False):
    """
    Render a file upload area with a consistent style.
    
    Args:
        label: Label for the upload area
        file_types: List of allowed file types (e.g., ["pdf", "docx"])
        accept_multiple_files: Whether to accept multiple files
        
    Returns:
        Uploaded file(s) from st.file_uploader
    """
    # Create a bordered container with custom styling
    upload_container = st.container()
    
    with upload_container:
        st.markdown("""
        <style>
        .upload-container {
            border: 2px dashed #aaa;
            border-radius: 5px;
            padding: 20px;
            text-align: center;
            margin-bottom: 10px;
        }
        </style>
        
        <div class="upload-container">
            <p>Drag and drop files here, or click to select</p>
        </div>
        """, unsafe_allow_html=True)
        
        return st.file_uploader(
            label,
            type=file_types,
            accept_multiple_files=accept_multiple_files,
            label_visibility="collapsed"
        )

def show_notification(message: str, type: str = "info", duration: int = 3):
    """
    Show a temporary notification message.
    
    Args:
        message: Message to display
        type: Type of notification ("info", "success", "warning", "error")
        duration: Duration in seconds to display the message
    """
    if type == "info":
        placeholder = st.info(message)
    elif type == "success":
        placeholder = st.success(message)
    elif type == "warning":
        placeholder = st.warning(message)
    elif type == "error":
        placeholder = st.error(message)
    else:
        placeholder = st.info(message)
    
    # Auto-dismiss after duration
    if duration > 0:
        time.sleep(duration)
        placeholder.empty()

def render_error_box(title: str, error_message: str, help_text: Optional[str] = None):
    """
    Render a styled error box with title and message.
    
    Args:
        title: Error title
        error_message: Detailed error message
        help_text: Optional help text with suggestions
    """
    st.error(f"**{title}**\n\n{error_message}")
    
    if help_text:
        st.info(f"**Suggestion:**\n\n{help_text}")

def render_empty_state(message: str, icon: str = "📚"):
    """
    Render an empty state message when no data is available.
    
    Args:
        message: Message to display
        icon: Icon to display before the message
    """
    st.markdown(f"""
    <div style="text-align: center; padding: 50px 0; color: #888;">
        <div style="font-size: 48px; margin-bottom: 20px;">{icon}</div>
        <p>{message}</p>
    </div>
    """, unsafe_allow_html=True)

def render_loading_spinner(text: str = "Loading..."):
    """
    Create a loading spinner with text.
    
    Args:
        text: Text to display with the spinner
        
    Returns:
        Spinner context manager
    """
    return st.spinner(text)
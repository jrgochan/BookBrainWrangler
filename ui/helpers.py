"""
UI helper functions for the Book Knowledge AI application.
Provides common UI components and utilities.
"""

import os
import io
import time
import base64
import tempfile
from typing import Dict, List, Any, Optional, Union, Callable, Tuple

import streamlit as st

# Page utilities
def create_page_header(title: str, description: str = None, icon: str = None):
    """
    Create a page header with title, description, and optional icon.
    
    Args:
        title: Page title
        description: Optional page description
        icon: Optional icon name or emoji
    """
    if icon:
        st.markdown(f"# {icon} {title}")
    else:
        st.title(title)
    
    if description:
        st.markdown(description)
    
    st.markdown("---")

# Icon utilities
def get_icon(name: str) -> str:
    """
    Get an icon by name.
    
    Args:
        name: Icon name
        
    Returns:
        Icon string (emoji)
    """
    icons = {
        "home": "🏠",
        "book": "📚",
        "document": "📄",
        "knowledge": "🧠",
        "search": "🔍",
        "settings": "⚙️",
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "chat": "💬",
        "user": "👤",
        "assistant": "🤖",
        "upload": "📤",
        "download": "📥",
        "chart": "📊",
        "edit": "✏️",
        "delete": "🗑️",
        "save": "💾",
        "refresh": "🔄",
        "link": "🔗",
        "time": "⏱️",
        "image": "🖼️",
        "gear": "⚙️",
        "cloud": "☁️",
        "light": "💡",
        "database": "🗃️",
        "analyze": "📈",
        "magic": "✨",
        "folder": "📁",
        "file": "📄",
        "loading": "⏳"
    }
    
    return icons.get(name.lower(), "")

# Notification utilities
def show_info(message: str):
    """
    Show an information message.
    
    Args:
        message: Message text
    """
    st.info(message)

def show_success(message: str):
    """
    Show a success message.
    
    Args:
        message: Message text
    """
    st.success(message)

def show_warning(message: str):
    """
    Show a warning message.
    
    Args:
        message: Message text
    """
    st.warning(message)

def show_error(message: str):
    """
    Show an error message.
    
    Args:
        message: Message text
    """
    st.error(message)

def show_notification(message: str, type: str = "info"):
    """
    Show a notification message.
    
    Args:
        message: Message text
        type: Notification type ("info", "success", "warning", "error")
    """
    if type == "info":
        show_info(message)
    elif type == "success":
        show_success(message)
    elif type == "warning":
        show_warning(message)
    elif type == "error":
        show_error(message)
    else:
        show_info(message)

# Loading and progress utilities
def show_spinner(text: str = "Processing..."):
    """
    Create a spinner context.
    
    Args:
        text: Spinner text
        
    Returns:
        Spinner context manager
    """
    return st.spinner(text)

def show_progress(function: Callable, *args, message: str = "Processing...", **kwargs):
    """
    Show a progress bar while executing a function.
    
    Args:
        function: Function to execute
        *args: Function arguments
        message: Progress message
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
    """
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    result = None
    
    try:
        # Show initial status
        status_text.text(f"{message}... (0%)")
        progress_bar.progress(0)
        
        # Execute function
        result = function(*args, **kwargs)
        
        # Show completion
        for i in range(10):
            # Simulate progress
            progress = min(100, (i + 1) * 10)
            status_text.text(f"{message}... ({progress}%)")
            progress_bar.progress(progress)
            time.sleep(0.05)
        
        return result
    
    finally:
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

def render_loading_spinner(duration: int = 2, message: str = "Loading..."):
    """
    Render a loading spinner for a specified duration.
    
    Args:
        duration: Duration in seconds
        message: Spinner message
    """
    with st.spinner(message):
        time.sleep(duration)

# Empty state utilities
def render_empty_state(message: str, icon: str = None):
    """
    Render an empty state message.
    
    Args:
        message: Empty state message
        icon: Optional icon name or emoji
    """
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        if icon:
            icon_str = get_icon(icon)
            st.markdown(f"<h1 style='text-align: center'>{icon_str}</h1>", unsafe_allow_html=True)
        
        st.markdown(f"<h3 style='text-align: center'>{message}</h3>", unsafe_allow_html=True)
        st.markdown("---")

# File utilities
def show_file_uploader(label: str, type: List[str] = None, accept_multiple_files: bool = False, key: str = None):
    """
    Show a file uploader.
    
    Args:
        label: Uploader label
        type: Allowed file types (e.g., ["pdf", "docx"])
        accept_multiple_files: Whether to accept multiple files
        key: Widget key
        
    Returns:
        Uploaded file or files
    """
    return st.file_uploader(label, type=type, accept_multiple_files=accept_multiple_files, key=key)

def save_uploaded_file(uploaded_file, directory: str = "uploads"):
    """
    Save an uploaded file to disk.
    
    Args:
        uploaded_file: Uploaded file object
        directory: Directory to save file
        
    Returns:
        Path to saved file
    """
    # Create directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(directory, uploaded_file.name)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def get_file_extension(file_path: str) -> str:
    """
    Get the file extension of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File extension (lowercase, without the dot)
    """
    _, ext = os.path.splitext(file_path)
    return ext.lower().lstrip(".")

def create_download_link(content, filename: str, text: str = "Download"):
    """
    Create a download link for file content.
    
    Args:
        content: File content (bytes or string)
        filename: Download filename
        text: Link text
        
    Returns:
        HTML download link
    """
    # Convert string to bytes if needed
    if isinstance(content, str):
        content = content.encode("utf-8")
    
    # Create download link
    b64 = base64.b64encode(content).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'
    
    return href
"""
UI helper functions for Streamlit components
"""

import time
import base64
import streamlit as st
from io import BytesIO

def set_page_config(page_title, page_icon, layout, initial_sidebar_state):
    """
    Configure the Streamlit page settings.
    
    Args:
        page_title: The title of the page
        page_icon: Icon to display in the browser tab
        layout: Page layout ('wide' or 'centered')
        initial_sidebar_state: Initial state of the sidebar ('auto', 'expanded', 'collapsed')
    """
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout=layout,
        initial_sidebar_state=initial_sidebar_state,
    )
    
    # Hide the default Streamlit nav menu above the title
    hide_streamlit_nav = """
    <style>
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Adjust spacing to compensate for hidden header */
        .main .block-container {padding-top: 2rem;}
    </style>
    """
    st.markdown(hide_streamlit_nav, unsafe_allow_html=True)

def show_progress_bar(container, current, total, label="Progress"):
    """
    Show a progress bar in the given container.
    
    Args:
        container: Streamlit container to render the progress bar in
        current: Current progress value
        total: Total value for 100% progress
        label: Label to show with the progress bar
    """
    if total <= 0:
        return
    
    percentage = min(100, int((current / total) * 100))
    container.progress(percentage / 100, text=f"{label}: {percentage}%")

def create_download_link(content, filename, link_text="Download file"):
    """
    Create a download link for content to be downloaded as a file.
    
    Args:
        content: The content to be downloaded
        filename: The name of the file
        link_text: The text to display for the download link
        
    Returns:
        HTML string for the download link
    """
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def create_thumbnail(image_data, max_width=200, max_height=300):
    """
    Create a thumbnail from image data.
    
    Args:
        image_data: Base64 encoded image data or file path
        max_width: Maximum width of the thumbnail
        max_height: Maximum height of the thumbnail
        
    Returns:
        HTML string for displaying the thumbnail
    """
    if not image_data:
        return None
    
    # If image_data is a base64 string, use it directly
    if isinstance(image_data, str) and image_data.startswith('data:image'):
        img_html = f'<img src="{image_data}" style="max-width:{max_width}px; max-height:{max_height}px;">'
        return img_html
    
    # If image_data is base64 encoded data without the prefix
    if isinstance(image_data, str) and len(image_data) > 100:  # Probably base64 data
        try:
            img_html = f'<img src="data:image/jpeg;base64,{image_data}" style="max-width:{max_width}px; max-height:{max_height}px;">'
            return img_html
        except:
            pass
    
    # Default placeholder
    return None
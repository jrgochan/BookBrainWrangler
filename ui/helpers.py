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
        total = 1  # Avoid division by zero
    
    percent = min(current / total, 1.0)
    container.progress(percent)
    container.caption(f"{label}: {int(percent * 100)}% ({current}/{total})")

def get_image_download_link(img, filename="image.png", button_text="Download Image"):
    """
    Generate a download link for an image.
    
    Args:
        img: PIL Image object
        filename: Name of the download file
        button_text: Text for the download button
        
    Returns:
        HTML string with download link
    """
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/png;base64,{img_str}" download="{filename}">{button_text}</a>'
    return href

def get_pdf_download_link(pdf_bytes, filename="document.pdf", button_text="Download PDF"):
    """
    Generate a download link for a PDF.
    
    Args:
        pdf_bytes: Bytes of the PDF file
        filename: Name of the download file
        button_text: Text for the download button
        
    Returns:
        HTML string with download link
    """
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">{button_text}</a>'
    return href

def get_text_download_link(text, filename="text.txt", button_text="Download Text"):
    """
    Generate a download link for text content.
    
    Args:
        text: Text content to download
        filename: Name of the download file
        button_text: Text for the download button
        
    Returns:
        HTML string with download link
    """
    b64 = base64.b64encode(text.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{button_text}</a>'
    return href

def simulate_typing(placeholder, text, speed=0.01):
    """
    Simulate typing effect for text responses.
    
    Args:
        placeholder: Streamlit placeholder object
        text: Text to display
        speed: Delay between characters in seconds
    """
    displayed_text = ""
    for char in text:
        displayed_text += char
        placeholder.markdown(displayed_text)
        time.sleep(speed)
        
def add_vertical_space(num_lines=1):
    """
    Add vertical space to the Streamlit UI.
    
    Args:
        num_lines: Number of line breaks to add
    """
    for _ in range(num_lines):
        st.markdown("<br>", unsafe_allow_html=True)
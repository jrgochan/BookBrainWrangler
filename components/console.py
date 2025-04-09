"""
Console component for displaying terminal-like output in Streamlit.
"""

import streamlit as st
from datetime import datetime
import time
from typing import List, Dict, Any, Optional

def render_console(
    logs: List[Dict[str, Any]],
    title: str = "Processing Console",
    max_height: int = 400,
    auto_scroll: bool = True,
    key: str = "console"
):
    """
    Render a terminal-like console in Streamlit.
    
    Args:
        logs: List of log entries with 'message', 'level', and 'timestamp' keys
        title: Console title
        max_height: Maximum height of the console in pixels
        auto_scroll: Whether to automatically scroll to the bottom
        key: Unique key for the component
    """
    # Container for the console
    st.subheader(title)
    
    # Create console container with custom styling
    console_container = st.container()
    
    # Apply custom styles for console appearance
    console_styles = """
    <style>
    .console-box {
        background-color: #0e1117;
        color: #ffffff;
        font-family: 'Courier New', monospace;
        padding: 10px;
        border-radius: 5px;
        overflow-y: auto;
        max-height: MAXHEIGHTpx;
        border: 1px solid #444;
    }
    .console-line {
        margin: 0;
        padding: 2px 0;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .console-info {
        color: #58a6ff;
    }
    .console-success {
        color: #3fb950;
    }
    .console-warning {
        color: #d29922;
    }
    .console-error {
        color: #f85149;
    }
    .console-debug {
        color: #8b949e;
    }
    .console-timestamp {
        color: #8b949e;
        font-size: 0.8em;
        margin-right: 5px;
    }
    </style>
    """.replace("MAXHEIGHT", str(max_height))
    
    st.markdown(console_styles, unsafe_allow_html=True)
    
    # Render logs
    log_html = '<div class="console-box">'
    
    for log in logs:
        timestamp = log.get('timestamp', datetime.now())
        level = log.get('level', 'INFO').upper()
        message = log.get('message', '')
        
        # Format timestamp
        timestamp_str = timestamp.strftime("%H:%M:%S.%f")[:-3]
        
        # Determine log level class
        level_class = "console-info"
        if level == "ERROR":
            level_class = "console-error"
        elif level == "WARNING":
            level_class = "console-warning"
        elif level == "SUCCESS":
            level_class = "console-success"
        elif level == "DEBUG":
            level_class = "console-debug"
        
        # Create log line
        log_html += f'<div class="console-line">'
        log_html += f'<span class="console-timestamp">{timestamp_str}</span>'
        log_html += f'<span class="{level_class}">[{level}]</span> {message}'
        log_html += '</div>'
    
    log_html += '</div>'
    
    # Add auto-scroll JavaScript if enabled
    if auto_scroll and logs:
        auto_scroll_js = """
        <script>
            // Auto-scroll to bottom of console
            const consoleBox = document.querySelector('.console-box');
            if (consoleBox) {
                consoleBox.scrollTop = consoleBox.scrollHeight;
            }
        </script>
        """
        log_html += auto_scroll_js
    
    # Render the HTML
    with console_container:
        st.markdown(log_html, unsafe_allow_html=True)
        
def create_processing_logger(console_logs: List[Dict[str, Any]]):
    """
    Create a callback function for logging processing progress.
    
    Args:
        console_logs: List that will be updated with log entries
        
    Returns:
        A callback function to be used during document processing
    """
    def log_progress(progress: float, message: str):
        """
        Log progress during document processing.
        
        Args:
            progress: Progress value between 0 and 1
            message: Progress message
        """
        # Format progress percentage
        progress_pct = int(progress * 100)
        
        # Create formatted message with progress bar
        bar_length = 20
        filled_length = int(bar_length * progress)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        formatted_message = f"{bar} {progress_pct}% | {message}"
        
        # Add to console logs
        console_logs.append({
            'timestamp': datetime.now(),
            'level': 'INFO',
            'message': formatted_message
        })
        
        # Simulate delay to make processing visible
        time.sleep(0.05)
        
    return log_progress
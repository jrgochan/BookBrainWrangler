"""
Settings page for the application.
This page allows users to configure application settings.
"""

import streamlit as st
import os
import platform
from typing import Dict, Any

from utils.logger import get_logger

# Get a logger for this module
logger = get_logger(__name__)

def render_settings_page(ai_client):
    """
    Render the Settings page.
    
    Args:
        ai_client: The AI client instance
    """
    logger.info("Rendering Settings page")
    st.title("Settings")
    
    # Create tabs for different settings categories
    settings_tabs = st.tabs(["Ollama", "OCR", "User Interface", "Advanced"])
    
    with settings_tabs[0]:
        render_ollama_settings(ai_client)
    
    with settings_tabs[1]:
        render_ocr_settings()
    
    with settings_tabs[2]:
        render_ui_settings()
    
    with settings_tabs[3]:
        render_advanced_settings()
    
    # Save settings button at the bottom of the page
    if st.button("Save All Settings", type="primary", use_container_width=True):
        logger.info("Saving all settings")
        st.success("All settings saved successfully!")
        st.rerun()

def render_ollama_settings(ai_client):
    """
    Render Ollama settings section.
    
    Args:
        ai_client: The AI client instance
    """
    st.header("Ollama AI Settings")
    
    # Initialize Ollama settings if they don't exist
    if 'ollama_settings' not in st.session_state:
        st.session_state.ollama_settings = {
            'model': os.environ.get("OLLAMA_MODEL", "llama2"),
            'server_url': os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
            'temperature': 0.7,
            'context_window': 4096,
        }
    
    # Server settings
    st.subheader("Server Configuration")
    
    # Get current status
    server_status = "Unknown"
    try:
        if ai_client.is_server_running():
            server_status = "Connected"
            status_color = "green"
        else:
            server_status = "Disconnected"
            status_color = "red"
    except Exception as e:
        server_status = f"Error: {str(e)}"
        status_color = "red"
        logger.error(f"Error checking Ollama server status: {str(e)}")
    
    # Display server status
    st.markdown(f"**Server Status:** <span style='color:{status_color}'>{server_status}</span>", unsafe_allow_html=True)
    
    # Server URL
    server_url = st.text_input(
        "Ollama Server URL",
        value=st.session_state.ollama_settings.get('server_url', "http://localhost:11434"),
        help="The URL of your Ollama server. Default is http://localhost:11434"
    )
    
    # Update settings if changed
    if server_url != st.session_state.ollama_settings.get('server_url'):
        st.session_state.ollama_settings['server_url'] = server_url
        
        # Update the client
        try:
            ai_client.server_url = server_url
            logger.info(f"Updated Ollama server URL to {server_url}")
            st.rerun()  # Rerun to refresh server status
        except Exception as e:
            logger.error(f"Error updating Ollama server URL: {str(e)}")
    
    # Model settings
    st.subheader("Model Configuration")
    
    # Get available models
    available_models = []
    try:
        available_models = ai_client.list_models()
        if not available_models:
            st.warning("No models found on the Ollama server.")
            available_models = ["llama2"]  # Default fallback
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        st.error(f"Error listing models: {str(e)}")
        available_models = ["llama2"]  # Default fallback
    
    # Model selection
    current_model = st.session_state.ollama_settings.get('model', "llama2")
    model_index = 0
    
    # Find the index of the current model
    if current_model in available_models:
        model_index = available_models.index(current_model)
    
    selected_model = st.selectbox(
        "Default AI Model",
        available_models,
        index=model_index,
        help="Select the default AI model to use for chat interactions"
    )
    
    # Update settings if changed
    if selected_model != st.session_state.ollama_settings.get('model'):
        st.session_state.ollama_settings['model'] = selected_model
        
        # Update the client
        try:
            ai_client.model_name = selected_model
            logger.info(f"Updated Ollama model to {selected_model}")
        except Exception as e:
            logger.error(f"Error updating Ollama model: {str(e)}")
    
    # Model parameters
    st.subheader("Generation Parameters")
    
    # Temperature
    temperature = st.slider(
        "Default Temperature",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.ollama_settings.get('temperature', 0.7),
        step=0.1,
        help="Controls randomness. Lower values are more deterministic, higher values are more creative."
    )
    
    # Update settings if changed
    if temperature != st.session_state.ollama_settings.get('temperature'):
        st.session_state.ollama_settings['temperature'] = temperature
    
    # Context window
    context_window = st.slider(
        "Default Context Window",
        min_value=1024,
        max_value=8192,
        value=st.session_state.ollama_settings.get('context_window', 4096),
        step=1024,
        help="Maximum number of tokens to consider for context."
    )
    
    # Update settings if changed
    if context_window != st.session_state.ollama_settings.get('context_window'):
        st.session_state.ollama_settings['context_window'] = context_window
    
    # Advanced Ollama settings
    with st.expander("Advanced Ollama Settings", expanded=False):
        st.markdown("""
        ### Model Management
        
        To install or update models, use the Ollama CLI:
        
        ```bash
        # Pull a model
        ollama pull llama2
        
        # List installed models
        ollama list
        ```
        
        For more information, visit the [Ollama documentation](https://github.com/ollama/ollama).
        """)

def render_ocr_settings():
    """
    Render OCR settings section.
    """
    st.header("OCR Settings")
    
    # Initialize OCR settings if they don't exist
    if 'ocr_settings' not in st.session_state:
        # Detect the operating system
        system = platform.system().lower()
        
        # Set a default Tesseract path based on the platform
        default_tesseract_path = ""
        if system == 'windows':
            default_tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        elif system == 'linux':
            default_tesseract_path = '/usr/bin/tesseract'
        elif system == 'darwin':  # macOS
            default_tesseract_path = '/usr/local/bin/tesseract'
        
        # Initialize OCR settings
        st.session_state.ocr_settings = {
            'show_current_image': True,
            'show_extracted_text': True,
            'use_ocr': True,
            'confidence_threshold': 70.0,  # percentage
            'display_interval': 5,  # show every 5th page
            'ocr_engine': 'pytesseract',  # Default OCR engine
            'languages': ['eng'],  # Default language for OCR
            'tesseract_path': default_tesseract_path  # Platform-specific default path
        }
    
    # OCR Engine settings
    st.subheader("OCR Engine")
    
    # OCR Engine selection
    ocr_engine = st.selectbox(
        "OCR Engine",
        ["pytesseract"],  # We could add more engines in the future
        index=0 if st.session_state.ocr_settings.get('ocr_engine') == 'pytesseract' else 0,
        help="OCR engine to use for text extraction from images"
    )
    
    # Update settings if changed
    if ocr_engine != st.session_state.ocr_settings.get('ocr_engine'):
        st.session_state.ocr_settings['ocr_engine'] = ocr_engine
    
    # Tesseract Path
    tesseract_path = st.text_input(
        "Tesseract Path",
        value=st.session_state.ocr_settings.get('tesseract_path', ''),
        help="Path to the Tesseract executable"
    )
    
    # Update settings if changed
    if tesseract_path != st.session_state.ocr_settings.get('tesseract_path'):
        st.session_state.ocr_settings['tesseract_path'] = tesseract_path
    
    # OCR Language settings
    st.subheader("OCR Language")
    
    # Language selection
    languages = st.multiselect(
        "OCR Languages",
        ["eng", "fra", "deu", "spa", "ita", "por", "nld", "jpn", "chi_sim", "chi_tra", "kor", "rus", "ara", "hin"],
        default=st.session_state.ocr_settings.get('languages', ['eng']),
        help="Languages to use for OCR. Select multiple for multilingual documents."
    )
    
    # Update settings if changed
    if languages != st.session_state.ocr_settings.get('languages'):
        st.session_state.ocr_settings['languages'] = languages
    
    # OCR Processing settings
    st.subheader("Processing Settings")
    
    # Use OCR checkbox
    use_ocr = st.checkbox(
        "Enable OCR for PDFs",
        value=st.session_state.ocr_settings.get('use_ocr', True),
        help="Enable OCR for text extraction from PDFs. Disable for PDFs with embedded text."
    )
    
    # Update settings if changed
    if use_ocr != st.session_state.ocr_settings.get('use_ocr'):
        st.session_state.ocr_settings['use_ocr'] = use_ocr
    
    # Confidence threshold
    confidence_threshold = st.slider(
        "Confidence Threshold (%)",
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.ocr_settings.get('confidence_threshold', 70.0),
        step=5.0,
        help="Minimum confidence level for OCR results. Lower values include more uncertain text."
    )
    
    # Update settings if changed
    if confidence_threshold != st.session_state.ocr_settings.get('confidence_threshold'):
        st.session_state.ocr_settings['confidence_threshold'] = confidence_threshold
    
    # OCR Display settings
    st.subheader("Display Settings")
    
    # Show current image checkbox
    show_current_image = st.checkbox(
        "Show Current Image During Processing",
        value=st.session_state.ocr_settings.get('show_current_image', True),
        help="Show the current image being processed during OCR"
    )
    
    # Update settings if changed
    if show_current_image != st.session_state.ocr_settings.get('show_current_image'):
        st.session_state.ocr_settings['show_current_image'] = show_current_image
    
    # Show extracted text checkbox
    show_extracted_text = st.checkbox(
        "Show Extracted Text During Processing",
        value=st.session_state.ocr_settings.get('show_extracted_text', True),
        help="Show the extracted text during OCR processing"
    )
    
    # Update settings if changed
    if show_extracted_text != st.session_state.ocr_settings.get('show_extracted_text'):
        st.session_state.ocr_settings['show_extracted_text'] = show_extracted_text
    
    # Display interval
    display_interval = st.slider(
        "Display Interval",
        min_value=1,
        max_value=20,
        value=st.session_state.ocr_settings.get('display_interval', 5),
        step=1,
        help="Show every Nth page during processing. Higher values improve performance."
    )
    
    # Update settings if changed
    if display_interval != st.session_state.ocr_settings.get('display_interval'):
        st.session_state.ocr_settings['display_interval'] = display_interval

def render_ui_settings():
    """
    Render user interface settings section.
    """
    st.header("User Interface Settings")
    
    # Initialize UI settings if they don't exist
    if 'ui_settings' not in st.session_state:
        st.session_state.ui_settings = {
            'show_welcome_message': True,
            'enable_animations': True,
            'dark_mode': True,
            'auto_save_edits': True,
            'thumbnail_size': 150,
        }
    
    # General UI settings
    st.subheader("General Settings")
    
    # Show welcome message checkbox
    show_welcome_message = st.checkbox(
        "Show Welcome Message",
        value=st.session_state.ui_settings.get('show_welcome_message', True),
        help="Show a welcome message when the application starts"
    )
    
    # Update settings if changed
    if show_welcome_message != st.session_state.ui_settings.get('show_welcome_message'):
        st.session_state.ui_settings['show_welcome_message'] = show_welcome_message
    
    # Enable animations checkbox
    enable_animations = st.checkbox(
        "Enable Animations",
        value=st.session_state.ui_settings.get('enable_animations', True),
        help="Enable animations in the user interface"
    )
    
    # Update settings if changed
    if enable_animations != st.session_state.ui_settings.get('enable_animations'):
        st.session_state.ui_settings['enable_animations'] = enable_animations
    
    # Dark mode checkbox
    dark_mode = st.checkbox(
        "Dark Mode",
        value=st.session_state.ui_settings.get('dark_mode', True),
        help="Use dark mode for the user interface"
    )
    
    # Update settings if changed
    if dark_mode != st.session_state.ui_settings.get('dark_mode'):
        st.session_state.ui_settings['dark_mode'] = dark_mode
    
    # Thumbnail size
    thumbnail_size = st.slider(
        "Thumbnail Size",
        min_value=50,
        max_value=300,
        value=st.session_state.ui_settings.get('thumbnail_size', 150),
        step=10,
        help="Size of book thumbnails in pixels"
    )
    
    # Update settings if changed
    if thumbnail_size != st.session_state.ui_settings.get('thumbnail_size'):
        st.session_state.ui_settings['thumbnail_size'] = thumbnail_size
    
    # Book management settings
    st.subheader("Book Management")
    
    # Auto-save edits checkbox
    auto_save_edits = st.checkbox(
        "Auto-save Edits",
        value=st.session_state.ui_settings.get('auto_save_edits', True),
        help="Automatically save edits to books"
    )
    
    # Update settings if changed
    if auto_save_edits != st.session_state.ui_settings.get('auto_save_edits'):
        st.session_state.ui_settings['auto_save_edits'] = auto_save_edits

def render_advanced_settings():
    """
    Render advanced settings section.
    """
    st.header("Advanced Settings")
    
    # Initialize advanced settings if they don't exist
    if 'advanced_settings' not in st.session_state:
        st.session_state.advanced_settings = {
            'log_level': 'INFO',
            'clear_cache_on_exit': True,
            'max_tokens_per_chunk': 500,
            'chunk_overlap': 50,
            'embedding_model': 'default',
            'vector_similarity_metric': 'cosine',
        }
    
    # Logging settings
    st.subheader("Logging")
    
    # Log level selection
    log_level = st.selectbox(
        "Log Level",
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(st.session_state.advanced_settings.get('log_level', 'INFO')),
        help="Set the logging level for the application"
    )
    
    # Update settings if changed
    if log_level != st.session_state.advanced_settings.get('log_level'):
        st.session_state.advanced_settings['log_level'] = log_level
        
        # Update logger configuration
        try:
            logger.setLevel(log_level)
            logger.info(f"Log level set to {log_level}")
        except Exception as e:
            logger.error(f"Error setting log level: {str(e)}")
    
    # Clear cache on exit checkbox
    clear_cache_on_exit = st.checkbox(
        "Clear Cache on Exit",
        value=st.session_state.advanced_settings.get('clear_cache_on_exit', True),
        help="Clear temporary files when the application exits"
    )
    
    # Update settings if changed
    if clear_cache_on_exit != st.session_state.advanced_settings.get('clear_cache_on_exit'):
        st.session_state.advanced_settings['clear_cache_on_exit'] = clear_cache_on_exit
    
    # Embedding settings
    st.subheader("Embedding and Indexing")
    
    # Max tokens per chunk
    max_tokens_per_chunk = st.slider(
        "Max Tokens Per Chunk",
        min_value=100,
        max_value=2000,
        value=st.session_state.advanced_settings.get('max_tokens_per_chunk', 500),
        step=50,
        help="Maximum number of tokens per chunk for knowledge base indexing"
    )
    
    # Update settings if changed
    if max_tokens_per_chunk != st.session_state.advanced_settings.get('max_tokens_per_chunk'):
        st.session_state.advanced_settings['max_tokens_per_chunk'] = max_tokens_per_chunk
    
    # Chunk overlap
    chunk_overlap = st.slider(
        "Chunk Overlap",
        min_value=0,
        max_value=200,
        value=st.session_state.advanced_settings.get('chunk_overlap', 50),
        step=10,
        help="Number of tokens of overlap between chunks"
    )
    
    # Update settings if changed
    if chunk_overlap != st.session_state.advanced_settings.get('chunk_overlap'):
        st.session_state.advanced_settings['chunk_overlap'] = chunk_overlap
    
    # Embedding model
    embedding_model = st.selectbox(
        "Embedding Model",
        ["default", "ollama"],
        index=0 if st.session_state.advanced_settings.get('embedding_model') == 'default' else 1,
        help="Model to use for embedding generation"
    )
    
    # Update settings if changed
    if embedding_model != st.session_state.advanced_settings.get('embedding_model'):
        st.session_state.advanced_settings['embedding_model'] = embedding_model
    
    # Vector similarity metric
    vector_similarity_metric = st.selectbox(
        "Vector Similarity Metric",
        ["cosine", "euclidean", "dot_product"],
        index=["cosine", "euclidean", "dot_product"].index(st.session_state.advanced_settings.get('vector_similarity_metric', 'cosine')),
        help="Metric to use for measuring vector similarity in search"
    )
    
    # Update settings if changed
    if vector_similarity_metric != st.session_state.advanced_settings.get('vector_similarity_metric'):
        st.session_state.advanced_settings['vector_similarity_metric'] = vector_similarity_metric
    
    # Danger Zone
    st.subheader("Danger Zone")
    
    with st.expander("Reset Application", expanded=False):
        st.warning("⚠️ These actions cannot be undone!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Reset All Settings", type="primary"):
                # Clear all settings
                if 'ollama_settings' in st.session_state:
                    del st.session_state.ollama_settings
                if 'ocr_settings' in st.session_state:
                    del st.session_state.ocr_settings
                if 'ui_settings' in st.session_state:
                    del st.session_state.ui_settings
                if 'advanced_settings' in st.session_state:
                    del st.session_state.advanced_settings
                
                logger.warning("All settings reset to defaults")
                st.success("All settings reset to defaults")
                time.sleep(1)
                st.rerun()
        
        with col2:
            if st.button("Clear Thumbnail Cache", type="primary"):
                # Clear thumbnail cache
                if 'thumbnail_cache' in st.session_state:
                    st.session_state.thumbnail_cache = {}
                
                logger.info("Thumbnail cache cleared")
                st.success("Thumbnail cache cleared")
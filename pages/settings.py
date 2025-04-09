"""
Settings page for the application.
"""

import streamlit as st
import os
from typing import Dict, List, Any, Tuple

def render_settings_page(ollama_client):
    """
    Render the Settings page.
    
    Args:
        ollama_client: The OllamaClient instance
    """
    st.title("Book Knowledge AI Settings")
    
    # Tabs for different settings
    tab1, tab2, tab3 = st.tabs(["AI Settings", "OCR Settings", "Display Settings"])
    
    with tab1:
        render_ai_settings(ollama_client)
    
    with tab2:
        render_ocr_settings()
    
    with tab3:
        render_display_settings()

def render_ai_settings(ollama_client):
    """
    Render AI settings section.
    
    Args:
        ollama_client: The OllamaClient instance
    """
    st.header("AI Server Settings")
    
    # Get current Ollama settings
    if 'ollama_settings' not in st.session_state:
        st.session_state.ollama_settings = {
            'model': 'llama2',
            'server_url': 'http://localhost:11434',
            'temperature': 0.7,
            'context_window': 4096,
        }
        
    current_host = st.session_state.ollama_settings['server_url']
    current_model = st.session_state.ollama_settings['model']
    
    # Connection status
    connection_status = ollama_client.is_server_running()
    
    if connection_status:
        st.success(f"✓ Connected to Ollama server at {current_host}")
        
        # Display available models
        model_names = ollama_client.get_available_models()
        if model_names:
            # Create a clickable list of models
            st.subheader("Available Models")
            
            for name in model_names:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{name}**")
                with col2:
                    if name == current_model:
                        st.success("Active")
                    else:
                        if st.button(f"Select", key=f"select_{name}"):
                            st.session_state.ollama_settings['model'] = name
                            st.success(f"Model changed to {name}")
                            st.rerun()
        else:
            st.warning("No models found on the Ollama server. Use 'ollama pull MODEL_NAME' to download models.")
    else:
        st.error(f"Cannot connect to Ollama server at {current_host}")
        st.info("""
            ### How to set up Ollama:
            1. Install Ollama from [ollama.ai](https://ollama.ai)
            2. Start the Ollama server
            3. Pull a model like 'llama2' using the command: `ollama pull llama2`
            4. Configure the connection below
        """)
    
    # Server configuration
    st.subheader("Server Configuration")
    
    with st.form("ollama_settings_form"):
        new_host = st.text_input("Ollama API Host", value=current_host)
        new_model = st.text_input("Default Model", value=current_model)
        
        submit_button = st.form_submit_button("Update Settings")
        
        if submit_button:
            if new_host != current_host or new_model != current_model:
                # Update settings
                # Update client configuration
                ollama_client.server_url = new_host
                ollama_client.model = new_model
                ollama_client.api_base = f"{new_host}/api"
                
                # Test connection
                if ollama_client.is_server_running():
                    # Update session state
                    st.session_state.ollama_settings['server_url'] = new_host
                    st.session_state.ollama_settings['model'] = new_model
                    st.success("Settings updated successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to connect to Ollama at {new_host}")

def render_ocr_settings():
    """Render OCR settings section."""
    st.header("OCR Settings")
    
    # OCR engine options
    OCR_ENGINES = {
        "pytesseract": "PyTesseract (Default)",
        "easyocr": "EasyOCR (Advanced)"
    }
    
    # Import conditionally to check if engines are available
    try:
        import easyocr
        EASYOCR_AVAILABLE = True
    except ImportError:
        EASYOCR_AVAILABLE = False
    
    # Get current OCR settings
    if 'ocr_settings' not in st.session_state:
        st.session_state.ocr_settings = {
            'display_interval': 1,
            'confidence_threshold': 70,
            'show_current_image': True,
            'show_extracted_text': True,
            'ocr_engine': 'pytesseract',
            'languages': ['en'],
            'tesseract_path': r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        }
    
    current_settings = st.session_state.ocr_settings
    
    # OCR Engine selection
    st.subheader("OCR Engine Configuration")
    
    # Display information about available OCR engines
    engine_info_col1, engine_info_col2 = st.columns(2)
    with engine_info_col1:
        st.info("**PyTesseract**: Standard OCR engine with good accuracy for most documents.")
    
    with engine_info_col2:
        if EASYOCR_AVAILABLE:
            st.info("**EasyOCR**: Advanced deep learning-based OCR with support for multiple languages.")
        else:
            st.error("**EasyOCR**: Not available. It needs to be installed to use this option.")
    
    with st.form("ocr_engine_form"):
        # OCR Engine selection
        ocr_engine = st.selectbox(
            "OCR Engine",
            options=list(OCR_ENGINES.keys()),
            format_func=lambda x: OCR_ENGINES[x],
            index=list(OCR_ENGINES.keys()).index(current_settings.get('ocr_engine', 'pytesseract')),
            help="Select which OCR engine to use for text extraction from images"
        )
        
        # EasyOCR-specific settings
        if ocr_engine == "easyocr":
            if not EASYOCR_AVAILABLE:
                st.warning("EasyOCR is not installed. The system will fall back to PyTesseract.")
            
            # Language selection
            languages_options = {
                'en': 'English', 
                'fr': 'French',
                'es': 'Spanish',
                'de': 'German',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'ja': 'Japanese',
                'ko': 'Korean',
                'zh': 'Chinese (Simplified)',
                'zh_tra': 'Chinese (Traditional)',
                'ar': 'Arabic'
            }
            
            # Select languages
            selected_languages = st.multiselect(
                "Languages to detect",
                options=list(languages_options.keys()),
                default=current_settings.get('languages', ['en']),
                format_func=lambda x: languages_options.get(x, x),
                help="Select languages to detect (English is recommended as primary language)"
            )
            
            # Ensure at least one language is selected
            if not selected_languages:
                selected_languages = ['en']
                st.info("At least one language must be selected. Defaulting to English.")
        
        # PyTesseract-specific settings
        if ocr_engine == "pytesseract":
            tesseract_path = st.text_input(
                "Tesseract executable path",
                value=current_settings.get('tesseract_path', r'C:\Program Files\Tesseract-OCR\tesseract.exe'),
                help="Path to Tesseract executable (Windows only, leave default on Linux/Mac)"
            )
        
        engine_submit_button = st.form_submit_button("Update OCR Engine")
        
        if engine_submit_button:
            # Update engine settings
            new_settings = current_settings.copy()
            new_settings['ocr_engine'] = ocr_engine
            
            if ocr_engine == "easyocr":
                new_settings['languages'] = selected_languages
            
            if ocr_engine == "pytesseract":
                new_settings['tesseract_path'] = tesseract_path
            
            st.session_state.ocr_settings = new_settings
            st.success(f"OCR engine updated to {OCR_ENGINES[ocr_engine]}!")
    
    # OCR visualization settings
    st.subheader("Document Processing Visualization")
    
    with st.form("ocr_settings_form"):
        show_current_image = st.toggle(
            "Show current page during processing",
            value=current_settings['show_current_image']
        )
        
        show_extracted_text = st.toggle(
            "Show extracted text during processing",
            value=current_settings['show_extracted_text']
        )
        
        display_interval = st.slider(
            "Update display every N pages",
            min_value=1,
            max_value=10,
            value=int(current_settings['display_interval']),
            step=1,
            help="Higher values may improve processing speed by reducing UI updates"
        )
        
        confidence_threshold = st.slider(
            "OCR confidence threshold (%)",
            min_value=0,
            max_value=100,
            value=int(current_settings['confidence_threshold']),
            step=1,
            help="Pages with OCR confidence below this threshold will be flagged as low quality"
        )
        
        submit_button = st.form_submit_button("Save Visualization Settings")
        
        if submit_button:
            # Update visualization settings but keep engine settings intact
            new_settings = st.session_state.ocr_settings.copy()
            new_settings.update({
                'display_interval': display_interval,
                'confidence_threshold': confidence_threshold,
                'show_current_image': show_current_image,
                'show_extracted_text': show_extracted_text
            })
            
            st.session_state.ocr_settings = new_settings
            st.success("OCR visualization settings updated!")

def render_display_settings():
    """Render display settings section."""
    st.header("Display Settings")
    
    # Thumbnail settings
    st.subheader("Book Thumbnails")
    
    # Initialize thumbnail settings if not present
    if 'thumbnail_size' not in st.session_state:
        st.session_state.thumbnail_size = (200, 280)
    if 'thumbnail_bg_color' not in st.session_state:
        st.session_state.thumbnail_bg_color = (240, 240, 240)
    if 'thumbnail_text_color' not in st.session_state:
        st.session_state.thumbnail_text_color = (70, 70, 70)
    
    with st.form("thumbnail_settings_form"):
        # Thumbnail size
        col1, col2 = st.columns(2)
        with col1:
            width = st.number_input(
                "Width (px)",
                min_value=100,
                max_value=500,
                value=st.session_state.thumbnail_size[0]
            )
        with col2:
            height = st.number_input(
                "Height (px)",
                min_value=100,
                max_value=700,
                value=st.session_state.thumbnail_size[1]
            )
        
        # Color settings
        st.subheader("Placeholder Colors")
        st.caption("For books without PDF cover pages")
        
        # Background color
        bg_color = st.color_picker(
            "Background Color",
            "#F0F0F0" if isinstance(st.session_state.thumbnail_bg_color, tuple) else st.session_state.thumbnail_bg_color
        )
        
        # Text color
        text_color = st.color_picker(
            "Text Color",
            "#464646" if isinstance(st.session_state.thumbnail_text_color, tuple) else st.session_state.thumbnail_text_color
        )
        
        # Save button
        submit_button = st.form_submit_button("Save Display Settings")
        
        if submit_button:
            # Convert hex colors to RGB tuples
            bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            text_rgb = tuple(int(text_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            
            # Update session state
            st.session_state.thumbnail_size = (width, height)
            st.session_state.thumbnail_bg_color = bg_rgb
            st.session_state.thumbnail_text_color = text_rgb
            
            # Clear thumbnail cache to regenerate with new settings
            if 'thumbnail_cache' in st.session_state:
                st.session_state.thumbnail_cache = {}
            
            st.success("Display settings updated!")
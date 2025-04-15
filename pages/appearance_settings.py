"""
Appearance settings page for Book Knowledge AI application.
Provides theme selection and user interface customization.
"""

import streamlit as st
from components.theme_selector import render_theme_selector, get_available_themes, get_theme, get_current_theme, apply_theme, get_theme_description, inject_custom_css
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

def render():
    """Render appearance settings section for theme selection."""
    st.title("Appearance Settings")
    
    # Apply theme's custom CSS
    inject_custom_css()
    
    st.write("**Theme Selection**")
    st.write("Choose a theme that matches your mood or enhances your reading experience.")
    
    # Get current theme
    current_theme_id = get_current_theme()
    current_theme = get_theme(current_theme_id)
    
    # Display current theme
    st.markdown(f"""
    <div style="background-color:{current_theme['primary']}; color:white; padding:15px; border-radius:8px; margin-bottom:20px;">
        <h3 style="margin:0;">{current_theme['name']}</h3>
        <p style="margin-top:5px;">{get_theme_description(current_theme_id)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Theme selector
    render_theme_selector()
    
    st.info("The theme will be applied to all pages in the application.")
    
    # Font size settings
    st.subheader("Font Settings")
    
    font_size = st.select_slider(
        "Font size:",
        options=["Small", "Medium", "Large"],
        value=st.session_state.get("font_size", "Medium")
    )
    st.session_state.font_size = font_size
    
    # Additional appearance options
    st.subheader("Customization")
    
    show_thumbnails = st.checkbox(
        "Show book thumbnails in list views", 
        value=st.session_state.get("show_thumbnails", True)
    )
    st.session_state.show_thumbnails = show_thumbnails
    
    compact_view = st.checkbox(
        "Use compact view for search results", 
        value=st.session_state.get("compact_view", False)
    )
    st.session_state.compact_view = compact_view
    
    # Save settings
    if st.button("Save Appearance Settings", type="primary"):
        st.success("Appearance settings saved successfully!")
        logger.info(f"Appearance settings updated: theme={current_theme_id}, font_size={font_size}")
        
    st.divider()
    
    # Advanced customization
    with st.expander("Advanced Customization (CSS)"):
        st.write("Add custom CSS to further customize the application's appearance.")
        
        custom_css = st.text_area(
            "Custom CSS:",
            value=st.session_state.get("custom_css", ""),
            height=200,
            help="Add custom CSS rules to customize the application appearance."
        )
        st.session_state.custom_css = custom_css
        
        if st.button("Apply Custom CSS"):
            st.success("Custom CSS applied successfully!")
            st.rerun()
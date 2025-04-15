"""
Theme selector component for Book Knowledge AI application.
Provides a user interface for selecting different mood-based themes.
"""

import json
import os
import streamlit as st
from typing import Dict, Any, List, Tuple, Optional

# Define available themes
THEMES = {
    "calm": {
        "name": "Calm Blue",
        "primary": "#4169E1",
        "background": "#F0F8FF",
        "secondary": "#87CEEB",
        "text": "#2C3E50",
        "accent": "#1E90FF",
        "font": "sans-serif"
    },
    "forest": {
        "name": "Forest Green",
        "primary": "#2E8B57",
        "background": "#F5F8F5",
        "secondary": "#8FBC8F",
        "text": "#2C3E30",
        "accent": "#3CB371",
        "font": "sans-serif"
    },
    "sunset": {
        "name": "Sunset Orange",
        "primary": "#FF7F50",
        "background": "#FFF5F0",
        "secondary": "#FFDAB9",
        "text": "#4E3A2D",
        "accent": "#FF6347",
        "font": "sans-serif"
    },
    "lavender": {
        "name": "Lavender Dreams",
        "primary": "#9370DB",
        "background": "#F8F5FF",
        "secondary": "#D8BFD8",
        "text": "#483D8B",
        "accent": "#8A2BE2",
        "font": "sans-serif"
    },
    "dark": {
        "name": "Dark Mode",
        "primary": "#607D8B",
        "background": "#2C3E50",
        "secondary": "#455A64",
        "text": "#ECEFF1",
        "accent": "#90A4AE",
        "font": "sans-serif"
    },
    "focus": {
        "name": "Deep Focus",
        "primary": "#2C3E50",
        "background": "#FFFFFF",
        "secondary": "#ECF0F1",
        "text": "#2C3E50",
        "accent": "#3498DB",
        "font": "serif"
    },
    "creative": {
        "name": "Creative Mode",
        "primary": "#9C27B0",
        "background": "#FCF5FF",
        "secondary": "#E1BEE7",
        "text": "#4A148C",
        "accent": "#7B1FA2",
        "font": "cursive"
    }
}

# Theme descriptions
THEME_DESCRIPTIONS = {
    "calm": "A calming blue theme that helps you focus while reading and researching.",
    "forest": "A natural green palette that creates a peaceful, organic environment.",
    "sunset": "Warm orange tones that inspire creativity and positive energy.",
    "lavender": "Gentle purple hues that stimulate imagination and intuition.",
    "dark": "Low-light theme that reduces eye strain during night sessions.",
    "focus": "High-contrast minimalist design for deep concentration.",
    "creative": "Vibrant colors to inspire creative thinking and exploration."
}

def get_theme(theme_id: str) -> Dict[str, Any]:
    """
    Get a theme by ID.
    
    Args:
        theme_id: ID of the theme to retrieve
        
    Returns:
        Theme dictionary with color and font values
    """
    if theme_id in THEMES:
        return THEMES[theme_id]
    return THEMES["calm"]  # Default theme

def get_available_themes() -> List[Tuple[str, str]]:
    """
    Get a list of available themes.
    
    Returns:
        List of tuples containing theme ID and name
    """
    return [(theme_id, theme_data["name"]) for theme_id, theme_data in THEMES.items()]

def get_theme_description(theme_id: str) -> str:
    """
    Get the description for a theme.
    
    Args:
        theme_id: ID of the theme
        
    Returns:
        Theme description
    """
    return THEME_DESCRIPTIONS.get(theme_id, "")

def apply_theme(theme_id: str) -> None:
    """
    Apply a theme to the application by setting it in session state.
    
    Args:
        theme_id: ID of the theme to apply
    """
    if theme_id in THEMES:
        st.session_state.theme = theme_id
        # Also update config.toml if needed
        update_theme_config(THEMES[theme_id])
        # Save preference
        save_theme_preference(theme_id)

def update_theme_config(theme: Dict[str, Any]) -> None:
    """
    Update the Streamlit theme configuration in config.toml.
    
    Args:
        theme: Theme dictionary with color and font values
    """
    # This is a placeholder for now
    # In a full implementation, we would modify .streamlit/config.toml
    pass

def save_theme_preference(theme_id: str) -> None:
    """
    Save the user's theme preference to persistent storage.
    
    Args:
        theme_id: ID of the theme to save
    """
    preferences = {"theme": theme_id}
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/user_preferences.json", "w") as f:
            json.dump(preferences, f)
    except Exception as e:
        st.error(f"Error saving theme preference: {str(e)}")

def load_theme_preference() -> str:
    """
    Load the user's theme preference from persistent storage.
    
    Returns:
        Theme ID from saved preferences, or 'calm' if not found
    """
    try:
        if os.path.exists("data/user_preferences.json"):
            with open("data/user_preferences.json", "r") as f:
                preferences = json.load(f)
                return preferences.get("theme", "calm")
    except Exception:
        pass
    return "calm"  # Default theme

def get_current_theme() -> str:
    """
    Get the current theme ID from session state or load from preferences.
    
    Returns:
        Current theme ID
    """
    if hasattr(st.session_state, "theme") and st.session_state.theme:
        return st.session_state.theme
    
    # Load from preferences
    theme_id = load_theme_preference()
    st.session_state.theme = theme_id
    return theme_id

def inject_custom_css() -> None:
    """
    Inject custom CSS for the current theme into the Streamlit app.
    """
    theme_id = get_current_theme()
    theme = get_theme(theme_id)
    
    css = f"""
    <style>
        :root {{
            --primary-color: {theme['primary']};
            --background-color: {theme['background']};
            --secondary-color: {theme['secondary']};
            --text-color: {theme['text']};
            --accent-color: {theme['accent']};
            --font-family: {theme['font']};
        }}
        
        .stApp {{
            background-color: var(--background-color);
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: var(--primary-color);
            font-family: var(--font-family);
        }}
        
        p, li, span, div {{
            color: var(--text-color);
            font-family: var(--font-family);
        }}
        
        .stButton>button {{
            background-color: var(--primary-color);
            color: white;
        }}
        
        .stTextInput>div>div>input {{
            border-color: var(--primary-color);
        }}
        
        .custom-card {{
            border: 1px solid #eee;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            background-color: white;
            transition: transform 0.2s;
        }}
        
        .custom-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
        .theme-preview {{
            border-radius: 8px;
            padding: 10px;
            margin: 5px;
            text-align: center;
            cursor: pointer;
            transition: transform 0.2s;
            color: white;
        }}
        
        .theme-preview:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)

def render_theme_selector() -> None:
    """
    Render the theme selector UI component.
    """
    current_theme_id = get_current_theme()
    
    # Display theme options in a grid
    st.write("Select a theme:")
    
    # Create a grid of theme options
    cols = st.columns(3)
    themes = get_available_themes()
    
    for i, (theme_id, theme_name) in enumerate(themes):
        theme = get_theme(theme_id)
        with cols[i % 3]:
            st.markdown(f"""
            <div class="theme-preview" style="background-color:{theme['primary']};" 
                 onclick="alert('Theme selected!')">
                {theme_name}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Select {theme_name}", key=f"theme_{theme_id}"):
                apply_theme(theme_id)
                st.rerun()
    
    # Show theme description
    st.markdown(f"**{get_theme_description(current_theme_id)}**")

def suggest_theme_based_on_content(text: str) -> Optional[str]:
    """
    Analyze content and suggest an appropriate theme based on mood.
    
    Args:
        text: Text content to analyze
        
    Returns:
        Suggested theme ID or None if no strong suggestion
    """
    # This is a simple keyword-based approach
    # In a full implementation, this would use NLP for sentiment analysis
    
    text = text.lower()
    
    if any(word in text for word in ["calm", "peace", "relax", "sooth", "tranquil"]):
        return "calm"
    
    if any(word in text for word in ["nature", "tree", "forest", "green", "earth"]):
        return "forest"
    
    if any(word in text for word in ["warm", "orange", "sunset", "sun", "bright"]):
        return "sunset"
    
    if any(word in text for word in ["purple", "dream", "imagine", "creative", "night"]):
        return "lavender"
    
    if any(word in text for word in ["dark", "night", "midnight", "evening", "low light"]):
        return "dark"
    
    if any(word in text for word in ["focus", "concentrate", "study", "work", "productive"]):
        return "focus"
    
    if any(word in text for word in ["creative", "art", "design", "vibrant", "color"]):
        return "creative"
    
    return None  # No strong preference detected
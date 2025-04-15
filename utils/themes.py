"""
Themes module for the Book Knowledge AI application.
Provides mood-based color palettes and theme management.
"""

import streamlit as st
from typing import Dict, Any, List, Tuple
import json
import os

# Theme data structure
# Each theme has:
# - primary: Primary brand color
# - secondary: Secondary accent color
# - background: Main background color
# - text: Main text color
# - card_bg: Card background color
# - sidebar_bg: Sidebar background color
# - success: Success message color
# - error: Error message color
# - warning: Warning message color
# - info: Information message color
# - font: Font family

# Define mood-based color palettes
THEMES = {
    "calm": {
        "name": "Calm",
        "description": "Serene blues and soft colors for a peaceful reading experience",
        "primary": "#1E88E5",
        "secondary": "#26A69A",
        "background": "#F5F7FA",
        "text": "#2C3E50",
        "card_bg": "#FFFFFF",
        "sidebar_bg": "#E3F2FD",
        "success": "#4CAF50",
        "error": "#E57373",
        "warning": "#FFB74D",
        "info": "#64B5F6",
        "font": "'Roboto', sans-serif"
    },
    "focus": {
        "name": "Focus",
        "description": "High contrast dark theme for distraction-free reading",
        "primary": "#5E35B1",
        "secondary": "#00ACC1",
        "background": "#263238",
        "text": "#ECEFF1",
        "card_bg": "#37474F",
        "sidebar_bg": "#1E272C",
        "success": "#00E676",
        "error": "#FF5252",
        "warning": "#FFD740",
        "info": "#40C4FF",
        "font": "'Roboto Mono', monospace"
    },
    "energetic": {
        "name": "Energetic",
        "description": "Vibrant colors to inspire creativity and engagement",
        "primary": "#FF5722",
        "secondary": "#FFC107",
        "background": "#FAFAFA",
        "text": "#212121",
        "card_bg": "#FFFFFF",
        "sidebar_bg": "#FFF3E0",
        "success": "#7CB342",
        "error": "#E53935",
        "warning": "#FFA000",
        "info": "#29B6F6",
        "font": "'Nunito', sans-serif"
    },
    "soothing": {
        "name": "Soothing",
        "description": "Gentle pastels and rounded corners for a soft visual experience",
        "primary": "#9C27B0",
        "secondary": "#4CAF50",
        "background": "#F3E5F5",
        "text": "#4A148C",
        "card_bg": "#FFFFFF",
        "sidebar_bg": "#E1BEE7",
        "success": "#66BB6A",
        "error": "#EF9A9A",
        "warning": "#FFCC80",
        "info": "#81D4FA",
        "font": "'Quicksand', sans-serif"
    },
    "classic": {
        "name": "Classic",
        "description": "Traditional library colors with a scholarly feel",
        "primary": "#795548",
        "secondary": "#607D8B",
        "background": "#EFEBE9",
        "text": "#3E2723",
        "card_bg": "#D7CCC8",
        "sidebar_bg": "#BCAAA4",
        "success": "#8BC34A",
        "error": "#FF8A65",
        "warning": "#FFB74D",
        "info": "#90CAF9",
        "font": "'Libre Baskerville', serif"
    }
}

def get_theme(theme_id: str) -> Dict[str, Any]:
    """
    Get a theme by ID.
    
    Args:
        theme_id: ID of the theme to retrieve
        
    Returns:
        Theme dictionary with color and font values
    """
    return THEMES.get(theme_id, THEMES["calm"])

def get_available_themes() -> List[Tuple[str, str]]:
    """
    Get a list of available themes.
    
    Returns:
        List of tuples containing theme ID and name
    """
    return [(theme_id, theme["name"]) for theme_id, theme in THEMES.items()]

def get_theme_description(theme_id: str) -> str:
    """
    Get the description for a theme.
    
    Args:
        theme_id: ID of the theme
        
    Returns:
        Theme description
    """
    theme = get_theme(theme_id)
    return theme.get("description", "")

def apply_theme_to_streamlit(theme_id: str) -> None:
    """
    Apply a theme to the Streamlit application by updating config.toml.
    
    Args:
        theme_id: ID of the theme to apply
    """
    theme = get_theme(theme_id)
    
    # Define the configuration to write
    config = {
        "theme": {
            "primaryColor": theme["primary"],
            "backgroundColor": theme["background"],
            "secondaryBackgroundColor": theme["card_bg"],
            "textColor": theme["text"],
            "font": theme["font"]
        }
    }
    
    # Ensure .streamlit directory exists
    os.makedirs(".streamlit", exist_ok=True)
    
    # Write to config.toml file
    with open(".streamlit/config.toml", "w") as f:
        f.write("[theme]\n")
        f.write(f'primaryColor = "{theme["primary"]}"\n')
        f.write(f'backgroundColor = "{theme["background"]}"\n')
        f.write(f'secondaryBackgroundColor = "{theme["card_bg"]}"\n')
        f.write(f'textColor = "{theme["text"]}"\n')
        f.write(f'font = "{theme["font"]}"\n')
        
        # Server settings
        f.write("\n[server]\n")
        f.write("headless = true\n")
        f.write("address = \"0.0.0.0\"\n")
        f.write("port = 5000\n")
    
    # Store the current theme ID in session state
    st.session_state.current_theme = theme_id
    
def load_current_theme() -> str:
    """
    Load the current theme ID from session state or default to 'calm'.
    
    Returns:
        Current theme ID
    """
    if "current_theme" not in st.session_state:
        st.session_state.current_theme = "calm"
    
    return st.session_state.current_theme

def get_css_variables(theme_id: str) -> str:
    """
    Generate CSS variables for a theme.
    
    Args:
        theme_id: ID of the theme
        
    Returns:
        CSS variable definitions
    """
    theme = get_theme(theme_id)
    
    css = """
    :root {
        --primary: %s;
        --secondary: %s;
        --background: %s;
        --text: %s;
        --card-bg: %s;
        --sidebar-bg: %s;
        --success: %s;
        --error: %s;
        --warning: %s;
        --info: %s;
        --font: %s;
    }
    """ % (
        theme["primary"],
        theme["secondary"],
        theme["background"],
        theme["text"],
        theme["card_bg"],
        theme["sidebar_bg"],
        theme["success"],
        theme["error"],
        theme["warning"],
        theme["info"],
        theme["font"]
    )
    
    return css

def inject_custom_css(theme_id: str) -> None:
    """
    Inject custom CSS for a theme into the Streamlit app.
    
    Args:
        theme_id: ID of the theme
    """
    # Get CSS variables
    css_variables = get_css_variables(theme_id)
    
    # Define custom CSS with the variables
    custom_css = css_variables + """
    /* Custom styles using the theme variables */
    .stApp {
        background-color: var(--background);
        color: var(--text);
        font-family: var(--font);
    }
    
    .stSidebar {
        background-color: var(--sidebar-bg);
    }
    
    /* Card styling */
    div.stCard {
        background-color: var(--card-bg);
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Button styling */
    .stButton>button {
        background-color: var(--primary);
        color: white;
        border: none;
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: var(--secondary);
        transform: translateY(-2px);
    }
    
    /* Success/error message styling */
    .success-box {
        background-color: var(--success);
        color: white;
        padding: 10px;
        border-radius: 4px;
    }
    
    .error-box {
        background-color: var(--error);
        color: white;
        padding: 10px;
        border-radius: 4px;
    }
    
    /* Theme selector styling */
    .theme-card {
        border: 2px solid transparent;
        border-radius: 8px;
        padding: 10px;
        transition: all 0.3s ease;
    }
    
    .theme-card:hover {
        border-color: var(--primary);
        transform: translateY(-5px);
    }
    
    .theme-card.selected {
        border-color: var(--primary);
        background-color: rgba(var(--primary-rgb), 0.1);
    }
    
    /* Custom header */
    .custom-header {
        background-color: var(--primary);
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    """
    
    # Inject the CSS with Streamlit
    st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

def render_theme_selector() -> None:
    """
    Render the theme selector UI component.
    
    This function creates a UI for selecting different themes/moods.
    """
    st.subheader("Application Theme")
    
    # Get current theme
    current_theme = load_current_theme()
    
    # Create columns for themes
    cols = st.columns(len(THEMES))
    
    # Show theme options
    for i, (theme_id, theme) in enumerate(THEMES.items()):
        with cols[i]:
            # Display theme card
            st.markdown(f"""
            <div class="theme-card {'selected' if current_theme == theme_id else ''}">
                <h4>{theme['name']}</h4>
                <div style="width:100%; height:20px; background-color:{theme['primary']}; 
                            margin-bottom:5px; border-radius:4px;"></div>
                <div style="width:100%; height:20px; background-color:{theme['secondary']}; 
                            margin-bottom:10px; border-radius:4px;"></div>
                <p style="font-size:12px;">{theme['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Button to select this theme
            if st.button(f"Select {theme['name']}", key=f"theme_{theme_id}"):
                # Apply the theme
                apply_theme_to_streamlit(theme_id)
                st.success(f"{theme['name']} theme applied! The page will refresh.")
                st.rerun()
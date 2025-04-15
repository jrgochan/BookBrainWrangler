"""
Utility functions for theme management in the Book Knowledge AI application.
"""

import json
import os
import re
import streamlit as st
from typing import Dict, Any, List, Tuple, Optional
import colorsys

# Import theme definitions from components
from components.theme_selector import THEMES, get_theme

def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex color code."""
    return f"#{r:02x}{g:02x}{b:02x}"

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color code to RGB values."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def lighten_color(hex_color: str, factor: float = 0.2) -> str:
    """Create a lighter version of the given color."""
    r, g, b = hex_to_rgb(hex_color)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return rgb_to_hex(r, g, b)

def darken_color(hex_color: str, factor: float = 0.2) -> str:
    """Create a darker version of the given color."""
    r, g, b = hex_to_rgb(hex_color)
    r = max(0, int(r * (1 - factor)))
    g = max(0, int(g * (1 - factor)))
    b = max(0, int(b * (1 - factor)))
    return rgb_to_hex(r, g, b)

def get_complementary_color(hex_color: str) -> str:
    """Get a complementary color for the given color."""
    r, g, b = hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    h = (h + 0.5) % 1.0
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return rgb_to_hex(int(r*255), int(g*255), int(b*255))

def generate_color_palette(primary_color: str, n: int = 5) -> List[str]:
    """Generate a color palette based on the primary color."""
    r, g, b = hex_to_rgb(primary_color)
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    
    palette = []
    for i in range(n):
        new_h = (h + i * (1.0/n)) % 1.0
        new_r, new_g, new_b = colorsys.hsv_to_rgb(new_h, s, v)
        palette.append(rgb_to_hex(int(new_r*255), int(new_g*255), int(new_b*255)))
    
    return palette

def update_streamlit_config_with_theme(theme_id: str) -> bool:
    """
    Update the Streamlit config.toml file with theme settings.
    
    Args:
        theme_id: ID of the theme to apply
        
    Returns:
        True if successful, False otherwise
    """
    try:
        theme = get_theme(theme_id)
        
        # Ensure .streamlit directory exists
        os.makedirs(".streamlit", exist_ok=True)
        
        # Read existing config if it exists
        config_path = ".streamlit/config.toml"
        config_content = ""
        
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config_content = f.read()
        else:
            # Create basic config with server settings
            config_content = """
[server]
headless = true
address = "0.0.0.0"
port = 5000
"""
        
        # Remove existing theme section if present
        config_content = re.sub(r'\[theme\].*?(?=\[\w+\]|\Z)', '', config_content, flags=re.DOTALL)
        
        # Add new theme section
        theme_config = f"""
[theme]
primaryColor = "{theme['primary']}"
backgroundColor = "{theme['background']}"
secondaryBackgroundColor = "{theme['secondary']}"
textColor = "{theme['text']}"
font = "{theme['font']}"
"""
        
        config_content += theme_config
        
        # Write updated config
        with open(config_path, "w") as f:
            f.write(config_content)
            
        return True
    except Exception as e:
        st.error(f"Error updating theme in config.toml: {str(e)}")
        return False

def get_theme_css(theme_id: str) -> str:
    """
    Get CSS for the specified theme.
    
    Args:
        theme_id: ID of the theme
        
    Returns:
        CSS string for the theme
    """
    theme = get_theme(theme_id)
    
    return f"""
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
    """

def export_theme_to_css(theme_id: str, output_path: str) -> bool:
    """
    Export a theme to a CSS file.
    
    Args:
        theme_id: ID of the theme to export
        output_path: Path to save the CSS file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        css = get_theme_css(theme_id)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w") as f:
            f.write(css)
            
        return True
    except Exception as e:
        st.error(f"Error exporting theme to CSS: {str(e)}")
        return False

def analyze_content_for_theme_suggestion(text: str) -> Optional[str]:
    """
    Analyze content and suggest a theme based on keywords and sentiment.
    This is a more sophisticated version of the suggest_theme_based_on_content
    function in theme_selector.py.
    
    Args:
        text: Text content to analyze
        
    Returns:
        Suggested theme ID or None
    """
    # Import here to avoid circular imports
    from components.theme_selector import suggest_theme_based_on_content
    
    # For now, just delegate to the simpler implementation
    return suggest_theme_based_on_content(text)
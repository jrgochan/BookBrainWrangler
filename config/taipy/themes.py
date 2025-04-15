"""
Theme configurations for the Taipy version of Book Knowledge AI application.
"""

from typing import Dict, Any

# Import theme data from Streamlit version
from components.theme_selector import THEMES

# Convert Streamlit themes to Taipy-compatible theme dictionaries
def get_taipy_theme(theme_id: str) -> Dict[str, Any]:
    """
    Get a Taipy-compatible theme dictionary by ID.
    
    Args:
        theme_id: ID of the theme to retrieve
        
    Returns:
        Theme dictionary formatted for Taipy
    """
    if theme_id not in THEMES:
        theme_id = "calm"  # Default
    
    theme = THEMES[theme_id]
    
    # Create Taipy theme dict
    return {
        "palette": {
            "primary": theme["primary"],
            "secondary": theme["secondary"],
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336",
            "info": theme["accent"],
            "background": theme["background"],
            "text": theme["text"],
        },
        "font": {
            "family": theme["font"],
            "size": "14px",
            "headings": {
                "family": theme["font"],
                "weight": "600",
            }
        },
        "card": {
            "background": "#FFFFFF",
            "border": f"1px solid {theme['secondary']}",
            "border_radius": "10px",
            "shadow": "0 2px 5px rgba(0,0,0,0.1)",
        },
        "button": {
            "border_radius": "5px",
            "padding": "0.5rem 1rem",
        },
        "input": {
            "border": f"1px solid {theme['secondary']}",
            "border_radius": "5px",
            "padding": "0.5rem",
        },
        "table": {
            "header_background": theme["primary"],
            "header_text": "#FFFFFF",
            "border": f"1px solid {theme['secondary']}",
            "row_odd_background": theme["background"],
            "row_even_background": "#FFFFFF",
        },
        "dialog": {
            "background": "#FFFFFF",
            "border_radius": "10px",
            "shadow": "0 4px 15px rgba(0,0,0,0.2)",
        },
        "chart": {
            "palette": [
                theme["primary"],
                theme["accent"],
                "#4CAF50",
                "#FF9800",
                "#9C27B0",
                "#3F51B5",
                "#009688",
            ]
        }
    }

# Predefined Taipy themes based on the Streamlit themes
TAIPY_THEMES = {theme_id: get_taipy_theme(theme_id) for theme_id in THEMES}

def apply_taipy_theme(gui, theme_id: str) -> None:
    """
    Apply a theme to the Taipy Gui.
    
    Args:
        gui: Taipy Gui instance
        theme_id: ID of the theme to apply
    """
    if theme_id in TAIPY_THEMES:
        gui.theme = TAIPY_THEMES[theme_id]

def get_taipy_css(theme_id: str) -> str:
    """
    Get CSS for the specified theme formatted for Taipy.
    
    Args:
        theme_id: ID of the theme
        
    Returns:
        CSS string for the theme in Taipy format
    """
    theme = get_taipy_theme(theme_id)
    
    return f"""
    :root {{
        --taipy-primary: {theme['palette']['primary']};
        --taipy-secondary: {theme['palette']['secondary']};
        --taipy-background: {theme['palette']['background']};
        --taipy-text: {theme['palette']['text']};
    }}
    
    .taipy-card {{
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }}
    
    .taipy-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }}
    
    body {{
        background-color: var(--taipy-background);
        color: var(--taipy-text);
        font-family: {theme['font']['family']};
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        color: var(--taipy-primary);
        font-family: {theme['font']['headings']['family']};
        font-weight: {theme['font']['headings']['weight']};
    }}
    
    .taipy-button {{
        background-color: var(--taipy-primary);
        color: white;
        border-radius: {theme['button']['border_radius']};
        padding: {theme['button']['padding']};
        border: none;
        cursor: pointer;
        transition: background-color 0.2s;
    }}
    
    .taipy-button:hover {{
        background-color: var(--taipy-secondary);
    }}
    """
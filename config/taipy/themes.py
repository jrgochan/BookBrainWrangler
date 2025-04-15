"""
Theme configuration for the Taipy version of Book Knowledge AI.
Provides mood-based color palettes and theme management.
"""

from typing import Dict, Any, List, Tuple
import os
import json

# Define mood-based color palettes - same structure as Streamlit version
# but with Taipy-specific implementation
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

def save_theme_preference(theme_id: str) -> None:
    """
    Save the user's theme preference to a JSON file.
    
    Args:
        theme_id: ID of the theme to save
    """
    preferences = {'theme': theme_id}
    
    # Create config directory if it doesn't exist
    os.makedirs('config/user', exist_ok=True)
    
    # Save preferences to JSON file
    with open('config/user/preferences.json', 'w') as f:
        json.dump(preferences, f)

def load_theme_preference() -> str:
    """
    Load the user's theme preference from a JSON file.
    
    Returns:
        Theme ID from saved preferences, or 'calm' if not found
    """
    try:
        with open('config/user/preferences.json', 'r') as f:
            preferences = json.load(f)
            return preferences.get('theme', 'calm')
    except (FileNotFoundError, json.JSONDecodeError):
        return 'calm'

def get_css_for_theme(theme_id: str) -> str:
    """
    Generate CSS for a theme.
    
    Args:
        theme_id: ID of the theme
        
    Returns:
        CSS code for the theme
    """
    theme = get_theme(theme_id)
    
    return f"""
    /* Theme: {theme["name"]} */
    :root {{
        --primary: {theme["primary"]};
        --secondary: {theme["secondary"]};
        --background: {theme["background"]};
        --text: {theme["text"]};
        --card-bg: {theme["card_bg"]};
        --sidebar-bg: {theme["sidebar_bg"]};
        --success: {theme["success"]};
        --error: {theme["error"]};
        --warning: {theme["warning"]};
        --info: {theme["info"]};
        --font: {theme["font"]};
    }}
    
    /* Base styles */
    body {{
        background-color: var(--background);
        color: var(--text);
        font-family: var(--font);
    }}
    
    /* Taipy-specific styles */
    .taipy-part {{
        background-color: var(--card-bg);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    
    /* Sidebar */
    .sidebar {{
        background-color: var(--sidebar-bg);
        color: var(--text);
        padding: 1rem 0.5rem;
    }}
    
    /* Navigation */
    .nav-button {{
        padding: 0.5rem 1rem;
        margin-bottom: 0.5rem;
        border-radius: 4px;
        background-color: transparent;
        color: var(--text);
        transition: all 0.3s ease;
        text-decoration: none;
        display: block;
    }}
    
    .nav-button:hover {{
        background-color: var(--primary);
        color: white;
    }}
    
    .nav-button-active {{
        background-color: var(--primary);
        color: white;
    }}
    
    /* Buttons */
    button {{
        background-color: var(--primary);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    
    button:hover {{
        background-color: var(--secondary);
        transform: translateY(-2px);
    }}
    
    /* Theme cards */
    .theme-card {{
        border: 2px solid transparent;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        cursor: pointer;
    }}
    
    .theme-card:hover {{
        border-color: var(--primary);
        transform: translateY(-5px);
    }}
    
    .theme-card.selected {{
        border-color: var(--primary);
        background-color: rgba({int(theme["primary"][1:3], 16)}, 
                                {int(theme["primary"][3:5], 16)}, 
                                {int(theme["primary"][5:7], 16)}, 0.1);
    }}
    
    /* Status messages */
    .status-success {{
        background-color: var(--success);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        margin-bottom: 1rem;
    }}
    
    .status-error {{
        background-color: var(--error);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        margin-bottom: 1rem;
    }}
    
    .status-warning {{
        background-color: var(--warning);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        margin-bottom: 1rem;
    }}
    
    .status-info {{
        background-color: var(--info);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        margin-bottom: 1rem;
    }}
    """

def generate_theme_selector_template() -> str:
    """
    Generate the HTML template for the theme selector component.
    
    Returns:
        HTML template code for the theme selector
    """
    template = """
    <h2>Application Theme</h2>
    <div style="display: flex; flex-wrap: wrap; gap: 1rem;">
    """
    
    for theme_id, theme in THEMES.items():
        template += f"""
        <div class="theme-card" id="theme-card-{theme_id}">
            <h4>{theme["name"]}</h4>
            <div style="width:100%; height:20px; background-color:{theme['primary']}; 
                        margin-bottom:5px; border-radius:4px;"></div>
            <div style="width:100%; height:20px; background-color:{theme['secondary']}; 
                        margin-bottom:10px; border-radius:4px;"></div>
            <p style="font-size:12px;">{theme['description']}</p>
            <|{theme_id}|button|label=Select {theme["name"]}|>
        </div>
        """
    
    template += """
    </div>
    <div>
        <|theme_status|>
    </div>
    """
    
    return template

def init_theme_state(state):
    """
    Initialize the theme-related state variables.
    
    Args:
        state: The Taipy application state
    """
    # Load the saved theme preference
    state.current_theme = load_theme_preference()
    state.theme_status = ""
    
    # Update the state with theme-specific data
    update_theme_state(state, state.current_theme)
    
def update_theme_state(state, theme_id):
    """
    Update the state with theme-specific data.
    
    Args:
        state: The Taipy application state
        theme_id: ID of the theme to apply
    """
    theme = get_theme(theme_id)
    state.theme_colors = theme
    state.theme_css = get_css_for_theme(theme_id)
    state.current_theme = theme_id

def on_theme_selected(state, id, action, payload):
    """
    Handle theme selection.
    
    Args:
        state: The Taipy application state
        id: ID of the button clicked
        action: Action performed
        payload: Additional data
    """
    # The theme ID is the same as the button callback ID
    theme_id = id
    
    # Update the state with the new theme
    update_theme_state(state, theme_id)
    
    # Save the theme preference
    save_theme_preference(theme_id)
    
    # Update status message
    theme_name = get_theme(theme_id)["name"]
    state.theme_status = f"<div class='status-success'>{theme_name} theme applied successfully!</div>"
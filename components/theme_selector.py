"""
Theme selector component for Book Knowledge AI application.
Provides a user interface for selecting different mood-based themes.
"""

import streamlit as st
from typing import Dict, List, Tuple, Optional, Any
import os
import json

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

# Key for session state
THEME_KEY = "current_theme"
THEME_CONFIG_FILE = ".streamlit/config.toml"

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

def apply_theme(theme_id: str) -> None:
    """
    Apply a theme to the application by setting it in session state.
    
    Args:
        theme_id: ID of the theme to apply
    """
    # Set current theme in session state
    st.session_state[THEME_KEY] = theme_id
    
    # Get theme data
    theme = get_theme(theme_id)
    
    # Apply the theme by writing to config.toml
    update_theme_config(theme)
    
    # Store the user's preference
    save_theme_preference(theme_id)

def update_theme_config(theme: Dict[str, Any]) -> None:
    """
    Update the Streamlit theme configuration in config.toml.
    
    Args:
        theme: Theme dictionary with color and font values
    """
    # Ensure .streamlit directory exists
    os.makedirs(".streamlit", exist_ok=True)
    
    # Create or update the config.toml file
    with open(THEME_CONFIG_FILE, "w") as f:
        # Write theme section
        f.write("[theme]\n")
        f.write(f'primaryColor = "{theme["primary"]}"\n')
        f.write(f'backgroundColor = "{theme["background"]}"\n')
        f.write(f'secondaryBackgroundColor = "{theme["card_bg"]}"\n')
        f.write(f'textColor = "{theme["text"]}"\n')
        f.write(f'font = "{theme["font"]}"\n')
        
        # Write server section
        f.write("\n[server]\n")
        f.write("headless = true\n")
        f.write("address = \"0.0.0.0\"\n")
        f.write("port = 5000\n")

def save_theme_preference(theme_id: str) -> None:
    """
    Save the user's theme preference to persistent storage.
    
    Args:
        theme_id: ID of the theme to save
    """
    # Create the user preferences directory if it doesn't exist
    os.makedirs("data/user", exist_ok=True)
    
    # Write the preference to a JSON file
    with open("data/user/theme_preference.json", "w") as f:
        json.dump({"theme": theme_id}, f)

def load_theme_preference() -> str:
    """
    Load the user's theme preference from persistent storage.
    
    Returns:
        Theme ID from saved preferences, or 'calm' if not found
    """
    try:
        with open("data/user/theme_preference.json", "r") as f:
            preferences = json.load(f)
            return preferences.get("theme", "calm")
    except (FileNotFoundError, json.JSONDecodeError):
        return "calm"

def get_current_theme() -> str:
    """
    Get the current theme ID from session state or load from preferences.
    
    Returns:
        Current theme ID
    """
    if THEME_KEY not in st.session_state:
        theme_id = load_theme_preference()
        st.session_state[THEME_KEY] = theme_id
    
    return st.session_state[THEME_KEY]

def inject_custom_css() -> None:
    """
    Inject custom CSS for the current theme into the Streamlit app.
    """
    theme_id = get_current_theme()
    theme = get_theme(theme_id)
    
    # Convert theme primary to RGB format
    primary_hex = theme["primary"].lstrip('#')
    primary_rgb = f"rgb({int(primary_hex[0:2], 16)}, {int(primary_hex[2:4], 16)}, {int(primary_hex[4:6], 16)})"
    
    # Create CSS with theme variables
    custom_css = f"""
    <style>
    /* Theme variables */
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
        --primary-rgb: {primary_rgb};
    }}
    
    /* Custom styling using theme variables */
    .custom-card {{
        background-color: var(--card-bg);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    
    .custom-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
    }}
    
    .custom-button {{
        background-color: var(--primary);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
        transition: background-color 0.3s ease, transform 0.2s ease;
    }}
    
    .custom-button:hover {{
        background-color: var(--secondary);
        transform: scale(1.05);
    }}
    
    .theme-card {{
        border: 2px solid transparent;
        border-radius: 8px;
        padding: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    
    .theme-card:hover {{
        border-color: var(--primary);
        transform: translateY(-5px);
    }}
    
    .theme-card.selected {{
        border-color: var(--primary);
        background-color: rgba(var(--primary-rgb), 0.1);
    }}
    
    /* Status messages */
    .success-message {{
        background-color: var(--success);
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }}
    
    .error-message {{
        background-color: var(--error);
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }}
    
    .warning-message {{
        background-color: var(--warning);
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }}
    
    .info-message {{
        background-color: var(--info);
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }}
    </style>
    """
    
    # Inject the CSS
    st.markdown(custom_css, unsafe_allow_html=True)

def render_theme_selector() -> None:
    """
    Render the theme selector UI component.
    """
    # Get current theme
    current_theme_id = get_current_theme()
    
    # Create columns for displaying themes
    num_themes = len(THEMES)
    if num_themes <= 3:
        columns = st.columns(num_themes)
    else:
        columns = st.columns(3)
    
    # Show themes in columns
    theme_items = list(THEMES.items())
    for i, (theme_id, theme) in enumerate(theme_items):
        col_index = i % len(columns)
        
        with columns[col_index]:
            # Display theme card
            st.markdown(f"""
            <div class="theme-card {'selected' if current_theme_id == theme_id else ''}">
                <h4>{theme["name"]}</h4>
                <div style="width:100%; height:20px; background-color:{theme['primary']}; 
                            margin-bottom:5px; border-radius:4px;"></div>
                <div style="width:100%; height:20px; background-color:{theme['secondary']}; 
                            margin-bottom:10px; border-radius:4px;"></div>
                <p style="font-size:12px;">{theme["description"]}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Button to select this theme
            if st.button(f"Select {theme['name']}", key=f"theme_{theme_id}"):
                apply_theme(theme_id)
                st.success(f"{theme['name']} theme applied!")
                st.rerun()

def suggest_theme_based_on_content(text: str) -> Optional[str]:
    """
    Analyze content and suggest an appropriate theme based on mood.
    
    Args:
        text: Text content to analyze
        
    Returns:
        Suggested theme ID or None if no strong suggestion
    """
    # Simple keyword-based mood detection (placeholder for more sophisticated NLP)
    text = text.lower()
    
    # Define mood keywords
    calm_keywords = ["peace", "calm", "relax", "gentle", "quiet", "serene", "tranquil"]
    focus_keywords = ["focus", "concentrate", "study", "academic", "research", "learn"]
    energetic_keywords = ["energy", "creative", "inspire", "motivate", "action", "exciting"]
    soothing_keywords = ["soothe", "comfort", "gentle", "soft", "pleasant", "healing"]
    classic_keywords = ["classic", "traditional", "historic", "scholarly", "academic", "formal"]
    
    # Count keyword occurrences
    mood_scores = {
        "calm": sum(1 for word in calm_keywords if word in text),
        "focus": sum(1 for word in focus_keywords if word in text),
        "energetic": sum(1 for word in energetic_keywords if word in text),
        "soothing": sum(1 for word in soothing_keywords if word in text),
        "classic": sum(1 for word in classic_keywords if word in text)
    }
    
    # Find the mood with highest score
    max_score = max(mood_scores.values())
    max_mood = max(mood_scores.items(), key=lambda x: x[1])[0]
    
    # Only suggest if score is significant
    if max_score > 2:
        return max_mood
    return None
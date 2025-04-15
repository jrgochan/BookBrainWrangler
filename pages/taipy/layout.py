"""
Common layout components for Taipy UI.
"""

from taipy.gui import navigate, notify, Gui

# Define common styles for our application
styles = """
<style>
/* Base styles */
:root {
    --primary-color: #1f77b4;
    --secondary-color: #ff7f0e;
    --success-color: #2ca02c;
    --info-color: #17becf;
    --warning-color: #d62728;
    --danger-color: #e377c2;
    --light-color: #f5f5f5;
    --dark-color: #333333;
    --gray-100: #f8f9fa;
    --gray-200: #e9ecef;
    --gray-300: #dee2e6;
    --gray-400: #ced4da;
    --gray-500: #adb5bd;
    --gray-600: #6c757d;
    --gray-700: #495057;
    --gray-800: #343a40;
    --gray-900: #212529;
    --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    --border-radius: 6px;
    --card-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
}

/* Global styles */
body {
    font-family: var(--font-family);
    background-color: var(--gray-100);
    color: var(--gray-900);
}

/* Card styling */
.card {
    background-color: white;
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--card-shadow);
    transition: transform 0.2s, box-shadow 0.2s;
    height: 100%;
}

.card:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}

/* Navigation styling */
.sidebar {
    background-color: white;
    padding: 1.5rem;
    box-shadow: var(--card-shadow);
    border-radius: var(--border-radius);
}

.sidebar h1 {
    margin-bottom: 1.5rem;
    font-size: 1.5rem;
    color: var(--primary-color);
}

.nav-button {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: var(--border-radius);
    background-color: var(--gray-100);
    transition: background-color 0.2s;
}

.nav-button:hover {
    background-color: var(--gray-200);
}

.nav-button-active {
    background-color: var(--primary-color);
    color: white;
}

/* Home page */
.home-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

/* Page container */
.page-container {
    padding: 2rem;
}

/* Headers */
h1, h2, h3, h4, h5, h6 {
    margin-bottom: 1rem;
    font-weight: 600;
}

/* Buttons */
button {
    border-radius: var(--border-radius);
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
    border: none;
    background-color: var(--primary-color);
    color: white;
    cursor: pointer;
    transition: background-color 0.2s;
}

button:hover {
    background-color: #1a68a0;
}

/* Form elements */
input, select, textarea {
    border-radius: var(--border-radius);
    padding: 0.5rem;
    border: 1px solid var(--gray-300);
    font-size: 0.9rem;
}

/* Console styling */
.console {
    background-color: var(--gray-900);
    color: white;
    padding: 1rem;
    border-radius: var(--border-radius);
    font-family: monospace;
    height: 300px;
    overflow: auto;
}

.console-message {
    padding: 0.25rem 0;
    border-bottom: 1px solid var(--gray-800);
}

.console-info {
    color: #63b3ed;
}

.console-success {
    color: #68d391;
}

.console-warning {
    color: #f6e05e;
}

.console-error {
    color: #fc8181;
}
</style>
"""

# Define the sidebar navigation template
sidebar_template = """
<|part|render=True|class_name=sidebar|
# 📚 Book Knowledge AI

<|{on_navigate}|button|class_name={get_nav_class("home")}|label=Home|page=home|>
<|{on_navigate}|button|class_name={get_nav_class("book_management")}|label=Book Management|page=book_management|>
<|{on_navigate}|button|class_name={get_nav_class("knowledge_base")}|label=Knowledge Base|page=knowledge_base|>
<|{on_navigate}|button|class_name={get_nav_class("chat")}|label=Chat with AI|page=chat|>
<|{on_navigate}|button|class_name={get_nav_class("archive_search")}|label=Archive Search|page=archive_search|>
<|{on_navigate}|button|class_name={get_nav_class("settings")}|label=Settings|page=settings|>
|>
"""

# Define the main layout template
main_layout_template = """
{styles}

<|layout|columns=1 5|
{sidebar_template}

<|part|render=True|class_name=page-container|
{current_page_content}
|>
|>
"""

def get_nav_class(page):
    """
    Get the CSS class for a navigation button.
    
    Args:
        page: The page identifier
        
    Returns:
        CSS class name string
    """
    def _get_class(state):
        if state.current_page == page:
            return "nav-button nav-button-active"
        return "nav-button"
    return _get_class

def get_layout_template():
    """
    Get the main layout template.
    
    Returns:
        Complete layout template string
    """
    return main_layout_template.format(
        styles=styles,
        sidebar_template=sidebar_template,
        current_page_content="{current_page_content}"
    )
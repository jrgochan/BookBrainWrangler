"""
Home page for the Book Knowledge AI application.
"""

from taipy.gui import navigate, notify

# Define the home page template
home_page_template = """
<|container|class_name=home-container|
# 📚 Book Knowledge AI

Welcome to Book Knowledge AI, your intelligent document management system.

<|layout|columns=1 1 1|gap=30px|
<|card|
## 📄 Book Management
Upload and manage your documents.

<|Navigate to Book Management|button|on_action=on_navigate|page=book_management|>
|>

<|card|
## 🧠 Knowledge Base
Explore your knowledge base.

<|Navigate to Knowledge Base|button|on_action=on_navigate|page=knowledge_base|>
|>

<|card|
## 💬 Chat with AI
Interact with your documents using AI.

<|Navigate to Chat|button|on_action=on_navigate|page=chat|>
|>
|>

<|layout|columns=1 1|gap=30px|
<|card|
## 🔍 Archive Search
Search for books in the Internet Archive.

<|Navigate to Archive Search|button|on_action=on_navigate|page=archive_search|>
|>

<|card|
## ⚙️ Settings
Configure your application settings.

<|Navigate to Settings|button|on_action=on_navigate|page=settings|>
|>
|>
|>
"""

def get_template():
    """Get the home page template."""
    return home_page_template

def on_navigate(state, page):
    """Handle page navigation."""
    state.current_page = page
    navigate(state, page)
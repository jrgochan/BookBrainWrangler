"""
Book Knowledge AI - Main Application
A Streamlit-powered book management and knowledge extraction application 
that transforms documents into an interactive, AI-enhanced knowledge base.
"""

import os
import streamlit as st
from datetime import datetime

from utils.logger import get_logger
from document_processing import DocumentProcessor
from knowledge_base import KnowledgeBase
from components.theme_selector import get_current_theme, inject_custom_css

# Initialize logger
logger = get_logger(__name__)

# Set page config
st.set_page_config(
    page_title="Book Knowledge AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply theme's custom CSS
inject_custom_css()

# Initialize session state
def init_session_state():
    """Initialize session state variables."""
    if "initialized" not in st.session_state:
        # Initialize core components
        st.session_state.initialized = True
        st.session_state.document_processor = DocumentProcessor()
        st.session_state.knowledge_base = KnowledgeBase()
        
        # Initialize AI client
        from ai import get_default_client
        st.session_state.ai_client = get_default_client()
        st.session_state.chat_ai_client = st.session_state.ai_client  # For chat interface
        
        # Initialize navigation and UI state
        st.session_state.current_page = "home"
        st.session_state.progress = 0.0
        st.session_state.logs = []
        
        # Book management state
        st.session_state.selected_book = None
        st.session_state.selected_category = "All"
        st.session_state.search_term = ""
        
        # Knowledge base state
        st.session_state.kb_search_term = ""
        st.session_state.kb_search_results = []
        st.session_state.kb_documents = []
        
        # Chat state
        st.session_state.chat_history = []
        st.session_state.use_knowledge_base = True
        
        # Archive search state
        st.session_state.archive_search_term = ""
        st.session_state.archive_search_results = []
        
        # Initialize other session variables as needed
        if "thumbnail_cache" not in st.session_state:
            st.session_state.thumbnail_cache = {}
            
        # Initialize notification system
        from utils.notifications import NotificationManager
        st.session_state.notification_manager = NotificationManager()
        st.session_state.notifications = st.session_state.notification_manager.get_all_notifications()
        
        logger.info("Session state initialized")

def render_sidebar():
    """Render the application sidebar."""
    with st.sidebar:
        st.image("generated-icon.png", width=100)
        st.title("Book Knowledge AI")
        
        # Navigation
        st.subheader("Navigation")
        
        if st.button("📋 Home", use_container_width=True):
            st.session_state.current_page = "home"
            st.rerun()
            
        if st.button("📚 Book Management", use_container_width=True):
            st.session_state.current_page = "book_management"
            st.rerun()
            
        if st.button("🧠 Knowledge Base", use_container_width=True):
            st.session_state.current_page = "knowledge_base"
            st.rerun()
            
        if st.button("💬 Chat with AI", use_container_width=True):
            st.session_state.current_page = "chat"
            st.rerun()
            
        if st.button("🔍 Archive Search", use_container_width=True):
            st.session_state.current_page = "archive_search"
            st.rerun()
            
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.current_page = "settings"
            st.rerun()
            
        if st.button("🔔 Notifications", use_container_width=True):
            st.session_state.current_page = "notifications"
            st.rerun()
            
        # Show number of unread notifications
        from utils.notification_helpers import count_unread_notifications
        unread_count = count_unread_notifications(st.session_state.notifications)
        if unread_count > 0:
            st.sidebar.markdown(f"<span style='color: red;'>🔔 {unread_count} unread</span>", unsafe_allow_html=True)
        
        # Additional sidebar info
        st.sidebar.divider()
        st.sidebar.info("""
        **Book Knowledge AI**
        A personal knowledge management system for book collections.
        
        Upload, process, and explore your books. The AI chatbot will help you
        understand and explore your book collection.
        """)
        
        # Show current theme
        current_theme_id = get_current_theme()
        from components.theme_selector import get_theme
        theme = get_theme(current_theme_id)
        st.sidebar.markdown(f"""
        <div style="background-color:{theme['primary']}; color:white; padding:10px; border-radius:5px; margin-top:10px;">
        Current Theme: {theme['name']}
        </div>
        """, unsafe_allow_html=True)

def render_home_page():
    """Render the home page."""
    st.title("Welcome to Book Knowledge AI")
    
    # App statistics
    st.subheader("Your Library at a Glance")
    
    # Get statistics
    from book_manager.manager_helpers import count_books, count_categories
    
    total_books = count_books()
    total_categories = count_categories()
    kb_documents = len(st.session_state.knowledge_base.get_documents())
    
    # Create metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Books", total_books)
    
    with col2:
        st.metric("Categories", total_categories)
    
    with col3:
        st.metric("Knowledge Base Documents", kb_documents)
    
    # Quick actions
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="custom-card">
            <h3>📚 Add New Book</h3>
            <p>Upload and process a new book to add to your collection.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Upload Book", key="upload_book_btn"):
            st.session_state.current_page = "book_management"
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="custom-card">
            <h3>🧠 Explore Knowledge</h3>
            <p>Search and explore your knowledge base.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Explore Knowledge Base", key="explore_kb_btn"):
            st.session_state.current_page = "knowledge_base"
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class="custom-card">
            <h3>💬 Chat with AI</h3>
            <p>Ask questions about your book collection.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Start Chatting", key="start_chat_btn"):
            st.session_state.current_page = "chat"
            st.rerun()
    
    # Recent Activity
    st.subheader("Recent Activity")
    
    # Get recent books
    from book_manager.manager_helpers import get_recent_books
    recent_books = get_recent_books(limit=5)
    
    if recent_books:
        for book in recent_books:
            title = book.get("title", "Untitled")
            author = book.get("author", "Unknown")
            added_date = book.get("created_at", datetime.now().strftime("%Y-%m-%d"))
            
            st.markdown(f"""
            <div style="padding: 10px; border-bottom: 1px solid #eee;">
                <strong>{title}</strong> by {author} - Added on {added_date}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No books have been added yet. Get started by uploading your first book.")

def render_book_management_page():
    """Render the knowledge management page."""
    from pages.book_management import render as render_book_management
    render_book_management()

def render_knowledge_base_page():
    """Render the knowledge base page."""
    from pages.knowledge_base import render as render_knowledge_base
    render_knowledge_base()

def render_chat_page():
    """Render the chat page."""
    from pages.chat_with_ai import render as render_chat
    render_chat()

def render_settings_page():
    """Render the settings page."""
    from pages.settings import settings_page as render_settings
    render_settings()

def render_archive_search_page():
    """Render the Internet Archive search page."""
    from pages.archive_search import render as render_archive_search
    render_archive_search()

def render_notifications_page():
    """Render the notifications page."""
    from pages.notifications import render as render_notifications
    render_notifications()

def main():
    """Main application function."""
    # Initialize session state
    init_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Display the appropriate page based on current_page in session state
    current_page = st.session_state.current_page
    
    if current_page == "home":
        render_home_page()
    elif current_page == "book_management":
        render_book_management_page()
    elif current_page == "knowledge_base":
        render_knowledge_base_page()
    elif current_page == "chat":
        render_chat_page()
    elif current_page == "settings":
        render_settings_page()
    elif current_page == "archive_search":
        render_archive_search_page()
    elif current_page == "notifications":
        render_notifications_page()

if __name__ == "__main__":
    main()
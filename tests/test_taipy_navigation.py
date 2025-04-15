"""
Test module for the Taipy application navigation system.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import application modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TaipyNavigationTests(unittest.TestCase):
    """Tests for the Taipy application navigation system."""
    
    def setUp(self):
        """Set up the test environment."""
        # Mock the core components
        self.mock_document_processor = MagicMock()
        self.mock_knowledge_base = MagicMock()
        self.mock_book_manager = MagicMock()
        self.mock_ai_client = MagicMock()
        
        # Mock the Taipy GUI
        self.mock_gui = MagicMock()
        
        # Mock navigation system
        self.mock_navigate = MagicMock()
        
        # Patch the components
        self.patches = [
            patch("document_processing.DocumentProcessor", return_value=self.mock_document_processor),
            patch("knowledge_base.KnowledgeBase", return_value=self.mock_knowledge_base),
            patch("book_manager.BookManager", return_value=self.mock_book_manager),
            patch("ai.get_default_client", return_value=self.mock_ai_client),
            patch("taipy.gui.Gui", return_value=self.mock_gui),
            patch("taipy.gui.navigate", self.mock_navigate)
        ]
        
        for p in self.patches:
            p.start()
    
    def tearDown(self):
        """Clean up after tests."""
        for p in self.patches:
            p.stop()
    
    def test_navigation_from_home(self):
        """Test navigation from the home page to other pages."""
        from pages.taipy.home import on_navigate
        
        # Create a mock state
        state = MagicMock()
        
        # Test navigation to book management
        on_navigate(state, "book_management")
        self.assertEqual(state.current_page, "book_management")
        self.mock_navigate.assert_called_with(state, "book_management")
        
        # Test navigation to knowledge base
        on_navigate(state, "knowledge_base")
        self.assertEqual(state.current_page, "knowledge_base")
        self.mock_navigate.assert_called_with(state, "knowledge_base")
        
        # Test navigation to chat
        on_navigate(state, "chat")
        self.assertEqual(state.current_page, "chat")
        self.mock_navigate.assert_called_with(state, "chat")
        
        # Test navigation to archive search
        on_navigate(state, "archive_search")
        self.assertEqual(state.current_page, "archive_search")
        self.mock_navigate.assert_called_with(state, "archive_search")
        
        # Test navigation to settings
        on_navigate(state, "settings")
        self.assertEqual(state.current_page, "settings")
        self.mock_navigate.assert_called_with(state, "settings")
    
    def test_navigation_from_app(self):
        """Test navigation handled by the main application."""
        from taipy_app import BookKnowledgeApp
        
        # Create the app
        app = BookKnowledgeApp()
        
        # Create a mock state
        state = MagicMock()
        
        # Test navigation
        app.on_navigate(state, "book_management")
        self.assertEqual(state.current_page, "book_management")
        self.mock_navigate.assert_called_with(state, "book_management")
    
    def test_sidebar_navigation(self):
        """Test that the sidebar navigation is correctly defined."""
        from pages.taipy.layout import sidebar_template, get_nav_class
        
        # Check that the sidebar template is defined
        self.assertIsInstance(sidebar_template, str)
        
        # Create a mock state
        state = MagicMock()
        state.current_page = "home"
        
        # Check that the get_nav_class function returns the correct classes
        nav_class_func = get_nav_class("home")
        self.assertEqual(nav_class_func(state), "nav-button nav-button-active")
        
        # Change the current page
        state.current_page = "book_management"
        self.assertEqual(nav_class_func(state), "nav-button")
    
    def test_initializer_navigation(self):
        """Test that the navigation is correctly initialized."""
        from config.taipy.initializer import AppInitializer
        
        # Create a mock state
        state = MagicMock()
        
        # Mock the core components init
        with patch.object(AppInitializer, "init_core_components", return_value={
            "document_processor": self.mock_document_processor,
            "knowledge_base": self.mock_knowledge_base,
            "book_manager": self.mock_book_manager,
            "ai_client": self.mock_ai_client
        }):
            # Mock the page-specific state initialization
            with patch("pages.taipy.book_management.init_state", MagicMock()):
                with patch("pages.taipy.knowledge_base.init_state", MagicMock()):
                    with patch("pages.taipy.chat.init_state", MagicMock()):
                        with patch("pages.taipy.archive_search.init_state", MagicMock()):
                            with patch("pages.taipy.settings.init_state", MagicMock()):
                                # Initialize the state
                                AppInitializer.init_state(state)
                                
                                # Check that current_page was set
                                self.assertEqual(state.current_page, "home")


if __name__ == "__main__":
    unittest.main()
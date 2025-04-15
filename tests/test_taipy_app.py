"""
Test module for the Taipy application.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import application modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TaipyAppTests(unittest.TestCase):
    """Tests for the Taipy application."""
    
    def setUp(self):
        """Set up the test environment."""
        # Mock the core components
        self.mock_document_processor = MagicMock()
        self.mock_knowledge_base = MagicMock()
        self.mock_book_manager = MagicMock()
        self.mock_ai_client = MagicMock()
        
        # Mock the Taipy GUI
        self.mock_gui = MagicMock()
        
        # Patch the components
        self.patches = [
            patch("document_processing.DocumentProcessor", return_value=self.mock_document_processor),
            patch("knowledge_base.KnowledgeBase", return_value=self.mock_knowledge_base),
            patch("book_manager.BookManager", return_value=self.mock_book_manager),
            patch("ai.get_default_client", return_value=self.mock_ai_client),
            patch("taipy.gui.Gui", return_value=self.mock_gui)
        ]
        
        for p in self.patches:
            p.start()
    
    def tearDown(self):
        """Clean up after tests."""
        for p in self.patches:
            p.stop()
    
    def test_app_initialization(self):
        """Test application initialization."""
        from taipy_app import BookKnowledgeApp
        
        app = BookKnowledgeApp()
        
        # Check that core components were initialized
        self.assertEqual(app.document_processor, self.mock_document_processor)
        self.assertEqual(app.knowledge_base, self.mock_knowledge_base)
        self.assertEqual(app.book_manager, self.mock_book_manager)
        self.assertEqual(app.ai_client, self.mock_ai_client)
        
        # Check that the GUI was created
        self.assertEqual(app.gui, self.mock_gui)
        
        # Check that callbacks were registered
        self.assertTrue(self.mock_gui.add_callback.called)
    
    def test_page_templates(self):
        """Test that all page templates are loaded correctly."""
        from taipy_app import BookKnowledgeApp
        
        with patch("pages.taipy.home.get_template", return_value="home_template"):
            with patch("pages.taipy.book_management.get_template", return_value="book_management_template"):
                with patch("pages.taipy.knowledge_base.get_template", return_value="knowledge_base_template"):
                    with patch("pages.taipy.chat.get_template", return_value="chat_template"):
                        with patch("pages.taipy.archive_search.get_template", return_value="archive_search_template"):
                            with patch("pages.taipy.settings.get_template", return_value="settings_template"):
                                app = BookKnowledgeApp()
                                
                                # Check that all templates were loaded
                                self.assertEqual(app.page_templates["home"], "home_template")
                                self.assertEqual(app.page_templates["book_management"], "book_management_template")
                                self.assertEqual(app.page_templates["knowledge_base"], "knowledge_base_template")
                                self.assertEqual(app.page_templates["chat"], "chat_template")
                                self.assertEqual(app.page_templates["archive_search"], "archive_search_template")
                                self.assertEqual(app.page_templates["settings"], "settings_template")
    
    def test_navigation(self):
        """Test page navigation."""
        from taipy_app import BookKnowledgeApp
        
        app = BookKnowledgeApp()
        
        # Create a mock state
        state = MagicMock()
        
        # Test navigation
        app.on_navigate(state, "book_management")
        
        # Check that state was updated
        self.assertEqual(state.current_page, "book_management")
        
        # Check that navigate was called
        from taipy.gui import navigate
        navigate.assert_called_once_with(state, "book_management")
    
    def test_callbacks(self):
        """Test that callbacks are properly wired up."""
        from taipy_app import BookKnowledgeApp
        
        # Create the app
        app = BookKnowledgeApp()
        
        # Check that callbacks were registered
        expected_callbacks = [
            "on_navigate",
            "on_process_book",
            "on_search_books",
            "on_search_knowledge_base",
            "on_filter_documents",
            "on_send_message",
            "on_new_chat",
            "on_search_archive",
            "on_download_book",
            "on_download_all",
            "on_clear_logs",
            "on_save_ai_settings",
            "on_save_kb_settings",
            "on_save_doc_settings",
            "on_save_ui_settings",
            "on_save_advanced_settings",
            "on_rebuild_index",
            "on_export_kb",
            "on_reset_settings",
            "on_delete_all_data"
        ]
        
        # Check that all expected callbacks were registered
        for callback in expected_callbacks:
            self.mock_gui.add_callback.assert_any_call(callback, getattr(app, callback))


if __name__ == "__main__":
    unittest.main()
"""
Test module for the Taipy application initializer.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, mock_open

# Add parent directory to path to import application modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class InitializerTests(unittest.TestCase):
    """Tests for the Taipy application initializer."""
    
    def test_load_css(self):
        """Test loading CSS styles."""
        from config.taipy.initializer import AppInitializer
        
        # Mock the open function to return a test CSS string
        test_css = "body { color: black; }"
        with patch("builtins.open", mock_open(read_data=test_css)):
            css = AppInitializer.load_css()
            self.assertEqual(css, test_css)
        
        # Test handling of file not found
        with patch("builtins.open", side_effect=FileNotFoundError):
            css = AppInitializer.load_css()
            self.assertEqual(css, "")
    
    def test_init_core_components(self):
        """Test initialization of core components."""
        from config.taipy.initializer import AppInitializer
        
        # Mock the components
        mock_document_processor = MagicMock()
        mock_knowledge_base = MagicMock()
        mock_book_manager = MagicMock()
        mock_ai_client = MagicMock()
        
        # Patch the imports
        with patch("document_processing.DocumentProcessor", return_value=mock_document_processor):
            with patch("knowledge_base.KnowledgeBase", return_value=mock_knowledge_base):
                with patch("book_manager.BookManager", return_value=mock_book_manager):
                    with patch("ai.get_default_client", return_value=mock_ai_client):
                        components = AppInitializer.init_core_components()
                        
                        # Check that all components were initialized
                        self.assertEqual(components["document_processor"], mock_document_processor)
                        self.assertEqual(components["knowledge_base"], mock_knowledge_base)
                        self.assertEqual(components["book_manager"], mock_book_manager)
                        self.assertEqual(components["ai_client"], mock_ai_client)
        
        # Test error handling
        with patch("document_processing.DocumentProcessor", side_effect=ImportError("Test error")):
            with self.assertRaises(ImportError):
                AppInitializer.init_core_components()
    
    def test_init_state(self):
        """Test state initialization."""
        from config.taipy.initializer import AppInitializer
        
        # Mock the state initialization functions
        mock_init_book_management_state = MagicMock()
        mock_init_knowledge_base_state = MagicMock()
        mock_init_chat_state = MagicMock()
        mock_init_archive_search_state = MagicMock()
        mock_init_settings_state = MagicMock()
        
        # Mock the components
        mock_components = {
            "document_processor": MagicMock(),
            "knowledge_base": MagicMock(),
            "book_manager": MagicMock(),
            "ai_client": MagicMock()
        }
        
        # Create a mock state
        mock_state = MagicMock()
        
        # Patch the imports and init_core_components
        with patch("pages.taipy.book_management.init_state", mock_init_book_management_state):
            with patch("pages.taipy.knowledge_base.init_state", mock_init_knowledge_base_state):
                with patch("pages.taipy.chat.init_state", mock_init_chat_state):
                    with patch("pages.taipy.archive_search.init_state", mock_init_archive_search_state):
                        with patch("pages.taipy.settings.init_state", mock_init_settings_state):
                            with patch.object(AppInitializer, "init_core_components", return_value=mock_components):
                                # Initialize the state
                                AppInitializer.init_state(mock_state)
                                
                                # Check that current_page was set
                                self.assertEqual(mock_state.current_page, "home")
                                
                                # Check that components were added to state
                                self.assertEqual(mock_state.document_processor, mock_components["document_processor"])
                                self.assertEqual(mock_state.knowledge_base, mock_components["knowledge_base"])
                                self.assertEqual(mock_state.book_manager, mock_components["book_manager"])
                                self.assertEqual(mock_state.ai_client, mock_components["ai_client"])
                                
                                # Check that page-specific state initialization was called
                                mock_init_book_management_state.assert_called_once_with(mock_state)
                                mock_init_knowledge_base_state.assert_called_once_with(mock_state)
                                mock_init_chat_state.assert_called_once_with(mock_state)
                                mock_init_archive_search_state.assert_called_once_with(mock_state)
                                mock_init_settings_state.assert_called_once_with(mock_state)
    
    def test_init_data_nodes(self):
        """Test initialization of data nodes."""
        from config.taipy.initializer import AppInitializer
        
        # Mock the config object
        mock_config = MagicMock()
        mock_config.data_nodes = {
            "books_data": MagicMock(),
            "knowledge_base_data": MagicMock(),
            "chat_history": MagicMock()
        }
        
        # Patch the config import
        with patch("config.taipy.config.config", mock_config):
            data_nodes = AppInitializer.init_data_nodes()
            
            # Check that all data nodes were initialized
            self.assertEqual(data_nodes["books_data"], mock_config.data_nodes["books_data"])
            self.assertEqual(data_nodes["knowledge_base_data"], mock_config.data_nodes["knowledge_base_data"])
            self.assertEqual(data_nodes["chat_history"], mock_config.data_nodes["chat_history"])
    
    def test_init_gui_settings(self):
        """Test initialization of GUI settings."""
        from config.taipy.initializer import AppInitializer
        
        # Get the GUI settings
        gui_settings = AppInitializer.init_gui_settings()
        
        # Check that all settings were initialized
        self.assertEqual(gui_settings["title"], "Book Knowledge AI")
        self.assertEqual(gui_settings["favicon"], "📚")
        self.assertEqual(gui_settings["host"], "0.0.0.0")
        self.assertEqual(gui_settings["port"], 5000)


if __name__ == "__main__":
    unittest.main()
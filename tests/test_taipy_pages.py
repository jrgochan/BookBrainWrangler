"""
Test module for the Taipy page implementations.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import application modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TaipyPagesTests(unittest.TestCase):
    """Tests for the Taipy page implementations."""
    
    def test_home_page(self):
        """Test home page implementation."""
        from pages.taipy.home import get_template, on_navigate
        
        # Check that template is returned
        template = get_template()
        self.assertIsInstance(template, str)
        self.assertIn("Book Knowledge AI", template)
        
        # Test navigation callback
        state = MagicMock()
        with patch("taipy.gui.navigate") as mock_navigate:
            on_navigate(state, "book_management")
            self.assertEqual(state.current_page, "book_management")
            mock_navigate.assert_called_once_with(state, "book_management")
    
    def test_book_management_page(self):
        """Test book management page implementation."""
        from pages.taipy.book_management import get_template, on_process_book, on_search_books, render_book_list, init_state
        
        # Check that template is returned
        template = get_template()
        self.assertIsInstance(template, str)
        self.assertIn("Book Management", template)
        
        # Test init_state
        state = MagicMock()
        init_state(state)
        self.assertEqual(state.file_path, None)
        self.assertEqual(state.title, "")
        self.assertEqual(state.author, "")
        self.assertEqual(state.categories, "")
        self.assertEqual(state.search_query, "")
        self.assertEqual(state.books, [])
        
        # Test process_book with missing fields
        state.file_path = None
        state.title = ""
        with patch("taipy.gui.notify") as mock_notify:
            on_process_book(state)
            mock_notify.assert_called_once_with(state, "Please select a file to upload", "error")
        
        # Test search_books
        state.search_query = "test"
        on_search_books(state)
        self.assertIsInstance(state.books, list)
        
        # Test render_book_list
        books = [
            {"id": 1, "title": "Book 1", "author": "Author 1", "categories": ["Fiction"]},
            {"id": 2, "title": "Book 2", "author": "Author 2", "categories": ["Non-fiction"]}
        ]
        html = render_book_list(books)
        self.assertIsInstance(html, str)
        self.assertIn("Book 1", html)
        self.assertIn("Book 2", html)
        self.assertIn("Author 1", html)
        self.assertIn("Author 2", html)
    
    def test_knowledge_base_page(self):
        """Test knowledge base page implementation."""
        from pages.taipy.knowledge_base import get_template, on_search_knowledge_base, on_filter_documents, render_search_results, render_document_list, init_state
        
        # Check that template is returned
        template = get_template()
        self.assertIsInstance(template, str)
        self.assertIn("Knowledge Base", template)
        
        # Test init_state
        state = MagicMock()
        init_state(state)
        self.assertEqual(state.search_query, "")
        self.assertEqual(state.search_results, [])
        self.assertEqual(state.document_filter, "All")
        self.assertIsInstance(state.document_categories, list)
        
        # Test search with empty query
        state.search_query = ""
        with patch("taipy.gui.notify") as mock_notify:
            on_search_knowledge_base(state)
            mock_notify.assert_called_once_with(state, "Please enter a search query", "warning")
        
        # Test search with valid query
        state.search_query = "test"
        on_search_knowledge_base(state)
        self.assertIsInstance(state.search_results, list)
        
        # Test filter_documents
        state.document_filter = "Fiction"
        on_filter_documents(state)
        self.assertIsInstance(state.documents, list)
        
        # Test render_search_results
        results = [
            {
                "text": "Sample text 1",
                "metadata": {"title": "Doc 1", "author": "Author 1", "score": 0.9}
            },
            {
                "text": "Sample text 2",
                "metadata": {"title": "Doc 2", "author": "Author 2", "score": 0.8}
            }
        ]
        html = render_search_results(results)
        self.assertIsInstance(html, str)
        self.assertIn("Doc 1", html)
        self.assertIn("Doc 2", html)
        
        # Test render_document_list
        documents = [
            {
                "id": "doc1",
                "title": "Document 1",
                "author": "Author 1",
                "categories": ["Fiction"],
                "chunk_count": 10,
                "word_count": 5000
            },
            {
                "id": "doc2",
                "title": "Document 2",
                "author": "Author 2",
                "categories": ["Non-fiction"],
                "chunk_count": 15,
                "word_count": 7500
            }
        ]
        html = render_document_list(documents)
        self.assertIsInstance(html, str)
        self.assertIn("Document 1", html)
        self.assertIn("Document 2", html)
    
    def test_chat_page(self):
        """Test chat page implementation."""
        from pages.taipy.chat import get_template, on_send_message, on_new_chat, render_chat_messages, render_referenced_documents, init_state
        
        # Check that template is returned
        template = get_template()
        self.assertIsInstance(template, str)
        self.assertIn("Chat with AI", template)
        
        # Test init_state
        state = MagicMock()
        init_state(state)
        self.assertEqual(state.chat_messages, [])
        self.assertEqual(state.user_message, "")
        self.assertEqual(state.use_knowledge_base, True)
        self.assertEqual(state.referenced_documents, [])
        
        # Test send_message with empty message
        state.user_message = ""
        on_send_message(state)
        self.assertEqual(state.chat_messages, [])
        
        # Test send_message with valid message
        state.user_message = "Hello, AI!"
        state.chat_messages = []
        with patch("time.sleep"):  # Mock sleep to speed up test
            on_send_message(state)
            self.assertEqual(len(state.chat_messages), 2)  # User message + AI response
            self.assertEqual(state.chat_messages[0]["role"], "user")
            self.assertEqual(state.chat_messages[0]["content"], "Hello, AI!")
            self.assertEqual(state.chat_messages[1]["role"], "assistant")
        
        # Test new_chat
        state.chat_messages = ["message1", "message2"]
        with patch("taipy.gui.notify") as mock_notify:
            on_new_chat(state)
            self.assertEqual(state.chat_messages, [])
            mock_notify.assert_called_once_with(state, "Started a new chat session", "success")
        
        # Test render_chat_messages
        messages = [
            {"role": "user", "content": "User message", "timestamp": "12:00"},
            {"role": "assistant", "content": "AI response", "timestamp": "12:01"}
        ]
        html = render_chat_messages(messages)
        self.assertIsInstance(html, str)
        self.assertIn("User message", html)
        self.assertIn("AI response", html)
        
        # Test render_referenced_documents
        documents = [
            {"title": "Doc 1", "author": "Author 1", "relevance": 0.9},
            {"title": "Doc 2", "author": "Author 2", "relevance": 0.8}
        ]
        html = render_referenced_documents(documents)
        self.assertIsInstance(html, str)
        self.assertIn("Doc 1", html)
        self.assertIn("Doc 2", html)
    
    def test_archive_search_page(self):
        """Test archive search page implementation."""
        from pages.taipy.archive_search import get_template, on_search_archive, on_download_book, on_download_all, on_clear_logs, add_log, render_book_grid, render_logs, init_state
        
        # Check that template is returned
        template = get_template()
        self.assertIsInstance(template, str)
        self.assertIn("Internet Archive Book Search", template)
        
        # Test init_state
        state = MagicMock()
        init_state(state)
        self.assertEqual(state.search_query, "")
        self.assertEqual(state.max_results, 24)
        self.assertEqual(state.media_type, "texts")
        self.assertEqual(state.search_results, [])
        self.assertEqual(state.processing_logs, [])
        
        # Test search with empty query
        state.search_query = ""
        with patch("taipy.gui.notify") as mock_notify:
            on_search_archive(state)
            mock_notify.assert_called_once_with(state, "Please enter a search query", "warning")
        
        # Test search with valid query
        state.search_query = "python programming"
        with patch("taipy.gui.notify") as mock_notify:
            with patch("time.sleep"):  # Mock sleep to speed up test
                on_search_archive(state)
                self.assertTrue(state.has_results)
                self.assertIsInstance(state.search_results, list)
                self.assertIsInstance(state.book_grid_content, str)
                mock_notify.assert_called_once_with(state, f"Searching Internet Archive for 'python programming'...", "info")
        
        # Test download_book with invalid book_id
        with patch("taipy.gui.notify") as mock_notify:
            on_download_book(state, "invalid_id")
            mock_notify.assert_called_once_with(state, "Book not found", "error")
        
        # Test download_all with no results
        state.search_results = []
        with patch("taipy.gui.notify") as mock_notify:
            on_download_all(state)
            mock_notify.assert_called_once_with(state, "No books to download", "warning")
        
        # Test clear_logs
        state.processing_logs = ["log1", "log2"]
        with patch("taipy.gui.notify") as mock_notify:
            on_clear_logs(state)
            self.assertEqual(state.processing_logs, [])
            self.assertEqual(state.processing_logs_content, "<p>No logs yet.</p>")
            self.assertEqual(state.has_logs, False)
            mock_notify.assert_called_once_with(state, "Logs cleared", "info")
        
        # Test add_log
        state.processing_logs = []
        add_log(state, "Test message", "INFO")
        self.assertEqual(len(state.processing_logs), 1)
        self.assertEqual(state.processing_logs[0]["message"], "Test message")
        self.assertEqual(state.processing_logs[0]["level"], "INFO")
        self.assertEqual(state.has_logs, True)
        
        # Test render_book_grid
        books = [
            {
                "identifier": "book1",
                "title": "Book 1",
                "author": "Author 1",
                "date": "2020",
                "downloads": 1000,
                "cover_url": "url1"
            },
            {
                "identifier": "book2",
                "title": "Book 2",
                "author": "Author 2",
                "date": "2021",
                "downloads": 500,
                "cover_url": "url2"
            }
        ]
        html = render_book_grid(books)
        self.assertIsInstance(html, str)
        self.assertIn("Book 1", html)
        self.assertIn("Book 2", html)
        self.assertIn("Author 1", html)
        self.assertIn("Author 2", html)
        
        # Test render_logs
        logs = [
            {"timestamp": "12:00", "level": "INFO", "message": "Info message"},
            {"timestamp": "12:01", "level": "ERROR", "message": "Error message"}
        ]
        html = render_logs(logs)
        self.assertIsInstance(html, str)
        self.assertIn("Info message", html)
        self.assertIn("Error message", html)
    
    def test_settings_page(self):
        """Test settings page implementation."""
        from pages.taipy.settings import get_template, on_save_ai_settings, on_save_kb_settings, on_save_doc_settings, on_save_ui_settings, on_save_advanced_settings, on_rebuild_index, on_export_kb, on_clear_logs, on_reset_settings, on_delete_all_data, init_state
        
        # Check that template is returned
        template = get_template()
        self.assertIsInstance(template, str)
        self.assertIn("Settings", template)
        
        # Test init_state
        state = MagicMock()
        init_state(state)
        self.assertEqual(state.ai_provider, "OpenAI")
        self.assertEqual(state.vector_store_type, "FAISS")
        self.assertEqual(state.enable_ocr, True)
        self.assertEqual(state.ui_theme, "Light")
        self.assertEqual(state.log_level, "INFO")
        
        # Test save_ai_settings
        with patch("taipy.gui.notify") as mock_notify:
            on_save_ai_settings(state)
            mock_notify.assert_called_once_with(state, "AI settings saved successfully", "success")
        
        # Test save_kb_settings
        with patch("taipy.gui.notify") as mock_notify:
            on_save_kb_settings(state)
            mock_notify.assert_called_once_with(state, "Knowledge Base settings saved successfully", "success")
        
        # Test save_doc_settings
        with patch("taipy.gui.notify") as mock_notify:
            on_save_doc_settings(state)
            mock_notify.assert_called_once_with(state, "Document processing settings saved successfully", "success")
        
        # Test save_ui_settings
        with patch("taipy.gui.notify") as mock_notify:
            on_save_ui_settings(state)
            mock_notify.assert_called_once_with(state, "UI settings saved successfully", "success")
        
        # Test save_advanced_settings
        with patch("taipy.gui.notify") as mock_notify:
            on_save_advanced_settings(state)
            mock_notify.assert_called_once_with(state, "Advanced settings saved successfully", "success")
        
        # Test rebuild_index
        with patch("taipy.gui.notify") as mock_notify:
            with patch("time.sleep"):  # Mock sleep to speed up test
                on_rebuild_index(state)
                mock_notify.assert_any_call(state, "Knowledge base index is being rebuilt...", "info")
                mock_notify.assert_any_call(state, "Knowledge base index rebuilt successfully", "success")
        
        # Test export_kb
        with patch("taipy.gui.notify") as mock_notify:
            with patch("time.sleep"):  # Mock sleep to speed up test
                on_export_kb(state)
                mock_notify.assert_any_call(state, "Knowledge base is being exported...", "info")
                mock_notify.assert_any_call(state, "Knowledge base exported successfully to exports/kb_export.zip", "success")
        
        # Test clear_logs
        with patch("taipy.gui.notify") as mock_notify:
            on_clear_logs(state)
            mock_notify.assert_called_once_with(state, "All logs have been cleared", "success")
        
        # Test reset_settings
        with patch("taipy.gui.notify") as mock_notify:
            # Setup init_state to be mocked since it will be called by reset
            with patch("pages.taipy.settings.init_state") as mock_init_state:
                on_reset_settings(state)
                mock_init_state.assert_called_once_with(state)
                mock_notify.assert_called_once_with(state, "All settings have been reset to defaults", "success")
        
        # Test delete_all_data
        with patch("taipy.gui.notify") as mock_notify:
            on_delete_all_data(state)
            mock_notify.assert_called_once()


if __name__ == "__main__":
    unittest.main()
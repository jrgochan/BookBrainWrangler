"""
Integration tests for the Taipy application.
"""

import os
import sys
import time
import unittest
import multiprocessing
import requests
from unittest.mock import MagicMock, patch

# Add parent directory to path to import application modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TaipyIntegrationTests(unittest.TestCase):
    """Integration tests for the Taipy application."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test class by starting the application in a separate process."""
        # Start the Taipy application in a separate process
        cls.app_process = multiprocessing.Process(target=cls._run_app)
        cls.app_process.daemon = True
        cls.app_process.start()
        
        # Wait for the application to start
        cls._wait_for_app_to_start()
    
    @classmethod
    def tearDownClass(cls):
        """Tear down the test class by stopping the application process."""
        # Stop the application process
        if cls.app_process.is_alive():
            cls.app_process.terminate()
            cls.app_process.join(timeout=5)
    
    @staticmethod
    def _run_app():
        """Run the Taipy application."""
        try:
            # Import and run the application with minimal components
            from taipy_app import BookKnowledgeApp
            
            # Mock core components
            with patch("document_processing.DocumentProcessor", return_value=MagicMock()):
                with patch("knowledge_base.KnowledgeBase", return_value=MagicMock()):
                    with patch("book_manager.BookManager", return_value=MagicMock()):
                        with patch("ai.get_default_client", return_value=MagicMock()):
                            # Create and run the application
                            app = BookKnowledgeApp()
                            app.run()
        except Exception as e:
            print(f"Error starting application: {e}")
            sys.exit(1)
    
    @classmethod
    def _wait_for_app_to_start(cls):
        """Wait for the application to start."""
        max_attempts = 30
        attempts = 0
        
        while attempts < max_attempts:
            try:
                # Try to connect to the application
                response = requests.get("http://localhost:5000/")
                if response.status_code == 200:
                    # Application is running
                    break
            except requests.exceptions.ConnectionError:
                # Application is not yet running
                pass
            
            # Wait before trying again
            time.sleep(1)
            attempts += 1
        
        if attempts == max_attempts:
            raise TimeoutError("Timed out waiting for application to start")
    
    def test_home_page(self):
        """Test that the home page loads correctly."""
        response = requests.get("http://localhost:5000/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Book Knowledge AI", response.text)
    
    def test_book_management_page(self):
        """Test that the book management page loads correctly."""
        response = requests.get("http://localhost:5000/book_management")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Book Management", response.text)
    
    def test_knowledge_base_page(self):
        """Test that the knowledge base page loads correctly."""
        response = requests.get("http://localhost:5000/knowledge_base")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Knowledge Base", response.text)
    
    def test_chat_page(self):
        """Test that the chat page loads correctly."""
        response = requests.get("http://localhost:5000/chat")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Chat with AI", response.text)
    
    def test_archive_search_page(self):
        """Test that the archive search page loads correctly."""
        response = requests.get("http://localhost:5000/archive_search")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Internet Archive Book Search", response.text)
    
    def test_settings_page(self):
        """Test that the settings page loads correctly."""
        response = requests.get("http://localhost:5000/settings")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings", response.text)


if __name__ == "__main__":
    unittest.main()
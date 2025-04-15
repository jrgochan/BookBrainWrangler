#!/usr/bin/env python3
"""
Run script for the Taipy version of the Book Knowledge AI application.
"""

import os
import sys
from config.taipy.initializer import AppInitializer
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

def main():
    """Run the Taipy application."""
    try:
        logger.info("Starting Book Knowledge AI with Taipy...")
        
        # Load the configuration
        from config.taipy.config import config
        
        # Import the main application
        from taipy_app import BookKnowledgeApp
        
        # Create and run the application
        app = BookKnowledgeApp()
        app.run()
        
    except ImportError as e:
        logger.error(f"Failed to import required modules: {str(e)}")
        print(f"Error: {str(e)}")
        print("Make sure Taipy is installed. Run: pip install taipy taipy-gui")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
# Book Knowledge AI Architecture

This document outlines the architecture and organization of the Book Knowledge AI codebase.

## Core Structure

```
book_knowledge_ai/
├── app.py                     # Main application entry point
├── core/                      # Core application modules
│   ├── __init__.py
│   ├── config.py              # Centralized configuration
│   ├── exceptions.py          # Custom exceptions
│   └── constants.py           # Application-wide constants
├── database/                  # Database layer
│   ├── __init__.py
│   ├── connection.py          # Database connection management
│   └── utils.py               # Database utilities
├── document_processing/       # Document processing functionality
│   ├── __init__.py
│   ├── processor.py           # Main document processor
│   ├── formats/               # Format-specific processors
│   │   ├── __init__.py
│   │   ├── pdf.py
│   │   └── docx.py
│   ├── metadata.py            # Metadata extraction
│   └── ocr.py                 # OCR functionality
├── knowledge_base/            # Knowledge base functionality
│   ├── __init__.py
│   ├── vector_store.py        # Vector storage implementation
│   ├── search.py              # Search functionality
│   ├── analytics.py           # Analytics and insights
│   ├── chunking.py            # Text chunking for embedding
│   ├── embedding.py           # Text embedding
│   └── utils.py               # Knowledge base utilities
├── ai/                        # AI integration
│   ├── __init__.py
│   ├── client.py              # Base AI client
│   ├── ollama/                # Ollama-specific implementation
│   │   ├── __init__.py
│   │   ├── client.py
│   │   └── models.py
│   └── utils.py               # AI utilities
├── ui/                        # UI components
│   ├── __init__.py
│   ├── components/            # Reusable UI components
│   │   ├── __init__.py
│   │   ├── book_list.py
│   │   ├── chat_interface.py
│   │   └── word_cloud.py
│   ├── pages/                 # Application pages
│   │   ├── __init__.py
│   │   ├── book_management.py
│   │   ├── chat_with_ai.py
│   │   ├── knowledge_base.py
│   │   └── settings.py
│   └── helpers.py             # UI helper functions
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── file_helpers.py        # File operations
│   ├── text_processing.py     # Text processing utilities
│   ├── image_helpers.py       # Image handling
│   ├── export_helpers.py      # Export functionality
│   └── logger.py              # Logging utilities
├── data/                      # Data storage
│   ├── exports/               # Exported data
│   ├── knowledge_base/        # Knowledge base data storage
│   └── temp/                  # Temporary files
└── scripts/                   # Utility scripts
    ├── setup.sh
    └── install_dependencies.sh
```

## Module Responsibilities

### Core
The `core` module contains essential application-level components including configuration, constants, and exception definitions. This centralizes the application's foundation.

### Database
The `database` module handles all database interactions, including connection management and SQL utilities. This isolates data persistence from business logic.

### Document Processing
The `document_processing` module is responsible for extracting and processing content from documents. It contains:

- A main `processor.py` module that provides a unified interface
- Format-specific handlers in the `formats/` directory
- OCR and metadata extraction utilities

### Knowledge Base
The `knowledge_base` module manages the vector database and provides search functionality. It includes:

- Vector store implementation
- Search algorithms
- Text chunking and embedding
- Analytics and utilities

### AI
The `ai` module handles interactions with AI models. It includes:

- A base `AIClient` class that defines the interface
- Provider-specific implementations in subdirectories
- Utility functions for AI operations

### UI
The `ui` module contains all user interface components:

- Reusable UI components in `components/`
- Application pages in `pages/`
- UI helper functions

### Utils
The `utils` module provides various utility functions used throughout the codebase, organized by functionality.

## Development Guidelines

1. **Follow the Module Structure**: Place new code in the appropriate module based on its functionality.
2. **Maintain Clean APIs**: Each module should expose a clean API through its `__init__.py` file.
3. **Handle Errors Consistently**: Use the custom exceptions defined in `core.exceptions`.
4. **Document Your Code**: Add docstrings to all functions, classes, and modules.
5. **Use Logging**: Log important events and errors using the logger from `utils.logger`.

## Future Enhancements

1. **Add Tests**: Create unit and integration tests for each module.
2. **Improve Documentation**: Add more detailed documentation for each module.
3. **Add Type Hints**: Add type hints to all functions for better IDE support.
4. **Add Continuous Integration**: Set up CI/CD for automated testing and deployment.
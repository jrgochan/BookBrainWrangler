# Book Knowledge AI - AI-Powered Book Management System

## Project Overview

Book Knowledge AI is a Streamlit-based application that transforms printed books and documents into an interactive, AI-enhanced knowledge base. The application allows users to upload books (PDFs or DOCX files), extract their content using OCR and text processing techniques, index the knowledge, and interact with it through an AI chatbot powered by Ollama.

This application is particularly useful for researchers, students, and knowledge workers who want to efficiently manage their digital library and extract insights from their collection of books and documents.

## Core Features

- **Document Management**: Upload, organize, categorize, and search through your books and documents.
- **Advanced OCR Processing**: Extract text from scanned PDFs with OCR capabilities powered by Tesseract.
- **Knowledge Base Building**: Convert your documents into a searchable knowledge base using vector embeddings.
- **AI-Powered Chat**: Ask questions about your books and get intelligent responses using a local LLM.
- **Knowledge Base Explorer**: Analyze and understand how information is retrieved from your books.
- **Word Cloud Generation**: Visualize the key terms and concepts from your documents.
- **Settings Management**: Configure OCR and AI model settings to your preferences.

## Technical Architecture

Book Knowledge AI follows a modular architecture with clearly separated components:

### Frontend

- **Streamlit**: Provides the web interface and interactive elements
- **Pages System**: Separate modules for different functionality areas
- **Component System**: Reusable UI components for consistency

### Backend

- **Document Processing**: OCR and text extraction via Tesseract and PyPDF2
- **Database Layer**: SQLite for storing book metadata and content
- **Knowledge Base**: Vector database for semantic search (currently simulated)
- **AI Integration**: Ollama client for local LLM interaction

### Data Flow

1. User uploads documents through the Streamlit interface
2. Documents are processed to extract text and metadata
3. Extracted content is stored in the database
4. Knowledge is indexed in the vector store when enabled
5. AI queries use the indexed knowledge to provide context-aware responses

## Key Components

### Core Modules

- **app.py**: Main application entry point that initializes components and routes to pages
- **book_manager.py**: Handles book database operations (CRUD) and metadata management
- **document_processor.py**: Processes documents, extracts text (via direct and OCR methods)
- **knowledge_base.py**: Manages the vector store and knowledge retrieval
- **ollama_client.py**: Interface to the Ollama AI system for generating responses

### Pages

- **book_management.py**: Interface for uploading and managing books
- **knowledge_base.py**: Controls which books are included in the knowledge base
- **chat_with_ai.py**: Chat interface for interacting with the AI about book content
- **knowledge_base_explorer.py**: Tools to explore how the knowledge base retrieves information
- **word_cloud_generator.py**: Creates word clouds to visualize document content
- **settings.py**: Configuration options for the application

### Utilities

- **file_helpers.py**: Functions for file operations
- **text_processing.py**: Text analysis and processing utilities
- **ui_helpers.py**: Shared UI components and functions

## Main Features Explained

### Document Management

The application provides a comprehensive system for managing your document library:

- **Upload Interface**: Clean, user-friendly upload form with automatic metadata extraction
- **Automatic Metadata Detection**: Attempts to identify title, author, and categories
- **Library View**: Searchable, filterable list of all your documents
- **CRUD Operations**: Complete Create, Read, Update, Delete functionalities

### OCR Processing

OCR (Optical Character Recognition) is a key feature for extracting text from scanned books:

- **Hybrid Extraction**: Tries direct PDF text extraction first, falls back to OCR when needed
- **Progress Visualization**: Shows each page as it's processed with extracted text
- **Confidence Metrics**: Reports OCR quality and flags low-confidence pages
- **Configuration Options**: Adjustable settings for OCR behavior and display

### Knowledge Base System

The knowledge base turns static documents into searchable, retrievable information:

- **Book Selection**: Choose which books to include in your knowledge base
- **Vectorization**: Processes document text into machine-understandable vectors
- **Retrieval System**: Finds the most relevant passages from your books based on queries
- **Context Building**: Assembles relevant information to provide to the AI model

### AI Chat Interface

The AI chat interface allows natural language interaction with your document knowledge:

- **Contextual Responses**: AI answers use information from your books
- **Conversation History**: Maintains the flow of the conversation
- **Export Capability**: Save conversations for future reference
- **Direct/Auto Mode**: Toggle between using book knowledge or just the AI's knowledge

## Setup and Installation

Book Knowledge AI supports multiple installation methods for different environments:

### Prerequisites

- Python 3.11+
- Tesseract OCR
- Ollama (for the AI models)
- Poppler (for PDF processing)
- Java JDK (for specific document processing features)

### Standard Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the environment
4. Install dependencies: `pip install -r requirements.txt`
5. Install Tesseract and ensure it's in your PATH
6. Setup Ollama and download a model (like llama2)
7. Run the application: `streamlit run app.py`

### Docker Installation

For containerized deployment, the application includes Docker support:

1. Ensure Docker and Docker Compose are installed
2. Run `./scripts/docker-start.sh` to build and start containers for:
   - The Streamlit application
   - Ollama service
   - Required model downloads

### WSL2 (Windows Subsystem for Linux) Setup

Special scripts are provided for WSL2 users to handle specific dependencies:

1. Follow the instructions in `scripts/WINDOWS_SETUP_INSTRUCTIONS.md`
2. Use the specialized setup script: `./scripts/wsl-setup.sh`
3. For jnius issues: `./scripts/fix-jnius-install.sh`

## Technical Details

### Database Schema

Book Knowledge AI uses SQLite with the following tables:

- **books**: Stores book metadata (title, author, file path)
- **categories**: Stores category names
- **book_categories**: Junction table for book-category relationships
- **book_contents**: Stores the extracted text content
- **indexed_books**: Tracks which books are included in the knowledge base

### OCR Pipeline

The OCR process works as follows:

1. For each page in a PDF document:
   a. Try direct text extraction with PyPDF2
   b. If insufficient text is found, convert the page to an image
   c. Use Tesseract OCR to extract text from the image
   d. Record confidence metrics and extracted text
   e. Optionally store page images for display

### Knowledge Base Implementation

The current knowledge base implementation:

- Uses a placeholder for future vector store integration
- Simulates the retrieval of relevant context based on queries
- Could be extended with a real vector database like ChromaDB
- Maintains a tracking system for which books are included

### AI Integration

The Ollama integration:

- Connects to a local Ollama server for AI processing
- Supports multiple models
- Provides both standard text generation and chat functions
- Includes context from the knowledge base in queries

## Troubleshooting

### Common Issues

1. **OCR Processing Errors**
   - Ensure Tesseract is properly installed and in your PATH
   - The application now explicitly sets the Tesseract path to `C:\Program Files\Tesseract-OCR\tesseract.exe` on Windows
   - For other platforms, you may need to modify this path in document_processor.py

2. **Ollama Connection Issues**
   - Verify Ollama service is running with `ollama serve`
   - Check that your chosen model is downloaded with `ollama list`
   - Ensure the correct server URL is set in settings

3. **jnius Installation Problems**
   - Follow the specialized instructions for your platform
   - Ensure Java JDK is correctly installed
   - Set the JAVA_HOME environment variable properly

4. **Database Errors**
   - Check file permissions in the application directory
   - Ensure SQLite is working correctly

5. **Memory Issues with Large Documents**
   - For very large documents, increase available memory
   - Consider processing documents in smaller batches

## Future Enhancements

Potential improvements for future development:

1. **Real Vector Database Integration**
   - Implement actual vector storage using ChromaDB or similar
   - Add vector search optimizations for large libraries

2. **Enhanced OCR Capabilities**
   - Add support for more languages
   - Implement layout analysis for tables and figures
   - Add OCR correction and training

3. **Advanced AI Features**
   - Support for more models and providers
   - Document summarization capabilities
   - Citation and source tracking

4. **Collaboration Features**
   - Multi-user support
   - Shared libraries and knowledge bases
   - Annotation and commenting

5. **Import/Export Capabilities**
   - Export/import knowledge bases
   - Standardized document exchange formats
   - Integration with other knowledge management systems

## Development Notes

### Code Structure Best Practices

When extending the application, follow these patterns:

1. Keep the modular architecture with clear separation of concerns
2. Add new pages in the pages/ directory and register them in app.py
3. Extend the database schema using similar patterns to the existing tables
4. Add utility functions to the appropriate utils/ modules
5. Document all new functions and classes thoroughly

### Testing Strategy

For testing new features:

1. Create unit tests for core functionality
2. Test OCR with a variety of document types and qualities
3. Verify AI interactions with different models and queries
4. Test the UI on different screen sizes and browsers
5. Validate database operations with large datasets

## Conclusion

Book Knowledge AI represents a powerful tool for knowledge workers who want to extract more value from their document collections. By combining OCR, databases, vector search, and AI, it creates a seamless system for not just storing documents, but truly interacting with their knowledge and content.

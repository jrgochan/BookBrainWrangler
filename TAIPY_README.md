# Book Knowledge AI - Taipy Version

Welcome to the Taipy version of Book Knowledge AI, a powerful application for managing book collections and creating an AI-powered knowledge base from your reading materials.

## Overview

This Taipy implementation provides all the same core functionality as the original Streamlit version, with enhanced UI, better state management, and improved performance.

## Features

- **Book Management**: Upload, categorize, search, edit, and delete books
- **Knowledge Base**: Select which books to include in your AI's knowledge
- **AI Chat**: Interact with an AI assistant that leverages information from your book collection
- **PDF Processing**: Extract text from PDFs with OCR capabilities for scanned documents
- **Enhanced UI**: Modern, responsive interface with improved user experience
- **Better State Management**: More robust handling of application state
- **Improved Performance**: More efficient rendering and data handling

## Running the Taipy Version

### Prerequisites

Ensure you have the required dependencies:

```bash
pip install -r requirements.txt
```

### Launch the Taipy Application

```bash
python run_taipy.py
```

The application will be available at http://localhost:5000

### Docker Setup

For a containerized setup that includes both the Taipy application and Ollama:

```bash
# Build and start the Docker containers
docker-compose -f docker-compose.taipy.yml up -d
```

This will:
1. Build and start the Taipy application container
2. Start an Ollama container
3. Connect them together

The application will be available at http://localhost:5000 and Ollama at http://localhost:11434.

## Switching Between Streamlit and Taipy

You can easily switch between the Streamlit and Taipy versions:

### Using Docker

```bash
# For Streamlit version
docker-compose up -d

# For Taipy version
docker-compose -f docker-compose.taipy.yml up -d
```

### Running Locally

```bash
# For Streamlit version
streamlit run app.py

# For Taipy version
python run_taipy.py
```

## Development

### Project Structure

The Taipy version follows a slightly different structure:

- `taipy_app.py` - Main Taipy application
- `run_taipy.py` - Entry point for the Taipy version
- `config/taipy/` - Taipy-specific configuration
- `pages/taipy/` - Taipy page implementations
- `tests/` - Unit and integration tests

### Testing

To run the tests for the Taipy implementation:

```bash
# Run unit tests
python tests/run_tests.py

# Run integration tests
python tests/integration_tests.py
```

## Taipy vs Streamlit

### Key Differences

1. **Template-Based UI**: Taipy uses an HTML-like template system instead of Streamlit's function-based approach
2. **State Management**: Taipy provides more robust state management with scenarios and data nodes
3. **Performance**: Taipy offers better performance, especially for complex UIs
4. **Flexibility**: Taipy provides more customization options for UI elements

### When to Use Each

- **Streamlit**: Better for quick prototyping and simpler applications
- **Taipy**: Better for complex applications with advanced state management needs

## Migration Guide

For details about the Streamlit to Taipy migration process, see the [TAIPY_MIGRATION_GUIDE.md](TAIPY_MIGRATION_GUIDE.md) document.

## License

[MIT License](LICENSE)

## Acknowledgements

- Built with [Taipy](https://www.taipy.io/)
- AI powered by [Ollama](https://ollama.com/)
- PDF processing with [PyPDF2](https://pypi.org/project/PyPDF2/) and [pytesseract](https://pypi.org/project/pytesseract/)
- Vector database using [ChromaDB](https://github.com/chroma-core/chroma)
- Text processing with [LangChain](https://github.com/langchain-ai/langchain)
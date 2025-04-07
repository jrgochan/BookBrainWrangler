# Book Knowledge AI

A Streamlit application for managing scanned books from CZUR ET24 Pro and incorporating their knowledge into an Ollama-powered AI chatbot.

## Overview

This application allows you to:

1. **Upload and manage books** scanned with CZUR ET24 Pro (or any PDF source)
2. **Extract text** from PDF files (using both direct extraction and OCR)
3. **Build a knowledge base** from selected books
4. **Chat with an AI** that has been "trained" on your book collection

## Features

- **Book Management**: Upload, categorize, search, edit, and delete books
- **Knowledge Base**: Select which books to include in your AI's knowledge
- **AI Chat**: Interact with an AI assistant that leverages information from your book collection
- **PDF Processing**: Extract text from PDFs with OCR capabilities for scanned documents

## Requirements

- Python 3.11+
- Ollama (for the AI models)
- PostgreSQL (optional, for larger deployments)
- CZUR ET24 Pro scanner (or any source of PDF files)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/book-knowledge-ai.git
cd book-knowledge-ai
```

### 2. Install Dependencies

Use the provided setup script:

```bash
./scripts/setup.sh
```

Or install manually:

```bash
pip install -r requirements.txt
```

### 3. Install and Set Up Ollama

Ollama is required to run the AI models locally. Follow these steps to install it:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start the Ollama service
ollama serve

# In a new terminal, pull the LLaMA2 model (or your preferred model)
ollama pull llama2
```

### 4. Launch the Application

Use the provided start script:

```bash
./scripts/start.sh
```

Or run manually:

```bash
streamlit run app.py
```

The application will be available at http://localhost:8501

## Development

### Project Structure

- `app.py` - Main Streamlit application
- `book_manager.py` - Handles book database operations
- `knowledge_base.py` - Manages the vector store and retrieval
- `ollama_client.py` - Interacts with the Ollama API
- `pdf_processor.py` - Extracts text from PDFs
- `utils.py` - Utility functions
- `database.py` - Database connection utilities

### Local Development Setup

For local development, see the scripts in the `scripts/` directory:

- `setup.sh` - Sets up the Python environment and dependencies
- `start.sh` - Runs the Streamlit server
- `update_requirements.sh` - Updates the requirements.txt file

## License

[MIT License](LICENSE)

## Acknowledgements

- Built with [Streamlit](https://streamlit.io/)
- AI powered by [Ollama](https://ollama.com/)
- PDF processing with [PyPDF2](https://pypi.org/project/PyPDF2/) and [pytesseract](https://pypi.org/project/pytesseract/)
- Vector database using [ChromaDB](https://github.com/chroma-core/chroma)
- Text processing with [LangChain](https://github.com/langchain-ai/langchain)
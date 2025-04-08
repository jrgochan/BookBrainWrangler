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

#### WSL2 Ubuntu Setup 

We've included specialized scripts for WSL2 Ubuntu users who might face dependency challenges:

```bash
# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Run the WSL2 Ubuntu specialized setup script
chmod +x scripts/wsl-setup.sh
./scripts/wsl-setup.sh
```

#### Handling jnius Package Issues

If you encounter problems with the jnius package, use our script to fix installation issues:

```bash
# Make the script executable 
chmod +x scripts/fix-jnius-install.sh

# Run the specialized jnius fix script
./scripts/fix-jnius-install.sh
```

For manual installation, follow these detailed steps:

1. **Install required system dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y default-jdk build-essential python3-dev
   ```

2. **Set up JAVA_HOME environment variable**:
   ```bash
   # Find your Java installation
   java_path=$(readlink -f $(which java) | sed 's:/bin/java::')
   
   # Set JAVA_HOME for current session
   export JAVA_HOME=$java_path
   
   # Add to .bashrc for persistence
   echo "export JAVA_HOME=$java_path" >> ~/.bashrc
   ```

3. **Install Cython first** (required by jnius):
   ```bash
   pip install Cython
   ```

4. **Install jnius with special flags**:
   ```bash
   # Use the no-binary flag to force compilation
   JAVA_HOME=$java_path pip install --no-binary :all: jnius
   ```

5. **Verify installation**:
   ```bash
   python -c 'import jnius; print("jnius installed successfully!")'
   ```

**Common jnius Installation Errors**:

- **Error**: `ModuleNotFoundError: No module named 'Cython'`  
  **Solution**: Install Cython first with `pip install Cython`

- **Error**: `error: command 'gcc' failed with exit status 1`  
  **Solution**: Install build tools with `sudo apt-get install build-essential python3-dev`

- **Error**: `Could not find JVM shared library`  
  **Solution**: Set JAVA_HOME correctly to your Java installation path

#### General Installation

For other systems, use the general dependency installation script:

```bash
# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Run the dependency installation script
chmod +x scripts/install-dependencies.sh
./scripts/install-dependencies.sh
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

#### WSL2 Ubuntu

For WSL2 Ubuntu:

```bash
./scripts/wsl-run.sh
```

#### General Launch

For other environments:

```bash
./scripts/start.sh
```

Or run manually:

```bash
streamlit run app.py
```

The application will be available at http://localhost:8501

### Docker Setup

For a containerized setup that includes both the application and Ollama:

```bash
# Start the Docker containers
./scripts/docker-start.sh
```

This will:
1. Build and start the Streamlit application container
2. Start an Ollama container
3. Download the llama2 model
4. Connect them together

The application will be available at http://localhost:8501 and Ollama at http://localhost:11434.

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

Our repository includes several scripts to handle different environments:

- `wsl-setup.sh` - Sets up the environment specifically for WSL2 Ubuntu
- `wsl-run.sh` - Runs the application on WSL2
- `fix-jnius-install.sh` - Fixes jnius installation issues on WSL2
- `install-dependencies.sh` - Specialized script to handle complex dependencies
- `docker-start.sh` - Runs the application in Docker with Ollama

### Troubleshooting Common Issues

#### jnius Installation Problems

If you encounter issues with jnius installation:
1. Use the `fix-jnius-install.sh` script
2. Ensure you have Java JDK installed
3. Set the JAVA_HOME environment variable correctly

#### Ollama Connection Issues

If the application can't connect to Ollama:
1. Ensure Ollama is running (`ollama serve`)
2. Check if the model is downloaded (`ollama list`)
3. Verify the connection settings in `ollama_client.py`

## License

[MIT License](LICENSE)

## Acknowledgements

- Built with [Streamlit](https://streamlit.io/)
- AI powered by [Ollama](https://ollama.com/)
- PDF processing with [PyPDF2](https://pypi.org/project/PyPDF2/) and [pytesseract](https://pypi.org/project/pytesseract/)
- Vector database using [ChromaDB](https://github.com/chroma-core/chroma)
- Text processing with [LangChain](https://github.com/langchain-ai/langchain)

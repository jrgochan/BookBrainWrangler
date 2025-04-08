#!/bin/bash

# Book Knowledge AI WSL Setup Script
echo "Setting up Book Knowledge AI on WSL2 Ubuntu..."

# Make sure we have the latest package lists
sudo apt-get update

# Install Python if not already installed
if ! command -v python3 &> /dev/null; then
    echo "Installing Python..."
    sudo apt-get install -y python3 python3-pip python3-venv
fi

# Install required system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y tesseract-ocr libtesseract-dev poppler-utils

# Install Java dependencies if needed (for jnius)
echo "Installing Java dependencies..."
sudo apt-get install -y default-jdk

# Create a virtual environment
echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
echo "Installing Python packages..."
pip install --upgrade pip

# Install Cython first (required for jnius)
echo "Installing Cython (required for some dependencies)..."
pip install Cython

# Create requirements.txt file for core dependencies
cat > requirements.txt << EOL
# Core requirements
chromadb>=1.0.3
langchain>=0.3.23
langchain-community>=0.3.21
langchain-text-splitters>=0.3.8
pdf2image>=1.17.0
pypdf2>=3.0.1
pytesseract>=0.3.13
requests>=2.32.3
streamlit>=1.44.1

# Additional dependencies from your project
attr>=0.3.2
ConfigParser>=7.2.0
contextlib2>=21.6.0
cryptography>=44.0.2
docutils>=0.21.2
filelock>=3.18.0
importlib_metadata>=8.6.1
ipython>=8.12.3
ipywidgets>=8.1.5
Jinja2>=3.1.6
# Note: jnius is optional and installed separately
EOL

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Try to install jnius with enhanced error handling for WSL2 environments
echo "Attempting to install jnius with special handling for WSL2..."

# Set JAVA_HOME properly
java_path=$(readlink -f $(which java) 2>/dev/null | sed 's:/bin/java::')
if [ -n "$java_path" ]; then
    echo "Found Java at: $java_path"
    export JAVA_HOME=$java_path
    echo "JAVA_HOME set to: $JAVA_HOME"
else
    echo "Warning: Could not determine Java path automatically."
    echo "You may need to set JAVA_HOME manually."
    echo "Typical locations include /usr/lib/jvm/default-java or /usr/lib/jvm/java-11-openjdk-amd64"
    echo "Export JAVA_HOME in your shell: export JAVA_HOME=/path/to/java"
fi

# Try installing with --no-binary flag which often works better in WSL2
echo "Installing jnius with special compilation flags..."
JAVA_HOME=$java_path pip install --no-binary :all: jnius || {
    echo "Standard jnius installation failed. Attempting alternative methods..."
    
    # Try with explicit compiler flags
    echo "Attempting installation with explicit compiler flags..."
    JAVA_HOME=$java_path CFLAGS="-fPIC" pip install jnius || {
        echo ""
        echo "jnius installation could not be completed automatically."
        echo "This is not uncommon in WSL2 environments."
        echo ""
        echo "For manual installation, run: ./scripts/fix-jnius-install.sh"
        echo "or follow the detailed instructions in README.md"
        echo ""
        echo "Note: jnius is optional and the core functionality should still work."
    }
}

# Create .streamlit directory if it doesn't exist
if [ ! -d .streamlit ]; then
    echo "Creating .streamlit directory..."
    mkdir -p .streamlit
fi

# Create config.toml for local development
cat > .streamlit/config.toml << EOL
[server]
port = 8501
address = "localhost"
EOL

# Instructions for installing Ollama
echo ""
echo "==== OLLAMA SETUP ===="
echo "The application requires Ollama for AI functionality."
echo "Install Ollama with the following commands:"
echo ""
echo "curl -fsSL https://ollama.com/install.sh | sh"
echo ""
echo "After installation, you need to:"
echo "1. Start the Ollama service: ollama serve"
echo "2. In a new terminal, pull the default model: ollama pull llama2"
echo ""
echo "==== SETUP COMPLETE ===="
echo "To run the application, use: ./scripts/wsl-run.sh"
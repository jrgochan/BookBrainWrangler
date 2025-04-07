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

# Create a virtual environment
echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
echo "Installing Python packages..."
pip install --upgrade pip

# Install packages from pyproject.toml using pip
pip install chromadb langchain langchain-community langchain-text-splitters pdf2image pypdf2 pytesseract requests streamlit

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
#!/bin/bash

# Script to properly install dependencies with special handling for jnius
echo "Installing dependencies for Book Knowledge AI..."

# Check if running in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "It's recommended to run this script inside a virtual environment."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please activate your virtual environment first."
        exit 1
    fi
fi

# Update pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install system dependencies
echo "Checking system dependencies (requires sudo)..."
if command -v apt-get &> /dev/null; then
    echo "Debian/Ubuntu detected, installing dependencies..."
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr libtesseract-dev poppler-utils default-jdk build-essential
else
    echo "Warning: Not running on Debian/Ubuntu. Please manually install these dependencies:"
    echo "- tesseract-ocr and development libraries"
    echo "- poppler-utils (for pdf2image)"
    echo "- Java JDK (for jnius)"
    echo "- Build tools (for Cython compilation)"
fi

# Install Cython first
echo "Installing Cython (required for jnius)..."
pip install Cython

# Create requirements files

# Core requirements that work reliably
echo "Creating core_requirements.txt..."
cat > core_requirements.txt << EOL
chromadb>=1.0.3
langchain>=0.3.23
langchain-community>=0.3.21
langchain-text-splitters>=0.3.8
pdf2image>=1.17.0
pypdf2>=3.0.1
pytesseract>=0.3.13
requests>=2.32.3
streamlit>=1.44.1
EOL

# Additional requirements that might be needed
echo "Creating additional_requirements.txt..."
cat > additional_requirements.txt << EOL
attr>=0.3.2
ConfigParser>=7.2.0
contextlib2>=21.6.0
cryptography>=44.0.2
docutils>=0.21.2
filelock>=3.18.0
HTMLParser>=0.0.2
importlib_metadata>=8.6.1
ipython>=8.12.3
ipywidgets>=8.1.5
Jinja2>=3.1.6
EOL

# Install core requirements
echo "Installing core requirements..."
pip install -r core_requirements.txt

# Attempt to install jnius separately
echo "Attempting to install jnius..."
pip install jnius || {
    echo "Warning: Failed to install jnius. Some features may not work correctly."
    echo "If this package is required, you might need to install additional dependencies."
}

# Install additional requirements
echo "Installing additional requirements (some might fail but are optional)..."
pip install -r additional_requirements.txt || echo "Some optional packages failed to install but core functionality should work."

# Clean up temporary files
echo "Cleaning up..."
rm core_requirements.txt additional_requirements.txt

echo "Installation process completed!"
echo "Note: If you encountered errors with specific packages, you might need to install them manually."
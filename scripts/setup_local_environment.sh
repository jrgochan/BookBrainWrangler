#!/bin/bash
# Script to set up the local environment for Book Knowledge AI

# Display banner
echo "====================================================="
echo "      Book Knowledge AI - Local Environment Setup     "
echo "====================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if virtual environment exists, if not create it
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Update pip
echo "Updating pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Additional dependencies
echo "Installing additional dependencies..."
pip install langchain-chroma

# Create config directories if they don't exist
echo "Setting up configuration directories..."
mkdir -p .streamlit
mkdir -p knowledge_base_data

# Check if .streamlit/config.toml exists, if not create it
if [ ! -f ".streamlit/config.toml" ]; then
    echo "Creating Streamlit configuration..."
    cat > .streamlit/config.toml << EOL
[server]
headless = true
address = "0.0.0.0"
port = 5000
EOL
fi

# Make sure start.sh is executable
chmod +x scripts/start.sh

# Check if Tesseract is installed
if ! command -v tesseract &> /dev/null; then
    echo "Warning: Tesseract OCR is not installed. PDF OCR functionality may not work."
    echo "To install Tesseract OCR, run: sudo apt-get install tesseract-ocr"
fi

# Success message
echo "====================================================="
echo "Setup complete! You can now run the application with:"
echo "source .venv/bin/activate"
echo "./scripts/start.sh"
echo "====================================================="
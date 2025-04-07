#!/bin/bash

# Book Knowledge AI Setup Script
echo "Setting up Book Knowledge AI..."

# Create and activate a virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install required system dependencies for tesseract OCR
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev poppler-utils

# Install Python dependencies
echo "Installing Python packages..."
pip install -r requirements.txt

# Check if requirements.txt exists, if not, create it
if [ ! -f requirements.txt ]; then
    echo "Creating requirements.txt..."
    pip install pipreqs
    pipreqs . --force
fi

# Create .streamlit directory if it doesn't exist
if [ ! -d .streamlit ]; then
    echo "Creating .streamlit directory..."
    mkdir -p .streamlit
fi

# Create config.toml if it doesn't exist
if [ ! -f .streamlit/config.toml ]; then
    echo "Creating .streamlit/config.toml..."
    cat > .streamlit/config.toml << EOL
[server]
headless = false
port = 8501
address = "localhost"
EOL
fi

# Check if Ollama is installed
echo "Checking if Ollama is installed..."
if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed. Please install it manually:"
    echo "curl -fsSL https://ollama.com/install.sh | sh"
    echo "Then run 'ollama serve' to start the Ollama service."
    echo "In a new terminal, run 'ollama pull llama2' to download the default model."
else
    echo "Ollama is already installed."
    echo "Ensure Ollama is running with: ollama serve"
fi

echo "Setup completed successfully!"
echo "You can now run the application with: ./scripts/start.sh"
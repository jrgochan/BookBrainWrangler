#!/bin/bash
# WSL2 Ubuntu Setup Script for Book Knowledge AI

# Display banner
echo "====================================================="
echo "      Book Knowledge AI - WSL2 Ubuntu Setup          "
echo "====================================================="

# Check if running in WSL
if ! grep -q Microsoft /proc/version; then
    echo "This script is designed for WSL2 Ubuntu. It appears you're not running in WSL."
    read -p "Continue anyway? (y/n): " continue_anyway
    if [[ ! $continue_anyway =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
fi

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y python3-pip python3-venv tesseract-ocr

# Install Ollama if not present
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "Note: You will need to start Ollama separately with 'ollama serve'"
else
    echo "Ollama is already installed."
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
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

# Update start.sh to use correct virtual environment path
echo "Updating start script..."
cat > scripts/start.sh << EOL
#!/bin/bash

# Book Knowledge AI Start Script
echo "Starting Book Knowledge AI..."

# Activate the virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found. Please run wsl-setup.sh first."
    exit 1
fi

# Check if Ollama is running
echo "Checking if Ollama service is running..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "WARNING: Ollama service doesn't seem to be running."
    echo "The AI chat functionality might not work properly."
    echo "Please start Ollama in another terminal with: ollama serve"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! \$REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please start Ollama and try again."
        exit 1
    fi
fi

# Run Streamlit app
echo "Launching Streamlit application..."
streamlit run app.py

# Deactivate virtual environment on exit
trap "deactivate" EXIT
EOL

# Make scripts executable
chmod +x scripts/start.sh
chmod +x scripts/wsl-setup.sh

# Success message
echo "====================================================="
echo "Setup complete! You can now run the application with:"
echo "./scripts/start.sh"
echo ""
echo "NOTE: Before running the app, start Ollama in a separate terminal:"
echo "ollama serve"
echo "====================================================="
#!/bin/bash

# Book Knowledge AI WSL Run Script
echo "Starting Book Knowledge AI on WSL2..."

# Activate the virtual environment
source .venv/bin/activate

# Check if Ollama is running
echo "Checking if Ollama service is running..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "WARNING: Ollama service doesn't seem to be running."
    echo "The AI chat functionality will not work properly."
    echo "Please open another terminal and run: ollama serve"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please start Ollama and try again."
        exit 1
    fi
fi

# Run Streamlit app
echo "Starting Streamlit application..."
streamlit run app.py
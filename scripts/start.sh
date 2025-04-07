#!/bin/bash

# Book Knowledge AI Start Script
echo "Starting Book Knowledge AI..."

# Activate the virtual environment
source venv/bin/activate

# Check if Ollama is running
echo "Checking if Ollama service is running..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "WARNING: Ollama service doesn't seem to be running."
    echo "The AI chat functionality might not work properly."
    echo "Please start Ollama in another terminal with: ollama serve"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please start Ollama and try again."
        exit 1
    fi
fi

# Run Streamlit app
echo "Launching Streamlit application..."
streamlit run app.py

# Deactivate virtual environment on exit
trap "deactivate" EXIT
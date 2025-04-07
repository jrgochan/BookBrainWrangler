#!/bin/bash

# Book Knowledge AI Docker Start Script
echo "Starting Book Knowledge AI with Docker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    echo "Visit https://docs.docker.com/engine/install/ for installation instructions."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit https://docs.docker.com/compose/install/ for installation instructions."
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Start the services
echo "Starting containers..."
docker-compose up -d

# Pull the default model for Ollama
echo "Pulling the llama2 model for Ollama (this may take a while)..."
sleep 5 # Give Ollama a moment to start
docker exec -it $(docker ps -qf "name=ollama") ollama pull llama2

echo "Application is now running!"
echo "- Streamlit: http://localhost:8501"
echo "- Ollama API: http://localhost:11434"
echo ""
echo "To view logs, run: docker-compose logs -f"
echo "To stop the application, run: docker-compose down"
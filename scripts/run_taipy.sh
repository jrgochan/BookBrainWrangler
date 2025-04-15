#!/bin/bash
# Run script for the Taipy version of Book Knowledge AI

# Activate virtual environment if present
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "Starting Book Knowledge AI with Taipy..."
python run_taipy.py
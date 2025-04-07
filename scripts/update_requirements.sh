#!/bin/bash

# Book Knowledge AI Update Requirements Script
echo "Updating requirements.txt file..."

# Activate the virtual environment
source venv/bin/activate

# Install pipreqs if not already installed
pip install pipreqs

# Generate requirements.txt
echo "Generating requirements.txt from installed packages..."
pipreqs . --force

# Add essential packages that might be missing
echo "Ensuring all necessary packages are included..."
cat << EOF >> requirements.txt
chromadb>=1.0.3
langchain>=0.3.23
langchain-community>=0.3.21
langchain-text-splitters>=0.3.8
pdf2image>=1.17.0
pypdf2>=3.0.1
pytesseract>=0.3.13
requests>=2.32.3
streamlit>=1.44.1
EOF

# Sort and deduplicate requirements
echo "Sorting and removing duplicates..."
sort -u requirements.txt -o requirements.txt

echo "Requirements file updated successfully!"
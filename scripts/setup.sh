#!/bin/bash
# Minimal setup script for Book Knowledge AI on Linux

echo "Book Knowledge AI Setup"
echo "======================="

# Check for Python
if command -v python3 &>/dev/null; then
    echo "[✓] Python: $(python3 --version)"
else
    echo "[✗] Python 3 not found. Please install Python 3.8+"
fi

# Check for Tesseract
if command -v tesseract &>/dev/null; then
    echo "[✓] Tesseract: $(tesseract --version | head -n 1)"
else
    echo "[✗] Tesseract not found. Install with package manager"
fi

# Check for virtual environment
if [ -d "venv" ]; then
    echo "[✓] Virtual environment exists"
else
    echo "[i] Create virtual environment with: python3 -m venv venv"
fi

echo ""
echo "Quick Start:"
echo "1. Activate: source venv/bin/activate"
echo "2. Run: streamlit run app.py"

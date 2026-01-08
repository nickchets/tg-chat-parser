#!/bin/bash
# Setup script for Telegram to Google Docs Exporter

echo "Setting up Python environment..."

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Installing python3-pip and python3-venv..."
    sudo apt update
    sudo apt install -y python3-pip python3-venv
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the exporter:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""

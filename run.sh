#!/bin/bash
# Simple launcher for RU_Bookmate_downloader on Mac

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Use the Python from the virtual environment
PYTHON="$DIR/venv/bin/python"

# Check if virtual environment exists
if [ ! -f "$PYTHON" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Run the downloader with all arguments passed to this script
"$PYTHON" "$DIR/RUBookmatedownloader.py" "$@"

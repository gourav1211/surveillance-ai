#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup YOLO model
python setup_yolo.py

# Create HLS output directory
mkdir -p hls_output

# Start the server
python main.py

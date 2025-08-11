#!/usr/bin/env python3
"""
Setup script to download YOLO model for person detection
"""

import os
import sys
from pathlib import Path

def setup_yolo():
    """Download YOLO model if it doesn't exist"""
    model_path = Path("yolov8n.pt")
    
    if model_path.exists():
        print(f"✅ YOLO model already exists: {model_path}")
        return True
    
    print("📥 Downloading YOLO model...")
    try:
        from ultralytics import YOLO
        # This will automatically download the model
        model = YOLO("yolov8n.pt")
        print(f"✅ YOLO model downloaded successfully: {model_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to download YOLO model: {e}")
        return False

if __name__ == "__main__":
    success = setup_yolo()
    sys.exit(0 if success else 1)

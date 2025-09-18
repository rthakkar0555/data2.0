"""
Vercel entry point for FastAPI backend
"""
import sys
import os
from pathlib import Path

# Add the parent directory to Python path so we can import our modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import the FastAPI app from main.py
from main import app

# This is the ASGI application that Vercel will use
handler = app

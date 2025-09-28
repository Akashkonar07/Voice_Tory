#!/usr/bin/env python3
"""
Main entry point for the Speech-to-Text and Text-to-Speech Application
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.backend.app import app
from config.config import *

if __name__ == '__main__':
    print(f"Starting {APP_NAME} v{VERSION}")
    print(f"Debug mode: {DEBUG}")
    print(f"Server running on http://{HOST}:{PORT}")
    
    app.run(
        debug=DEBUG,
        host=HOST,
        port=PORT,
        threaded=False,
        use_reloader=False
    )

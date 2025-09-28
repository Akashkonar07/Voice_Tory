"""
Configuration settings for the speech-to-text application
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Application settings
APP_NAME = "Speech-to-Text and Text-to-Speech Application"
VERSION = "1.0.0"
DEBUG = False
HOST = "0.0.0.0"
PORT = 5000

# File paths
UPLOAD_FOLDER = BASE_DIR / "data" / "uploads"
TEXT_LOGS_FOLDER = BASE_DIR / "data" / "text_logs"
TEMPLATES_FOLDER = BASE_DIR / "src" / "frontend" / "templates"

# Ensure directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
TEXT_LOGS_FOLDER.mkdir(parents=True, exist_ok=True)

# Flask configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac', 'm4a', 'wma'}

# Speech recognition settings
RECOGNITION_LANGUAGE = 'en-US'
RECOGNITION_TIMEOUT = 5
PHRASE_TIME_LIMIT = 10

# Logging settings
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

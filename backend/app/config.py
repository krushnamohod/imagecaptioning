"""
Centralized Configuration Module
================================
Manages application constants, environment variables, supported languages,
writing styles, social media platforms, and system directories.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Server Config
HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# BLIP Model Settings
BLIP_MODEL_NAME: str = os.getenv("BLIP_MODEL_NAME", "Salesforce/blip-image-captioning-base")

# Ollama LLM Settings
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# Storage Directories
UPLOAD_DIR: Path = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
OUTPUT_DIR: Path = BASE_DIR / os.getenv("OUTPUT_DIR", "outputs")
DATA_DIR: Path = BASE_DIR.parent / "data"

# Ensure storage directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database Settings
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'history.db'}")

# CORS Settings
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
]

# Supported Application Options (Constants to avoid duplication across backend/frontend)
SUPPORTED_LANGUAGES: list[str] = [
    "English",
    "Hindi",
    "Marathi",
]

SUPPORTED_STYLES: list[str] = [
    "Normal",
    "Formal",
    "Creative",
    "Humorous",
    "Marketing",
    "Travel",
    "Accessibility / Alt Text",
]

SUPPORTED_PLATFORMS: list[str] = [
    "Instagram",
    "LinkedIn",
    "Facebook",
    "X (Twitter)",
]

# Security & Validation Constants
MAX_FILE_SIZE_MB: int = 10  # 10 MB limit
ALLOWED_EXTENSIONS: set[str] = {"jpg", "jpeg", "png", "webp"}
ALLOWED_MIME_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}

"""
Main Server Configuration
"""
import os
from pathlib import Path

# API Authentication
API_KEY = os.getenv("API_KEY", "main-server-secret-key-change-me")

# Server settings
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 8000))

# Storage paths - use /data for cloud persistent disk
DATA_DIR = Path(os.getenv("DATA_DIR", "."))
STORAGE_DIR = DATA_DIR / "storage"
PENDING_DIR = STORAGE_DIR / "pending"
PROCESSED_DIR = STORAGE_DIR / "processed"
DATABASE_PATH = DATA_DIR / "data.db"

# GPU Server connection (will be set via env var on cloud)
GPU_SERVER_URL = os.getenv("GPU_SERVER_URL", "http://localhost:8001")
GPU_SERVER_API_KEY = os.getenv("GPU_SERVER_API_KEY", "gpu-server-secret-key-change-me")

# Batch processing
BATCH_SIZE = 10
GPU_REQUEST_TIMEOUT = 30

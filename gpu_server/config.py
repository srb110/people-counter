"""
GPU Server Configuration
"""
import os

# API Authentication
API_KEY = os.getenv("API_KEY", "gpu-server-secret-key-change-me")

# Server settings
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 8001))

# Mock model settings
MIN_PEOPLE = 0
MAX_PEOPLE = 15
PROCESSING_DELAY_MS = 100
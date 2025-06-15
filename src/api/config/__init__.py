"""
Configuration module for Business Interior Design Chatbot
Contains settings and configuration following Azure best practices
"""

import os
from pathlib import Path

# Azure best practice - centralized configuration management
# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SRC_DIR = BASE_DIR / 'src'

# Environment detection - Azure best practice for conditional configuration
IS_PRODUCTION = os.environ.get("ENVIRONMENT", "development") == "production"
IS_AZURE = os.environ.get("AZURE_ENVIRONMENT", "false").lower() == "true"

# API configuration
API_CONFIG = {
    "model_id": os.environ.get("MODEL_ID", "gemini-2.0-flash"),
    "temperature": float(os.environ.get("MODEL_TEMPERATURE", "0.7")),
    "max_tokens": int(os.environ.get("MODEL_MAX_TOKENS", "1024")),
    "top_p": float(os.environ.get("MODEL_TOP_P", "0.95")),
    "top_k": int(os.environ.get("MODEL_TOP_K", "40"))
}

# Azure configuration - following Azure best practices
AZURE_CONFIG = {
    "key_vault_name": os.environ.get("AZURE_KEY_VAULT_NAME"),
    "app_insights_connection_string": os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"),
    "storage_account_name": os.environ.get("AZURE_STORAGE_ACCOUNT"),
    "storage_connection_string": os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
}

# Function to get complete configurations
def get_config():
    """Get complete configuration with conditional Azure settings"""
    config = {
        "api": API_CONFIG,
        "azure": AZURE_CONFIG if IS_AZURE else {},
        "environment": "production" if IS_PRODUCTION else "development",
        "is_azure": IS_AZURE
    }
    return config
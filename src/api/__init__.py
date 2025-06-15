"""
API module for Business Interior Design Chatbot
Contains API clients and integration with external services
Following Azure best practices for secure API integration
"""

# Import key components for simplified access
from src.api.gemini_client import GeminiClient

# Define API-level constants
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.5  # exponential backoff factor for retries

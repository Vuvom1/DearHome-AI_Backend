from typing import Optional, Any

class ChromaServiceError(Exception):
    """Base exception class for ChromaDB service errors"""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.details = details

class ChromaConnectionError(ChromaServiceError):
    """Raised when there are issues connecting to ChromaDB"""
    pass

class ChromaQueryError(ChromaServiceError):
    """Raised when there are issues with query operations"""
    pass

class ChromaUpdateError(ChromaServiceError):
    """Raised when there are issues with update operations"""
    pass

class ChromaBatchError(ChromaServiceError):
    """Raised when there are issues with batch operations"""
    pass

class ChromaCollectionError(ChromaServiceError):
    """Raised when there are issues with collection operations"""
    pass

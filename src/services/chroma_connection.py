from typing import Optional, Dict
from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from chromadb.api.models.Collection import Collection
from src.config.chroma_config import ChromaConfig
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class ChromaConnectionManager:
    """Manages ChromaDB client connections and collection access"""
    
    def __init__(self, config: ChromaConfig):
        self.config = config
        self._client = None
        self._collections: Dict[str, Collection] = {}
        
    @property
    def client(self):
        """Get or create ChromaDB client"""
        if self._client is None:
            settings = Settings(
                anonymized_telemetry=self.config.enable_telemetry,
                allow_reset=self.config.allow_reset,
                is_persistent=self.config.is_persistent,
                persist_directory=str(self.config.db_directory)
            )
            self._client = chromadb.PersistentClient(settings=settings)
            logger.info("Created ChromaDB client with persistent storage")
        return self._client
    
    def get_collection(self, collection_name: str) -> Collection:
        """Get or create a specific ChromaDB collection"""
        if collection_name not in self._collections:
            try:
                collection_config = self.config.collections[collection_name]
                self._collections[collection_name] = self.client.get_or_create_collection(
                    name=collection_config.name,
                    metadata={"description": collection_config.description},
                    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=collection_config.embedding_model,
                        device=collection_config.device
                    )
                )
                logger.info(f"Connected to collection: {collection_name}")
            except KeyError:
                raise ValueError(f"Collection '{collection_name}' not configured")
            except Exception as e:
                logger.error(f"Error connecting to collection {collection_name}: {e}")
                raise
        
        return self._collections[collection_name]
    
    def reset_collection(self, collection_name: str) -> None:
        """Reset a specific collection by deleting and recreating it"""
        if not self.config.allow_reset:
            raise PermissionError("Collection reset is not allowed by configuration")
        
        if collection_name in self._collections:
            self.client.delete_collection(collection_name)
            self._collections.pop(collection_name)
            logger.info(f"Reset collection: {collection_name}")
            # Recreate the collection
            self.get_collection(collection_name)
    
    def close(self) -> None:
        """Close the ChromaDB client connection"""
        if self._client:
            self._client = None
            self._collections.clear()
            logger.info("Closed ChromaDB connection")
    
    @contextmanager
    def collection_context(self, collection_name: str):
        """Context manager for safe collection access"""
        try:
            yield self.get_collection(collection_name)
        except Exception as e:
            logger.error(f"Error accessing ChromaDB collection {collection_name}: {e}")
            raise
        finally:
            logger.debug(f"Exiting ChromaDB collection context for {collection_name}")
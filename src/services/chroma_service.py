import asyncio
import uuid
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
from sentence_transformers import SentenceTransformer
from src.config.chroma_config import ChromaConfig
from src.services.chroma_connection import ChromaConnectionManager
from src.models.search_result import SearchResultFormatter, SearchResults
from src.exceptions.chroma_exceptions import *
import logging
import time
from functools import wraps
import os
from pathlib import Path
import json

from src.models.product import ProductMetadata
from src.models.variant import VariantMetadata

logger = logging.getLogger(__name__)

def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator for retrying operations on failure.
    This version is async-aware.
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs): # 1. Wrapper phải là 'async def'
            last_error = None
            for attempt in range(max_retries):
                try:
                    # 2. Phải 'await' hàm gốc để thực thi nó và bắt lỗi
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} of {max_retries} for {func.__name__} failed, "
                            f"retrying in {delay}s: {str(e)}"
                        )
                        # 3. Dùng asyncio.sleep thay vì time.sleep để không block event loop
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts for {func.__name__} failed.")
            raise last_error
        
        # Trả về wrapper bất đồng bộ
        return async_wrapper
    return decorator

class ChromaService:
    """Service class for managing ChromaDB vector database operations"""

    def __init__(self, config: Optional[ChromaConfig] = None, collection_name: str = "variants"):
        """Initialize ChromaDB service with embedding function and collection"""
        self.config = config or ChromaConfig()
        self.collection_name = collection_name
        # Setup database directory
        self.config.db_directory.mkdir(parents=True, exist_ok=True)
        
        # Get collection config
        collection_config = self.config.collections[self.collection_name]
        
        # Initialize model and formatter
        self.model = SentenceTransformer(collection_config.embedding_model, device=collection_config.device)
        self.formatter = SearchResultFormatter()
        
        # Initialize connection manager
        self.connection = ChromaConnectionManager(self.config)
        self.collection = self.connection.get_collection(self.collection_name)

    async def _handle_operation(self, operation_name: str, func, *args, **kwargs) -> Any:
        """Generic error handler for database operations"""
        try:
            result = await func(*args, **kwargs)
            logger.info(f"Successfully completed {operation_name}")
            return result
        except Exception as e:
            logger.error(f"Error during {operation_name}: {e}")
            raise

    async def delete_item(self, item_id: str) -> None:
        """Delete a product or variant from the database"""
        await self._handle_operation(
            "delete_item",
            self.collection.delete,
            ids=[item_id]
        )

    async def get_similar_items(self, item_id: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Find similar products or variants using semantic similarity"""
        results = await self._handle_operation(
            "get_similar_items",
            self.collection.query,
            query_ids=[item_id],
            n_results=n_results + 1,  # Add 1 to exclude the query item
            include=['metadatas', 'distances']
        )
        
        # Remove the query item from results
        search_results = []
        for id, metadata, distance in zip(
            results['ids'][0][1:],  # Skip first result (query item)
            results['metadatas'][0][1:],
            results['distances'][0][1:]
        ):
            similarity = 1 - (distance / 2)
            search_results.append({
                "id": id,
                "metadata": metadata,
                "similarity_score": round(similarity, 4)
            })
        
        return search_results

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for input text"""
        try:
            return self.model.encode(text).tolist()
        except Exception as e:
            raise ChromaQueryError(f"Error generating embedding: {str(e)}")
    
    @retry_on_error()
    async def search_items(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for items in the vector database"""
        try:
            # Generate embedding for query
            query_embedding = self._generate_embedding(query)
            
            # Use collection directly since ChromaDB operations are synchronous
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['metadatas', 'distances']
            )
            
            if not results["ids"] or len(results["ids"][0]) == 0:
                logger.warning(f"No results found for query: {query}")
                return []
            
            # Format search results
            search_results = []
            for id, metadata, distance in zip(
                results['ids'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                similarity = 1 - (distance / 2)  # Convert distance to similarity score
                search_results.append({
                    "id": id,
                    "metadata": metadata,
                    "similarity_score": round(similarity, 4)
                })
            
            return sorted(
                search_results,
                key=lambda x: x['similarity_score'],
                reverse=True
            )
        except Exception as e:
            logger.error(f"Error searching items: {str(e)}")
            raise ChromaQueryError(f"Error performing search: {str(e)}")
        
    @retry_on_error()
    async def add_document(
        self,
        id: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding_text: Optional[str] = None
    ) -> None:
        """Update a document in the vector database"""
        try:
            with self.connection.collection_context(self.collection_name) as collection:
                embedding = self._generate_embedding(embedding_text) if embedding_text else None
                if metadata is not None:
                    metadata = self._flatten_metadata(metadata)
                collection.upsert(
                    ids=[id],
                    embeddings=[embedding],
                    metadatas=[metadata]
                )
                logger.info(f"Updated document {id}")

                return True
        except Exception as e:
            raise ChromaUpdateError(f"Error updating document: {str(e)}")

    # @retry_on_error()
    async def update_document(
        self,
        id: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding_text: Optional[str] = None
    ) -> None:
        """Update a document in the vector database"""
        try:
            with self.connection.collection_context(self.collection_name) as collection:
                embedding = self._generate_embedding(embedding_text) if embedding_text else None
                if metadata is not None:
                    metadata = self._flatten_metadata(metadata)
                collection.upsert(
                    ids=[id],
                    embeddings=[embedding],
                    metadatas=[metadata]
                )
                logger.info(f"Updated document {id}")

                return True
        except Exception as e:
            raise ChromaUpdateError(f"Error updating document: {str(e)}")
    
    @retry_on_error()
    async def delete_documents(self, ids: List[str]) -> None:
        """Delete documents from the vector database"""
        try:
            with self.connection.collection_context(self.collection_name) as collection:
                collection.delete(ids=ids)
                logger.info(f"Deleted {len(ids)} documents")
        except Exception as e:
            raise ChromaUpdateError(f"Error deleting documents: {str(e)}")
    
    def reset_collection(self) -> None:
        """Reset the entire collection"""
        self.connection.reset_collection()
    
    def close(self) -> None:
        """Close the service and its connections"""
        self.connection.close()

    def _flatten_metadata(self, metadata: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary into dot notation and ensure values are primitive types"""
        items: List[Tuple[str, Any]] = []
        
        for k, v in metadata.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                # Recursively flatten nested dictionaries
                items.extend(self._flatten_metadata(v, new_key, sep=sep).items())
            elif isinstance(v, (list, tuple)):
                # Convert lists to strings
                items.append((new_key, json.dumps(v)))
            elif isinstance(v, (str, int, float, bool)) or v is None:
                # Keep primitive types as is
                items.append((new_key, v))
            else:
                # Convert other types to string representation
                items.append((new_key, str(v)))
        
        return dict(items)
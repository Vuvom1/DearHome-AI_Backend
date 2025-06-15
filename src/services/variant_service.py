from typing import Dict, List, Any, Optional
import logging
from src.services.chroma_service import ChromaService

logger = logging.getLogger(__name__)

class VariantService:
    """Service for managing variants using ChromaDB as the underlying storage."""

    def __init__(self):
        """Initialize with a ChromaService instance."""
        self.collection_name = "variants"
        self.chroma_service = ChromaService(collection_name=self.collection_name)
        logger.info("VariantService initialized")

    def _prepare_variant_embedding_text(self, variant: Dict[str, Any]) -> str:
        """Prepare text for embedding generation."""
        return f"{variant.get('name', '')} {variant.get('sku', '')} {variant.get('price', '')} {variant.get('stock_quantity', '')} {variant.get('attributes', '')}"

    async def create_variant(self, variant_data: Dict[str, Any]) -> bool:
        try:
            result = await self.chroma_service.add_document(
                id=variant_data.get('id'),
                embedding_text=self._prepare_variant_embedding_text(variant_data),
                metadata=variant_data
            )
            if not result:
                logger.warning(f"Variant with ID {variant_data.get('id')} already exists")
                return False
            logger.info(f"Created variant with ID: {variant_data.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Error creating variant: {str(e)}")
            return False

    async def update_variant(self, id: str, variant_data: Dict[str, Any]) -> bool:
        """
        Update an existing variant in the database.
        
        Args:
            variant_id: Unique identifier for the variant to update
            variant_data: New data for the variant
            metadata: Optional metadata to update
            
        Returns:
            bool: Success status
        """
        try:
            result = await self.chroma_service.update_document(
                id=id,
                embedding_text=self._prepare_variant_embedding_text(variant_data),  
                metadata=variant_data
            )
            if not result:
                logger.warning(f"Variant with ID {id} does not exist")
                return False
            logger.info(f"Updated variant with ID: {id}")
            return True
        except Exception as e:
            logger.error(f"Error updating variant: {str(e)}")
            return False

    async def delete_variant(self, id: str) -> bool:
        """
        Delete a variant from the database.
        
        Args:
            variant_id: Unique identifier for the variant to delete
            
        Returns:
            bool: Success status
        """
        try:
            result = await self.chroma_service.delete_documents(ids=[id])
            if not result:
                logger.warning(f"Variant with ID {  id} does not exist")
                return False
            logger.info(f"Deleted variant with ID: {id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting variant: {str(e)}")
            return False

    def get_variant(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a variant from the database.
        
        Args:
            variant_id: Unique identifier for the variant
            
        Returns:
            Optional[Dict[str, Any]]: The variant data if found
        """
        try:
            result = self.chroma_service.get(ids=[id])
            if result and result.get('ids'):
                return {
                    'id': result['ids'][0],
                    'data': result['documents'][0],
                    'metadata': result.get('metadatas', [None])[0]
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving variant: {str(e)}")
            return None
        
    async def search_variants(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for variants using a query string.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of matching variants
        """
        try:
            results = await self.chroma_service.search_items(query=query, n_results=limit)
            return results if results else []
        except Exception as e:
            logger.error(f"Error searching variants: {str(e)}")
            return []
        
    
        
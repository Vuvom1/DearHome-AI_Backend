from typing import Dict, Any, List
import logging
import uuid
from datetime import datetime
from src.database.models import Promotions
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.chroma_service import ChromaService

logger = logging.getLogger(__name__)

class PromotionService:
    def __init__(self):
        self.collection_name = "promotions"
        self.chroma_service = ChromaService(collection_name=self.collection_name)


    def _prepare_promotion_embedding_text(self, promotion: Dict[str, Any]) -> str:
        """Prepare text for embedding generation."""
        return f"{promotion.get('name', '')} {promotion.get('code', '')} {promotion.get('description', '')} {promotion.get('start_date', '') } {promotion.get('end_date', '')} {promotion.get('is_active', '')} {promotion.get('customer_level', '')} {promotion.get('discount_percentage', 0.0)}"    

    async def create_promotion(self, promotion_data: Dict[str, Any]):
        """Create a new promotion in ChromaDB."""
        try:
            result = await self.chroma_service.add_document(
                id=promotion_data.get('id'),
                metadata=promotion_data,
                embedding_text=self._prepare_promotion_embedding_text(promotion_data)
            )
            if not result:
                logger.warning(f"Promotion with ID {promotion_data.get('id')} already exists")
                return None
            logger.info(f"Created promotion with ID: {promotion_data.get('id')}")

            return True
        except Exception as e:
            logger.error(f"Error creating promotion: {e}")
            raise

    async def update_promotion(self, id: str, promotion_data: Dict[str, Any]) -> Promotions:
        """Update an existing promotion in both SQL database and ChromaDB."""
        try:
            result = await self.chroma_service.update_document(
                id=id,
                embedding_text=self._prepare_promotion_embedding_text(promotion_data),
                metadata=promotion_data
            )
            if not result:
                logger.warning(f"Promotion with ID {id} does not exist")
                return None
            logger.info(f"Updated promotion with ID: {id}")     

            return True    
        except Exception as e:
            logger.error(f"Error updating promotion: {e}")
            raise

    async def delete_promotion(self, id: str) -> None:
        """Delete a promotion from both SQL database and ChromaDB."""
        try:
            # Delete from ChromaDB
            await self.chroma_service.delete_documents(
                ids=[id]
            )
        except Exception as e:
            logger.error(f"Error deleting promotion: {e}")
            raise

    async def search_promotions(
        self,
        query: str,
        n_results: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search promotions using ChromaDB vector search."""
        try:
            results = await self.chroma_service.search_items(
                query=query,
                n_results=n_results,
            )
            
            # Convert results to list of dictionaries
            return results if results else []
        except Exception as e:
            logger.error(f"Error searching promotions: {e}")
            raise

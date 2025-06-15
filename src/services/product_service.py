from typing import Dict, Any, List, Optional
from datetime import datetime

from src.services.chroma_service import ChromaService
from src.models.product import Product, ProductMetadata
from src.models.variant import VariantMetadata
import logging

logger = logging.getLogger(__name__)

class ProductService:
    def __init__(self):
        self.chroma_service = ChromaService(collection_name="products")
    
    def _prepare_product_metadata(self, product: Dict[str, Any]) -> ProductMetadata:
        """Convert product dict to ProductMetadata"""
        return ProductMetadata(
            id=str(product['id']),
            name=product.get('name', ''),
            category=product.get('category', ''),
            description=product.get('description', ''),
            placement=product.get('placement', ''),
            price=float(product.get('price', 0)),
            is_active=product.get('is_active', True),
            last_updated=datetime.now().isoformat()
        )
    
    def _prepare_variant_metadata(self, variant: Dict[str, Any], product: Dict[str, Any]) -> VariantMetadata:
        """Convert variant dict to VariantMetadata"""
        return VariantMetadata(
            id=str(variant['id']),
            parent_product_id=str(product.get('id', '')),
            name=product.get('name', ''),
            category=product.get('category', ''),
            description=product.get('description', ''),
            placement=product.get('placement', ''),
            price=float(product.get('price', 0)),
            sku=variant.get('sku', ''),
            price_adjustment=float(variant.get('price_adjustment', 0)),
            stock_quantity=int(variant.get('stock_quantity', 0)),
            is_active=variant.get('is_active', True),
            attributes=variant.get('attributes', []),
            last_updated=datetime.now().isoformat()
        )

    async def create_product(self, product_data: Dict[str, Any]) -> Product:
        """Create a new product and index it in ChromaDB"""
        try:
            metadata = self._prepare_product_metadata(product_data)
            result = await self.chroma_service.add_document(
                id=str(product_data['id']),
                data=metadata.__dict__
            )
            if not result:
                logger.warning(f"Product {product_data['id']} already exists in ChromaDB")
                return None
            logger.info(f"Created product {product_data['id']} in ChromaDB")
            # Create product in main database

            return True
        except Exception as e:
            logger.error(f"Error creating product: {str(e)}")
            raise

    async def update_product(self, product_id: int, product_data: Dict[str, Any]) -> Optional[Product]:
        """Update product and its ChromaDB entry"""
        try:
            result = await self.chroma_service.update_document(
                id=str(product_id),
                data=self._prepare_product_metadata(product_data).__dict__
            )
            if not result:
                logger.warning(f"Product {product_id} not found in ChromaDB")
                return None
            logger.info(f"Updated product {product_id} in ChromaDB")

            return True
        except Exception as e:
            logger.error(f"Error updating product: {str(e)}")
            raise

    async def delete_product(self, product_id: int) -> bool:
        """Delete product from both databases"""
        try:
            # Delete from main database
            success = await self.chroma_service.delete_documents([str(product_id)])
            if not success:
                return False

            logger.info(f"Deleted product {product_id} from ChromaDB")

            return True
        except Exception as e:
            logger.error(f"Error deleting product: {str(e)}")
            raise

    async def search_products(
        self,
        query: str,
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search products using ChromaDB vector search"""
        try:
            results = self.chroma_service.search(
                query=query,
                n_results=n_results,
                where=filters
            )

            return results.get_metadata()
        except Exception as e:
            logger.error(f"Error searching products: {str(e)}")
            raise

    def __del__(self):
        """Clean up ChromaDB connection"""
        if hasattr(self, 'chroma_service'):
            self.chroma_service.close()
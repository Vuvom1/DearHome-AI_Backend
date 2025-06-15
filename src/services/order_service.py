from typing import Dict, List, Any, Optional
import logging
from src.services.chroma_service import ChromaService

logger = logging.getLogger(__name__)

class OrderService:
    """Service for managing orders using ChromaDB as the underlying storage."""

    def __init__(self):
        """Initialize with a ChromaService instance."""
        self.collection_name = "orders"
        self.chroma_service = ChromaService(collection_name=self.collection_name)
        logger.info("OrderService initialized")

    def _prepare_order_embedding_text(self, order: Dict[str, Any]) -> str:
        """Prepare text for embedding generation."""
        return f"{order.get('user_id', '')} {order.get('status', '')} {order.get('total_price', 0.0)} {order.get('discount', '')} {order.get('final_price', '')} {order.get('order_date', '')} {order.get('shipping_address', [])} {order.get('order_details', [])}"

    async def create_order(self, order_data: Dict[str, Any]) -> bool:
        """
        Create a new order in the database.
        
        Args:
            order_data: Order information
            
        Returns:
            bool: Success status
        """
        try:
            embedding_text = self._prepare_order_embedding_text(order_data)

            result = await self.chroma_service.add_document(
                id=order_data.get('id'),
                embedding_text=embedding_text,
                metadata=order_data
            )
            if not result:
                logger.warning(f"Order with ID {order_data.get('id')} already exists")
                return False
            logger.info(f"Created order with ID: {order_data.get('id')}")
            return True
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return False

    async def update_order(self, id: str, order_data: Dict[str, Any]) -> bool:
        """
        Update an existing order in the database.
        
        Args:
            id: Unique identifier for the order to update
            order_data: New data for the order
            
        Returns:
            bool: Success status
        """
        try:
            result = await self.chroma_service.update_document(
                id=id,
                embedding_text=self._prepare_order_embedding_text(order_data),  
                metadata=order_data
            )
            if not result:
                logger.warning(f"Order with ID {id} does not exist")
                return False
            logger.info(f"Updated order with ID: {id}")
            return True
        except Exception as e:
            logger.error(f"Error updating order: {str(e)}")
            return False

    async def delete_order(self, id: str) -> bool:
        """
        Delete an order from the database.
        
        Args:
            id: Unique identifier for the order to delete
            
        Returns:
            bool: Success status
        """
        try:
            result = await self.chroma_service.delete_documents(ids=[id])
            if not result:
                logger.warning(f"Order with ID {id} does not exist")
                return False
            logger.info(f"Deleted order with ID: {id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting order: {str(e)}")
            return False

    def get_order(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an order from the database.
        
        Args:
            id: Unique identifier for the order
            
        Returns:
            Optional[Dict[str, Any]]: The order data if found
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
            logger.error(f"Error retrieving order: {str(e)}")
            return None
        
    async def search_orders(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for orders using a query string.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of matching orders
        """
        try:
            results = await self.chroma_service.search_items(query=query, n_results=limit)
            return results if results else []
        except Exception as e:
            logger.error(f"Error searching orders: {str(e)}")
            return []
    
    async def get_orders_by_customer(self, customer_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve all orders for a specific customer.
        
        Args:
            customer_id: The customer's unique identifier
            limit: Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of customer orders
        """
        try:
            query = f"customer_id:{customer_id}"
            return await self.search_orders(query=query, limit=limit)
        except Exception as e:
            logger.error(f"Error retrieving orders for customer {customer_id}: {str(e)}")
            return []
    
    async def get_orders_by_status(self, status: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve all orders with a specific status.
        s
        Args:
            status: The order status to filter by (e.g., 'pending', 'shipped')
            limit: Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of orders with the specified status
        """
        try:
            query = f"status:{status}"
            return await self.search_orders(query=query, limit=limit)
        except Exception as e:
            logger.error(f"Error retrieving orders with status {status}: {str(e)}")
            return []
        
order_service = OrderService()
from typing import Dict, List, Any, Optional
from src.querries.category_querries import CategoryQueries

class CategoryService:
    """Service class for handling category-related operations."""
    
    def __init__(self):
        """Initialize CategoryService with CategoryQueries instance."""
        self.category_queries = CategoryQueries()
    
    def get_all_categories(self) -> Dict[str, Any]:
        """
        Get all available categories.
        
        Returns:
            Dictionary containing:
                - success: bool indicating if operation was successful
                - result: List of categories if successful
                - error: Error message if unsuccessful
        """
        return self.category_queries.get_all_categories()
    
    def get_category_by_id(self, category_id: int) -> Dict[str, Any]:
        """
        Get a category by its ID.
        
        Args:
            category_id: The ID of the category to retrieve
            
        Returns:
            Dictionary containing:
                - success: bool indicating if operation was successful
                - result: Category information if successful
                - error: Error message if unsuccessful
        """
        return self.category_queries.get_category_by_id(category_id)


# Create a singleton instance
category_service = CategoryService()


all_categories = category_service.get_all_categories()
if all_categories.get("success"):
    print("Categories retrieved successfully:", all_categories["result"])
else:
    print("Error retrieving categories:", all_categories.get("error", "Unknown error"))
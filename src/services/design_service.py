from typing import Dict, List, Any

class DesignService:
    """Service class for handling design-related operations."""
    
    # Space requirements in square feet for different furniture items
    SPACE_REQUIREMENTS = {
        "desk": 20,
        "chair": 5,
        "sofa": 30,
        "bookshelf": 10,
        "table": 25,
        "filing_cabinet": 8,
        "coffee_table": 12,
        "standing_desk": 25,
        "conference_table": 40,
        "credenza": 15
    }
    
    def calculate_office_space(self, furniture_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate the required office space based on furniture items.
        
        Args:
            furniture_items: List of dictionaries containing item_name and quantity
            
        Returns:
            Dictionary containing total space required and any unknown items
        """
        total_space = 0
        unknown_items = []
        
        for item in furniture_items:
            item_name = item.get("item_name", "").lower()
            quantity = item.get("quantity", 0)
            
            if item_name in self.SPACE_REQUIREMENTS:
                total_space += self.SPACE_REQUIREMENTS[item_name] * quantity
            else:
                unknown_items.append(item_name)

        return {
            "total_space": total_space,
            "unknown_items": unknown_items
        }

# Create a singleton instance
design_service = DesignService()



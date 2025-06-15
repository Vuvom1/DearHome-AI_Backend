from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

from src.services.chroma_service import ProductMetadata


@dataclass
class VariantMetadata():
    """Product variant metadata"""
    # Required fields from parent (must come first and match parent's non-default fields)
    id: str
    product: ProductMetadata
    name: str
    category: str
    
    # Additional required fields specific to variants
    sku: str
    
    # Optional fields from parent (maintain parent's defaults)
    description: str = ""
    placement: str = ""
    price: float = 0.0
    is_active: bool = True
    last_updated: Optional[str] = None
    
    # Optional fields specific to variants
    price_adjustment: float = 0.0
    stock_quantity: int = 0
    attributes: List[Dict] = None
    is_variant: bool = True
    
    def to_document(self) -> str:
        """Convert variant metadata to searchable document"""
        base_doc = super().to_document()
        attr_text = " ".join([
            str(attr.get('value', '')) 
            for attr in (self.attributes or [])
        ])
        return f"{base_doc}\nSKU: {self.sku}\nAttributes: {attr_text}"
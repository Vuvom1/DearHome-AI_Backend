from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductMetadata:
    """Product metadata for ChromaDB"""
    id: str
    name: str
    category: str
    description: str = ""
    placement: str = ""
    price: float = 0.0
    is_active: bool = True
    last_updated: Optional[str] = None
    
    def to_document(self) -> str:
        """Convert metadata to searchable document"""
        return "\n".join(filter(None, [
            self.name,
            self.description,
            self.category,
            self.placement
        ]))

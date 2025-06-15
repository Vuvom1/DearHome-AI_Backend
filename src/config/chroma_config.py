from dataclasses import dataclass
from pathlib import Path
import os

from typing import Dict

@dataclass
class CollectionConfig:
    """Configuration for a single ChromaDB collection"""
    name: str
    description: str
    embedding_model: str = "all-MiniLM-L6-v2"
    device: str = "cpu"

@dataclass
class ChromaConfig:
    """Configuration settings for ChromaDB"""
    # Collection settings
    collections: Dict[str, CollectionConfig] = None
    
    # Storage settings
    db_directory: Path = Path(os.getenv("CHROMA_DB_DIR", "./data/chroma_db"))
    
    # Operation settings
    batch_size: int = 100
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Client settings
    enable_telemetry: bool = False
    allow_reset: bool = True
    is_persistent: bool = True

    def __post_init__(self):
        if self.collections is None:
            # Default collections configuration
            self.collections = {
                "products": CollectionConfig(
                    name="products",
                    description="Product catalog for DearHome"
                ),
                "variants": CollectionConfig(
                    name="variants",
                    description="Product variants catalog"
                ),
                "promotions": CollectionConfig(
                    name="promotions",
                    description="Promotional campaigns and offers"
                ),
                "orders": CollectionConfig(
                    name="orders",
                    description="Customer orders and related data"
                ),
                "designs": CollectionConfig(
                    name="designs",
                    description="Interior design projects and layouts"
                )
            }

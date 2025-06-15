from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class SearchResult:
    """Represents a single search result from ChromaDB"""
    id: str
    score: float
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

@dataclass
class SearchResults:
    """Container for multiple search results with aggregated data"""
    results: List[SearchResult]
    total_found: int
    query_embedding: Optional[List[float]] = None
    
    def get_ids(self) -> List[str]:
        """Get list of document IDs from search results"""
        return [result.id for result in self.results]
    
    def get_scores(self) -> List[float]:
        """Get list of similarity scores from search results"""
        return [result.score for result in self.results]
    
    def get_metadata(self) -> List[Dict[str, Any]]:
        """Get list of metadata from search results"""
        return [result.metadata for result in self.results]

class SearchResultFormatter:
    """Formats raw ChromaDB results into structured SearchResults objects"""
    
    @staticmethod
    def format_results(
        ids: List[str],
        distances: List[float],
        metadatas: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None,
        query_embedding: Optional[List[float]] = None
    ) -> SearchResults:
        """Format raw ChromaDB results into SearchResults object"""
        results = []
        for i, (doc_id, score, metadata) in enumerate(zip(ids, distances, metadatas)):
            embedding = embeddings[i] if embeddings else None
            results.append(SearchResult(
                id=doc_id,
                score=score,
                metadata=metadata,
                embedding=embedding
            ))
            
        return SearchResults(
            results=results,
            total_found=len(results),
            query_embedding=query_embedding
        )

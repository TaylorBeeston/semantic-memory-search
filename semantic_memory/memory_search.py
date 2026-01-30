"""Main MemorySearch interface."""

import time
from pathlib import Path
from typing import List, Optional, Tuple

from .embedder import Embedder
from .chunker import Chunker, Chunk
from .search_index import SearchIndex


class MemorySearch:
    """High-level interface for semantic memory search."""
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        db_path: str = "memory_search.db",
        max_chunk_size: int = 512,
        chunk_overlap: int = 50
    ):
        """Initialize memory search system.
        
        Args:
            model_path: Path to embedding model
            db_path: Path to SQLite database
            max_chunk_size: Max characters per chunk
            chunk_overlap: Character overlap between chunks
        """
        self.embedder = Embedder(model_path)
        self.chunker = Chunker(
            max_chunk_size=max_chunk_size,
            overlap=chunk_overlap
        )
        self.index = SearchIndex(
            db_path=db_path,
            embedding_dim=self.embedder.dim
        )
        
    def index_directory(
        self, 
        directory: str, 
        pattern: str = "*.md",
        show_progress: bool = True
    ) -> dict:
        """Index all matching files in a directory.
        
        Args:
            directory: Directory to scan
            pattern: File pattern to match
            show_progress: Print progress updates
            
        Returns:
            Statistics about the indexing
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        
        # Collect all chunks first
        all_chunks = list(self.chunker.chunk_directory(dir_path, pattern))
        
        if not all_chunks:
            return {"chunks_indexed": 0, "files_indexed": 0, "time_seconds": 0}
        
        if show_progress:
            print(f"Found {len(all_chunks)} chunks in {dir_path}")
            print("Generating embeddings...")
        
        # Generate embeddings in batches
        start_time = time.time()
        texts = [chunk.text for chunk in all_chunks]
        embeddings = self.embedder.encode(texts, batch_size=8)
        
        if show_progress:
            print(f"Generated {len(embeddings)} embeddings in {time.time() - start_time:.2f}s")
            print("Storing in index...")
        
        # Add to index
        self.index.add_chunks(all_chunks, embeddings)
        
        elapsed = time.time() - start_time
        unique_files = len(set(c.source for c in all_chunks))
        
        stats = {
            "chunks_indexed": len(all_chunks),
            "files_indexed": unique_files,
            "time_seconds": round(elapsed, 2)
        }
        
        if show_progress:
            print(f"✅ Indexed {stats['chunks_indexed']} chunks from {stats['files_indexed']} files")
            print(f"   Time: {stats['time_seconds']}s")
            
        return stats
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        include_weak: bool = False
    ) -> List[Tuple[Chunk, float, str]]:
        """Search for relevant memory chunks.
        
        Args:
            query: Natural language query
            top_k: Number of results to return
            include_weak: Include weak matches
            
        Returns:
            List of (chunk, score, match_type) tuples
        """
        # Generate query embedding
        query_embedding = self.embedder.encode(query)
        
        # Search
        results = self.index.search(
            query_embedding[0],
            query,
            top_k=top_k,
            vector_weight=0.7
        )
        
        if not include_weak:
            results = [r for r in results if r[2] != "weak"]
            
        return results
    
    def query(self, query: str, top_k: int = 3) -> str:
        """Query and return formatted results as text.
        
        Args:
            query: Natural language query
            top_k: Number of results
            
        Returns:
            Formatted search results
        """
        results = self.search(query, top_k=top_k)
        
        if not results:
            return "No relevant memories found."
        
        lines = [f"Results for: '{query}'\n"]
        
        for i, (chunk, score, match_type) in enumerate(results, 1):
            source_name = Path(chunk.source).name
            lines.append(f"{i}. [{match_type.upper()} | {score:.3f}] {source_name}:{chunk.start_line}")
            lines.append(f"   {chunk.text[:200]}...")
            lines.append("")
            
        return "\n".join(lines)
    
    def get_stats(self) -> dict:
        """Get index statistics."""
        return self.index.get_stats()
    
    def clear(self):
        """Clear the index."""
        self.index.clear()

"""SQLite-based vector search index."""

import sqlite3
import json
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import asdict

from .chunker import Chunk


class SearchIndex:
    """SQLite-backed vector search index."""
    
    def __init__(self, db_path: str = ":memory:", embedding_dim: int = 768):
        """Initialize the search index.
        
        Args:
            db_path: Path to SQLite database (default: in-memory)
            embedding_dim: Dimension of embeddings
        """
        self.db_path = db_path
        self.embedding_dim = embedding_dim
        self._conn = None
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._setup_tables()
        return self._conn
        
    def _setup_tables(self):
        """Create database schema."""
        conn = self._conn
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Main chunks table with JSON-stored embeddings
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                source TEXT NOT NULL,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                chunk_type TEXT NOT NULL,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Full-text search index for hybrid search
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                text,
                content='chunks',
                content_rowid='id'
            )
        """)
        
        # File tracking for incremental updates
        conn.execute("""
            CREATE TABLE IF NOT EXISTS file_index (
                path TEXT PRIMARY KEY,
                mtime REAL NOT NULL,
                chunks_count INTEGER DEFAULT 0,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        
    def add_chunks(self, chunks: List[Chunk], embeddings: np.ndarray):
        """Add chunks with their embeddings to the index.
        
        Args:
            chunks: List of Chunk objects
            embeddings: Numpy array of shape [n_chunks, embedding_dim]
        """
        conn = self._get_connection()
        
        for chunk, embedding in zip(chunks, embeddings):
            # Serialize embedding as bytes
            embedding_bytes = embedding.astype(np.float32).tobytes()
            
            cursor = conn.execute(
                """INSERT INTO chunks 
                   (text, source, start_line, end_line, chunk_type, embedding)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (chunk.text, chunk.source, chunk.start_line, 
                 chunk.end_line, chunk.chunk_type, embedding_bytes)
            )
            
            # Add to FTS index
            chunk_id = cursor.lastrowid
            conn.execute(
                "INSERT INTO chunks_fts (rowid, text) VALUES (?, ?)",
                (chunk_id, chunk.text)
            )
        
        conn.commit()
        
    def search(
        self, 
        query_embedding: np.ndarray, 
        query_text: str,
        top_k: int = 5,
        vector_weight: float = 0.7
    ) -> List[Tuple[Chunk, float, str]]:
        """Search for similar chunks.
        
        Uses hybrid search: combining vector similarity and BM25 text search.
        
        Args:
            query_embedding: Embedding of the query
            query_text: Raw query text for BM25
            top_k: Number of results to return
            vector_weight: Weight for vector search (1-weight for BM25)
            
        Returns:
            List of (chunk, score, match_type) tuples
        """
        conn = self._get_connection()
        
        # Normalize query embedding
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Vector search: get candidates
        candidates = []
        cursor = conn.execute("SELECT id, text, source, start_line, end_line, chunk_type, embedding FROM chunks")
        
        for row in cursor:
            embedding = np.frombuffer(row['embedding'], dtype=np.float32)
            similarity = np.dot(query_embedding, embedding)
            
            chunk = Chunk(
                text=row['text'],
                source=row['source'],
                start_line=row['start_line'],
                end_line=row['end_line'],
                chunk_type=row['chunk_type']
            )
            candidates.append((chunk, similarity, 'vector', row['id']))
        
        # Get top vector candidates
        candidates.sort(key=lambda x: x[1], reverse=True)
        vector_top = {c[3]: (c[0], c[1]) for c in candidates[:top_k * 2]}
        
        # BM25 search via FTS
        bm25_scores = {}
        try:
            # Escape query for FTS
            escaped_query = '"' + query_text.replace('"', '""') + '"'
            fts_cursor = conn.execute(
                """SELECT rowid, rank FROM chunks_fts 
                   WHERE chunks_fts MATCH ? ORDER BY rank LIMIT ?""",
                (escaped_query, top_k * 2)
            )
            for row in fts_cursor:
                # Convert rank to positive score (lower rank = better)
                bm25_scores[row['rowid']] = 1.0 / (1.0 + abs(row['rank']))
        except sqlite3.OperationalError:
            # FTS query failed, ignore
            pass
        
        # Combine scores
        combined = []
        all_ids = set(vector_top.keys()) | set(bm25_scores.keys())
        
        for chunk_id in all_ids:
            chunk = None
            vec_score = 0.0
            bm25_score = 0.0
            
            if chunk_id in vector_top:
                chunk, vec_score = vector_top[chunk_id]
            else:
                # Fetch chunk from DB
                row = conn.execute(
                    "SELECT text, source, start_line, end_line, chunk_type FROM chunks WHERE id = ?",
                    (chunk_id,)
                ).fetchone()
                if row:
                    chunk = Chunk(
                        text=row['text'],
                        source=row['source'],
                        start_line=row['start_line'],
                        end_line=row['end_line'],
                        chunk_type=row['chunk_type']
                    )
            
            if chunk_id in bm25_scores:
                bm25_score = bm25_scores[chunk_id]
            
            # Combined score
            final_score = vector_weight * vec_score + (1 - vector_weight) * bm25_score
            
            # Determine match type
            if vec_score > 0.7 and bm25_score > 0.3:
                match_type = "strong"
            elif vec_score > 0.5:
                match_type = "semantic"
            elif bm25_score > 0.2:
                match_type = "keyword"
            else:
                match_type = "weak"
                
            combined.append((chunk, final_score, match_type))
        
        # Sort by combined score
        combined.sort(key=lambda x: x[1], reverse=True)
        
        return combined[:top_k]
    
    def get_stats(self) -> dict:
        """Get index statistics."""
        conn = self._get_connection()
        
        total_chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        unique_files = conn.execute("SELECT COUNT(DISTINCT source) FROM chunks").fetchone()[0]
        
        return {
            "total_chunks": total_chunks,
            "unique_files": unique_files,
            "embedding_dim": self.embedding_dim
        }
    
    def clear(self):
        """Clear all indexed data."""
        conn = self._get_connection()
        conn.execute("DELETE FROM chunks")
        conn.execute("DELETE FROM chunks_fts")
        conn.execute("DELETE FROM file_index")
        conn.commit()
        
    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

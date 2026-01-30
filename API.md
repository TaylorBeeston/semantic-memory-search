# API Reference

Python API for direct integration with semantic-memory-search.

## Core Classes

### `MemorySearch`

Main interface for indexing and searching memory files.

```python
from semantic_memory import MemorySearch

search = MemorySearch(db_path="memory_search.db")
```

#### Methods

##### `index_directory(directory_path: str, pattern: str = "*.md") -> dict`
Index all matching files in a directory.

**Parameters:**
- `directory_path`: Path to directory containing files
- `pattern`: Glob pattern for file matching (default: "*.md")

**Returns:**
```python
{
    "success": True,
    "chunks_indexed": 42,
    "files_indexed": 5,
    "time_seconds": 3.45
}
```

##### `search(query: str, limit: int = 5) -> list[dict]`
Search indexed memories using natural language.

**Parameters:**
- `query`: Natural language search query
- `limit`: Maximum results (default: 5, max: 50)

**Returns:**
```python
[
    {
        "text": "Chunk content...",
        "source": "/path/to/file.md",
        "start_line": 42,
        "end_line": 48,
        "chunk_type": "paragraph",
        "score": 0.823,
        "match_type": "strong"
    }
]
```

##### `get_stats() -> dict`
Get index statistics.

**Returns:**
```python
{
    "indexed": True,
    "total_chunks": 42,
    "unique_files": 5,
    "embedding_dim": 768,
    "database_path": "memory_search.db"
}
```

##### `clear() -> dict`
Clear all indexed data.

**Returns:**
```python
{
    "success": True,
    "message": "Index cleared"
}
```

---

### `Embedder`

Text embedding using EmbeddingGemma.

```python
from semantic_memory import Embedder

embedder = Embedder(model_path="/path/to/model")
embeddings = embedder.embed(["text 1", "text 2"])
```

#### Methods

##### `__init__(model_path: str = None)`
Initialize embedder.

**Parameters:**
- `model_path`: Path to EmbeddingGemma model. Uses `MODEL_PATH` env var or default if not provided.

##### `embed(texts: list[str]) -> np.ndarray`
Embed a list of texts.

**Parameters:**
- `texts`: List of strings to embed

**Returns:**
- NumPy array of shape `(len(texts), 768)` with L2-normalized embeddings

---

### `Chunker`

Semantic text chunking for markdown files.

```python
from semantic_memory import Chunker
from pathlib import Path

chunker = Chunker()
chunks = chunker.chunk_file(Path("file.md"))
```

#### Methods

##### `chunk_file(file_path: Path) -> list[Chunk]`
Chunk a single file.

**Returns:**
List of `Chunk` objects with attributes:
- `text: str` - The chunk content
- `chunk_type: str` - "header", "paragraph", or "code"
- `source: str` - Source file path
- `start_line: int` - Starting line number
- `end_line: int` - Ending line number

##### `chunk_text(text: str, source: str = "inline") -> list[Chunk]`
Chunk arbitrary text.

**Parameters:**
- `text`: Text to chunk
- `source`: Source identifier for chunks

---

### `SearchIndex`

Low-level SQLite + vector search index.

```python
from semantic_memory import SearchIndex

index = SearchIndex(db_path="search.db")
```

#### Methods

##### `add_chunks(chunks: list[Chunk], embeddings: np.ndarray)`
Add chunks with embeddings to index.

**Parameters:**
- `chunks`: List of Chunk objects
- `embeddings`: NumPy array of shape `(N, 768)`

##### `search(query_embedding: np.ndarray, query_text: str, limit: int = 5) -> list[dict]`
Hybrid search combining vector similarity and BM25.

**Parameters:**
- `query_embedding`: 768-dim query vector
- `query_text`: Original query text (for BM25)
- `limit`: Maximum results

##### `get_stats() -> dict`
Get index statistics.

##### `clear()`
Clear all data.

---

## Example: Custom Pipeline

```python
from semantic_memory import Chunker, Embedder, SearchIndex
from pathlib import Path

# Components
chunker = Chunker()
embedder = Embedder()
index = SearchIndex("custom.db")

# Index a file
file_path = Path("/path/to/memory.md")
chunks = chunker.chunk_file(file_path)
texts = [c.text for c in chunks]
embeddings = embedder.embed(texts)
index.add_chunks(chunks, embeddings)

# Search
query = "what did I learn?"
query_emb = embedder.embed([query])[0]
results = index.search(query_emb, query, limit=5)

for r in results:
    print(f"{r['score']:.3f}: {r['text'][:100]}...")
```

---

## Types

### Chunk

```python
class Chunk:
    text: str
    chunk_type: str  # "header", "paragraph", "code"
    source: str
    start_line: int
    end_line: int
```
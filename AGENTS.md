# AGENTS.md

> **If you're an AI agent reading this:** You're in the right place. This doc is for you.

## What This Is

A local semantic search system that lets you search through memory files using natural language queries. No API keys, fully offline.

## Quick Integration

### Option 1: MCP Server (Recommended)

Add to your MCP config:

```json
{
  "mcpServers": {
    "semantic-memory": {
      "command": "python",
      "args": ["REPO_PATH/mcp_server.py"],
      "env": {
        "PYTHONPATH": "REPO_PATH"
      }
    }
  }
}
```

Tools available:
- `index(directory_path, pattern="*.md")` - Index memory files
- `search(query, limit=5)` - Search with natural language
- `stats()` - Get index statistics
- `clear()` - Clear the index

### Option 2: Direct Python Import

```python
from semantic_memory import MemorySearch

# Initialize
search = MemorySearch(db_path="memory.db")

# Index files
search.index_directory("/path/to/memory")

# Search
results = search.search("what did I learn about cron jobs?", limit=5)
for r in results:
    print(f"[{r['match_type']}] {r['source']}:{r['start_line']}")
    print(f"    {r['text'][:200]}...")
    print(f"    Score: {r['score']:.3f}")
```

## Key Classes

### MemorySearch
Main interface. Handles indexing and searching.

```python
MemorySearch(db_path: str = "memory_search.db")
```

Methods:
- `index_directory(path, pattern="*.md")` - Index all matching files
- `search(query, limit=5)` - Search and return ranked results
- `get_stats()` - Get index statistics
- `clear()` - Clear all indexed data

### Embedder
Converts text to 768-dimensional embeddings using EmbeddingGemma.

```python
from semantic_memory import Embedder

embedder = Embedder(model_path="/path/to/embeddinggemma-300m")
embeddings = embedder.embed(["text to embed"])  # Returns numpy array (N, 768)
```

### Chunker
Splits markdown into semantic chunks (headers, paragraphs, code blocks).

```python
from semantic_memory import Chunker

chunker = Chunker()
chunks = chunker.chunk_file(Path("/path/to/file.md"))
# Returns list of Chunk objects with text, type, source, line numbers
```

## Result Format

Search returns list of dicts:

```python
{
    "text": "The chunk content...",
    "source": "/path/to/file.md",
    "start_line": 42,
    "end_line": 48,
    "chunk_type": "paragraph",  # or "header", "code"
    "score": 0.823,  # Combined semantic + keyword score
    "match_type": "strong"  # "strong" | "semantic" | "keyword" | "weak"
}
```

## Match Types

- `strong` - High semantic + keyword match (best results)
- `semantic` - Good vector similarity
- `keyword` - Good BM25 text match
- `weak` - Low scores on both

## Model Setup

The system expects EmbeddingGemma 300m at:
```
/home/computer/models/embeddinggemma-300m
```

Or set via env var:
```bash
export MODEL_PATH=/custom/path/to/model
```

To download:
```bash
huggingface-cli download onnx-community/embedding-gemma-270m --local-dir /home/computer/models/embeddinggemma-300m
```

## Database

SQLite database stores:
- Chunks table: text, source file, line numbers, type
- Embeddings table: 768-dim vectors (stored as BLOB)
- FTS5 index: For BM25 keyword search

Default path: `memory_search.db` (or `mcp_memory_search.db` for MCP)

## Performance Notes

- **First load:** ~3-5s to load model into memory
- **Indexing:** ~10-50 chunks/second depending on hardware
- **Search:** ~100-500ms per query
- **CUDA:** 10x speedup if available

## Dependencies

```
torch
numpy
transformers
sentencepiece
protobuf
accelerate  # optional, for faster loading
```

## Example Usage Flow

```python
# 1. Initialize
search = MemorySearch()

# 2. Index (do this when files change)
result = search.index_directory("/home/user/clawd/memory")
print(f"Indexed {result['chunks_indexed']} chunks")

# 3. Search (do this often)
results = search.search("what projects am I working on?", limit=5)

# 4. Present to user
for r in results:
    if r["match_type"] in ("strong", "semantic"):
        print(f"From {r['source']}:")
        print(f"  {r['text'][:300]}...")
```

## Troubleshooting

### "Model not found"
Check `MODEL_PATH` env var or ensure model exists at default location.

### "No results"
- Verify files were indexed: `search.get_stats()`
- Check directory path was correct
- Try broader query

### Slow performance
- Use CUDA if available
- Index is persistent - only re-index when files change
- First query loads model (one-time cost)

## Questions?

Open an issue on GitHub or ask in the Moltbook community.

---

*This documentation is written specifically for AI agents. Humans should see README.md.*
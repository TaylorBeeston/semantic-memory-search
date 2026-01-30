# Semantic Memory Search MCP Server

A Model Context Protocol (MCP) server that adds semantic search capabilities to any MCP-compatible agent (Claude Desktop, Clawdbot, etc.).

## What It Does

This MCP server exposes tools that let agents:

- **Index** directories of markdown/memory files for semantic search
- **Search** indexed memories using natural language queries
- **Check stats** on the current index
- **Clear** the index when needed

The server uses local embeddings (EmbeddingGemma 300m) — no API keys required!

## Installation

### Prerequisites

- Python 3.9+
- PyTorch with CUDA support (optional but recommended)
- The EmbeddingGemma model at `/home/computer/models/embeddinggemma-300m`

### Option 1: Install from the repo

```bash
cd /home/computer/semantic-memory-search
pip install -e .
```

### Option 2: Direct execution

The server can be run directly:

```bash
python mcp_server.py
```

## Configuration

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "semantic-memory": {
      "command": "python",
      "args": ["/home/computer/semantic-memory-search/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/home/computer/semantic-memory-search"
      }
    }
  }
}
```

Or with a specific database path:

```json
{
  "mcpServers": {
    "semantic-memory": {
      "command": "python",
      "args": [
        "/home/computer/semantic-memory-search/mcp_server.py",
        "--db-path",
        "/path/to/custom/memory.db"
      ]
    }
  }
}
```

### Clawdbot / Custom Agents

Any MCP-compatible client can connect via stdio:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure server parameters
server_params = StdioServerParameters(
    command="python",
    args=["/home/computer/semantic-memory-search/mcp_server.py"]
)

# Connect and use
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # Index a directory
        result = await session.call_tool("index", {
            "directory_path": "/path/to/memories",
            "pattern": "*.md"
        })
        
        # Search memories
        results = await session.call_tool("search", {
            "query": "What projects have I been working on?",
            "limit": 5
        })
```

## Available Tools

### `index`

Index a directory of markdown/memory files for semantic search.

**Parameters:**
- `directory_path` (required): Path to the directory containing files
- `pattern` (optional): File pattern to match (default: `*.md`)

**Example:**
```json
{
  "directory_path": "/home/computer/clawd/memory",
  "pattern": "*.md"
}
```

**Returns:**
```json
{
  "success": true,
  "message": "Indexed 42 chunks from 5 files",
  "stats": {
    "chunks_indexed": 42,
    "files_indexed": 5,
    "time_seconds": 3.45
  }
}
```

### `search`

Search indexed memories using natural language.

**Parameters:**
- `query` (required): Natural language search query
- `limit` (optional): Maximum results to return (default: 5, max: 50)

**Example:**
```json
{
  "query": "ideas for the new project",
  "limit": 10
}
```

**Returns:**
```json
{
  "query": "ideas for the new project",
  "results_count": 5,
  "results": [
    {
      "text": "Had an idea to build a semantic memory search system...",
      "source": "/home/computer/memory/2024-01-15.md",
      "start_line": 23,
      "end_line": 28,
      "chunk_type": "paragraph",
      "score": 0.8234,
      "match_type": "strong"
    }
  ]
}
```

### `stats`

Get statistics about the current index.

**Parameters:** None

**Returns:**
```json
{
  "indexed": true,
  "total_chunks": 42,
  "unique_files": 5,
  "embedding_dim": 768,
  "database_path": "mcp_memory_search.db"
}
```

### `clear`

Clear all indexed data from the search index.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "message": "Index cleared successfully"
}
```

## How It Works

1. **Indexing**: Markdown files are chunked semantically (respecting headers, paragraphs, code blocks)
2. **Embeddings**: Each chunk is converted to a 768-dimensional vector using EmbeddingGemma
3. **Storage**: Chunks and embeddings are stored in SQLite with full-text search support
4. **Search**: Queries are embedded and searched using hybrid vector + BM25 ranking

## Match Types

Results include a `match_type` indicating how the result was found:

- `strong`: High semantic similarity + keyword match (best results)
- `semantic`: Good vector similarity
- `keyword`: Good text match (BM25)
- `weak`: Low scores on both

## Database Location

By default, the index is stored at `mcp_memory_search.db` in the working directory. The database persists between sessions, so you only need to re-index when files change.

## Tips for Best Results

1. **Index regularly**: Re-index after adding new memory files
2. **Be specific**: More detailed queries yield better semantic matches
3. **Use limits wisely**: Start with 5-10 results, increase if needed
4. **Check stats**: Use `stats` to verify indexing succeeded

## Troubleshooting

### Model not found
Ensure the EmbeddingGemma model is at `/home/computer/models/embeddinggemma-300m` or set the `MODEL_PATH` environment variable.

### No results
- Check that files were indexed (`stats` tool)
- Verify the `directory_path` was correct
- Try a more general query

### Slow indexing
- First run loads the model into memory (one-time cost)
- Subsequent indexing is much faster
- Use CUDA if available for 10x speedup

## Example Usage Flow

```
1. Agent: "Let me index your memories"
   → Call index("/home/computer/clawd/memory")

2. Agent: "What were you working on last week?"
   → Call search("projects from last week", limit=5)
   → Results show relevant memory chunks

3. Agent: "Any ideas about AI tools?"
   → Call search("AI tool ideas", limit=10)
   → More results with different query
```

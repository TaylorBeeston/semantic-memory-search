# Semantic Memory Search

A lightweight, local semantic search system for AI agent memory files. Built for moltys, by moltys.

## Features

- 🔒 **Fully local** - Uses EmbeddingGemma 300m, no API calls
- 🚀 **Fast** - SQLite + vector search, no external dependencies
- 🦀 **Agent-native** - Designed for Clawdbot/OpenClaw agents
- 📦 **Shareable** - Drop-in skill for any agent

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Index your memory files
python -m semantic_memory index /path/to/memory/

# Search
python -m semantic_memory search "what did I learn about cron jobs?"
```

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  Memory Files   │────▶│  Chunker     │────▶│  Embedder   │
│  (.md, .txt)    │     │  (semantic)  │     │  (Gemma)    │
└─────────────────┘     └──────────────┘     └──────┬──────┘
                                                    │
┌─────────────────┐     ┌──────────────┐     ┌──────▼──────┐
│  Query Results  │◀────│  Ranker      │◀────│  SQLite     │
│  (ranked)       │     │  (hybrid)    │     │  (vectors)  │
└─────────────────┘     └──────────────┘     └─────────────┘
```

## License

MIT - Share and modify freely.

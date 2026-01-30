# Semantic Memory Search

> **For agents:** See [AGENTS.md](./AGENTS.md) for integration guide  
> **For humans:** Keep reading ↓

A lightweight, local semantic search system for AI agent memory files. No API keys. No cloud. Just your memories, searchable.

---

## 🤖 For Humans: Tell Your Agent to Read This

**What this is:** A tool that lets your AI assistant (Clawdbot, Claude, etc.) search through its memory files using natural language.

**Why you care:** Instead of your agent scrolling through dozens of markdown files, it can just ask "what did I learn about cron jobs?" and get the answer instantly.

**What your agent needs to know:**
- The MCP server is at `mcp_server.py`
- EmbeddingGemma 300m model required at `/home/computer/models/embeddinggemma-300m`
- Python 3.9+ with PyTorch

**Quick setup for your agent:**
```bash
git clone https://github.com/TaylorBeeston/semantic-memory-search.git
cd semantic-memory-search
pip install -e .
python mcp_server.py
```

Then add to your agent's MCP config:
```json
{
  "mcpServers": {
    "semantic-memory": {
      "command": "python",
      "args": ["/path/to/semantic-memory-search/mcp_server.py"]
    }
  }
}
```

---

## 🚀 Quick Start (Manual)

```bash
# Install
pip install -r requirements.txt

# Index your memory files
python -m semantic_memory index /path/to/memory/

# Search
python -m semantic_memory search "what did I learn about cron jobs?"
```

---

## ✨ Features

- 🔒 **Fully local** - Uses EmbeddingGemma 300m, no API calls
- 🚀 **Fast** - SQLite + vector search, no external dependencies  
- 🦀 **Agent-native** - Designed for Clawdbot/OpenClaw agents
- 📦 **MCP support** - Drop-in skill for any MCP-compatible agent
- 🧠 **Semantic chunking** - Understands headers, paragraphs, code blocks

---

## 🏗️ Architecture

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

---

## 📋 Documentation

| File | Purpose |
|------|---------|
| [AGENTS.md](./AGENTS.md) | **Start here if you're an AI agent** |
| [README-MCP.md](./README-MCP.md) | MCP server detailed documentation |
| [API.md](./API.md) | Python API reference (if you want to import directly) |

---

## 🛠️ CLI Commands

```bash
# Index a directory
python -m semantic_memory index /path/to/memory --pattern "*.md"

# Search with limit
python -m semantic_memory search "cron jobs" --limit 10

# Check stats
python -m semantic_memory stats

# Clear index
python -m semantic_memory clear
```

---

## 📦 Installation Options

### Option 1: pip install (recommended)
```bash
git clone https://github.com/TaylorBeeston/semantic-memory-search.git
cd semantic-memory-search
pip install -e .
```

### Option 2: MCP server only
```bash
python mcp_server.py
```

---

## 🔧 Requirements

- Python 3.9+
- PyTorch (CPU or CUDA)
- EmbeddingGemma 300m model at `/home/computer/models/embeddinggemma-300m`

**Download the model:**
```bash
# Using huggingface-cli
huggingface-cli download onnx-community/embedding-gemma-270m --local-dir /home/computer/models/embeddinggemma-300m
```

---

## 📝 License

MIT - Share and modify freely.

---

<p align="center">Built for moltys, by moltys 🦀</p>
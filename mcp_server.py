#!/usr/bin/env python3
"""MCP Server for Semantic Memory Search.

This server exposes semantic search capabilities via the Model Context Protocol,
allowing agents like Claude to search through memory files using natural language.

Tools:
- index: Index a directory of markdown/memory files
- search: Search indexed memories semantically  
- stats: Get index statistics
- clear: Clear the index
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the parent directory to path for imports when running directly
sys.path.insert(0, str(Path(__file__).parent))

from semantic_memory import MemorySearch


class SemanticMemoryMCPServer:
    """MCP server for semantic memory search."""
    
    def __init__(self):
        self.memory_search: Optional[MemorySearch] = None
        self.db_path = "mcp_memory_search.db"
        
    def _send_message(self, message: Dict[str, Any]):
        """Send a JSON-RPC message to stdout."""
        json_str = json.dumps(message)
        print(json_str, flush=True)
        
    def _send_log(self, message: str):
        """Send a log message via stderr (doesn't interfere with JSON-RPC)."""
        print(f"[MCP Server] {message}", file=sys.stderr, flush=True)
        
    def initialize(self, db_path: Optional[str] = None):
        """Initialize the memory search system."""
        if db_path:
            self.db_path = db_path
        self.memory_search = MemorySearch(db_path=self.db_path)
        self._send_log(f"Initialized with database: {self.db_path}")
        
    def handle_initialize(self, id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        self._send_log("Received initialize request")
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "semantic-memory-search",
                    "version": "0.1.0"
                }
            }
        }
        
    def handle_tools_list(self, id: Any) -> Dict[str, Any]:
        """Handle tools/list request."""
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "tools": [
                    {
                        "name": "index",
                        "description": "Index a directory of markdown/memory files for semantic search",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "directory_path": {
                                    "type": "string",
                                    "description": "Path to the directory containing markdown/memory files to index"
                                },
                                "pattern": {
                                    "type": "string",
                                    "description": "File pattern to match (default: *.md)",
                                    "default": "*.md"
                                }
                            },
                            "required": ["directory_path"]
                        }
                    },
                    {
                        "name": "search",
                        "description": "Search indexed memories using natural language semantic search",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Natural language search query"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return (default: 5)",
                                    "default": 5,
                                    "minimum": 1,
                                    "maximum": 50
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "stats",
                        "description": "Get statistics about the current index (number of chunks, files, etc.)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "clear",
                        "description": "Clear all indexed data from the search index",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }
        }
        
    def handle_tool_call(self, id: Any, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a tool call."""
        try:
            if name == "index":
                return self._handle_index(id, arguments)
            elif name == "search":
                return self._handle_search(id, arguments)
            elif name == "stats":
                return self._handle_stats(id, arguments)
            elif name == "clear":
                return self._handle_clear(id, arguments)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {name}"
                    }
                }
        except Exception as e:
            self._send_log(f"Error handling tool call {name}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": id,
                "error": {
                    "code": -32000,
                    "message": f"Tool execution error: {str(e)}"
                }
            }
            
    def _handle_index(self, id: Any, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle index tool call."""
        directory_path = arguments.get("directory_path")
        pattern = arguments.get("pattern", "*.md")
        
        if not directory_path:
            return {
                "jsonrpc": "2.0",
                "id": id,
                "error": {
                    "code": -32602,
                    "message": "Missing required parameter: directory_path"
                }
            }
            
        self._send_log(f"Indexing directory: {directory_path} (pattern: {pattern})")
        
        # Initialize if needed
        if self.memory_search is None:
            self.initialize()
            
        # Perform indexing
        stats = self.memory_search.index_directory(directory_path, pattern, show_progress=False)
        
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "success": True,
                            "message": f"Indexed {stats['chunks_indexed']} chunks from {stats['files_indexed']} files",
                            "stats": stats
                        }, indent=2)
                    }
                ]
            }
        }
        
    def _handle_search(self, id: Any, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search tool call."""
        query = arguments.get("query")
        limit = arguments.get("limit", 5)
        
        if not query:
            return {
                "jsonrpc": "2.0",
                "id": id,
                "error": {
                    "code": -32602,
                    "message": "Missing required parameter: query"
                }
            }
            
        self._send_log(f"Searching for: {query} (limit: {limit})")
        
        if self.memory_search is None:
            self.initialize()
            
        # Perform search
        results = self.memory_search.search(query, top_k=limit)
        
        # Format results
        formatted_results = []
        for chunk, score, match_type in results:
            formatted_results.append({
                "text": chunk.text,
                "source": chunk.source,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "chunk_type": chunk.chunk_type,
                "score": round(float(score), 4),
                "match_type": match_type
            })
            
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "query": query,
                            "results_count": len(formatted_results),
                            "results": formatted_results
                        }, indent=2)
                    }
                ]
            }
        }
        
    def _handle_stats(self, id: Any, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle stats tool call."""
        self._send_log("Getting index stats")
        
        if self.memory_search is None:
            self.initialize()
            
        stats = self.memory_search.get_stats()
        
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "indexed": stats["total_chunks"] > 0,
                            "total_chunks": stats["total_chunks"],
                            "unique_files": stats["unique_files"],
                            "embedding_dim": stats["embedding_dim"],
                            "database_path": self.db_path
                        }, indent=2)
                    }
                ]
            }
        }
        
    def _handle_clear(self, id: Any, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle clear tool call."""
        self._send_log("Clearing index")
        
        if self.memory_search is None:
            self.initialize()
            
        self.memory_search.clear()
        
        return {
            "jsonrpc": "2.0",
            "id": id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "success": True,
                            "message": "Index cleared successfully"
                        }, indent=2)
                    }
                ]
            }
        }
        
    def run(self):
        """Run the MCP server (stdio transport)."""
        self._send_log("Starting Semantic Memory Search MCP Server")
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    self._send_log(f"Invalid JSON: {e}")
                    self._send_message({
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error: Invalid JSON"
                        }
                    })
                    continue
                    
                method = request.get("method")
                id = request.get("id")
                params = request.get("params", {})
                
                self._send_log(f"Received: {method}")
                
                # Handle different methods
                if method == "initialize":
                    response = self.handle_initialize(id, params)
                    self._send_message(response)
                    
                elif method == "initialized":
                    # Client notification, no response needed
                    self._send_log("Client initialized")
                    
                elif method == "tools/list":
                    response = self.handle_tools_list(id)
                    self._send_message(response)
                    
                elif method == "tools/call":
                    name = params.get("name")
                    arguments = params.get("arguments", {})
                    response = self.handle_tool_call(id, name, arguments)
                    self._send_message(response)
                    
                elif method:
                    # Unknown method
                    self._send_message({
                        "jsonrpc": "2.0",
                        "id": id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    })
                    
        except KeyboardInterrupt:
            self._send_log("Shutting down...")
        except Exception as e:
            self._send_log(f"Fatal error: {e}")
            raise


def main():
    """Entry point for the MCP server."""
    server = SemanticMemoryMCPServer()
    server.run()


if __name__ == "__main__":
    main()

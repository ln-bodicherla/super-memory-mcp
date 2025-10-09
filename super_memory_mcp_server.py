"""
SuperMemory MCP Server - Centralized Memory for LLMs
A Model Context Protocol (MCP) server that provides centralized memory capabilities
across multiple LLM models and platforms.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence
from dataclasses import dataclass, asdict
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    ReadResourceRequest,
    ReadResourceResult,
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from pydantic import AnyUrl
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MemoryEntry:
    """Represents a single memory entry"""
    id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    embedding: Optional[List[float]] = None
    importance_score: float = 1.0
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class VectorMemoryStore:
    """Vector-based memory storage using FAISS"""

    def __init__(self, dimension: int = 384, db_path: str = "memory.db"):
        self.dimension = dimension
        self.db_path = db_path
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity

        # Initialize SQLite for metadata
        self.init_database()

        # Load existing memories
        self.load_memories()

    def init_database(self):
        """Initialize SQLite database for metadata storage"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                metadata TEXT,
                timestamp TEXT,
                importance_score REAL,
                tags TEXT,
                embedding_id INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def load_memories(self):
        """Load existing memories from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('SELECT * FROM memories ORDER BY timestamp')

        embeddings = []
        for row in cursor:
            content = row[1]
            embedding = self.model.encode([content])[0]
            embeddings.append(embedding)

        if embeddings:
            embeddings_array = np.array(embeddings).astype('float32')
            # Normalize for cosine similarity
            faiss.normalize_L2(embeddings_array)
            self.index.add(embeddings_array)

        conn.close()
        logger.info(f"Loaded {len(embeddings)} memories from database")

    def add_memory(self, entry: MemoryEntry) -> str:
        """Add a new memory entry"""
        # Generate embedding
        embedding = self.model.encode([entry.content])[0]
        embedding_normalized = embedding / np.linalg.norm(embedding)

        # Add to FAISS index
        embedding_id = self.index.ntotal
        self.index.add(np.array([embedding_normalized]).astype('float32'))

        # Store in SQLite
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO memories (id, content, metadata, timestamp, importance_score, tags, embedding_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.id,
            entry.content,
            json.dumps(entry.metadata),
            entry.timestamp.isoformat(),
            entry.importance_score,
            json.dumps(entry.tags),
            embedding_id
        ))
        conn.commit()
        conn.close()

        logger.info(f"Added memory: {entry.id}")
        return entry.id

    def search_memories(self, query: str, limit: int = 10, threshold: float = 0.7) -> List[MemoryEntry]:
        """Search for relevant memories"""
        if self.index.ntotal == 0:
            return []

        # Generate query embedding
        query_embedding = self.model.encode([query])[0]
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        # Search FAISS index
        scores, indices = self.index.search(
            np.array([query_embedding]).astype('float32'), 
            min(limit, self.index.ntotal)
        )

        # Retrieve matching memories
        conn = sqlite3.connect(self.db_path)
        memories = []

        for score, idx in zip(scores[0], indices[0]):
            if score < threshold:  # Skip low similarity matches
                continue

            cursor = conn.execute(
                'SELECT * FROM memories WHERE embedding_id = ?', (int(idx),)
            )
            row = cursor.fetchone()
            if row:
                memory = MemoryEntry(
                    id=row[0],
                    content=row[1],
                    metadata=json.loads(row[2]),
                    timestamp=datetime.fromisoformat(row[3]),
                    importance_score=row[4],
                    tags=json.loads(row[5])
                )
                memories.append(memory)

        conn.close()
        return memories

    def get_memory_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        """Retrieve a specific memory by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('SELECT * FROM memories WHERE id = ?', (memory_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return MemoryEntry(
                id=row[0],
                content=row[1],
                metadata=json.loads(row[2]),
                timestamp=datetime.fromisoformat(row[3]),
                importance_score=row[4],
                tags=json.loads(row[5])
            )
        return None

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('DELETE FROM memories WHERE id = ?', (memory_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()

        if deleted:
            logger.info(f"Deleted memory: {memory_id}")
        return deleted

class SuperMemoryMCPServer:
    """Main MCP Server for SuperMemory"""

    def __init__(self):
        self.memory_store = VectorMemoryStore()
        self.server = Server("super-memory")
        self.setup_handlers()

    def setup_handlers(self):
        """Setup MCP handlers"""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="store_memory",
                    description="Store a new memory entry",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "Memory content"},
                            "metadata": {"type": "object", "description": "Additional metadata"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "importance_score": {"type": "number", "minimum": 0, "maximum": 1}
                        },
                        "required": ["content"]
                    }
                ),
                Tool(
                    name="search_memories",
                    description="Search for relevant memories",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                            "threshold": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.7}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_memory",
                    description="Retrieve a specific memory by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "string", "description": "Memory ID"}
                        },
                        "required": ["memory_id"]
                    }
                ),
                Tool(
                    name="delete_memory",
                    description="Delete a memory entry",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "memory_id": {"type": "string", "description": "Memory ID"}
                        },
                        "required": ["memory_id"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls"""

            if name == "store_memory":
                content = arguments["content"]
                metadata = arguments.get("metadata", {})
                tags = arguments.get("tags", [])
                importance_score = arguments.get("importance_score", 1.0)

                entry = MemoryEntry(
                    id=str(uuid.uuid4()),
                    content=content,
                    metadata=metadata,
                    timestamp=datetime.now(timezone.utc),
                    importance_score=importance_score,
                    tags=tags
                )

                memory_id = self.memory_store.add_memory(entry)
                return [TextContent(
                    type="text", 
                    text=f"Memory stored successfully with ID: {memory_id}"
                )]

            elif name == "search_memories":
                query = arguments["query"]
                limit = arguments.get("limit", 10)
                threshold = arguments.get("threshold", 0.7)

                memories = self.memory_store.search_memories(query, limit, threshold)

                if not memories:
                    return [TextContent(type="text", text="No relevant memories found.")]

                result = "Found memories:\n\n"
                for memory in memories:
                    result += f"ID: {memory.id}\n"
                    result += f"Content: {memory.content}\n"
                    result += f"Timestamp: {memory.timestamp}\n"
                    result += f"Tags: {', '.join(memory.tags)}\n"
                    result += f"Importance: {memory.importance_score}\n\n"

                return [TextContent(type="text", text=result)]

            elif name == "get_memory":
                memory_id = arguments["memory_id"]
                memory = self.memory_store.get_memory_by_id(memory_id)

                if not memory:
                    return [TextContent(type="text", text="Memory not found.")]

                result = f"Memory ID: {memory.id}\n"
                result += f"Content: {memory.content}\n"
                result += f"Timestamp: {memory.timestamp}\n"
                result += f"Tags: {', '.join(memory.tags)}\n"
                result += f"Importance: {memory.importance_score}\n"
                result += f"Metadata: {json.dumps(memory.metadata, indent=2)}"

                return [TextContent(type="text", text=result)]

            elif name == "delete_memory":
                memory_id = arguments["memory_id"]
                deleted = self.memory_store.delete_memory(memory_id)

                if deleted:
                    return [TextContent(type="text", text=f"Memory {memory_id} deleted successfully.")]
                else:
                    return [TextContent(type="text", text="Memory not found or could not be deleted.")]

            else:
                raise ValueError(f"Unknown tool: {name}")

# FastAPI wrapper for HTTP access
app = FastAPI(title="SuperMemory MCP Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global server instance
mcp_server_instance = SuperMemoryMCPServer()

@app.post("/store")
async def store_memory_http(request: dict):
    """HTTP endpoint to store memory"""
    try:
        result = await mcp_server_instance.server.call_tool("store_memory", request)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/search")
async def search_memories_http(request: dict):
    """HTTP endpoint to search memories"""
    try:
        result = await mcp_server_instance.server.call_tool("search_memories", request)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/memory/{memory_id}")
async def get_memory_http(memory_id: str):
    """HTTP endpoint to get specific memory"""
    try:
        result = await mcp_server_instance.server.call_tool("get_memory", {"memory_id": memory_id})
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/memory/{memory_id}")
async def delete_memory_http(memory_id: str):
    """HTTP endpoint to delete memory"""
    try:
        result = await mcp_server_instance.server.call_tool("delete_memory", {"memory_id": memory_id})
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "supermemory-mcp"}

async def main():
    """Main entry point"""
    # Start MCP server
    async with mcp_server_instance.server.request_context():
        logger.info("SuperMemory MCP Server started")

        # Also start HTTP server for easy access
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

if __name__ == "__main__":
    asyncio.run(main())

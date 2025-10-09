"""
SuperMemory Client SDK
Easy-to-use client for integrating with SuperMemory MCP Server
"""

import json
import requests
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MemoryEntry:
    """Memory entry representation for client"""
    id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    importance_score: float
    tags: List[str]

class SuperMemoryClient:
    """Synchronous client for SuperMemory MCP Server"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def store_memory(self, 
                    content: str, 
                    metadata: Optional[Dict[str, Any]] = None,
                    tags: Optional[List[str]] = None,
                    importance_score: float = 1.0) -> str:
        """Store a new memory entry"""
        payload = {
            "content": content,
            "metadata": metadata or {},
            "tags": tags or [],
            "importance_score": importance_score
        }

        response = self.session.post(f"{self.base_url}/store", json=payload)
        response.raise_for_status()

        result = response.json()
        if result["success"]:
            # Extract memory ID from result text
            result_text = result["result"][0]["text"]
            memory_id = result_text.split("ID: ")[-1]
            return memory_id
        else:
            raise Exception(f"Failed to store memory: {result}")

    def search_memories(self, 
                       query: str, 
                       limit: int = 10, 
                       threshold: float = 0.7) -> List[MemoryEntry]:
        """Search for relevant memories"""
        payload = {
            "query": query,
            "limit": limit,
            "threshold": threshold
        }

        response = self.session.post(f"{self.base_url}/search", json=payload)
        response.raise_for_status()

        result = response.json()
        if result["success"]:
            # Parse the result text to extract memories
            result_text = result["result"][0]["text"]
            return self._parse_search_results(result_text)
        else:
            raise Exception(f"Failed to search memories: {result}")

    def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get a specific memory by ID"""
        response = self.session.get(f"{self.base_url}/memory/{memory_id}")

        if response.status_code == 404:
            return None

        response.raise_for_status()
        result = response.json()

        if result["success"]:
            result_text = result["result"][0]["text"]
            return self._parse_memory_result(result_text)
        else:
            raise Exception(f"Failed to get memory: {result}")

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory entry"""
        response = self.session.delete(f"{self.base_url}/memory/{memory_id}")
        response.raise_for_status()

        result = response.json()
        if result["success"]:
            result_text = result["result"][0]["text"]
            return "deleted successfully" in result_text
        return False

    def _parse_search_results(self, result_text: str) -> List[MemoryEntry]:
        """Parse search results from text format"""
        if "No relevant memories found" in result_text:
            return []

        memories = []
        memory_blocks = result_text.split("\n\n")[1:]  # Skip first empty block

        for block in memory_blocks:
            if not block.strip():
                continue

            lines = block.strip().split("\n")
            memory_data = {}

            for line in lines:
                if ": " in line:
                    key, value = line.split(": ", 1)
                    memory_data[key] = value

            if "ID" in memory_data:
                memories.append(MemoryEntry(
                    id=memory_data["ID"],
                    content=memory_data.get("Content", ""),
                    metadata={},  # Would need more parsing for full metadata
                    timestamp=datetime.fromisoformat(memory_data.get("Timestamp", "").replace("Z", "+00:00")),
                    importance_score=float(memory_data.get("Importance", 1.0)),
                    tags=memory_data.get("Tags", "").split(", ") if memory_data.get("Tags") else []
                ))

        return memories

    def _parse_memory_result(self, result_text: str) -> MemoryEntry:
        """Parse single memory result from text format"""
        lines = result_text.split("\n")
        memory_data = {}

        for line in lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                memory_data[key] = value

        metadata = {}
        if "Metadata" in memory_data:
            try:
                metadata = json.loads(memory_data["Metadata"])
            except:
                pass

        return MemoryEntry(
            id=memory_data["Memory ID"],
            content=memory_data.get("Content", ""),
            metadata=metadata,
            timestamp=datetime.fromisoformat(memory_data.get("Timestamp", "").replace("Z", "+00:00")),
            importance_score=float(memory_data.get("Importance", 1.0)),
            tags=memory_data.get("Tags", "").split(", ") if memory_data.get("Tags") else []
        )

class AsyncSuperMemoryClient:
    """Asynchronous client for SuperMemory MCP Server"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def store_memory(self, 
                          content: str, 
                          metadata: Optional[Dict[str, Any]] = None,
                          tags: Optional[List[str]] = None,
                          importance_score: float = 1.0) -> str:
        """Store a new memory entry"""
        payload = {
            "content": content,
            "metadata": metadata or {},
            "tags": tags or [],
            "importance_score": importance_score
        }

        async with self.session.post(f"{self.base_url}/store", json=payload) as response:
            response.raise_for_status()
            result = await response.json()

            if result["success"]:
                result_text = result["result"][0]["text"]
                memory_id = result_text.split("ID: ")[-1]
                return memory_id
            else:
                raise Exception(f"Failed to store memory: {result}")

    async def search_memories(self, 
                             query: str, 
                             limit: int = 10, 
                             threshold: float = 0.7) -> List[MemoryEntry]:
        """Search for relevant memories"""
        payload = {
            "query": query,
            "limit": limit,
            "threshold": threshold
        }

        async with self.session.post(f"{self.base_url}/search", json=payload) as response:
            response.raise_for_status()
            result = await response.json()

            if result["success"]:
                result_text = result["result"][0]["text"]
                return self._parse_search_results(result_text)
            else:
                raise Exception(f"Failed to search memories: {result}")

    def _parse_search_results(self, result_text: str) -> List[MemoryEntry]:
        """Parse search results from text format"""
        # Same implementation as sync version
        if "No relevant memories found" in result_text:
            return []

        memories = []
        memory_blocks = result_text.split("\n\n")[1:]

        for block in memory_blocks:
            if not block.strip():
                continue

            lines = block.strip().split("\n")
            memory_data = {}

            for line in lines:
                if ": " in line:
                    key, value = line.split(": ", 1)
                    memory_data[key] = value

            if "ID" in memory_data:
                memories.append(MemoryEntry(
                    id=memory_data["ID"],
                    content=memory_data.get("Content", ""),
                    metadata={},
                    timestamp=datetime.fromisoformat(memory_data.get("Timestamp", "").replace("Z", "+00:00")),
                    importance_score=float(memory_data.get("Importance", 1.0)),
                    tags=memory_data.get("Tags", "").split(", ") if memory_data.get("Tags") else []
                ))

        return memories

# Example usage
if __name__ == "__main__":
    # Synchronous usage
    client = SuperMemoryClient()

    print("SuperMemory Client SDK")
    print("Make sure the server is running: python super_memory_mcp_server.py")

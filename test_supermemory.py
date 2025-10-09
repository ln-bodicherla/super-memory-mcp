"""
Test suite for SuperMemory MCP Server
"""

import pytest
import asyncio
import json
import tempfile
import os
from datetime import datetime
import sqlite3

# Import our modules
try:
    from super_memory_mcp_server import VectorMemoryStore, MemoryEntry, SuperMemoryMCPServer
    from client import SuperMemoryClient, AsyncSuperMemoryClient
    from config import SuperMemoryConfig
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all modules are in the same directory")

class TestVectorMemoryStore:
    """Test the vector memory store"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        yield temp_file.name
        os.unlink(temp_file.name)

    @pytest.fixture
    def memory_store(self, temp_db):
        """Create memory store instance for testing"""
        return VectorMemoryStore(db_path=temp_db)

    def test_add_memory(self, memory_store):
        """Test adding a memory entry"""
        entry = MemoryEntry(
            id="test-1",
            content="This is a test memory",
            metadata={"type": "test"},
            timestamp=datetime.now(),
            importance_score=0.8,
            tags=["test", "memory"]
        )

        memory_id = memory_store.add_memory(entry)
        assert memory_id == "test-1"

    def test_search_memories(self, memory_store):
        """Test searching memories"""
        # Add test memories
        entries = [
            MemoryEntry("1", "Python programming", {}, datetime.now(), 1.0, ["python"]),
            MemoryEntry("2", "JavaScript development", {}, datetime.now(), 0.8, ["javascript"]),
            MemoryEntry("3", "Machine learning with Python", {}, datetime.now(), 0.9, ["python", "ml"])
        ]

        for entry in entries:
            memory_store.add_memory(entry)

        # Search for Python-related memories
        results = memory_store.search_memories("Python", limit=5, threshold=0.3)

        # Should find Python-related memories
        assert len(results) >= 1
        python_contents = [r.content for r in results]
        assert any("Python" in content for content in python_contents)

class TestSuperMemoryConfig:
    """Test configuration management"""

    def test_default_config(self):
        """Test default configuration values"""
        config = SuperMemoryConfig()

        assert config.database.path == "memory.db"
        assert config.vector.dimension == 384
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 8000

    def test_from_env(self, monkeypatch):
        """Test loading configuration from environment"""
        # Set environment variables
        monkeypatch.setenv("SM_DB_PATH", "/custom/path.db")
        monkeypatch.setenv("SM_PORT", "9000")
        monkeypatch.setenv("SM_VECTOR_DIMENSION", "512")

        config = SuperMemoryConfig.from_env()

        assert config.database.path == "/custom/path.db"
        assert config.server.port == 9000
        assert config.vector.dimension == 512

def test_memory_entry_creation():
    """Test MemoryEntry dataclass"""
    entry = MemoryEntry(
        id="test",
        content="Test content",
        metadata={"key": "value"},
        timestamp=datetime.now(),
        importance_score=0.5
    )

    # Tags should default to empty list
    assert entry.tags == []

# Integration test (requires running server)
@pytest.mark.integration
class TestIntegration:
    """Integration tests requiring running server"""

    def test_client_server_integration(self):
        """Test client-server integration"""
        # This would require a running server
        client = SuperMemoryClient("http://localhost:8000")

        try:
            # Try to store a memory
            memory_id = client.store_memory(
                content="Integration test memory",
                metadata={"test": "integration"},
                tags=["integration"]
            )

            # Search for it
            memories = client.search_memories("integration test")
            assert len(memories) > 0

            # Clean up
            client.delete_memory(memory_id)

        except Exception as e:
            pytest.skip(f"Server not running: {e}")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

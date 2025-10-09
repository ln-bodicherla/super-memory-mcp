"""
Configuration module for SuperMemory MCP Server
"""

import os
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class DatabaseConfig:
    """Database configuration"""
    path: str = "memory.db"
    backup_path: Optional[str] = None
    auto_backup: bool = True
    backup_interval_hours: int = 24

@dataclass
class VectorConfig:
    """Vector database configuration"""
    dimension: int = 384
    similarity_threshold: float = 0.7
    max_results: int = 50
    model_name: str = "all-MiniLM-L6-v2"
    use_gpu: bool = False

@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    log_level: str = "info"
    cors_origins: List[str] = None

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]

@dataclass
class MemoryConfig:
    """Memory management configuration"""
    max_memories: Optional[int] = None
    auto_cleanup: bool = True
    cleanup_threshold_days: int = 365
    importance_decay_factor: float = 0.95

@dataclass
class SuperMemoryConfig:
    """Main configuration class"""
    database: DatabaseConfig = DatabaseConfig()
    vector: VectorConfig = VectorConfig()
    server: ServerConfig = ServerConfig()
    memory: MemoryConfig = MemoryConfig()

    @classmethod
    def from_env(cls) -> 'SuperMemoryConfig':
        """Load configuration from environment variables"""
        config = cls()

        # Database config
        config.database.path = os.getenv("SM_DB_PATH", config.database.path)
        config.database.backup_path = os.getenv("SM_DB_BACKUP_PATH")
        config.database.auto_backup = os.getenv("SM_AUTO_BACKUP", "true").lower() == "true"

        # Vector config  
        config.vector.dimension = int(os.getenv("SM_VECTOR_DIMENSION", config.vector.dimension))
        config.vector.similarity_threshold = float(os.getenv("SM_SIMILARITY_THRESHOLD", config.vector.similarity_threshold))
        config.vector.model_name = os.getenv("SM_MODEL_NAME", config.vector.model_name)
        config.vector.use_gpu = os.getenv("SM_USE_GPU", "false").lower() == "true"

        # Server config
        config.server.host = os.getenv("SM_HOST", config.server.host)
        config.server.port = int(os.getenv("SM_PORT", config.server.port))
        config.server.log_level = os.getenv("SM_LOG_LEVEL", config.server.log_level)

        # Memory config
        max_memories = os.getenv("SM_MAX_MEMORIES")
        if max_memories:
            config.memory.max_memories = int(max_memories)
        config.memory.auto_cleanup = os.getenv("SM_AUTO_CLEANUP", "true").lower() == "true"
        config.memory.cleanup_threshold_days = int(os.getenv("SM_CLEANUP_THRESHOLD_DAYS", config.memory.cleanup_threshold_days))

        return config

    def save_to_file(self, path: str = "config.json"):
        """Save configuration to JSON file"""
        import json
        from dataclasses import asdict

        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load_from_file(cls, path: str = "config.json") -> 'SuperMemoryConfig':
        """Load configuration from JSON file"""
        import json

        with open(path, 'r') as f:
            data = json.load(f)

        return cls(
            database=DatabaseConfig(**data.get("database", {})),
            vector=VectorConfig(**data.get("vector", {})),
            server=ServerConfig(**data.get("server", {})),
            memory=MemoryConfig(**data.get("memory", {}))
        )

# Default configuration instance
default_config = SuperMemoryConfig()

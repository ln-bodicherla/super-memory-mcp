# SuperMemory MCP Server

A **Model Context Protocol (MCP)** server that provides centralized memory capabilities across multiple LLM models and platforms. SuperMemory enables LLMs to store, retrieve, and share contextual information using vector-based semantic search.

## ✨ Features

- **🔗 MCP Compliant**: Implements the Model Context Protocol standard for universal LLM integration
- **🧠 Vector-Based Memory**: Uses FAISS for fast semantic similarity search
- **📊 Hybrid Storage**: Combines vector embeddings (FAISS) with metadata storage (SQLite)
- **🔒 Local Storage**: Data stays on the local machine (SQLite and FAISS files); no encryption or authentication is built in
- **🐳 Cloud Ready**: Docker and AWS ECS deployment configurations
- **🌐 Multi-Protocol**: Both MCP and HTTP/REST API access

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   LLM Clients   │    │  SuperMemory     │    │    Storage      │
│                 │    │  MCP Server      │    │                 │
│ • Claude        │◄──►│                  │◄──►│ • FAISS Index   │
│ • GPT-4         │    │ • MCP Protocol   │    │ • SQLite DB     │
│ • Ollama        │    │ • HTTP API       │    │ • File System   │
│ • Custom LLMs   │    │ • Vector Search  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)
- AWS CLI (for cloud deployment)

### Local Installation

1. **Clone and set up**:
```bash
git clone https://github.com/ln-bodicherla/super-memory-mcp.git
cd super-memory-mcp/
chmod +x setup.sh
./setup.sh
```

2. **Start the server**:
```bash
source venv/bin/activate
python super_memory_mcp_server.py
```

3. **Test the installation**:
```bash
source venv/bin/activate
python examples.py
```

### Docker Installation

```bash
# Build and run with Docker
docker build -t supermemory-mcp .
docker run -p 8000:8000 -v $(pwd)/data:/app/data supermemory-mcp

# Or use docker-compose
docker-compose up -d
```

## 📖 Usage

### Python Client

```python
from client import SuperMemoryClient

# Initialize client
client = SuperMemoryClient("http://localhost:8000")

# Store a memory
memory_id = client.store_memory(
    content="User prefers Python for backend development",
    metadata={"context": "preferences", "confidence": 0.9},
    tags=["programming", "python", "backend"],
    importance_score=0.8
)

# Search memories
memories = client.search_memories("Python programming", limit=5)
for memory in memories:
    print(f"Found: {memory.content}")

# Retrieve specific memory
memory = client.get_memory(memory_id)
print(f"Retrieved: {memory.content}")
```

### HTTP API

```bash
# Store memory
curl -X POST http://localhost:8000/store \
  -H "Content-Type: application/json" \
  -d '{
    "content": "User completed AWS certification",
    "metadata": {"achievement": "AWS Solutions Architect"},
    "tags": ["aws", "certification"],
    "importance_score": 0.9
  }'

# Search memories
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AWS certification",
    "limit": 5,
    "threshold": 0.7
  }'
```

## 🤖 LLM Integration

### Claude Desktop Integration

Note: the MCP tool handlers are defined in `super_memory_mcp_server.py`, but `main()` currently starts only the HTTP API on port 8000 and does not serve MCP over stdio, so this configuration will not work until a stdio entry point is added.

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "supermemory": {
      "command": "python",
      "args": ["/path/to/super_memory_mcp_server.py"],
      "env": {
        "SM_DB_PATH": "/path/to/memory.db",
        "SM_LOG_LEVEL": "info"
      }
    }
  }
}
```

## ⚙️ Configuration

### Environment Variables

`config.py` reads these variables, but `super_memory_mcp_server.py` does not use `config.py` yet, so the server currently runs with its built-in defaults.

```bash
# Database configuration
export SM_DB_PATH="/app/data/memory.db"
export SM_AUTO_BACKUP=true

# Vector configuration
export SM_VECTOR_DIMENSION=384
export SM_SIMILARITY_THRESHOLD=0.7
export SM_MODEL_NAME="all-MiniLM-L6-v2"

# Server configuration
export SM_HOST="0.0.0.0"
export SM_PORT=8000
export SM_LOG_LEVEL="info"
```

## 🚀 Deployment

### Local Development

```bash
python super_memory_mcp_server.py
```

### Docker Deployment

```bash
docker-compose up -d
```

### AWS ECS Deployment

```bash
# Set required environment variables
export VPC_ID=vpc-xxxxxxxx
export SUBNET_IDS=subnet-xxxxxxxx,subnet-yyyyyyyy
export SECURITY_GROUP_ID=sg-xxxxxxxx

# Deploy to AWS
./deploy-aws.sh
```

## 🧪 Testing

```bash
# Run all tests
source venv/bin/activate
pytest test_supermemory.py -v

# Run examples
python examples.py
```

## 📊 Performance

Performance has not been benchmarked; no throughput, latency or memory figures are published. Search uses an exact FAISS `IndexFlatIP` index over `all-MiniLM-L6-v2` embeddings, so search time grows linearly with the number of stored memories.

## 🔒 Security

### Data Protection

- **Local Storage**: All data stored locally by default
- **No built-in encryption, authentication or TLS**: the HTTP API is unauthenticated and binds to `0.0.0.0:8000`; put it behind a reverse proxy with auth and TLS, or bind it to localhost, before exposing it on a network

## 📝 API Reference

### MCP Tools

#### `store_memory`
Store a new memory entry.

**Parameters:**
- `content` (string, required): The memory content
- `metadata` (object, optional): Additional metadata
- `tags` (array, optional): List of tags
- `importance_score` (number, optional): Importance score (0.0-1.0)

#### `search_memories`
Search for relevant memories.

**Parameters:**
- `query` (string, required): Search query
- `limit` (integer, optional): Maximum results (default: 10)
- `threshold` (number, optional): Similarity threshold (default: 0.7)

### HTTP Endpoints

- `POST /store` - Store memory
- `POST /search` - Search memories  
- `GET /memory/{id}` - Get memory by ID
- `DELETE /memory/{id}` - Delete memory
- `GET /health` - Health check

## 🐛 Troubleshooting

### Common Issues

**Server won't start:**
```bash
# Check Python version
python --version  # Should be 3.11+

# Install dependencies
pip install -r requirements.txt

# Check port availability
lsof -i :8000
```

**Memory search not working:**
```bash
# Check database
ls -la data/memory.db

# Check embedding model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Model Context Protocol** by Anthropic
- **FAISS** by Facebook Research  
- **Sentence Transformers** by UKP Lab
- **FastAPI** by Sebastián Ramirez

---

**SuperMemory MCP Server** - Centralized Memory for the LLM Era 🧠✨

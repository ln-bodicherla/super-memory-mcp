#!/bin/bash
# SuperMemory MCP Server Setup Script

echo "🚀 Setting up SuperMemory MCP Server..."

# Check Python version
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create data and logs directories
echo "📁 Creating directories..."
mkdir -p data logs

# Set permissions for deployment scripts
chmod +x deploy-aws.sh

echo "✅ Setup complete!"
echo ""
echo "🚀 To start the server:"
echo "  source venv/bin/activate"
echo "  python super_memory_mcp_server.py"
echo ""
echo "🧪 To run tests:"
echo "  source venv/bin/activate" 
echo "  pytest test_supermemory.py -v"
echo ""
echo "📚 To run examples:"
echo "  source venv/bin/activate"
echo "  python examples.py"
echo ""
echo "🐳 To run with Docker:"
echo "  docker-compose up -d"
echo ""
echo "☁️  To deploy to AWS:"
echo "  ./deploy-aws.sh"

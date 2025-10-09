"""
Example usage of SuperMemory MCP Server
"""

import asyncio
from client import SuperMemoryClient, AsyncSuperMemoryClient
from datetime import datetime

def sync_example():
    """Example using synchronous client"""
    print("🔄 Synchronous Client Example")
    print("=" * 40)

    # Initialize client
    client = SuperMemoryClient("http://localhost:8000")

    try:
        # Store some memories
        print("📝 Storing memories...")

        memory_ids = []

        # Store programming preferences
        id1 = client.store_memory(
            content="User prefers Python over JavaScript for backend development",
            metadata={
                "context": "programming_preferences", 
                "confidence": 0.9,
                "source": "conversation_2023-10-01"
            },
            tags=["programming", "preferences", "python", "backend"],
            importance_score=0.9
        )
        memory_ids.append(id1)
        print(f"✅ Stored preference memory: {id1}")

        # Store project information
        id2 = client.store_memory(
            content="Working on AWS ECS deployment with ALB integration for microservices",
            metadata={
                "context": "current_projects",
                "technologies": ["AWS", "ECS", "ALB", "Docker"],
                "status": "in_progress"
            },
            tags=["aws", "ecs", "deployment", "microservices"],
            importance_score=0.8
        )
        memory_ids.append(id2)
        print(f"✅ Stored project memory: {id2}")

        # Search for memories
        print("\n🔍 Searching memories...")

        # Search for AWS-related memories
        aws_memories = client.search_memories("AWS deployment", limit=5, threshold=0.5)
        print(f"\n📋 Found {len(aws_memories)} AWS-related memories:")
        for memory in aws_memories:
            print(f"  - {memory.content[:60]}...")
            print(f"    Tags: {', '.join(memory.tags)}")
            print(f"    Importance: {memory.importance_score}")

        # Search for programming memories
        prog_memories = client.search_memories("Python programming", limit=3)
        print(f"\n💻 Found {len(prog_memories)} programming memories:")
        for memory in prog_memories:
            print(f"  - {memory.content}")

        return memory_ids

    except Exception as e:
        print(f"❌ Error: {e}")
        return []

async def async_example():
    """Example using asynchronous client"""
    print("\n🔄 Asynchronous Client Example")
    print("=" * 40)

    async with AsyncSuperMemoryClient("http://localhost:8000") as client:
        try:
            # Store memories concurrently
            print("📝 Storing memories asynchronously...")

            tasks = [
                client.store_memory(
                    content="Async memory storage test 1",
                    metadata={"test": "async", "batch": 1},
                    tags=["async", "test"]
                ),
                client.store_memory(
                    content="Async memory storage test 2", 
                    metadata={"test": "async", "batch": 2},
                    tags=["async", "test"]
                ),
                client.store_memory(
                    content="Async memory storage test 3",
                    metadata={"test": "async", "batch": 3},
                    tags=["async", "test"]
                )
            ]

            memory_ids = await asyncio.gather(*tasks)
            print(f"✅ Stored {len(memory_ids)} memories concurrently")

            # Search asynchronously
            memories = await client.search_memories("async test", limit=10)
            print(f"\n🔍 Found {len(memories)} async test memories:")
            for memory in memories:
                print(f"  - {memory.content}")

        except Exception as e:
            print(f"❌ Async error: {e}")

def llm_integration_example():
    """Example showing how LLMs would integrate with SuperMemory"""
    print("\n🤖 LLM Integration Example")
    print("=" * 40)

    client = SuperMemoryClient("http://localhost:8000")

    # Simulate LLM storing context from conversation
    conversation_context = {
        "user_id": "user_123",
        "conversation_id": "conv_456", 
        "session": "2023-10-09",
        "model": "claude-3.5"
    }

    try:
        # Store user preferences discovered during conversation
        client.store_memory(
            content="User mentioned they work as a cloud engineer with AWS expertise",
            metadata={
                **conversation_context,
                "type": "user_profile",
                "category": "professional_background"
            },
            tags=["user_profile", "aws", "cloud_engineer"],
            importance_score=0.9
        )

        # Store task-specific information
        client.store_memory(
            content="User is building an MCP server for centralized LLM memory management",
            metadata={
                **conversation_context,
                "type": "current_task",
                "category": "project_context"
            },
            tags=["mcp", "llm", "memory_management", "project"],
            importance_score=0.8
        )

        print("✅ Stored LLM conversation context")

        # Simulate LLM retrieving relevant context for new conversation
        print("\n🔍 Retrieving context for new conversation...")

        # Get user background
        background = client.search_memories("cloud engineer AWS", limit=3)
        print("Background context:")
        for memory in background:
            print(f"  - {memory.content}")

        # Get current project context
        project = client.search_memories("MCP memory management", limit=2)
        print("\nProject context:")
        for memory in project:
            print(f"  - {memory.content}")

    except Exception as e:
        print(f"❌ LLM integration error: {e}")

if __name__ == "__main__":
    print("🚀 SuperMemory MCP Server Examples")
    print("=" * 50)
    print("Make sure the server is running: python super_memory_mcp_server.py")
    print("")

    # Run synchronous example
    memory_ids = sync_example()

    # Run asynchronous example
    asyncio.run(async_example())

    # Run LLM integration example
    llm_integration_example()

    print("\n✨ Examples completed!")
    print(f"Created {len(memory_ids)} example memories")

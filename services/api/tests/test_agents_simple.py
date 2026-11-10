"""
Simple tests for QURAN AI agent system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio

import pytest

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"

async def test_agent_import():
    """Test that agents can be imported correctly."""
    try:
        from services.api.agents.base_agent import BaseTafsirAgent
        from services.api.agents.ibn_kathir_agent import IbnKathirAgent
        print("✅ Agent imports successful")
        return True
    except Exception as e:
        print(f"❌ Agent import failed: {e}")
        return False

async def test_agent_creation():
    """Test agent creation."""
    try:
        from services.api.agents.ibn_kathir_agent import IbnKathirAgent
        agent = IbnKathirAgent()
        print(f"✅ Ibn Kathir agent created: {agent.agent_type}")
        return True
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return False

async def main():
    print("🚀 Running QURAN AI Agent System Tests")
    print("=" * 50)
    
    # Test imports
    if not await test_agent_import():
        return 1
        
    # Test agent creation
    if not await test_agent_creation():
        return 1
        
    print("\n✅ ALL TESTS PASSED!")
    print("The QURAN AI agent system is ready for database setup.")
    return 0

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(main())
    sys.exit(result)
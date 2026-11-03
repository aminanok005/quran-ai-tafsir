"""
Tests for QURAN AI agent system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import asyncio
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ibn_kathir_agent():
    """Test Ibn Kathir agent functionality."""
    try:
        from agents.ibn_kathir_agent import IbnKathirAgent
        agent = IbnKathirAgent()
        
        # Test explanation generation
        result = await agent.explain_ayah(36, 13, {})
        
        assert result['agent_type'] == 'ibn_kathir'
        print("✅ Ibn Kathir agent explanation generation successful")
        
        # Check evidence level
        assert result['evidence_level'] in ['VERIFIED', 'SOURCE-ATTRIBUTED', 'SCHOLARLY-DIFFERENCE', 'UNVERIFIED', 'AI-SYNTHESIS']
        print(f"✅ Evidence level: {result['evidence_level']}")
        
        # Check confidence score
        assert result['validation']['confidence_score'] > 0.8
        print(f"✅ Confidence score: {result['validation']['confidence_score']}")
        
        # Check citations
        assert len(result['citations']) > 0
        print(f"✅ Citations found: {len(result['citations'])}")
        
        print("✅ Ibn Kathir agent functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Ibn Kathir agent test failed: {e}")
        return False

async def test_al_tabari_agent():
    """Test Al-Tabari agent functionality."""
    try:
        from agents.al_tabari_agent import AlTabariAgent
        agent = AlTabariAgent()
        
        result = await agent.explain_ayah(36, 13, {})
        
        assert result['agent_type'] == 'al_tabari'
        print(f"✅ Al-Tabari agent explanation generated")
        print(f"   Evidence level: {result['evidence_level']}")
        print(f"   ✅ Valid: {result['validation']['valid']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Al-Tabari agent test failed: {e}")
        return False

async def test_ibn_ashur_agent():
    """Test Ibn Ashur agent functionality."""
    try:
        from agents.ibn_ashur_agent import IbnAshurAgent
        agent = IbnAshurAgent()
        
        result = await agent.explain_ayah(36, 13, {})
        
        assert result['agent_type'] == 'ibn_ashur'
        print(f"✅ Ibn Ashur agent explanation generated")
        print(f"   Evidence level: {result['evidence_level']}")
        print(f"   ✅ Valid: {result['validation']['valid']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ibn Ashur agent test failed: {e}")
        return False

async def test_al_saadi_agent():
    """Test Al-Sa'di agent functionality."""
    try:
        from agents.al_saadi_agent import AlSaadiAgent
        agent = AlSaadiAgent()
        
        result = await agent.explain_ayah(36, 13, {})
        
        assert result['agent_type'] == 'al_saadi'
        print(f"✅ Al-Saadi agent explanation generated")
        print(f"   Evidence level: {result['evidence_level']}")
        print(f"   ✅ Valid: {result['validation']['valid']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Al-Saadi agent test failed: {e}")
        return False

async def test_al_zuhayli_agent():
    """Test Al-Zuhayli agent functionality."""
    try:
        from agents.al_zuhayli_agent import AlZuhayliAgent
        agent = AlZuhayliAgent()
        
        result = await agent.explain_ayah(36, 13, {})
        
        assert result['agent_type'] == 'al_zuhayli'
        print(f"✅ Al-Zuhayli agent explanation generated")
        print(f"   Evidence level: {result['evidence_level']}")
        print(f"   ✅ Valid: {result['validation']['valid']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Al-Zuhayli agent test failed: {e}")
        return False

async def test_all_agents():
    """Test all agent implementations."""
    test_list = [
        ("ibn_kathir", "Ibn Kathir"),
        ("al_tabari", "Al-Tabari"),
        ("ibn_ashur", "Ibn Ashur"),
        ("al_saadi", "Al-Sa'di"),
        ("al_zuhayli", "Al-Zuhayli")
    ]
    
    success_count = 0
    total = len(test_list)
    
    for agent_name, _ in test_list:
        try:
            if isinstance(agent_name, str):
                if agent_name == "ibn_kathir":
                    result = await test_ibn_kathir_agent()
                elif agent_name == "al_tabari":
                    result = await test_al_tabari_agent()
                elif agent_name == "ibn_ashur":
                    result = await test_ibn_ashur_agent()
                elif agent_name == "al_saadi":
                    result = await test_al_saadi_agent()
                elif agent_name == "al_zuhayli":
                    result = await test_al_zuhayli_agent()
                else:
                    result = await test_all_agents()
                    
                if result:
                    success_count += 1
                    
        except Exception as e:
            print(f"❌ Test for {agent_name} failed: {e}")
            
    return success_count == total

async def main():
    print("🚀 Running QURAN AI Agent System Tests")
    print("=" * 50)
    
    # Test imports
    try:
        from agents.base_agent import BaseTafsirAgent
        from agents.ibn_kathir_agent import IbnKathirAgent
        from agents.al_tabari_agent import AlTabariAgent
        from agents.al_qurtubi_agent import AlQurtubiAgent
        from agents.ibn_ashur_agent import IbnAshurAgent
        from agents.al_saadi_agent import AlSaadiAgent
        from agents.al_zuhayli_agent import AlZuhayliAgent
        print("✅ All agent imports successful")
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return 1
    
    # Test agent initialization
    try:
        agents = [
            IbnKathirAgent(),
            AlTabariAgent(),
            AlQurtubiAgent(),
            IbnAshurAgent(),
            AlSaadiAgent(),
            AlZuhayliAgent()
        ]
        
        for i, agent in enumerate(agents):
            print(f"✅ Agent {i+1} ({agent.agent_type}) initialized successfully")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return 1
    
    # Test agent functionality
    tests = [
        ("Ibn Kathir Agent", test_ibn_kathir_agent),
        ("Al-Tabari Agent", test_al_tabari_agent),
        ("Ibn Ashur Agent", test_ibn_ashur_agent),
        ("Al-Saadi Agent", test_al_saadi_agent),
        ("Al-Zuhayli Agent", test_al_zuhayli_agent),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("The QURAN AI agent system is fully functional.")
        return 0
    else:
        print(f"\n❌ {failed} TESTS FAILED")
        return 1

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(main())
    sys.exit(result)
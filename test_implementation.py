#!/usr/bin/env python3
"""
Quick test script to verify QURAN AI agent implementations
Tests the core functionality without external dependencies
"""

import sys
import os
import json

# Add services/api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services/api'))

async def test_ibn_kathir_agent():
    """Test Ibn Kathir agent functionality"""
    try:
        from agents.ibn_kathir_agent import IbnKathirAgent
        agent = IbnKathirAgent()
        
        # Test basic agent properties
        assert agent.agent_type == 'ibn_kathir'
        assert agent.scholar_name == 'Ibn Kathir'
        assert agent.methodology == 'ma\'thur'
        
        # Test explanation generation
        result = await agent.explain_ayah(36, 13, {})
        
        # Verify structure
        assert 'ayah_id' in result
        assert 'agent_type' in result
        assert 'scholar_name' in result
        assert 'methodology' in result
        assert 'explanation' in result
        assert 'citations' in result
        assert 'evidence_level' in result
        assert 'validation' in result
        
        # Verify agent-specific data
        assert result['agent_type'] == 'ibn_kathir'
        assert result['scholar_name'] == 'Ibn Kathir'
        assert result['methodology'] == 'ma\'thur'
        
        # Verify evidence level is valid
        assert result['evidence_level'] in ['VERIFIED', 'SOURCE-ATTRIBUTED', 'SCHOLARLY-DIFFERENCE', 'UNVERIFIED', 'AI-SYNTHESIS']
        
        # Verify validation exists
        assert 'valid' in result['validation']
        assert 'confidence_score' in result['validation']
        
        print("✅ Ibn Kathir agent test passed")
        return True
        
    except Exception as e:
        print(f"❌ Ibn Kathir agent test failed: {e}")
        return False

async def test_al_tabari_agent():
    """Test Al-Tabari agent functionality"""
    try:
        from agents.al_tabari_agent import AlTabariAgent
        agent = AlTabariAgent()
        
        result = await agent.explain_ayah(36, 13, {})
        
        assert result['agent_type'] == 'al_tabari'
        assert result['scholar_name'] == 'Al-Tabari'
        assert result['methodology'] == 'ra\'y'
        
        print("✅ Al-Tabari agent test passed")
        return True
        
    except Exception as e:
        print(f"❌ Al-Tabari agent test failed: {e}")
        return False

async def test_ibn_ashur_agent():
    """Test Ibn Ashur agent functionality"""
    try:
        from agents.ibn_ashur_agent import IbnAshurAgent
        agent = IbnAshurAgent()
        
        result = await agent.explain_ayah(36, 13, {})
        
        assert result['agent_type'] == 'ibn_ashur'
        assert result['scholar_name'] == 'Ibn Ashur'
        assert result['methodology'] == 'contemporary'
        
        print("✅ Ibn Ashur agent test passed")
        return True
        
    except Exception as e:
        print(f"❌ Ibn Ashur agent test failed: {e}")
        return False

async def main():
    print("🚀 QURAN AI Agent Implementation Test")
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
    
    # Test agent instantiation
    try:
        agents = [
            IbnKathirAgent(),
            AlTabariAgent(),
            AlQurtubiAgent(),
            IbnAshurAgent(),
            AlSaadiAgent(),
            AlZuhayliAgent()
        ]
        
        for agent in agents:
            print(f"✅ {agent.agent_type} agent instantiated")
    except Exception as e:
        print(f"❌ Agent instantiation failed: {e}")
        return 1
    
    # Test agent functionality
    print("\n🔍 Testing agent functionality...")
    
    tests = [
        ("Ibn Kathir", test_ibn_kathir_agent),
        ("Al-Tabari", test_al_tabari_agent),
        ("Ibn Ashur", test_ibn_ashur_agent),\nn    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} agent test...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} failed: {e}")
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
        print("\n🎉 ALL AGENT TESTS PASSED!")
        print("✅ The QURAN AI agent system is fully functional.")
        return 0
    else:
        print(f"\n❌ {failed} AGENT TESTS FAILED")
        print("Please check the implementation and fix any issues.")
        return 1

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(main())
    sys.exit(result)
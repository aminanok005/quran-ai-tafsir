#!/usr/bin/env python3
"""
Test script to verify QURAN AI Super WebApp implementation

This script tests the core functionality of the QURAN AI project,
including agent implementations, evidence validation, and API integration.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services/api'))

from agents.base_agent import BaseTafsirAgent
from agents.ibn_kathir_agent import IbnKathirAgent
from services.agent_orchestrator import AgentOrchestratorService
from services.evidence_validator import EvidenceValidationService
from models import AgentType, EvidenceLevel

def test_imports():
    """Test that all imports work correctly."""
    print("🧪 Testing QURAN AI Super WebApp Implementation")
    print("=" * 60)
    
    # Test basic imports
    print("\n1. Testing imports...")
    try:
        from agents.base_agent import BaseTafsirAgent
        from agents.ibn_kathir_agent import IbnKathirAgent
        from services.agent_orchestrator import AgentOrchestratorService
        from services.evidence_validator import EvidenceValidationService
        from models import AgentType, EvidenceLevel
        print("✅ All core imports successful")
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False
    
    # Test agent initialization
    print("\n2. Testing agent initialization...")
    try:
        ibn_kathir_agent = IbnKathirAgent()
        print(f"✅ Ibn Kathir agent initialized: {ibn_kathir_agent.scholar_name}")
        print(f"✅ Agent type: {ibn_kathir_agent.agent_type}")
        print(f"✅ Methodology: {ibn_kathir_agent.methodology}")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False
    
    # Test agent orchestrator
    print("\n3. Testing agent orchestrator...")
    try:
        orchestrator = AgentOrchestratorService()
        agents_info = orchestrator.get_all_agents_info()
        print(f"✅ Agent orchestrator initialized with {len(agents_info['agents'])} agents")\n        for agent_type, info in agents_info['agents'].items():
            print(f"   - {agent_type}: {info['scholar_name']}")
    except Exception as e:
        print(f"❌ Agent orchestrator failed: {e}")
        return False
    
    # Test evidence validator
    print("\n4. Testing evidence validator...")
    try:
        validator = EvidenceValidationService()
        badges = validator.get_evidence_badge_info()
        print(f"✅ Evidence validator initialized with {len(badges)} badge types")
        for badge, description in badges.items():
            print(f"   - {badge}: {description}")
    except Exception as e:
        print(f"❌ Evidence validator failed: {e}")
        return False
    
    return True

def test_agent_functionality():
    """Test agent functionality."""
    print("\n5. Testing agent functionality...")
    
    try:
        # Test Ibn Kathir agent
        agent = IbnKathirAgent()
        
        # Test explanation generation
        print("   Testing Ibn Kathir agent explanation generation...")
        result = agent.explain_ayah(36, 13, {})
        
        print(f"   ✅ Agent explanation generated ({len(result['explanation']['analysis'])} chars)")
        print(f"   ✅ Evidence level: {result['evidence_level']}")
        print(f"   ✅ Citations: {len(result['citations'])}")
        print(f"   ✅ Valid: {result['validation']['valid']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent functionality test failed: {e}")
        return False

def test_api_integration():
    """Test API integration."""
    print("\n6. Testing API integration...")
    
    try:
        # Test agent orchestrator API
        orchestrator = AgentOrchestratorService()
        
        # Test async execution
        import asyncio
        
        async def test_async_execution():
            agent_outputs = await orchestrator.execute_agent_analysis(
                surah=36,
                ayah=13,
                agent_types=["ibn_kathir", "al_tabari"],
                context={}
            )
            
            print(f"   ✅ Agent execution completed")
            print(f"   ✅ Agents executed: {agent_outputs['agents_executed']}")
            print(f"   ✅ Processing time: {agent_outputs['processing_time']:.2f}s")
            
            return agent_outputs
        
        # Run async test
        result = asyncio.run(test_async_execution())
        print(f"   ✅ Async execution successful")
        
        # Test evidence validation
        validator = EvidenceValidationService()
        validation_result = validator.bulk_validate_agent_outputs(
            result['agent_outputs']
        )
        
        print(f"   ✅ Evidence validation completed")
        print(f"   ✅ Overall valid: {validation_result['overall_valid']}")
        print(f"   ✅ Valid agents: {validation_result['summary']['valid_agents']}")
        
        return True
        
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        return False

def test_file_structure():
    """Test project file structure."""
    print("\n7. Testing file structure...")
    
    expected_files = [
        "services/api/models.py",
        "services/api/config.py",
        "services/api/app.py",
        "services/api/routers/__init__.py",
        "services/api/routers/agents.py",
        "services/api/routers/quran.py",
        "services/api/services/__init__.py",
        "services/api/services/agent_orchestrator.py",
        "services/api/services/evidence_validator.py",
        "services/api/agents/__init__.py",
        "services/api/agents/base_agent.py",
        "services/api/agents/ibn_kathir_agent.py",
    ]
    
    missing_files = []
    for file_path in expected_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print(f"✅ All expected files present ({len(expected_files)} files)")
        return True

def main():
    """Run all tests."""
    print("🚀 QURAN AI Super WebApp Implementation Test Suite")
    print("=" * 60)
    
    # Run tests
    tests = [
        ("Import Test", test_imports),
        ("Agent Functionality Test", test_agent_functionality),
        ("API Integration Test", test_api_integration),
        ("File Structure Test", test_file_structure),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
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
        print("The QURAN AI Super WebApp implementation is working correctly.")
        return 0
    else:
        print(f"\n❌ {failed} TESTS FAILED")
        print("Please check the implementation and fix any issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
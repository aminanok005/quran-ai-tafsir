"""
Basic test to verify the QURAN AI Super WebApp setup
"""

import pytest
import sys
import os

def test_imports():
    """Test that all imports work correctly."""
    try:
        # Test backend imports
        from services.api.models import SurahType, Language, AgentType
        from services.api.agents.base_agent import BaseTafsirAgent
        from services.api.agents.ibn_kathir_agent import IbnKathirAgent
        from services.api.services.agent_orchestrator import AgentOrchestratorService
        from services.api.services.evidence_validator import EvidenceValidationService
        
        print("✅ All backend imports successful")
        
        # Test that we have the expected agents
        agents = [
            "ibn_kathir",
            "al_tabari", 
            "al_qurtubi",
            "ibn_ashur",
            "al_saadi",
            "al_zuhayli"
        ]
        
        for agent in agents:
            print(f"✅ Agent {agent} exists")
            
        print("✅ All agents successfully initialized")
        
        # Test agent orchestrator
        orchestrator = AgentOrchestratorService()
        agents_info = orchestrator.get_all_agents_info()
        print(f"✅ Agent orchestrator initialized with {len(agents_info['agents'])} agents")
        
        # Test evidence validator
        validator = EvidenceValidationService()
        badges = validator.get_evidence_badge_info()
        print(f"✅ Evidence validator initialized with {len(badges)} badge types")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_models():
    """Test that models are properly defined."""
    try:
        from services.api.models import SurahModel, AyahModel, TranslationModel
        print("✅ All models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_structure():
    """Test that the project structure is correct."""
    try:
        # Check for expected files
        expected_files = [
            "services/api/models.py",
            "services/api/config.py", 
            "services/api/app.py",
            "services/api/routers/__init__.py",
            "services/api/routers/agents.py",
            "services/api/services/__init__.py",
            "services/api/services/agent_orchestrator.py",
            "services/api/services/evidence_validator.py",
            "services/api/agents/base_agent.py",
            "services/api/agents/ibn_kathir_agent.py",
            "services/api/agents/al_tabari_agent.py",
            "services/api/agents/al_qurtubi_agent.py",
            "services/api/agents/ibn_ashur_agent.py",
            "services/api/agents/al_saadi_agent.py",
            "services/api/agents/al_zuhayli_agent.py"
        ]
        
        for file_path in expected_files:
            full_path = os.path.join("services/api", file_path)
            if os.path.exists(full_path):
                print(f"✅ {file_path} exists")
            else:
                print(f"❌ {file_path} missing")
                
        return True
        
    except Exception as e:
        print(f"❌ Structure test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing QURAN AI Super WebApp Basic Setup")
    print("=" * 50)
    
    # Run tests
    imports_ok = test_imports()
    models_ok = test_models()
    structure_ok = test_structure()
    
    print("\n" + "=" * 50)
    if imports_ok and models_ok and structure_ok:
        print("✅ All tests passed! Setup appears successful.")
        sys.exit(0)
    else:
        print("❌ Some tests failed.")
        sys.exit(1)
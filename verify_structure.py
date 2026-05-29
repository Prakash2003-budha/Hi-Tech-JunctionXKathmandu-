#!/usr/bin/env python3
"""Verify the refactored project structure."""
import sys
import traceback

def test_imports():
    """Test that all imports work correctly."""
    print("Testing Backend imports...")
    print("=" * 60)
    
    tests = [
        ("Config", "from Backend.app.config import Settings, get_settings"),
        ("Dependencies", "from Backend.app.dependencies import get_app_state, AppStateDep"),
        ("Engines - Social", "from Backend.app.engines.social_graph import build_graph, score_merchant_social"),
        ("Engines - Psychometric", "from Backend.app.engines.psychometric import run_psychometric_assessment"),
        ("Engines - Behavioral", "from Backend.app.engines.behavioral import compute_behavioral_score"),
        ("Engines - Fusion", "from Backend.app.engines.fusion import fuse_scores"),
        ("Models", "from Backend.app.models import MerchantBase, TrustScore"),
        ("App Factory", "from Backend.app import create_app"),
        ("Main Entry", "from Backend.main import app"),
    ]
    
    passed = 0
    failed = 0
    
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print(f"✓ {name:<25} OK")
            passed += 1
        except Exception as e:
            print(f"✗ {name:<25} FAILED: {str(e)[:50]}")
            traceback.print_exc()
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    return failed == 0

def test_app_creation():
    """Test that the app can be created."""
    print("\nTesting app creation...")
    print("=" * 60)
    
    try:
        from Backend.app import create_app
        app = create_app()
        print(f"✓ App created successfully")
        print(f"  - Title: {app.title}")
        print(f"  - Version: {app.version}")
        print(f"  - Routes: {len(app.routes)} endpoints")
        return True
    except Exception as e:
        print(f"✗ Failed to create app: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports() and test_app_creation()
    print("\n" + ("="*60))
    if success:
        print("✓ All tests passed! Structure is correct.")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Check errors above.")
        sys.exit(1)

#!/usr/bin/env python3
"""Test OrgClaw Skill installation and functionality."""

import sys
from pathlib import Path

def test_installation():
    """Run all installation tests."""
    
    print("=" * 70)
    print("🧪 OrgClaw Skill Installation Test")
    print("=" * 70)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Skill directory exists
    print("\n[1/6] Checking skill directory...")
    skill_dir = Path.home() / ".openclaw" / "skills" / "orgclaw"
    if skill_dir.exists():
        print(f"   ✅ Skill directory: {skill_dir}")
        tests_passed += 1
    else:
        print(f"   ❌ Skill directory not found: {skill_dir}")
        tests_failed += 1
    
    # Test 2: Core modules exist
    print("\n[2/6] Checking core modules...")
    required_files = [
        "orgclaw/__init__.py",
        "orgclaw/auto_extract.py",
        "orgclaw/analyzer/extractor.py",
        "orgclaw/analyzer/quality_scorer.py",
        "hooks/post_task.py",
    ]
    
    all_exist = True
    for file in required_files:
        path = skill_dir / file
        if path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} (missing)")
            all_exist = False
            tests_failed += 1
    
    if all_exist:
        tests_passed += 1
    
    # Test 3: Can import orgclaw
    print("\n[3/6] Testing imports...")
    try:
        sys.path.insert(0, str(skill_dir))
        
        # Mock dependencies
        class Mock: pass
        class MockChromaDB:
            class config:
                class Settings: pass
            class Client: pass
        
        sys.modules['git'] = Mock()
        sys.modules['chromadb'] = MockChromaDB()
        sys.modules['chromadb.config'] = MockChromaDB.config
        sys.modules['requests'] = Mock()
        sys.modules['yaml'] = Mock()
        
        from orgclaw import ExperienceExtractor, ExperienceScorer, AutoExtractor
        print("   ✅ All core imports successful")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        tests_failed += 1
    
    # Test 4: Hook functionality
    print("\n[4/6] Testing hook functionality...")
    try:
        from orgclaw.auto_extract import on_task_complete
        
        test_task = {
            "task_id": "test-001",
            "description": "Fixed memory leak in cache",
            "repo_path": ".",
            "lines_added": 10,
            "lines_removed": 5,
        }
        
        result = on_task_complete(test_task)
        if result and result.get("extracted"):
            print(f"   ✅ Hook works (quality: {result.get('quality_score', 0):.2f})")
            tests_passed += 1
        else:
            print("   ⚠️  Hook returned no result")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ Hook test failed: {e}")
        tests_failed += 1
    
    # Test 5: Configuration
    print("\n[5/6] Checking configuration...")
    config_file = Path.home() / ".openclaw" / "config.yaml"
    if config_file.exists():
        content = config_file.read_text()
        if "orgclaw:" in content:
            print(f"   ✅ OrgClaw configured in {config_file}")
            tests_passed += 1
        else:
            print(f"   ⚠️  OrgClaw not in config (will use defaults)")
            tests_passed += 1
    else:
        print(f"   ⚠️  No config file (will use defaults)")
        tests_passed += 1
    
    # Test 6: Storage directory
    print("\n[6/6] Checking storage...")
    personal_dir = Path.home() / ".orgclaw" / "personal"
    personal_dir.mkdir(parents=True, exist_ok=True)
    
    if personal_dir.exists():
        files = list(personal_dir.glob("*.json"))
        print(f"   ✅ Storage ready: {personal_dir}")
        print(f"   📊 Existing experiences: {len(files)}")
        tests_passed += 1
    else:
        print(f"   ❌ Cannot create storage: {personal_dir}")
        tests_failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    print(f"Passed: {tests_passed}/6")
    print(f"Failed: {tests_failed}/6")
    
    if tests_failed == 0:
        print("\n✅ All tests passed! OrgClaw Skill is ready to use.")
        print("\nNext steps:")
        print("  1. Run an OpenClaw task")
        print("  2. Watch for [OrgClaw] output")
        print("  3. Check: orgclaw stats")
        return 0
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(test_installation())

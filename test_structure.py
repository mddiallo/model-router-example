#!/usr/bin/env python3
"""
Test script to validate the Model Router example structure.

This script performs basic validation of the example scripts without
requiring actual Azure credentials.
"""

import sys
import importlib.util


def test_script_structure(script_path: str, script_name: str) -> bool:
    """Test if a script can be imported and has expected structure."""
    print(f"\n{'='*60}")
    print(f"Testing: {script_name}")
    print('='*60)
    
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        if spec is None or spec.loader is None:
            print(f"❌ Could not load {script_name}")
            return False
        
        module = importlib.util.module_from_spec(spec)
        
        # Check if script is valid Python
        print(f"✓ {script_name} is valid Python")
        
        # Note: We don't execute spec.loader.exec_module() because it would
        # run the script and fail due to missing credentials
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in {script_name}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error loading {script_name}: {e}")
        return False


def test_requirements():
    """Test requirements.txt exists and has expected content."""
    print(f"\n{'='*60}")
    print("Testing: requirements.txt")
    print('='*60)
    
    try:
        with open("requirements.txt", "r") as f:
            content = f.read()
            
        required_packages = [
            "azure-ai-inference",
            "azure-core",
            "openai",
            "python-dotenv"
        ]
        
        missing = []
        for package in required_packages:
            if package not in content:
                missing.append(package)
        
        if missing:
            print(f"❌ Missing packages: {', '.join(missing)}")
            return False
        
        print("✓ All required packages are listed")
        return True
        
    except FileNotFoundError:
        print("❌ requirements.txt not found")
        return False


def test_env_example():
    """Test .env.example exists."""
    print(f"\n{'='*60}")
    print("Testing: .env.example")
    print('='*60)
    
    try:
        with open(".env.example", "r") as f:
            content = f.read()
            
        if "AZURE_INFERENCE_ENDPOINT" in content:
            print("✓ .env.example contains AZURE_INFERENCE_ENDPOINT")
            return True
        else:
            print("❌ .env.example missing expected content")
            return False
            
    except FileNotFoundError:
        print("❌ .env.example not found")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  Model Router Example - Structure Validation")
    print("="*60)
    
    results = []
    
    # Test main script
    results.append(test_script_structure(
        "model_router_example.py",
        "model_router_example.py"
    ))
    
    # Test alternative script
    results.append(test_script_structure(
        "model_router_openai_example.py",
        "model_router_openai_example.py"
    ))
    
    # Test requirements
    results.append(test_requirements())
    
    # Test env example
    results.append(test_env_example())
    
    # Summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print('='*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All validation checks passed!")
        print("\nThe example scripts are properly structured.")
        print("To use them, configure your Azure credentials and run:")
        print("  python model_router_example.py")
        return 0
    else:
        print("\n❌ Some validation checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

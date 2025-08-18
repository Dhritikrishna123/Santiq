#!/usr/bin/env python3
"""Test script to verify workflow functionality."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n🔍 Testing: {description}")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ {description} - PASSED")
        if result.stdout.strip():
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr.strip()}")
        return False


def main():
    """Run all workflow tests."""
    print("🚀 Testing Santiq Workflows")
    print("=" * 50)

    # Test basic installation
    tests = [
        (["python", "-m", "pip", "install", "-e", ".[dev]"], "Package installation"),
        (["python", "-m", "santiq.cli.main", "--help"], "CLI help command"),
        (["python", "-m", "santiq.cli.main", "plugin", "list"], "Plugin listing"),
        (
            [
                "python",
                "-c",
                "import yaml; yaml.safe_load(open('examples/basic_pipeline.yml'))",
            ],
            "YAML validation",
        ),
        (
            ["python", "-m", "pytest", "tests/test_core/test_engine.py", "-v"],
            "Basic tests",
        ),
        (["black", "--check", "--diff", "santiq"], "Code formatting check"),
        (["isort", "--check-only", "--diff", "santiq"], "Import sorting check"),
    ]

    passed = 0
    total = len(tests)

    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1

    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Workflows should work correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""
Comprehensive test runner script for santiq project.
Provides various test execution options for different scenarios.
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional


def run_command(cmd: List[str], description: str = "") -> int:
    """Run a command and return exit code."""
    if description:
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(cmd)}")
        print('='*60)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}")
        return 1


def run_unit_tests(coverage: bool = True, verbose: bool = False) -> int:
    """Run unit tests."""
    cmd = ["pytest", "tests/test_core/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=santiq", "--cov-report=term-missing"])
    
    return run_command(cmd, "Unit Tests")


def run_integration_tests(verbose: bool = False) -> int:
    """Run integration tests."""
    cmd = ["pytest", "tests/", "-m", "integration"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Integration Tests")


def run_cli_tests(verbose: bool = False) -> int:
    """Run CLI tests."""
    cmd = ["pytest", "tests/", "-m", "cli"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "CLI Tests")


def run_compatibility_tests(verbose: bool = False) -> int:
    """Run plugin compatibility tests."""
    cmd = ["pytest", "tests/", "-m", "compatibility"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Plugin Compatibility Tests")


def run_github_workflow_tests(verbose: bool = False) -> int:
    """Run GitHub workflow specific tests."""
    cmd = ["pytest", "tests/test_core/github_workflow_test.py"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "GitHub Workflow Tests")


def run_external_plugin_tests(verbose: bool = False) -> int:
    """Run external plugin management tests."""
    cmd = ["pytest", "tests/", "-m", "external_plugin"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "External Plugin Management Tests")


def run_linting() -> int:
    """Run code linting checks."""
    exit_codes = []
    
    # Black formatting check
    exit_codes.append(run_command(
        ["black", "--check", "--diff", "santiq", "tests"],
        "Black Code Formatting Check"
    ))
    
    # Import sorting check
    exit_codes.append(run_command(
        ["isort", "--check-only", "--profile", "black", "santiq", "tests"],
        "Import Sorting Check"
    ))
    
    # Type checking
    exit_codes.append(run_command(
        ["mypy", "santiq", "--ignore-missing-imports"],
        "Type Checking"
    ))
    
    return max(exit_codes) if exit_codes else 0


def run_security_checks() -> int:
    """Run security checks."""
    exit_codes = []
    
    # Bandit security check
    try:
        exit_codes.append(run_command(
            ["bandit", "-r", "santiq", "-f", "json"],
            "Security Vulnerability Check"
        ))
    except:
        print("Warning: bandit not installed, skipping security check")
    
    return max(exit_codes) if exit_codes else 0


def run_performance_tests() -> int:
    """Run performance/benchmark tests."""
    # Create test data for benchmarking
    create_benchmark_data_script = """
import pandas as pd
import numpy as np
from pathlib import Path

# Create benchmark data directory
benchmark_dir = Path("/tmp/santiq_benchmark")
benchmark_dir.mkdir(exist_ok=True)

# Create datasets of different sizes
sizes = [1000, 10000]  # Reduced for CI

for size in sizes:
    data = pd.DataFrame({
        'id': range(1, size + 1),
        'name': [f'Person_{i}' for i in range(1, size + 1)],
        'age': np.random.randint(18, 80, size),
        'email': [f'person_{i}@test.com' for i in range(1, size + 1)],
        'score': np.random.uniform(0, 100, size),
        'nullable_col': np.random.choice([None, 'value'], size, p=[0.1, 0.9]),
    })
    
    # Add some duplicates
    if size > 100:
        duplicate_indices = np.random.choice(size, min(size // 100, 10), replace=False)
        for idx in duplicate_indices:
            data.iloc[idx] = data.iloc[0]
    
    output_file = benchmark_dir / f"benchmark_data_{size}.csv"
    data.to_csv(output_file, index=False)
    print(f"Created benchmark dataset: {output_file} ({size} rows)")

print("Benchmark data created successfully")
"""
    
    # Run benchmark data creation
    exit_code = run_command(
        ["python", "-c", create_benchmark_data_script],
        "Creating Benchmark Data"
    )
    
    if exit_code != 0:
        return exit_code
    
    # Run actual performance test
    performance_test_script = """
import time
import pandas as pd
from santiq.core.engine import ETLEngine
from santiq.core.config import PipelineConfig
from pathlib import Path

engine = ETLEngine()
benchmark_dir = Path("/tmp/santiq_benchmark")
sizes = [1000, 10000]
results = []

print("Running performance benchmarks...")

for size in sizes:
    input_file = benchmark_dir / f"benchmark_data_{size}.csv"
    output_file = benchmark_dir / f"benchmark_output_{size}.csv"
    
    if not input_file.exists():
        print(f"Benchmark data file not found: {input_file}")
        continue
    
    config = PipelineConfig(
        extractor={
            'plugin': 'csv_extractor',
            'params': {'path': str(input_file)}
        },
        profilers=[{
            'plugin': 'basic_profiler',
            'params': {}
        }],
        transformers=[{
            'plugin': 'basic_cleaner',
            'params': {
                'drop_nulls': True,
                'drop_duplicates': True
            }
        }],
        loaders=[{
            'plugin': 'csv_loader',
            'params': {'path': str(output_file)}
        }]
    )
    
    start_time = time.time()
    try:
        result = engine.run_pipeline_from_config(config, mode='controlled-auto')
        end_time = time.time()
        
        execution_time = end_time - start_time
        rows_per_second = size / execution_time if execution_time > 0 else 0
        
        print(f"✅ Processed {size} rows in {execution_time:.2f}s ({rows_per_second:.0f} rows/sec)")
        
        if not result['success']:
            print(f"⚠️  Pipeline execution reported failure for size {size}")
        
    except Exception as e:
        print(f"❌ Error processing {size} rows: {e}")

print("Performance benchmarks completed")
"""
    
    return run_command(
        ["python", "-c", performance_test_script],
        "Performance Benchmarks"
    )


def run_all_tests(verbose: bool = False, include_slow: bool = False) -> int:
    """Run all tests in sequence."""
    test_functions = [
        (run_linting, "Code Quality Checks"),
        (lambda: run_unit_tests(coverage=True, verbose=verbose), "Unit Tests"),
        (lambda: run_integration_tests(verbose=verbose), "Integration Tests"),
        (lambda: run_cli_tests(verbose=verbose), "CLI Tests"),
        (lambda: run_compatibility_tests(verbose=verbose), "Compatibility Tests"),
        (lambda: run_external_plugin_tests(verbose=verbose), "External Plugin Management Tests"),
        (lambda: run_github_workflow_tests(verbose=verbose), "GitHub Workflow Tests"),
        (run_security_checks, "Security Checks"),
    ]
    
    if include_slow:
        test_functions.append((run_performance_tests, "Performance Tests"))
    
    exit_codes = []
    failed_tests = []
    
    print(f"\n{'='*80}")
    print("RUNNING COMPREHENSIVE TEST SUITE")
    print(f"{'='*80}")
    
    for test_func, description in test_functions:
        print(f"\n🔄 Starting: {description}")
        exit_code = test_func()
        exit_codes.append(exit_code)
        
        if exit_code == 0:
            print(f"✅ {description}: PASSED")
        else:
            print(f"❌ {description}: FAILED (exit code: {exit_code})")
            failed_tests.append(description)
    
    # Summary
    print(f"\n{'='*80}")
    print("TEST SUITE SUMMARY")
    print(f"{'='*80}")
    
    passed_count = sum(1 for code in exit_codes if code == 0)
    total_count = len(exit_codes)
    
    print(f"Total Tests: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    
    if failed_tests:
        print("\nFailed Tests:")
        for test in failed_tests:
            print(f"  ❌ {test}")
    
    overall_exit_code = max(exit_codes) if exit_codes else 0
    
    if overall_exit_code == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  SOME TESTS FAILED (exit code: {overall_exit_code})")
    
    return overall_exit_code


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="santiq Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_tests.py --all                 # Run all tests
  python scripts/run_tests.py --unit                # Run only unit tests  
  python scripts/run_tests.py --integration         # Run only integration tests
  python scripts/run_tests.py --external-plugin     # Test external plugin management
  python scripts/run_tests.py --github-workflow     # Run GitHub workflow tests
  python scripts/run_tests.py --lint                # Run only linting checks
  python scripts/run_tests.py --performance         # Run performance benchmarks
  python scripts/run_tests.py --all --include-slow  # Run all tests including slow ones
        """
    )
    
    # Test selection arguments
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--cli", action="store_true", help="Run CLI tests")
    parser.add_argument("--compatibility", action="store_true", help="Run compatibility tests")
    parser.add_argument("--external-plugin", action="store_true", help="Run external plugin management tests")
    parser.add_argument("--github-workflow", action="store_true", help="Run GitHub workflow tests")
    parser.add_argument("--lint", action="store_true", help="Run linting checks")
    parser.add_argument("--security", action="store_true", help="Run security checks")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    
    # Options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--include-slow", action="store_true", help="Include slow tests")
    parser.add_argument("--no-coverage", action="store_true", help="Skip coverage reporting")
    
    args = parser.parse_args()
    
    # If no specific test type is selected, show help
    if not any([args.all, args.unit, args.integration, args.cli, args.compatibility,
                args.external_plugin, args.github_workflow, args.lint, args.security, 
                args.performance]):
        parser.print_help()
        return 1
    
    exit_code = 0
    
    if args.all:
        exit_code = run_all_tests(verbose=args.verbose, include_slow=args.include_slow)
    else:
        # Run individual test types
        if args.lint:
            exit_code = max(exit_code, run_linting())
        
        if args.unit:
            exit_code = max(exit_code, run_unit_tests(
                coverage=not args.no_coverage, 
                verbose=args.verbose
            ))
        
        if args.integration:
            exit_code = max(exit_code, run_integration_tests(verbose=args.verbose))
        
        if args.cli:
            exit_code = max(exit_code, run_cli_tests(verbose=args.verbose))
        
        if args.compatibility:
            exit_code = max(exit_code, run_compatibility_tests(verbose=args.verbose))
        
        if args.external_plugin:
            exit_code = max(exit_code, run_external_plugin_tests(verbose=args.verbose))
        
        if args.github_workflow:
            exit_code = max(exit_code, run_github_workflow_tests(verbose=args.verbose))
        
        if args.security:
            exit_code = max(exit_code, run_security_checks())
        
        if args.performance:
            exit_code = max(exit_code, run_performance_tests())
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
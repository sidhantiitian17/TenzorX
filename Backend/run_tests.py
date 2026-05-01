"""Run all integration tests."""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

test_files = [
    "tests/test_langchain_integration.py",
    "tests/test_integration.py",
    "tests/test_knowledge_graph.py",
    "tests/test_graphrag_integration.py",
]

all_passed = True
for test_file in test_files:
    if os.path.exists(test_file):
        print(f"\n{'='*60}")
        print(f"Running: {test_file}")
        print('='*60)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        if result.returncode != 0:
            all_passed = False
    else:
        print(f"\n⚠️  File not found: {test_file}")

print(f"\n{'='*60}")
if all_passed:
    print("✅ All tests passed!")
else:
    print("❌ Some tests failed!")
print('='*60)

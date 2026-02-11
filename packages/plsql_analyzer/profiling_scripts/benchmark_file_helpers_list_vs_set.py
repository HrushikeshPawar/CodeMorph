import time
import sys
import os
from pathlib import Path
from typing import List

# Setup path to import plsql_analyzer
# Assuming we are running from the repo root
repo_root = Path(os.getcwd())
src_path = repo_root / "packages/plsql_analyzer/src"
sys.path.append(str(src_path))

try:
    from plsql_analyzer.utils.file_helpers import FileHelpers
except ImportError as e:
    print(f"Error importing plsql_analyzer: {e}")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

# Mock logger
class MockLogger:
    def bind(self, **kwargs):
        return self
    def trace(self, msg):
        pass
    def error(self, msg):
        pass
    def warning(self, msg):
        pass
    def exception(self, msg):
        pass
    def debug(self, msg):
        pass
    def info(self, msg):
        pass

def run_benchmark():
    logger = MockLogger()
    helpers = FileHelpers(logger)

    # Setup
    num_iterations = 50000
    # A mix of common exclusions and random ones
    exclude_list = ["src", "packages", "tests", "utils", "common", "core", "legacy", "build", "dist", "node_modules", "target", "bin", "obj", "lib", "include", "scripts", "docs", "tools", "resources", "assets"]
    # Add many more to make the linear scan costly (simulating a complex project setup or extensive exclusions)
    exclude_list.extend([f"dir_{i}" for i in range(500)])

    # A reasonably deep path
    # Path depth also matters as it multiplies the number of checks
    deep_path_parts = ["root"] + [f"dir_{i}" for i in range(50)] + ["final_file.py"]
    # Ensure some parts are in the exclusion list to trigger 'True' branch of check
    # But mostly 'False' checks dominate if list is large and path parts are unique
    deep_fpath = Path(*deep_path_parts)

    print(f"Benchmarking get_processed_fpath with {num_iterations} iterations...")
    print(f"Exclusion list size: {len(exclude_list)}")
    print(f"Path depth: {len(deep_fpath.parts)}")

    start_time = time.time()
    for _ in range(num_iterations):
        helpers.get_processed_fpath(deep_fpath, exclude_list)
    duration = time.time() - start_time

    print(f"Total time: {duration:.4f} seconds")
    print(f"Average time per call: {duration/num_iterations:.6f} seconds")

if __name__ == "__main__":
    run_benchmark()

import time
import tempfile
from pathlib import Path
import random

def create_mock_codebase(root_dir, num_dirs, num_files, extensions):
    root_path = Path(root_dir)
    dirs = [root_path]
    for i in range(num_dirs):
        d = root_path / f"dir_{i}"
        d.mkdir(parents=True, exist_ok=True)
        dirs.append(d)

    for i in range(num_files):
        d = random.choice(dirs)
        ext = random.choice(extensions)
        f = d / f"file_{i}.{ext}"
        f.touch()

    # Add some files with other extensions that we don't care about
    for i in range(num_files):
        d = random.choice(dirs)
        f = d / f"other_{i}.txt"
        f.touch()

def current_implementation(source_folder, extensions_to_include):
    files_to_process = []
    for extension in extensions_to_include:
        # Using rglob to find all files matching the extension recursively
        files_to_process.extend(list(source_folder.rglob(f"*.{extension}")))
    return files_to_process

def optimized_implementation(source_folder, extensions_to_include):
    # Normalize extensions to include leading dot and be lowercase
    extensions = {f".{ext.lower().lstrip('.')}" for ext in extensions_to_include}
    return [
        fpath
        for fpath in source_folder.rglob("*")
        if fpath.suffix.lower() in extensions and fpath.is_file()
    ]

def run_benchmark():
    num_dirs = 1000
    num_files = 10000
    extensions_to_include = ["sql", "pkb", "pks", "prc", "fnc", "trg", "vw", "typ", "tps", "tpb"]

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Creating mock codebase in {tmpdir}...")
        create_mock_codebase(tmpdir, num_dirs, num_files, extensions_to_include)
        source_folder = Path(tmpdir)

        print(f"Running current implementation with {len(extensions_to_include)} extensions...")
        start_time = time.time()
        current_files = current_implementation(source_folder, extensions_to_include)
        current_duration = time.time() - start_time
        print(f"Current implementation found {len(current_files)} files in {current_duration:.4f} seconds.")

        print(f"Running optimized implementation with {len(extensions_to_include)} extensions...")
        start_time = time.time()
        optimized_files = optimized_implementation(source_folder, extensions_to_include)
        optimized_duration = time.time() - start_time
        print(f"Optimized implementation found {len(optimized_files)} files in {optimized_duration:.4f} seconds.")

        if len(current_files) != len(optimized_files):
            print(f"WARNING: File count mismatch! Current: {len(current_files)}, Optimized: {len(optimized_files)}")

        improvement = (current_duration - optimized_duration) / current_duration * 100
        print(f"Improvement: {improvement:.2f}%")

if __name__ == "__main__":
    run_benchmark()

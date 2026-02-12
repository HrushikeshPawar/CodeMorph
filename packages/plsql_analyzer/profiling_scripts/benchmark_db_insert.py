
import sys
import time
import shutil
import tempfile
from pathlib import Path
import loguru

# Adjust python path to include src
sys.path.append(str(Path(__file__).parent / "src"))

from plsql_analyzer.persistence.database_manager import DatabaseManager
from plsql_analyzer.core.code_object import PLSQL_CodeObject, CodeObjectType

def run_benchmark():
    # Setup
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "bench.db"
    logger = loguru.logger
    logger.remove() # quiet

    db_manager = DatabaseManager(db_path, logger)
    db_manager.setup_database()

    # Generate dummy objects
    objects = []
    for i in range(1000):
        obj = PLSQL_CodeObject(
            name=f"proc_{i}",
            package_name="bench_pkg",
            clean_code="BEGIN NULL; END;",
            type=CodeObjectType.PROCEDURE,
            start_line=1,
            end_line=5
        )
        obj.generate_id()
        objects.append(obj)

    fpath = str(Path(temp_dir) / "bench.sql")
    db_manager.update_file_hash(fpath, "dummyhash")

    # Benchmark Single Insert
    start_time = time.time()
    for obj in objects:
        db_manager.add_codeobject(obj, fpath)
    end_time = time.time()

    print(f"Time for 1000 inserts (single): {end_time - start_time:.4f} seconds")

    # Benchmark Batch Insert
    # Clean up previous inserts
    db_manager.update_file_hash(fpath, "dummyhash_batch")

    start_time_batch = time.time()
    db_manager.add_codeobjects_batch(objects, fpath)
    end_time_batch = time.time()

    print(f"Time for 1000 inserts (batch): {end_time_batch - start_time_batch:.4f} seconds")

    # Verify count
    all_objs = db_manager.get_all_codeobjects()
    # Note: get_all_codeobjects returns list of dicts.
    # Since we cleared and re-inserted, we expect 1000.
    print(f"Total objects in DB: {len(all_objs)}")

    # Cleanup
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    run_benchmark()

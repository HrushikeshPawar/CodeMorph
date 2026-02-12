import timeit
import sys
from pathlib import Path
from plsql_analyzer.utils.file_helpers import FileHelpers
import loguru as lg

def benchmark():
    # Setup
    logger = lg.logger
    # Disable logging to avoid overhead
    logger.remove()
    file_helpers = FileHelpers(logger)

    # Prepare data
    # Create a large exclusion list to make the linear scan noticeable
    exclude_list = [f"exclude_part_{i}" for i in range(100)] + ["project", "src", "common"]

    # Path with some parts in exclusion list and some not
    fpath = Path("project/src/common/module/submodule/file.sql")

    # 1. Benchmark get_processed_fpath
    def run_get_processed_fpath():
        file_helpers.get_processed_fpath(fpath, exclude_list)

    iterations = 20000
    time_get_processed = timeit.timeit(run_get_processed_fpath, number=iterations)

    print(f"get_processed_fpath: Total time for {iterations} iterations: {time_get_processed:.4f} seconds")
    print(f"get_processed_fpath: Average time per call: {time_get_processed/iterations:.6f} seconds")

    # 2. Benchmark derive_package_name_from_path (Normal case)
    package_name_from_code = "some.package"
    file_extensions = ["sql"]

    def run_derive_package():
        file_helpers.derive_package_name_from_path(
            package_name_from_code, fpath, file_extensions, exclude_list
        )

    time_derive = timeit.timeit(run_derive_package, number=iterations)

    print(f"derive_package_name_from_path (short): Total time for {iterations} iterations: {time_derive:.4f} seconds")
    print(f"derive_package_name_from_path (short): Average time per call: {time_derive/iterations:.6f} seconds")

    # 3. Benchmark derive_package_name_from_path (Long case)
    long_package_name = ".".join([f"part_{i}" for i in range(50)])

    def run_derive_package_long():
        file_helpers.derive_package_name_from_path(
            long_package_name, fpath, file_extensions, exclude_list
        )

    time_derive_long = timeit.timeit(run_derive_package_long, number=iterations)

    print(f"derive_package_name_from_path (long): Total time for {iterations} iterations: {time_derive_long:.4f} seconds")
    print(f"derive_package_name_from_path (long): Average time per call: {time_derive_long/iterations:.6f} seconds")

if __name__ == "__main__":
    benchmark()

import time
import loguru as lg
from typing import List
from plsql_analyzer.core.code_object import PLSQL_CodeObject, CodeObjectType
from dependency_analyzer.builder.graph_constructor import GraphConstructor

def benchmark():
    # Disable logging to focus on performance
    lg.logger.remove()

    num_objects = 100000
    code_objects = []
    for i in range(num_objects):
        # Create many overloaded objects with unique names but only 1 object per name
        # to trigger the logic in the loop we are optimizing
        obj = PLSQL_CodeObject(
            name=f"proc_{i}",
            package_name="pkg",
            type=CodeObjectType.PROCEDURE,
            overloaded=True,
            clean_code="BEGIN NULL; END;"
        )
        obj.id = f"pkg.proc_{i}"
        code_objects.append(obj)

    constructor = GraphConstructor(code_objects, lg.logger)

    start_time = time.perf_counter()
    constructor._initialize_lookup_structures()
    end_time = time.perf_counter()

    print(f"Time taken for _initialize_lookup_structures with {num_objects} objects: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    benchmark()

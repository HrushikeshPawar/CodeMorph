# packages/plsql_analyzer/profiling_scripts/profile_signature_parser.py
import cProfile
import pstats
import io
from loguru import logger # Assuming PLSQLSignatureParser expects a loguru logger

# Adjust this import based on your actual project structure
# This assumes 'packages' is a root for imports or your PYTHONPATH is set up accordingly.
from plsql_analyzer.parsing.signature_parser import PLSQLSignatureParser

# Sample signature for profiling - use more and varied samples for real profiling
SAMPLE_SIGNATURE_VALID = "PROCEDURE my_proc (p_param1 IN VARCHAR2, p_param2 OUT NUMBER) IS"
SAMPLE_SIGNATURE_COMPLEX = """
    CREATE OR REPLACE FUNCTION get_complex_data (
        p_user_id IN users.id%TYPE,
        p_filter IN VARCHAR2 DEFAULT NULL,
        p_active_only IN BOOLEAN DEFAULT TRUE
    ) RETURN SYS_REFCURSOR IS
"""
NUM_ITERATIONS = 500 # Number of times to parse for more stable profiling data

def run_parsing_task():
    # Create a minimal logger for the parser.
    # For profiling, you might want to disable or reduce logging verbosity.
    prof_logger = logger.patch(lambda record: record.update(name="profiling_logger"))
    prof_logger.remove() # Remove default console handler
    # prof_logger.add(lambda _: None, level="ERROR") # Add a null sink if needed

    parser = PLSQLSignatureParser(logger=prof_logger)
    for i in range(NUM_ITERATIONS):
        parser.parse(SAMPLE_SIGNATURE_VALID)
        parser.parse(SAMPLE_SIGNATURE_COMPLEX)

if __name__ == "__main__":
    print(f"Profiling PLSQLSignatureParser.parse over {NUM_ITERATIONS*2} total calls...")

    profiler = cProfile.Profile()
    profiler.enable()

    run_parsing_task()

    profiler.disable()

    s = io.StringIO()
    # Sort stats by total time spent in the function itself
    ps = pstats.Stats(profiler, stream=s).sort_stats('tottime')
    ps.print_stats(20) # Print the top 20 time-consuming functions

    print("\n--- Profiling Results (Top 20 by Total Time) ---")
    print(s.getvalue())

    # For more detailed analysis, you can dump stats to a file:
    profiler.dump_stats(r"packages\plsql_analyzer\profiling_scripts\signature_parser.prof")
    # And then view it with a visualizer like snakeviz.
    print("\nTo visualize, uncomment dump_stats line and use a tool like snakeviz.")
    print("Install snakeviz with: pip install snakeviz")
    print("Then run: snakeviz packages\plsql_analyzer\profiling_scripts\signature_parser.prof")
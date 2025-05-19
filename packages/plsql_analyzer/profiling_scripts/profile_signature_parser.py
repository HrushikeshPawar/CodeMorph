import cProfile
import pstats
import io
from pathlib import Path
from loguru import logger # Assuming PLSQLSignatureParser expects a loguru logger

from plsql_analyzer.settings import AppConfig
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

def run_parsing_task(app_config):
    # Create a minimal logger for the parser.
    # For profiling, you might want to disable or reduce logging verbosity.
    prof_logger = logger.patch(lambda record: record.update(name="profiling_logger"))
    prof_logger.remove() # Remove default console handler
    # prof_logger.add(lambda _: None, level="ERROR") # Add a null sink if needed

    parser = PLSQLSignatureParser(logger=prof_logger)
    for i in range(NUM_ITERATIONS):
        parser.parse(SAMPLE_SIGNATURE_VALID)
        parser.parse(SAMPLE_SIGNATURE_COMPLEX)
    
    return app_config.output_base_dir

if __name__ == "__main__":
    # Create AppConfig instance
    app_config = AppConfig(
        source_code_root_dir=Path("/media/hrushikesh/SharedDrive/ActiveProjects/CodeMorph/packages/plsql_analyzer/tests/test_data"),
        output_base_dir=Path("/media/hrushikesh/SharedDrive/ActiveProjects/CodeMorph/generated/artifacts"),
        log_verbose_level=0,  # Minimal logging for profiling
        enable_profiler=True
    )
    
    # Make sure artifact directories exist
    app_config.ensure_artifact_dirs()
    
    print(f"Profiling PLSQLSignatureParser.parse over {NUM_ITERATIONS*2} total calls...")

    profiler = cProfile.Profile()
    profiler.enable()

    output_dir = run_parsing_task(app_config)

    profiler.disable()

    s = io.StringIO()
    # Sort stats by total time spent in the function itself
    ps = pstats.Stats(profiler, stream=s).sort_stats('tottime')
    ps.print_stats(20) # Print the top 20 time-consuming functions

    print("\n--- Profiling Results (Top 20 by Total Time) ---")
    print(s.getvalue())

    # For more detailed analysis, dump stats to a file using the AppConfig output directory
    profile_output = output_dir / "signature_parser.prof"
    profiler.dump_stats(profile_output)
    
    print(f"\nProfile data saved to: {profile_output}")
    print("To visualize, use a tool like snakeviz:")
    print("Install snakeviz with: pip install snakeviz")
    print(f"Then run: snakeviz {profile_output}")
# packages/plsql_analyzer/profiling_scripts/profile_structural_parser.py
import cProfile
import pstats
import io
from tqdm.auto  import tqdm
# from pathlib import Path

# Adjust the import path according to your project structure
from plsql_analyzer.orchestration.extraction_workflow import clean_code_and_map_literals
from plsql_analyzer.parsing.structural_parser import PlSqlStructuralParser

# --- Mock Logger (to minimize logging overhead during profiling) ---
class MockLogger:
    def bind(self, **kwargs): return self
    def trace(self, msg): pass
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass
    def critical(self, msg): pass
    def exception(self, msg): pass
    def success(self, msg): pass
    def log(self, level, msg): pass

mock_logger = MockLogger()
NUM_ITERATIONS = 500

# --- Profiler Runner ---
def run_profiler(func_to_profile, *args, **kwargs):
    profiler = cProfile.Profile()
    profiler.enable()
    for _ in tqdm(range(NUM_ITERATIONS), "Run Iterations"):
        result = func_to_profile(*args, **kwargs)
    profiler.disable()
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats()
    print(s.getvalue())

    # For more detailed analysis, you can dump stats to a file:
    profiler.dump_stats(r"packages\plsql_analyzer\profiling_scripts\structural_parser.prof")
    return result

# --- SQL File Path (User needs to set this) ---
# Replace with the actual path to your AUTOFAX_PKG.sql file
USER_SQL_FILE_PATH = r"c:\Users\C9B6J9\Projects\CodeMorph\data\Bulk Download\fop_owner\PACKAGE_BODIES\AUTOFAX_PKG.sql"

def read_sql_file(file_path_str: str) -> str | None:
    try:
        with open(file_path_str, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
            clean_code, _ = clean_code_and_map_literals(code, mock_logger)
            return clean_code
    except FileNotFoundError:
        print(f"Error: SQL file not found at {file_path_str}")
        return None

def profile_structural_parser_main():
    sql_content = read_sql_file(USER_SQL_FILE_PATH)
    if not sql_content:
        return

    parser = PlSqlStructuralParser(logger=mock_logger, verbose_lvl=0)

    print(f"\n--- Profiling PlSqlStructuralParser.parse() with {USER_SQL_FILE_PATH} ---")
    run_profiler(parser.parse, sql_content)

if __name__ == "__main__":
    profile_structural_parser_main()
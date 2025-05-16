# filepath: profile_extraction_workflow.py
import cProfile
import pstats
import io
import tempfile
import shutil
from pathlib import Path

# Adjust import paths according to your project structure
from plsql_analyzer import config
from plsql_analyzer.orchestration.extraction_workflow import ExtractionWorkflow
from plsql_analyzer.parsing.structural_parser import PlSqlStructuralParser
from plsql_analyzer.parsing.signature_parser import PLSQLSignatureParser
from plsql_analyzer.parsing.call_extractor import CallDetailExtractor
from plsql_analyzer.utils.file_helpers import FileHelpers # Assuming this class exists
# from plsql_analyzer.persistence.database_manager import DatabaseManager # For type hint if needed
# from plsql_analyzer.core.code_object import PLSQL_CodeObject, CodeObjectType # For type hint if needed
# from plsql_analyzer import config # For type hint if needed


# --- Mock Components ---
class MockLogger:
    def bind(self, **kwargs): return self
    def trace(self, msg): pass
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass
    def critical(self, msg): pass
    def exception(self, e_or_msg): pass # Adjusted to match typical logger.exception usage
    def success(self, msg): pass
    def log(self, level, msg): pass

mock_logger_instance = MockLogger()

class MockConfig:
    SOURCE_CODE_ROOT_DIR = "" # Will be set to temp dir
    FILE_EXTENSION = "sql"    # Or "SQL", ensure case matches rglob pattern
    EXCLUDE_FROM_PROCESSED_PATH = ["exclude_this_part_of_path"] # Example
    EXCLUDE_FROM_PATH_FOR_PACKAGE_DERIVATION = ["another_exclude"] # Example
    # Add any other config attributes used by ExtractionWorkflow or its dependencies

class MockDatabaseManager:
    def get_file_hash(self, fpath_str: str) -> str | None: return None
    def update_file_hash(self, fpath_str: str, file_hash: str) -> bool: return True
    def add_codeobject(self, code_obj: any, fpath_str: str) -> bool: return True
    def remove_file_record(self, fpath_str: str) -> bool: return True
    # Add other methods if called by the workflow

# --- Profiler Runner ---
def run_profiler(func_to_profile, *args, **kwargs):
    profiler = cProfile.Profile()
    profiler.enable()
    result = func_to_profile(*args, **kwargs)
    profiler.disable()
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats()
    print(s.getvalue())

    profiler.dump_stats(r"packages\plsql_analyzer\profiling_scripts\profile_extraction_workflow.prof")

    return result

# --- SQL File Path (User needs to set this) ---
USER_SQL_FILE_PATH = r"c:\Users\C9B6J9\Projects\CodeMorph\data\Bulk Download\fop_owner\PACKAGE_BODIES\AUTOFAX_PKG.sql"

def read_sql_file(file_path_str: str) -> str | None:
    try:
        with open(file_path_str, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except FileNotFoundError:
        mock_logger_instance.error(f"Error: SQL file not found at {file_path_str}")
        return None

def profile_extraction_workflow_main():
    sql_content_to_write = read_sql_file(USER_SQL_FILE_PATH)
    if not sql_content_to_write:
        return

    temp_source_dir = tempfile.mkdtemp(prefix="profile_workflow_")
    # Ensure the filename matches the configured FILE_EXTENSION for rglob
    temp_sql_file_path = Path(temp_source_dir) / (Path(USER_SQL_FILE_PATH).stem + ".sql")


    try:
        with open(temp_sql_file_path, 'w', encoding='utf-8') as f:
            f.write(sql_content_to_write)
        mock_logger_instance.info(f"Created temp file: {temp_sql_file_path}")


        mock_config_instance = MockConfig()
        mock_config_instance.SOURCE_CODE_ROOT_DIR = str(temp_source_dir)

        # keywords_for_call_extractor = [
        #     "IF", "THEN", "ELSE", "ELSIF", "END", "LOOP", "WHILE", "FOR", "BEGIN", "EXCEPTION",
        #     "DECLARE", "SELECT", "INSERT", "UPDATE", "DELETE", "FROM", "WHERE", "GROUP", "ORDER",
        #     "BY", "HAVING", "CREATE", "ALTER", "DROP", "TABLE", "VIEW", "INDEX", "PROCEDURE",
        #     "FUNCTION", "PACKAGE", "BODY", "TYPE", "CURSOR", "RETURN", "IS", "AS", "CONSTANT",
        #     "NULL", "OTHERS", "RAISE", "OPEN", "FETCH", "CLOSE", "COMMIT", "ROLLBACK", "SAVEPOINT",
        #     "EXECUTE", "IMMEDIATE", "GRANT", "REVOKE", "LOCK", "MERGE", "CASE", "WHEN", "EXIT"
        # ]

        db_manager = MockDatabaseManager()
        structural_parser = PlSqlStructuralParser(logger=mock_logger_instance, verbose_lvl=0)
        signature_parser = PLSQLSignatureParser(logger=mock_logger_instance)
        call_extractor = CallDetailExtractor(logger=mock_logger_instance, keywords_to_drop=config.CALL_EXTRACTOR_KEYWORDS_TO_DROP)
        
        # Assuming FileHelpers takes a logger and its methods are compatible
        # If FileHelpers has other dependencies or complex setup, adjust instantiation.
        try:
            file_helpers = FileHelpers(logger=mock_logger_instance)
        except TypeError as e:
            mock_logger_instance.error(f"Error instantiating FileHelpers: {e}. It might need more arguments or a different setup.")
            mock_logger_instance.error("Please ensure FileHelpers is correctly mocked or instantiated for profiling.")
            return


        workflow = ExtractionWorkflow(
            config=mock_config_instance,
            logger=mock_logger_instance,
            db_manager=db_manager,
            structural_parser=structural_parser,
            signature_parser=signature_parser,
            call_extractor=call_extractor,
            file_helpers=file_helpers
        )

        print(f"\n--- Profiling ExtractionWorkflow.run() with {temp_sql_file_path} ---")
        run_profiler(workflow.run)

    finally:
        shutil.rmtree(temp_source_dir)
        mock_logger_instance.info(f"Cleaned up temporary directory: {temp_source_dir}")

if __name__ == "__main__":
    profile_extraction_workflow_main()
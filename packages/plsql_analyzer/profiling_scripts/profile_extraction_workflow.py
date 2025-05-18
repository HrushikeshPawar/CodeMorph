import cProfile
import pstats
import io
import tempfile
import shutil
from pathlib import Path

# Import components using the new configuration system
from plsql_analyzer.settings import AppConfig
from plsql_analyzer.orchestration.extraction_workflow import ExtractionWorkflow
from plsql_analyzer.parsing.structural_parser import PlSqlStructuralParser
from plsql_analyzer.parsing.signature_parser import PLSQLSignatureParser
from plsql_analyzer.parsing.call_extractor import CallDetailExtractor
from plsql_analyzer.utils.file_helpers import FileHelpers
from plsql_analyzer.persistence.database_manager import DatabaseManager


# --- Mock Logger ---
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

# --- Profiler Runner ---
def run_profiler(func_to_profile, output_dir, *args, **kwargs):
    profiler = cProfile.Profile()
    profiler.enable()
    result = func_to_profile(*args, **kwargs)
    profiler.disable()
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats()
    print(s.getvalue())

    # Use output directory from AppConfig
    profile_output = output_dir / "profile_extraction_workflow.prof"
    profiler.dump_stats(profile_output)
    print(f"Profile data saved to: {profile_output}")

    return result

# --- SQL File Path (User needs to set this) ---
USER_SQL_FILE_PATH = "/media/hrushikesh/SharedDrive/ActiveProjects/CodeMorph/packages/plsql_analyzer/tests/test_data/large_example.sql"

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

        # Create AppConfig instance
        app_config = AppConfig(
            source_code_root_dir=temp_source_dir,
            output_base_dir=Path("/media/hrushikesh/SharedDrive/ActiveProjects/CodeMorph/generated/artifacts"),
            log_verbose_level=0,  # Minimal logging for profiling
            enable_profiler=True
        )
        
        # Make sure artifact directories exist
        app_config.ensure_artifact_dirs()

        db_manager = DatabaseManager(app_config.database_path, mock_logger_instance)
        try:
            db_manager.setup_database()  # Create tables if they don't exist
        except Exception as e:
            mock_logger_instance.error(f"Database setup failed: {e}.")
            return
            
        structural_parser = PlSqlStructuralParser(logger=mock_logger_instance, verbose_lvl=0)
        signature_parser = PLSQLSignatureParser(logger=mock_logger_instance)
        call_extractor = CallDetailExtractor(logger=mock_logger_instance, keywords_to_drop=app_config.call_extractor_keywords_to_drop)
        
        try:
            file_helpers = FileHelpers(logger=mock_logger_instance)
        except TypeError as e:
            mock_logger_instance.error(f"Error instantiating FileHelpers: {e}. It might need more arguments or a different setup.")
            mock_logger_instance.error("Please ensure FileHelpers is correctly mocked or instantiated for profiling.")
            return

        workflow = ExtractionWorkflow(
            config=app_config,
            logger=mock_logger_instance,
            db_manager=db_manager,
            structural_parser=structural_parser,
            signature_parser=signature_parser,
            call_extractor=call_extractor,
            file_helpers=file_helpers
        )

        print(f"\n--- Profiling ExtractionWorkflow.run() with {temp_sql_file_path} ---")
        run_profiler(workflow.run, app_config.output_base_dir)

    finally:
        shutil.rmtree(temp_source_dir)
        mock_logger_instance.info(f"Cleaned up temporary directory: {temp_source_dir}")

if __name__ == "__main__":
    profile_extraction_workflow_main()
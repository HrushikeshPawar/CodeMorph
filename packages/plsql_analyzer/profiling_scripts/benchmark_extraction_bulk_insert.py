import time
import tempfile
import shutil
import json
from pathlib import Path
import loguru as lg

# Import components
from plsql_analyzer.settings import PLSQLAnalyzerSettings
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
    def exception(self, e_or_msg): pass
    def success(self, msg): pass
    def log(self, level, msg): pass

mock_logger_instance = MockLogger()

def generate_large_sql_file(file_path: Path, num_procedures: int = 500):
    with open(file_path, 'w') as f:
        f.write("CREATE OR REPLACE PACKAGE BODY massive_pkg IS\n")
        for i in range(num_procedures):
            f.write(f"  PROCEDURE proc_{i} (p_param_{i} IN NUMBER) IS\n")
            f.write(f"    v_temp NUMBER;\n")
            f.write(f"  BEGIN\n")
            f.write(f"    v_temp := p_param_{i} * 2;\n")
            f.write(f"    dbms_output.put_line('Proc {i}');\n")
            f.write(f"  END proc_{i};\n\n")
        f.write("END massive_pkg;\n")

def run_benchmark():
    # Use a temp directory for the benchmark
    temp_dir = tempfile.mkdtemp(prefix="benchmark_plsql_")
    try:
        source_dir = Path(temp_dir) / "source"
        source_dir.mkdir()

        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir()

        sql_file_path = source_dir / "large_test.sql"
        num_procedures = 500
        print(f"Generating synthetic SQL file with {num_procedures} procedures...")
        generate_large_sql_file(sql_file_path, num_procedures=num_procedures)

        # Configure settings
        # Note: We pass raw strings/paths, Pydantic will handle conversion
        app_config = PLSQLAnalyzerSettings(
            source_code_root_dir=source_dir,
            output_base_dir=output_dir,
            log_verbose_level=0,
            database_filename="plsql_analysis.db"
        )

        app_config.ensure_artifact_dirs()

        # Setup components
        db_manager = DatabaseManager(app_config.database_path, mock_logger_instance)
        db_manager.setup_database()

        structural_parser = PlSqlStructuralParser(logger=mock_logger_instance, verbose_lvl=0)
        signature_parser = PLSQLSignatureParser(logger=mock_logger_instance)
        call_extractor = CallDetailExtractor(
            logger=mock_logger_instance,
            keywords_to_drop=app_config.call_extractor_keywords_to_drop
        )
        file_helpers = FileHelpers(logger=mock_logger_instance)

        workflow = ExtractionWorkflow(
            config=app_config,
            logger=mock_logger_instance,
            db_manager=db_manager,
            structural_parser=structural_parser,
            signature_parser=signature_parser,
            call_extractor=call_extractor,
            file_helpers=file_helpers
        )

        print(f"Starting extraction benchmark...")
        start_time = time.time()

        # We call _process_single_file directly to avoid directory scanning overhead and focus on processing/insertion
        workflow._process_single_file(sql_file_path)

        end_time = time.time()

        duration = end_time - start_time
        print(f"Extraction completed in {duration:.4f} seconds.")

        # Verification
        objects = db_manager.get_all_codeobjects()
        print(f"Total objects extracted: {len(objects)}")

        # Verify we got expected number of objects (procedures + maybe package body itself depending on parser)
        # Structural parser usually returns the package body container AND items inside if parsed deeply.
        # But here we are interested in relative performance.

        return duration

    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    run_benchmark()

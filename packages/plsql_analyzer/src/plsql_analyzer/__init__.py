# plsql_analyzer/main.py
import cProfile
import pstats
import io
from pathlib import Path

from plsql_analyzer import config as cfg_module # Use an alias to avoid conflict
from plsql_analyzer.utils.logging_setup import configure_logger
from plsql_analyzer.utils.file_helpers import FileHelpers
from plsql_analyzer.persistence.database_manager import DatabaseManager
from plsql_analyzer.parsing.structural_parser import PlSqlStructuralParser
from plsql_analyzer.parsing.signature_parser import PLSQLSignatureParser
from plsql_analyzer.parsing.call_extractor import CallDetailExtractor
from plsql_analyzer.orchestration.extraction_workflow import ExtractionWorkflow

def main():
    # Setting up Profiler
    profiler = cProfile.Profile()
    profiler.enable()

    # Ensure artifact directories (logs, db) exist
    config.ensure_artifact_dirs()

    # 1. Configure Logger
    logger = configure_logger(config.LOG_VERBOSE_LEVEL, config.LOGS_DIR)
    logger.info(f"Application Started. Base directory: {config.BASE_DIR}")
    logger.info(f"Artifacts will be stored in: {config.ARTIFACTS_DIR}")
    logger.info(f"Source code configured from: {config.SOURCE_CODE_ROOT_DIR}")

    # 2. Initialize Helper and Manager Classes
    file_helpers = FileHelpers(logger)
    
    db_manager = DatabaseManager(config.DATABASE_PATH, logger)
    try:
        db_manager.setup_database() # Create tables if they don't exist
    except Exception as e:
        logger.critical(f"Database setup failed: {e}. Halting application.")
        return # Stop if DB can't be set up

    for fpath in config.REMOVE_FPATH:
        db_manager.remove_file_record(fpath)
        

    # 3. Initialize Parsers
    # Parsers are generally stateless or reset per call, so one instance can be reused.
    structural_parser = PlSqlStructuralParser(logger, config.LOG_VERBOSE_LEVEL)
    signature_parser = PLSQLSignatureParser(logger) # Does not depend on verbose_lvl for its own ops
    call_extractor = CallDetailExtractor(logger, config.CALL_EXTRACTOR_KEYWORDS_TO_DROP)

    # 4. Initialize and Run the Extraction Workflow
    workflow = ExtractionWorkflow(
        config=config, # Pass the config module/object
        logger=logger,
        db_manager=db_manager,
        structural_parser=structural_parser,
        signature_parser=signature_parser,
        call_extractor=call_extractor,
        file_helpers=file_helpers
    )

    try:
        workflow.run()
    except Exception as e:
        logger.critical("Unhandled exception in the main extraction workflow. Application will exit.")
        logger.exception(e)
    finally:
        logger.info("Application Finished.")
    
    profiler.disable()
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats()
    print(s.getvalue())

    profiler.dump_stats(r"packages\plsql_analyzer\profiling_scripts\profile_plsql_analyzer_complete_run_v1-20250515.prof")

if __name__ == "__main__":
    # This allows running `python -m plsql_analyzer.main` if plsql_analyzer's parent is in PYTHONPATH
    # Or if you are in the directory containing `plsql_analyzer` and run `python -m plsql_analyzer.main`
    # If running `python plsql_analyzer/main.py` directly, imports might need adjustment
    # (e.g. `from config import ...` if `plsql_analyzer` is the current working directory).
    # The current relative imports `from . import config` assume `main.py` is run as part of the package.
    
    # For direct script execution from the project root (e.g., `python plsql_analyzer/main.py`):
    # You might need to adjust PYTHONPATH or change imports to be relative to the script's location
    # or use absolute package imports if `plsql_analyzer` is installed or in PYTHONPATH.
    # One common way is to add the project root to sys.path if running script directly:
    import sys
    # Assuming main.py is in plsql_analyzer/ and project_root is parent of plsql_analyzer/
    project_root = Path(__file__).resolve().parent.parent 
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    # After this, `from plsql_analyzer import config` should work.
    # Re-importing with adjusted path (if necessary for direct script run)
    
    
    # Re-assign config for the main function call if it was re-imported
    global config
    config = cfg_module

    main()
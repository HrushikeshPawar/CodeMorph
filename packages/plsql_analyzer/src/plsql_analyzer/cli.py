from __future__ import annotations

import io
import pstats
import cProfile
import tomllib
import cyclopts

from pathlib import Path
from typing import Optional, List, Sequence, Annotated, TYPE_CHECKING
from cyclopts import App, Parameter, validators, Token

from plsql_analyzer.settings import AppConfig
from plsql_analyzer.utils.logging_setup import configure_logger
from plsql_analyzer.utils.file_helpers import FileHelpers
from plsql_analyzer.persistence.database_manager import DatabaseManager
from plsql_analyzer.parsing.structural_parser import PlSqlStructuralParser
from plsql_analyzer.parsing.signature_parser import PLSQLSignatureParser
from plsql_analyzer.parsing.call_extractor import CallDetailExtractor
from plsql_analyzer.orchestration.extraction_workflow import ExtractionWorkflow

if TYPE_CHECKING:
    from loguru import Logger

app = App(help="PL/SQL Analyzer CLI")

def convert_to_path(_, path_str:Sequence[Token]) -> Path:
    """
    Convert a string to a Path object.
    """
    
    return Path(path_str[0].value)

def validate_path(_, path: Optional[Path]):
    """
    Validate that the given path exists.
    """
    if path is None:
        return
    if not path.exists():
        raise cyclopts.ValidationError(msg=f"Given Path `{path}` does not exist.\n")

def fext_parser(_, fext: Sequence[Token]) -> List[str]:
    """
    Convert a list of file extensions to a list of strings.
    """
    return [ext.value.split(".")[1] if '.' in ext.value else ext.value for ext in fext]

@app.command
def parse(
    source_dir: Annotated[Optional[Path], Parameter(help="Root directory of the source code.", converter=convert_to_path, validator=validate_path)],
    config_file: Annotated[Optional[Path], Parameter(help="Path to the configuration file (TOML).", converter=convert_to_path, validator=validate_path)] = None,
    output_dir: Annotated[Optional[Path], Parameter(help="Base directory for all generated artifacts.", converter=convert_to_path)] = None,
    verbose: Annotated[int, Parameter(help="Verbosity level (0=ERROR, 1=INFO, 2=DEBUG, 3=TRACE).", name=["--verbose", "-v"], validator=validators.Number(gte=0, lte=3))] = 1,
    profile: Annotated[Optional[bool], Parameter(help="Enable profiling.", name=["--profile"])] = None,
    include_patterns: Annotated[Optional[List[str]], Parameter(help="File extensions to include in analysis.", name=["--fext", "-e"], consume_multiple=True, converter=fext_parser)] = None,
    exclude_dirs: Annotated[Optional[List[str]], Parameter(help="Directory names to exclude from analysis.", name=["--exd"], consume_multiple=True)] = None,
    exclude_names: Annotated[Optional[List[str]], Parameter(help="Directory names to exclude from package naming process.", name=["--exn"], consume_multiple=True)] = None,
    database_filename: Annotated[Optional[str], Parameter(help="Name of the SQLite database file.", name=["--db-filename", "--dbf"])] = None,
):
    """
    Parse PL/SQL source code to extract various code objects - Procedures and Function.
    """
    config_data = {}
    if config_file:
        if config_file.exists():
            config_data = tomllib.loads(config_file.read_text())
        else:
            print(f"Warning: Config file {config_file} not found.")

    # Precedence: Pydantic defaults < TOML file < CLI arguments
    cli_args = {
        "source_code_root_dir": source_dir,
        "output_base_dir": output_dir,
        "log_verbose_level": verbose,
        "enable_profiler": profile,
        "file_extensions_to_include": include_patterns,
        "exclude_names_from_processed_path": exclude_dirs,
        "exclude_names_for_package_derivation": exclude_names,
        "database_filename": database_filename,
    }

    # Filter out None values from CLI args to not override TOML/defaults unnecessarily
    cli_args_provided = {k: v for k, v in cli_args.items() if v is not None}

    # Merge configurations: start with TOML, then override with CLI args
    merged_config_data = {**config_data, **cli_args_provided}

    try:
        app_config = AppConfig(**merged_config_data)

        # Configure logger using AppConfig
        logger: Logger = configure_logger(app_config.log_verbose_level, app_config.logs_dir)
        logger.info("Logger configured based on AppConfig.")
        logger.info("Application Started.")
        logger.info(f"Artifacts will be stored in: {app_config.artifacts_dir}")
        logger.info(f"Source code configured from: {app_config.source_code_root_dir}")


        app_config.ensure_artifact_dirs()

        run_plsql_analyzer(app_config, logger)

    except Exception as e:
        print(f"Error initializing AppConfig or running analysis: {e}")
        return


def run_plsql_analyzer(app_config: AppConfig, logger:'Logger'):
    logger.info(f"Starting PL/SQL analysis with source: {app_config.source_code_root_dir}")
    
    if app_config.enable_profiler:
        profiler = cProfile.Profile()
        profiler.enable()

    # 2. Initialize Helper and Manager Classes
    file_helpers = FileHelpers(logger)
    
    db_manager = DatabaseManager(app_config.database_path, logger)
    try:
        db_manager.setup_database() # Create tables if they don't exist
    except Exception as e:
        logger.critical(f"Database setup failed: {e}. Halting application.")
        return # Stop if DB can't be set up

    # TODO: Handle the removal of files from the database if needed
    # for fpath in config.REMOVE_FPATH:
    #     db_manager.remove_file_record(fpath)
        

    # 3. Initialize Parsers
    # Parsers are generally stateless or reset per call, so one instance can be reused.
    structural_parser = PlSqlStructuralParser(logger, app_config.log_verbose_level)
    signature_parser = PLSQLSignatureParser(logger) # Does not depend on verbose_lvl for its own ops
    call_extractor = CallDetailExtractor(logger, app_config.call_extractor_keywords_to_drop)

    # 4. Initialize and Run the Extraction Workflow
    workflow = ExtractionWorkflow(
        config=app_config, # Pass the config module/object
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
    
    if app_config.enable_profiler:
        profiler.disable()
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats()
        print(s.getvalue())

        profiler.dump_stats(r"packages\plsql_analyzer\profiling_scripts\profile_plsql_analyzer_complete_run_v1-20250515.prof")


if __name__ == "__main__":
    app()

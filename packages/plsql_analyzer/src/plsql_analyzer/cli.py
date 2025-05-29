from __future__ import annotations

import io
import pstats
import cProfile
import tomllib
import cyclopts
import tomlkit # Added for TOML generation

from pathlib import Path
from typing import Optional, List, Sequence, Annotated, TYPE_CHECKING
from cyclopts import App, Parameter, validators, Token

from plsql_analyzer.settings import PLSQLAnalyzerSettings
from plsql_analyzer.utils.logging_setup import configure_logger
from plsql_analyzer.utils.file_helpers import FileHelpers
from plsql_analyzer.persistence.database_manager import DatabaseManager
from plsql_analyzer.parsing.structural_parser import PlSqlStructuralParser
from plsql_analyzer.parsing.signature_parser import PLSQLSignatureParser
from plsql_analyzer.parsing.call_extractor import CallDetailExtractor
from plsql_analyzer.orchestration.extraction_workflow import ExtractionWorkflow
import tomlkit.items

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

@app.command
def parse(
    source_dir: Annotated[Optional[Path], Parameter(help="Root directory of the source code.", converter=convert_to_path, validator=validate_path)],
    config_file: Annotated[Optional[Path], Parameter(help="Path to the configuration file (TOML).", converter=convert_to_path, validator=validate_path)] = None,
    output_dir: Annotated[Optional[Path], Parameter(help="Base directory for all generated artifacts.", converter=convert_to_path)] = None,
    verbose: Annotated[int, Parameter(help="Verbosity level (0=ERROR, 1=INFO, 2=DEBUG, 3=TRACE).", name=["--verbose", "-v"], validator=validators.Number(gte=0, lte=3))] = 1,
    profile: Annotated[Optional[bool], Parameter(help="Enable profiling.", name=["--profile"])] = None,
    include_patterns: Annotated[Optional[List[str]], Parameter(help="File extensions to include in analysis.", name=["--fext", "-e"], consume_multiple=True)] = None,
    exclude_dirs: Annotated[Optional[List[str]], Parameter(help="Directory names to exclude from analysis.", name=["--exd"], consume_multiple=True)] = None,
    exclude_names: Annotated[Optional[List[str]], Parameter(help="Directory names to exclude from package naming process.", name=["--exn"], consume_multiple=True)] = None,
    database_filename: Annotated[Optional[str], Parameter(help="Name of the SQLite database file.", name=["--db-filename", "--df"])] = None,
    force_reprocess: Annotated[Optional[List[str]], Parameter(help="Force reprocessing specific files, bypassing hash checks.", name=["--force-reprocess"], consume_multiple=True)] = None,
    clear_history_for_file: Annotated[Optional[List[str]], Parameter(help="Clear history for specific files (using processed paths as stored in DB).", name=["--clear-history-for-file"], consume_multiple=True)] = None,
    strict_calls: Annotated[Optional[bool], Parameter(help="Only consider identifiers followed by '(' as calls, ignoring ';' terminated identifiers.", name=["--strict-calls"])] = None,
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
        "force_reprocess": set(force_reprocess) if force_reprocess else None,
        "clear_history_for_file": set(clear_history_for_file) if clear_history_for_file else None,
        "strict_lpar_only_calls": strict_calls,
    }

    # Filter out None values from CLI args to not override TOML/defaults unnecessarily
    cli_args_provided = {k: v for k, v in cli_args.items() if v is not None}

    # Merge configurations: start with TOML, then override with CLI args
    merged_config_data = {**config_data, **cli_args_provided}
    logger = None
    try:
        app_config = PLSQLAnalyzerSettings(**merged_config_data)

        # Configure logger using PLSQLAnalyzerSettings
        logger: Logger = configure_logger(app_config.log_verbose_level, app_config.logs_dir)
        logger.info("Logger configured based on PLSQLAnalyzerSettings.")
        logger.info("Application Started.")
        logger.info(f"Artifacts will be stored in: {app_config.artifacts_dir}")
        logger.info(f"Source code configured from: {app_config.source_code_root_dir}")


        app_config.ensure_artifact_dirs()

        run_plsql_analyzer(app_config, logger)

    except Exception as e:
        if logger:
            logger.critical("Error initializing PLSQLAnalyzerSettings or running analysis.")
            logger.exception(e)
        else:
            print("Error initializing PLSQLAnalyzerSettings or running analysis.")
            print(e)
        return


def run_plsql_analyzer(app_config: PLSQLAnalyzerSettings, logger:'Logger'):
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

    # Handle clearing history for specified files
    if hasattr(app_config, 'clear_history_for_file') and app_config.clear_history_for_file:
        for fpath in app_config.clear_history_for_file:
            logger.info(f"Clearing history for file: {fpath}")
            if db_manager.remove_file_record(fpath):
                logger.success(f"Successfully cleared history for {fpath}")
            else:
                logger.error(f"Failed to clear history for {fpath}")
        

    # 3. Initialize Parsers
    # Parsers are generally stateless or reset per call, so one instance can be reused.
    structural_parser = PlSqlStructuralParser(logger, app_config.log_verbose_level)
    signature_parser = PLSQLSignatureParser(logger) # Does not depend on verbose_lvl for its own ops
    call_extractor = CallDetailExtractor(logger, app_config.call_extractor_keywords_to_drop, app_config.strict_lpar_only_calls)

    # 4. Initialize and Run the Extraction Workflow
    workflow = ExtractionWorkflow(
        config=app_config, # Pass the PLSQLAnalyzerSettings instance
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

        profiler.dump_stats(app_config.output_base_dir / f"profile_plsql_analyzer-{app_config.source_code_root_dir.name}-{app_config.database_filename}.prof")


@app.command
def init(
    file_path: Annotated[Path, Parameter(help="Path to generate the configuration file.", converter=convert_to_path)] = Path("plsql_analyzer_config.toml"),
    force: Annotated[bool, Parameter(help="Overwrite existing configuration file without prompting.")] = False,
):
    """
    Initialize a new PL/SQL Analyzer configuration file.

    Generates a default configuration file (plsql_analyzer_config.toml)
    in the specified path or current working directory.
    The file will be pre-populated with all available settings,
    their default values, and descriptive comments.
    """
    # Determine config file path: if relative, use current working directory (respecting patched Path.cwd)
    if file_path.is_absolute():
        config_file_path = file_path
    else:
        config_file_path = Path.cwd() / file_path

    if config_file_path.exists() and not force:
        overwrite = input(
            f"Configuration file '{config_file_path}' already exists. Overwrite? [y/N]: "
        )
        if overwrite.lower() not in ["y", "yes"]:
            print("Aborted. Configuration file not created.")
            return

    try:
        config_content = generate_default_config_toml()
        config_file_path.write_text(config_content)
        print(f"Successfully created configuration file: {config_file_path}")
    except Exception as e:
        print(f"Error creating configuration file: {e}")

def generate_default_config_toml() -> str:
    """
    Generates the TOML content for the default configuration file
    based on the PLSQLAnalyzerSettings model.
    """
    doc = tomlkit.document()
    doc.add(tomlkit.comment("PL/SQL Analyzer Configuration File"))
    doc.add(tomlkit.comment("Generated by 'plsql-analyzer init'"))
    doc.add(tomlkit.nl())

    settings_model = PLSQLAnalyzerSettings

    for field_name, field_info in settings_model.model_fields.items():
        
        # Skip computed fields, as they are derived and not set by users in config
        if field_name in settings_model.model_computed_fields: # Check against model's computed fields
            continue

        # Add field description as a comment
        description = field_info.description or f"Configuration for {field_name}"
        doc.add(tomlkit.comment(description))
        
        default_value = None
        # Pydantic's FieldInfo.is_required() correctly identifies fields without defaults
        is_required_field = field_info.is_required()

        if is_required_field:
            if field_name == "source_code_root_dir":
                default_value = "./plsql_source_code"  # Specific placeholder
            else:
                # Generic placeholder for other required fields
                default_value = f"REPLACE_WITH_YOUR_{field_name.upper()}_VALUE"
                # Add a comment indicating it's required
                doc.add(tomlkit.comment(f"Note: The field '{field_name}' is required."))
        else:
            # For optional fields or fields with defaults, get their default value or factory output
            default_value = field_info.get_default(call_default_factory=True)

        # Convert specific types to TOML-compatible formats
        if isinstance(default_value, Path):
            default_value = str(default_value)
        elif isinstance(default_value, (set, list)): # Convert set to list for TOML
            # For lists, convert to TOML array format
            if len(default_value) == 0:
                default_value = []
            else:
                toml_array:tomlkit.items.Array = tomlkit.array()
                toml_array.extend(default_value)
                default_value = toml_array.multiline(True)

        doc.add(field_name, default_value)
        doc.add(tomlkit.nl())

    return tomlkit.dumps(doc)

if __name__ == "__main__":
    app()

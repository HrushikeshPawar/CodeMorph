"""
Dependency Analyzer Package.

This package takes the output from plsql_analyzer (specifically, the
database of parsed PL/SQL code objects) and constructs a dependency graph.
It then performs various analyses on this graph, such as identifying
circular dependencies, unused objects, and can generate visualizations.
"""
from __future__ import annotations

import cProfile
import pstats
import io

# Local application/library specific imports
# It's good practice to import specific names rather than the whole module if `config` is a common variable name.
from dependency_analyzer import config as da_config
from dependency_analyzer.utils.logging_setup import configure_logger
from dependency_analyzer.utils.database_loader import DatabaseLoader
from dependency_analyzer.builder.graph_constructor import GraphConstructor
from dependency_analyzer.persistence.graph_storage import GraphStorage
from dependency_analyzer.orchestration.analysis_workflow import AnalysisWorkflow
from plsql_analyzer.persistence.database_manager import DatabaseManager


def main() -> None:
    """
    Main entry point for the Dependency Analyzer application.

    Orchestrates the process of:
    1. Setting up configuration and logging.
    2. Connecting to the database populated by `plsql_analyzer`.
    3. Loading code objects from the database.
    4. Constructing a dependency graph.
    5. Saving the constructed graph.
    6. Running an analysis workflow (e.g., finding cycles, unused objects, visualizations).
    7. Reporting performance profiling statistics.
    """
    # --- Profiling Setup ---
    profiler = cProfile.Profile()
    profiler.enable()

    # --- 1. Initial Setup (Config and Logging) ---
    # Ensure artifact directories (logs, graphs, visualizations) exist
    da_config.ensure_artifact_dirs()

    # Configure logger
    # The logger instance is returned but also globally configured by `configure_logger`
    logger = configure_logger(da_config.LOG_VERBOSE_LEVEL, da_config.LOGS_DIR)
    logger.info(f"Dependency Analyzer started. Base directory: {da_config.BASE_DIR}")
    logger.info(f"Artifacts will be stored in: {da_config.ARTIFACTS_DIR}")
    logger.info(f"Using database: {da_config.DATABASE_PATH}")

    if DatabaseManager is None: # Check if import failed
        logger.critical("DatabaseManager from plsql_analyzer could not be imported. Cannot proceed.")
        return

    # --- 2. Database Connection ---
    logger.info("Initializing DatabaseManager...")
    db_manager = DatabaseManager(da_config.DATABASE_PATH, logger)
    # Test connection or check if DB exists
    if not da_config.DATABASE_PATH.exists():
        logger.critical(f"Database file not found at {da_config.DATABASE_PATH}. "
                        "Please run plsql_analyzer first to generate the database.")
        return

    # --- 3. Load Code Objects ---
    logger.info("Initializing DatabaseLoader to load code objects...")
    loader = DatabaseLoader(db_manager, logger)
    code_objects = loader.load_all_objects()

    if not code_objects:
        logger.warning("No code objects were loaded from the database. The resulting graph will be empty.")
        # Decide whether to proceed or exit. For now, proceed to see empty graph handling.
    else:
        logger.info(f"Successfully loaded {len(code_objects)} PLSQL_CodeObject instances from the database.")

    # --- 4. Build Dependency Graph ---
    logger.info("Initializing GraphConstructor to build the dependency graph...")
    # Assuming GraphConstructor is robust enough for empty code_objects list
    graph_constructor = GraphConstructor(code_objects, logger, verbose=(da_config.LOG_VERBOSE_LEVEL >= 2))
    dependency_graph, out_of_scope_calls = graph_constructor.build_graph()

    logger.info(
        f"Graph construction complete. "
        f"Graph has {dependency_graph.number_of_nodes()} nodes and {dependency_graph.number_of_edges()} edges."
    )
    if out_of_scope_calls:
        logger.warning(f"Encountered {len(out_of_scope_calls)} out-of-scope/unresolved calls during graph construction.")
        # Details are logged by GraphConstructor

    # --- 5. Save Graph ---
    logger.info("Initializing GraphStorage to save the constructed graph...")
    graph_storage = GraphStorage(logger)
    # Construct a unique filename for the graph
    graph_filename = f"dependency_graph_{da_config.TIMESTAMP}.{da_config.DEFAULT_GRAPH_FORMAT}"
    graph_filepath = da_config.GRAPHS_DIR / graph_filename

    save_success = graph_storage.save_graph(dependency_graph, graph_filepath, format=da_config.DEFAULT_GRAPH_FORMAT)
    if save_success:
        logger.info(f"Dependency graph saved successfully to: {graph_filepath}")
    else:
        logger.error(f"Failed to save dependency graph to: {graph_filepath}")

    # --- 6. Run Analysis Workflow ---
    if dependency_graph.number_of_nodes() > 0 : # Only run workflow if graph is not empty
        logger.info("Initializing AnalysisWorkflow to perform analyses and generate visualizations...")
        analysis_workflow = AnalysisWorkflow(
            config_module=da_config, # Pass the config module
            logger=logger,
            graph=dependency_graph,
            graph_storage=graph_storage # Pass storage for potential re-use (e.g. loading subgraphs)
        )
        analysis_workflow.run()
        logger.info("Analysis workflow completed.")
    else:
        logger.info("Skipping analysis workflow as the graph is empty.")


    # --- Finalize Profiling ---
    profiler.disable()
    s = io.StringIO()
    # Sort stats by cumulative time
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats() # Print to the StringIO stream
    
    # Log profiling results
    logger.info("--- CProfile Statistics ---")
    # Split the string output by lines and log each line
    for line in s.getvalue().splitlines():
        logger.info(line)
    logger.info("--- End CProfile Statistics ---")
    
    # Optionally, dump stats to a file for more detailed analysis (e.g., with snakeviz)
    profile_dump_path = da_config.LOGS_DIR / f"dependency_analyzer_profile_{da_config.TIMESTAMP}.prof"
    try:
        profiler.dump_stats(profile_dump_path)
        print(f"Profiler data dumped to: {profile_dump_path}")
    except Exception as e:
        logger.error(f"Failed to dump profiler stats: {e}")

    logger.info("Dependency Analyzer finished.")


if __name__ == "__main__":
    # This block allows the script to be run directly, e.g., `python -m dependency_analyzer`
    # or `python path/to/dependency_analyzer/__init__.py` (if project root is in PYTHONPATH).

    # The sys.path modification at the top of the file helps if running the script directly
    # from within its package structure without the package being formally "installed".

    # Call the main function
    main()
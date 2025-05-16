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
from plsql_analyzer.persistence.database_manager import DatabaseManager
from loguru import logger


def main_cli():
    """
    Entry point for the CLI using cyclopts.
    This function will typically be called by the console script.
    """
    # --- Profiling Setup ---
    profiler = None
    if getattr(da_config, "ENABLE_PROFILER", False):
        profiler = cProfile.Profile()
        profiler.enable()

    try:
        from dependency_analyzer.cli import app # Import the cyclopts app
        app() # Run the cyclopts app
    except ImportError:
        # Use logger instead of print
        logger.error("Could not import CLI components. Ensure cyclopts is installed and project structure is correct.")
        # Fallback or raise error
    except Exception as e:
        # Use logger instead of print
        logger.error(f"An unexpected error occurred in CLI execution: {e}")
    finally:
        # --- Finalize Profiling ---
        if profiler is not None:
            profiler.disable()
            s = io.StringIO()
            # Sort stats by cumulative time
            ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
            ps.print_stats() # Print to the StringIO stream

            # Optionally, dump stats to a file for more detailed analysis (e.g., with snakeviz)
            profile_dump_path = da_config.LOGS_DIR / f"dependency_analyzer_profile_{da_config.TIMESTAMP}.prof"
            try:
                profiler.dump_stats(profile_dump_path)
                # Use logger instead of print
                logger.info(f"Profiler data dumped to: {profile_dump_path}")
            except Exception as e:
                # This already uses logger, assuming it's configured
                logger.error(f"Failed to dump profiler stats: {e}")

        # Use logger instead of print (assuming this was intended as a final log)
        logger.info("Dependency Analyzer finished.")


if __name__ == "__main__":
    # This allows running the CLI via `python -m dependency_analyzer`
    # or `python path/to/dependency_analyzer/__init__.py`
    # Assuming configure_logger is called elsewhere to set up loguru handlers
    # If not, you might need to add logger.add(...) here or in configure_logger
    main_cli()

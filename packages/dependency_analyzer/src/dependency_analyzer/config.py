"""
Configuration module for the Dependency Analyzer package.

Handles settings for paths, logging, graph processing, and artifact storage.
Reads some configurations from environment variables if available.
"""
from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
import loguru as lg # type: ignore

# --- Base Directories ---
# Assumes this config.py is at packages/dependency_analyzer/src/dependency_analyzer/config.py
# So, BASE_DIR should be the root of the CodeMorph project.
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "generated"

ARTIFACTS_DIR = BASE_DIR / "artifacts"
LOGS_DIR = ARTIFACTS_DIR / "logs" / "dependency_analyzer"
GRAPHS_DIR = ARTIFACTS_DIR / "graphs"
VISUALIZATIONS_DIR = ARTIFACTS_DIR / "visualizations"

# --- Database Configuration ---
# Path to the database created by the plsql_analyzer package.
DATABASE_PATH = ARTIFACTS_DIR / "PLSQL_Analysis_Test.db"

# --- Logging Configuration ---
# Verbosity level for console logging:
# 0: WARNING
# 1: INFO (default)
# 2: DEBUG
# 3: TRACE
# Can be overridden by the DEPENDENCY_ANALYZER_VERBOSE environment variable.
LOG_VERBOSE_LEVEL = 1

# --- Graph Storage Configuration ---
# Default format for saving and loading graphs.
# Options: "gpickle" (Python-specific, fast), "graphml" (XML, interoperable),
#          "gexf" (XML, for Gephi), "json" (node-link format for web).
DEFAULT_GRAPH_FORMAT = os.environ.get("DEPENDENCY_ANALYZER_GRAPH_FORMAT", "gpickle").lower()
VALID_GRAPH_FORMATS = ["gpickle", "graphml", "gexf", "json"]
if DEFAULT_GRAPH_FORMAT not in VALID_GRAPH_FORMATS:
    lg.logger.warning(
        f"Invalid DEFAULT_GRAPH_FORMAT '{DEFAULT_GRAPH_FORMAT}'. "
        f"Falling back to 'gpickle'. Valid options are: {VALID_GRAPH_FORMATS}"
    )
    DEFAULT_GRAPH_FORMAT = "gpickle"

# Timestamp for unique filenames (e.g., for logs, graphs).
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# --- Visualization Configuration ---
DEFAULT_VISUALIZATION_ENGINE = "graphviz" # "pyvis" or "graphviz"
PACKAGE_COLORS_DEFAULT: dict[str, str] = {
    "SYS": "lightcoral",
    "DBMS_": "lightblue",
    "UTL_": "lightgreen",
    "STANDARD": "lightgoldenrodyellow",
    "UNKNOWN": "whitesmoke", # For placeholder nodes
    # Add more application-specific package prefixes and their colors
    "APP_CORE": "khaki",
    "APP_SERVICE": "mediumpurple",
    "APP_UTIL": "lightseagreen",
}


def ensure_artifact_dirs() -> None:
    """
    Creates necessary artifact directories if they don't already exist.

    This function is typically called at the beginning of the main application script.
    """
    dirs_to_create = [LOGS_DIR, GRAPHS_DIR, VISUALIZATIONS_DIR]
    for dir_path in dirs_to_create:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            # lg.logger.trace(f"Ensured directory exists: {dir_path}") # Too verbose for INFO
        except OSError as e:
            # Use a pre-configured logger if possible, or print if logger not yet set up.
            error_msg = f"Error creating directory {dir_path}: {e}"
            try:
                lg.logger.error(error_msg)
            except Exception: # Fallback if logger is not available/configured
                print(f"ERROR: {error_msg}")
            # Depending on severity, might raise the error or exit
            # For now, just log it.

if __name__ == "__main__":
    # Example of how to use this module and print some config values
    # This block will run if the script is executed directly.
    ensure_artifact_dirs() # Create dirs if they don't exist

    print(f"Base Directory: {BASE_DIR}")
    print(f"Artifacts Directory: {ARTIFACTS_DIR}")
    print(f"Logs Directory: {LOGS_DIR}")
    print(f"Graphs Directory: {GRAPHS_DIR}")
    print(f"Visualizations Directory: {VISUALIZATIONS_DIR}")
    print(f"Database Path: {DATABASE_PATH}")
    print(f"Log Verbose Level: {LOG_VERBOSE_LEVEL}")
    print(f"Default Graph Format: {DEFAULT_GRAPH_FORMAT}")
    print(f"Current Timestamp Suffix: {TIMESTAMP}")

    # Test logger (it might not be fully configured here as this is just config.py)
    lg.logger.info("Config module executed directly (for testing).")
    lg.logger.info(f"Test: Artifact directories ensured. Check {ARTIFACTS_DIR}.")
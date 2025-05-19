# PL/SQL Analyzer (`plsql-analyzer`)

## Overview

The `plsql-analyzer` is a Python package designed to parse and analyze PL/SQL source code. It extracts structural information, procedure/function signatures, call dependencies, and other relevant metadata from PL/SQL files (packages, procedures, functions). The extracted information is then stored in a SQLite database for further analysis, such as dependency graph construction or migration assessment.

This package is a core component of the CodeMorph project, aimed at facilitating the migration of legacy PL/SQL codebases.

## Features

*   **Structural Parsing**: Identifies PL/SQL blocks like packages, procedures, functions, loops, and conditional statements.
*   **Signature Parsing**: Extracts detailed information about procedure and function signatures, including parameters (name, mode, type, default value) and return types.
*   **Call Extraction**: Identifies calls made from one PL/SQL object to another, capturing both positional and named parameters.
*   **Code Cleaning**: Preprocesses PL/SQL code by removing comments and replacing string literals with placeholders to simplify parsing.
*   **Persistent Storage**: Stores extracted metadata and file processing status in a SQLite database using `DatabaseManager`.
*   **Change Detection**: Processes only new or modified files based on their content hash.
*   **Configurable**: Behavior can be customized through a TOML configuration file or CLI arguments.
*   **Logging**: Comprehensive logging using `loguru` for diagnostics and tracing.
*   **Profiling Scripts**: Includes scripts to profile the performance of key parsing components.
*   **Unit Tested**: Comes with a suite of unit tests using `pytest`.

## Directory Structure

```
plsql_analyzer/
├── pyproject.toml        # Project metadata, dependencies, and build configuration
├── README.md             # This file
├── profiling_scripts/    # Scripts for performance profiling
│   ├── profile_extraction_workflow.py
│   ├── profile_signature_parser.py
│   └── profile_structural_parser.py
├── src/
│   └── plsql_analyzer/   # Source code for the package
│       ├── __init__.py   # Main entry point, `main()` function
│       ├── config.py     # Configuration settings
│       ├── core/         # Core data structures
│       │   ├── __init__.py
│       │   └── code_object.py # Defines PLSQL_CodeObject
│       ├── orchestration/  # Workflow management
│       │   ├── __init__.py
│       │   └── extraction_workflow.py # Orchestrates the parsing process
│       ├── parsing/      # Parsing modules
│       │   ├── __init__.py
│       │   ├── call_extractor.py
│       │   ├── signature_parser.py
│       │   └── structural_parser.py
│       ├── persistence/  # Database interaction
│       │   ├── __init__.py
│       │   └── database_manager.py
│       └── utils/        # Utility functions
│           ├── __init__.py
│           ├── file_helpers.py
│           └── logging_setup.py
└── tests/                # Unit tests
    ├── conftest.py       # Pytest configuration and fixtures
    ├── core/
    ├── orchestration/
    ├── parsing/
    ├── persistence/
    └── utils/
```

## Installation

The package is managed using a `pyproject.toml` file.

1.  **Prerequisites**:
    *   Python >= 3.12
    *   A build backend like Hatchling (specified in `pyproject.toml`)

2.  **Install Dependencies**:
    Navigate to the `packages/plsql_analyzer` directory. You can install the package and its dependencies using a tool that supports `pyproject.toml`, such as `pip`:
    ```bash
    pip install .
    ```
    To include development dependencies (like `pytest` for testing):
    ```bash
    pip install .[dev]
    ```

## Usage

The primary way to use the PL/SQL Analyzer is through its command-line interface (CLI):

```bash
plsql-analyzer analyze [OPTIONS]
```

### CLI Options

The following options are available for the `analyze` command:

*   `--source-dir DIRECTORY`: Specifies the root directory containing the PL/SQL source code to be analyzed.
    *   Example: `plsql-analyzer analyze --source-dir ./my_plsql_project/src`
*   `--output-dir DIRECTORY`: Specifies the base directory where analysis artifacts (database, logs, etc.) will be stored.
    *   Example: `plsql-analyzer analyze --output-dir ./analysis_results`
*   `--config-file FILE`: Specifies the path to a custom configuration TOML file. If not provided falls back to default values or other cli options given.
    *   Example: `plsql-analyzer analyze --config-file ./custom_config.toml`
*   `-v, --verbose INTEGER`: Sets the verbosity level for logging.
    *   `0`: ERROR
    *   `1`: INFO (default)
    *   `2`: DEBUG
    *   `3`: TRACE
    *   Example: `plsql-analyzer analyze -v 2`
*   `--profile / --no-profile`: Enables or disables performance profiling of the analyzer. Defaults to `no-profile`.
    *   Example: `plsql-analyzer analyze --profile`
*   `--force-reprocess TEXT`: A comma-separated list of file paths (relative to `source-dir`) that should be reprocessed even if they haven't changed since the last analysis.
    *   Example: `plsql-analyzer analyze --force-reprocess "schema1/package1.pkb,schema2/procedure1.sql"`
*   `--clear-history-for-file TEXT`: A comma-separated list of file paths (relative to `source-dir`) for which historical processing records should be cleared before analysis. This is useful if a file's history is corrupted or needs a fresh start.
    *   Example: `plsql-analyzer analyze --clear-history-for-file "schema1/old_package.pks"`

## Configuration

### Configuration File (`plsql_analyzer_config.toml`)

The PL/SQL Analyzer can be configured using a TOML file, typically named `plsql_analyzer_config.toml`.

*   **Purpose**: The TOML configuration file allows you to set various parameters for the analysis process, providing more granular control than CLI arguments alone.
*   **Location**: You can specify a different location using the `--config-file` CLI option.
*   **Interaction with CLI Arguments**: CLI arguments generally override the corresponding settings in the configuration file. For example, if `source_code_root_dir` is set in the TOML file and `--source-dir` is also provided on the command line, the CLI value will be used.

### Key Configuration Parameters

Here are some of the key parameters you can set in `plsql_analyzer_config.toml`:

*   `source_code_root_dir` (string): The root directory of your PL/SQL source code.
    *   Example: `source_code_root_dir = "project/sql_sources"`
*   `output_base_dir` (string): The directory where output artifacts (like the analysis database and logs) will be saved.
    *   Example: `output_base_dir = "analysis_output"`
*   `file_extensions_to_include` (array of strings): A list of file extensions to be considered as PL/SQL files.
    *   Example: `file_extensions_to_include = ["sql", "pks", "pkb", "fnc", "prc"]`
*   `log_verbose_level` (integer): Sets the logging verbosity (0=ERROR, 1=INFO, 2=DEBUG, 3=TRACE).
    *   Example: `log_verbose_level = 1`
*   `database_filename` (string): The name of the SQLite database file where analysis results will be stored.
    *   Example: `database_filename = "plsql_analysis.db"`
*   `exclude_names_from_processed_path` (array of strings): A list of directory or file name patterns to exclude from processing. This helps in ignoring irrelevant files or temporary directories.
    *   Example: `exclude_names_from_processed_path = [".svn", "temp_files"]`
*   `exclude_names_for_package_derivation` (array of strings): A list of directory names to exclude when trying to derive a package name from a file's path. For instance, if your files are in `packages/my_pkg/file.sql`, and `packages` is in this list, `my_pkg` might be considered part of the package name.
    *   Example: `exclude_names_for_package_derivation = ["PACKAGE_BODIES", "PROCEDURES"]`
*   `enable_profiler` (boolean): Set to `true` to enable performance profiling of the analyzer.
    *   Example: `enable_profiler = false`
*   `call_extractor_keywords_to_drop` (array of strings): A list of keywords that should be ignored by the call extractor. This is useful for filtering out common SQL functions or keywords that are not relevant for dependency analysis.
    *   Example: `call_extractor_keywords_to_drop = ["COUNT", "SUM", "DBMS_OUTPUT.PUT_LINE"]`
*   `force_reprocess` (array of strings, optional): A list of file paths (relative to `source_code_root_dir`) to force reprocess.
    *   Example: `force_reprocess = ["schema_app_core/functions/is_employee_active.sql"]`
*   `clear_history_for_file` (array of strings, optional): A list of file paths (relative to `source_code_root_dir`) to clear processing history for.
    *   Example: `clear_history_for_file = ["schema_app_core/procedures/old_unused_procedure.sql"]`

See the example `plsql_analyzer_config.toml` in the project root for more details and default values.

## Core Components

*   **__init__.py**:
    Contains the `main()` function, which serves as the entry point for the analyzer. It orchestrates the setup of logging, database, parsers, and the extraction workflow.

*   **`src/plsql_analyzer/core/code_object.py`**:
    Defines the `PLSQL_CodeObject` class, which is the central data structure for storing information about each parsed PL/SQL entity (procedure, function, package). It includes attributes for name, type, parameters, return type, extracted calls, source code location, etc. Also defines `CodeObjectType` enum.

*   **`src/plsql_analyzer/parsing/structural_parser.py`**:
    The `PlSqlStructuralParser` class is responsible for analyzing the overall structure of PL/SQL code. It identifies packages, procedures, functions, and block structures (IF, LOOP, BEGIN/END) by processing the code line by line and maintaining a scope stack.

*   **`src/plsql_analyzer/parsing/signature_parser.py`**:
    The `PLSQLSignatureParser` class uses `pyparsing` to parse the signature of procedures and functions. It extracts the name, parameters (including mode, type, and default values), and return type for functions.

*   **`src/plsql_analyzer/parsing/call_extractor.py`**:
    The `CallDetailExtractor` class identifies calls to other procedures or functions within a PL/SQL code block. It uses `pyparsing` and custom logic to find call names and extract their positional and named arguments. It also handles preprocessing of code to remove comments and map string literals.

*   **`src/plsql_analyzer/orchestration/extraction_workflow.py`**:
    The `ExtractionWorkflow` class manages the end-to-end process of analyzing PL/SQL files. It iterates through source files, checks for modifications using file hashes, and coordinates the actions of the various parsers and the database manager to extract and store data. Includes the `clean_code_and_map_literals` utility function.

*   **`src/plsql_analyzer/persistence/database_manager.py`**:
    The `DatabaseManager` class handles all interactions with the SQLite database. This includes setting up the schema, storing and retrieving file processing status (hashes), and adding/querying `PLSQL_CodeObject` data.

*   **`src/plsql_analyzer/utils/logging_setup.py`**:
    The `configure_logger` function sets up `loguru` for console and file-based logging, with configurable verbosity levels.

*   **`src/plsql_analyzer/utils/file_helpers.py`**:
    The `FileHelpers` class provides utility functions for file operations, such as computing file hashes and deriving package names from file paths.

## Profiling

The package includes scripts in the `profiling_scripts/` directory to help analyze the performance of key components:
*   profile_extraction_workflow.py: Profiles the entire extraction workflow.
*   `profiling_scripts/profile_signature_parser.py`: Profiles the `PLSQLSignatureParser`.
*   `profiling_scripts/profile_structural_parser.py`: Profiles the `PlSqlStructuralParser`.

These scripts use `cProfile` and `pstats` and can generate `.prof` files that can be visualized with tools like `snakeviz`.

## Testing

Unit tests are written using the `pytest` framework and are located in the `tests/` directory, mirroring the structure of the src directory.

To run the tests:
1.  Ensure you have installed the development dependencies: `pip install .[dev]`
2.  Navigate to the plsql_analyzer directory.
3.  Run `pytest`:
    ```bash
    pytest
    ```
    You can also run with coverage:
    ```bash
    pytest --cov=src/plsql_analyzer
    ```

Test fixtures and common configurations are defined in `tests/conftest.py`.

## Dependencies

Main dependencies are listed in pyproject.toml:
*   `loguru`: For flexible and powerful logging.
*   `pyparsing`: Used for defining grammars for signature and call extraction.
*   `regex`: An alternative regular expression module (potentially used for more advanced regex features if needed, though standard `re` is also used).
*   `tqdm`: For progress bars during file processing.

Development dependencies include:
*   `pytest` and related plugins (`pytest-cov`, `pytest-mock`, `pytest-xdist`) for testing.
*   `ipykernel`, `ipywidgets` for interactive development (e.g., Jupyter notebooks).
*   `snakeviz` for visualizing profiling data.

## Contributing

Contributions are welcome! Please follow these general guidelines:
*   Adhere to the coding style and conventions used in the project (PEP 8, type hinting).
*   Write unit tests for new features or bug fixes.
*   Update documentation if applicable.
*   Ensure tests pass before submitting a pull request.
*   Follow conventional commit messages.

## License

(License information to be added here if applicable)

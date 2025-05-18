# PL/SQL Analyzer (`plsql-analyzer`)
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
*   **Configurable**: Behavior can be customized through `config.py` (e.g., source directories, file extensions, keywords to ignore).
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

## Configuration

The primary configuration for the `plsql-analyzer` is managed in [`src/plsql_analyzer/config.py`](src/plsql_analyzer/config.py). Key settings include:

*   `BASE_DIR`: Base directory for generated artifacts.
*   `ARTIFACTS_DIR`: Directory for storing artifacts like logs and the database.
*   `LOGS_DIR`: Specific directory for log files.
*   `DATABASE_PATH`: Path to the SQLite database file.
*   `SOURCE_CODE_ROOT_DIR`: Path to the root directory of your PL/SQL source code. **This needs to be configured by the user.**
*   `FILE_EXTENSION`: The file extension(s) to scan for PL/SQL files (e.g., "sql", "pks", "pkb").
*   `LOG_VERBOSE_LEVEL`: Controls console logging verbosity (0=WARNING, 1=INFO, 2=DEBUG, 3=TRACE).
*   `EXCLUDE_FROM_PROCESSED_PATH`: List of path segments to exclude when forming processed file paths for database records.
*   `EXCLUDE_FROM_PATH_FOR_PACKAGE_DERIVATION`: List of path segments to exclude when deriving package names from file paths.
*   `CALL_EXTRACTOR_KEYWORDS_TO_DROP`: A list of PL/SQL keywords to ignore during call extraction to reduce noise.
*   `REMOVE_FPATH`: A list of specific file paths to remove/ignore from processing.

Modify [`src/plsql_analyzer/config.py`](src/plsql_analyzer/config.py) to suit your environment and PL/SQL codebase.

## Usage

The `plsql-analyzer` can be run as a script, which will initiate the extraction workflow:

```bash
python -m plsql_analyzer
```
Alternatively, if the package is installed and the script `plsql-analyzer` is in your PATH (as defined in pyproject.toml):
```bash
plsql-analyzer
```

The main workflow will:
1.  Configure logging.
2.  Initialize the database and ensure the schema is set up.
3.  Scan the `SOURCE_CODE_ROOT_DIR` for PL/SQL files.
4.  For each new or modified file (based on hash comparison):
    *   Clean the code (remove comments, replace literals).
    *   Perform structural parsing to identify code objects.
    *   Perform signature parsing for procedures and functions.
    *   Extract calls made by each object.
    *   Store the extracted `PLSQL_CodeObject` instances in the database.
5.  Log a summary of the extraction process.

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

*   **file_helpers.py**:
    The `FileHelpers` class provides utility functions for file operations, such as computing file hashes and deriving package names from file paths.

## Profiling

The package includes scripts in the `profiling_scripts/` directory to help analyze the performance of key components:
*   profile_extraction_workflow.py: Profiles the entire extraction workflow.
*   `profile_signature_parser.py`: Profiles the `PLSQLSignatureParser`.
*   `profile_structural_parser.py`: Profiles the `PlSqlStructuralParser`.

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

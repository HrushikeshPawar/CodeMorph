---
applyTo: '**'
---
## Core Practices

1.  **Changelog Maintenance**:
    *   All significant changes to the codebase (new features, bug fixes, refactoring) must be recorded in `changelog.md`.
    *   Each entry should include the current timestamp (YYYY-MM-DD HH:MM:SS) and a concise description of the change.
    *   Example entry:
        ```markdown
        ## 2025-05-16 14:30:00
        - Modified `main()` in `dependency_analyzer/__init__.py` to make profiling optional based on `config.ENABLE_PROFILER`.
        - Added `ENABLE_PROFILER` to `dependency_analyzer/config.py`, controllable via the `DEPENDENCY_ANALYZER_ENABLE_PROFILER` environment variable.
        ```

2.  **Logging**:
    *   `loguru` is the standard logging library for this project.
    *   Ensure all new modules and significant functions incorporate appropriate logging using `loguru`.
    *   Leverage `loguru`'s features for structured logging and easy configuration.

3.  **Testing**:
    *   `pytest` is the designated framework for writing and running tests.
    *   Unit tests should be placed in a `tests` subdirectory within the package or module they are testing (e.g., `packages/dependency_analyzer/src/dependency_analyzer/tests/`).
    *   Integration tests can be placed in a top-level `tests/integration` directory or a relevant package-level `tests` directory.
    *   Strive for high test coverage for new and modified code.

4.  **Code Style and Formatting**:
    *   Adhere to PEP 8 style guidelines.
    *   Use a code formatter like Black or Ruff Formatter to ensure consistent code style. Run the formatter before committing changes.
    *   Employ a linter like Ruff or Pylint to catch potential errors and style issues.

5.  **Type Hinting**:
    *   Use Python type hints for all function signatures (arguments and return types) and important variables.
    *   Run a static type checker like MyPy as part of the development or CI process.

6.  **Docstrings**:
    *   Write clear and comprehensive docstrings for all public modules, classes, functions, and methods.
    *   Follow a consistent docstring format (e.g., Google, NumPy, or reStructuredText).

7.  **Commit Messages**:
    *   Follow the Conventional Commits specification for writing commit messages. This helps in automating changelog generation and makes the commit history more readable.
    *   Example: `feat(profiler): make profiler optional via config`

8.  **Modularity and Single Responsibility**:
    *   Design functions and classes to be small, focused, and adhere to the Single Responsibility Principle (SRP).
    *   Aim for high cohesion and low coupling between modules.

9.  **Configuration Management**:
    *   Prefer external configuration (e.g., environment variables, configuration files like TOML or YAML) over hardcoding values directly in the code.
    *   Centralize configuration access, similar to the existing `config.py` pattern.

10. **Error Handling**:
    *   Implement robust error handling using specific exception types.
    *   Avoid catching generic `Exception` unless absolutely necessary and re-raising or logging appropriately.
    *   Provide informative error messages.

11. **Dependency Management**:
    *   Manage project dependencies using `pyproject.toml` (e.g., with Poetry or PDM) or a well-maintained `requirements.txt` file.
    *   Pin dependency versions to ensure reproducible builds.

12. **Security**:
    *   Be mindful of security best practices (e.g., avoid hardcoding secrets, sanitize inputs, be cautious with external process calls).
    *   Regularly update dependencies to patch security vulnerabilities.

13. **Resource Management**:
    *   Ensure proper management of resources like file handles, database connections, and network sockets, typically using `with` statements.

14. **Clarity and Readability**:
    *   Prioritize writing code that is clear, readable, and maintainable.
    *   Use meaningful variable and function names.
    *   Add comments to explain complex logic or non-obvious decisions.
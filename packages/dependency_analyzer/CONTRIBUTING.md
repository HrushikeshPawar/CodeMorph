# Contributing to Dependency Analyzer

Thank you for your interest in contributing to the Dependency Analyzer package! This document provides guidelines for contributing to this component of the CodeMorph project.

## Overview

The Dependency Analyzer is a critical component of the CodeMorph project that creates and analyzes dependency graphs from PL/SQL code objects to facilitate migration to Java SpringBoot.

## Development Setup

### Prerequisites

- Python 3.12+
- uv — a Python dependency management tool (see [uv documentation](https://github.com/uv-tool/uv) for details)
- Git

### Setting Up Development Environment

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd CodeMorph/packages/dependency_analyzer
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. **Run tests to verify setup:**
   ```bash
   uv run pytest
   ```

## Development Guidelines

### Code Style

- **Follow PEP 8**: Use consistent Python coding style
- **Type Hints**: All functions and methods must include type hints
- **Docstrings**: Use Google-style docstrings for all public functions and classes
- **Import Organization**: Use isort for import sorting

Example:
```python
from typing import List, Optional
from pathlib import Path


def analyze_graph(
    graph_path: Path,
    output_dir: Optional[Path] = None,
    verbose: bool = False
) -> List[str]:
    """Analyze a dependency graph and return classification results.
    
    Args:
        graph_path: Path to the graph file to analyze
        output_dir: Optional output directory for results
        verbose: Enable verbose logging
        
    Returns:
        List of node classifications
        
    Raises:
        FileNotFoundError: If graph file doesn't exist
        ValueError: If graph format is invalid
    """
    # Implementation here
    pass
```

### Testing

- **Write Tests**: All new features must include comprehensive tests
- **Test Coverage**: Maintain high test coverage (aim for >90%)
- **Test Types**: Include unit tests, integration tests, and CLI tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/dependency_analyzer

# Run specific test file
uv run pytest tests/test_analysis.py
```

### Logging

Use `loguru` for all logging:

```python
from loguru import logger

logger.info("Processing graph with {} nodes", len(graph.nodes))
logger.debug("Analysis parameters: {}", analysis_config)
```

### Configuration

- **TOML Configuration**: All configuration should use the TOML system
- **Pydantic Models**: Use Pydantic for configuration validation
- **Default Values**: Provide sensible defaults for all configuration options

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Follow the coding guidelines above
- Add tests for new functionality
- Update documentation if needed
- Update CHANGELOG.md with your changes

### 3. Test Your Changes

```bash
# Run tests
uv run pytest

# Test CLI functionality
dependency-analyzer --help
dependency-analyzer init
# Test your specific changes
```

### 4. Update Documentation

- Update README.md if adding new features
- Update CONFIGURATION.md if adding new config options
- Update API_REFERENCE.md if adding new CLI commands
- Add docstrings to new functions/classes

### 5. Commit and Push

```bash
git add .
git commit -m "feat: add new analysis feature

- Added cycle detection algorithm
- Enhanced CLI with new analyze command
- Updated configuration schema
- Added comprehensive tests"

git push origin feature/your-feature-name
```

## Contribution Types

### 🐛 Bug Fixes

- Fix incorrect behavior
- Improve error handling
- Resolve performance issues

### ✨ New Features

- New analysis algorithms
- Enhanced CLI commands
- Additional visualization options
- Configuration improvements

### 📚 Documentation

- Improve existing documentation
- Add examples and tutorials
- Fix typos and clarity issues

### 🔧 Maintenance

- Code refactoring
- Dependency updates
- Test improvements

## Code Review Process

1. **Create Pull Request**: Submit your changes via pull request
2. **Automated Checks**: Ensure all CI checks pass
3. **Code Review**: Address feedback from maintainers
4. **Testing**: Verify functionality works as expected
5. **Merge**: Changes will be merged after approval

## Architecture Guidelines

### Project Structure

```
packages/dependency_analyzer/
├── src/dependency_analyzer/
│   ├── cli_app.py              # Main CLI application
│   ├── cli/                    # CLI components
│   │   ├── service.py          # Business logic
│   │   └── parameters.py       # CLI parameters
│   ├── settings.py             # Configuration management
│   ├── builder/                # Graph construction
│   ├── analysis/               # Analysis algorithms
│   ├── visualization/          # Visualization engines
│   └── persistence/            # Graph storage
├── tests/                      # Test suite
├── docs/                       # Documentation
└── examples/                   # Usage examples
```

### Key Design Principles

1. **Separation of Concerns**: CLI, business logic, and algorithms should be separate
2. **Configuration-Driven**: Behavior should be configurable via TOML files
3. **Extensible**: New analysis algorithms and visualization engines should be easy to add
4. **Performance**: Handle large graphs efficiently with appropriate data structures
5. **Error Handling**: Provide clear, actionable error messages

## Performance Considerations

- Use appropriate graph formats (gpickle for performance, graphml for compatibility)
- Implement lazy loading for large datasets
- Consider memory usage when processing large graphs
- Profile performance-critical code paths

## Documentation Standards

- **Clear Examples**: Include practical examples in documentation
- **Configuration Documentation**: Document all configuration options thoroughly
- **API Documentation**: Maintain comprehensive API reference
- **Migration Guides**: Help users transition between versions

## Getting Help

- **Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use discussions for general questions and ideas
- **Code Review**: Don't hesitate to ask for feedback during development

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to the Dependency Analyzer! Your contributions help make PL/SQL to Java migration more efficient and reliable.

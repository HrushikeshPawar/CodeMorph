# Dependency Analyzer

A powerful tool for analyzing and visualizing code dependencies from PL/SQL codebases. Part of the [CodeMorph](../../README.md) project for LLM-assisted code migration.

## Overview

The Dependency Analyzer creates and analyzes dependency graphs (call graphs) from PL/SQL code objects, providing insights into code structure, relationships, and complexity. It's designed to help with code migration planning, impact analysis, and architectural understanding.

## Features

### 🔍 **Graph Construction**
- **Full Dependency Graphs**: Build complete call graphs from PL/SQL analyzer database
- **Subgraph Extraction**: Extract focused subgraphs around specific nodes
- **Multiple Formats**: Support for GraphML, GPickle, GEXF, and JSON formats
- **Complexity Metrics**: Automatic calculation of node complexity and graph metrics

### 📊 **Analysis Capabilities**
- **Node Classification**: Automatic identification of hubs, utilities, orphans, and terminals
- **Cycle Detection**: Find and analyze circular dependencies
- **Reachability Analysis**: Discover upstream/downstream dependencies
- **Path Finding**: Find shortest paths between any two nodes

### 🎨 **Visualization**
- **Engine**: Support for Graphviz visualizations
- **Customizable Styling**: Package-based coloring and node styling
- **Export Formats**: PNG, SVG, and HTML output formats

### ⚙️ **Configuration**
- **TOML Configuration**: Comprehensive configuration management
- **CLI Integration**: Powerful command-line interface with subcommands
- **Flexible Output**: Configurable output directories and formats

## Installation

The dependency analyzer is part of the CodeMorph monorepo and can be installed using either modern Python package managers or traditional pip.

### Prerequisites

- **Python >= 3.12**
- A build backend like Hatchling (automatically handled by package managers)

### Method 1: Using uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package and project manager. If you have `uv` installed:

```bash
# From the project root (installs all workspace packages)
uv sync

# Or install just the dependency analyzer
cd packages/dependency_analyzer
uv sync

# For development with all dev dependencies
uv sync --group dev
```

### Method 2: Using pip (Fallback)

If you don't have `uv` installed or prefer traditional pip:

```bash
# Navigate to the dependency analyzer directory
cd packages/dependency_analyzer

# Install the package
pip install .

# For development with all dev dependencies
pip install .[dev]
```

### Method 3: Development Installation

For development work where you want editable installs:

**With uv:**
```bash
cd packages/dependency_analyzer
uv sync --group dev
```

**With pip:**
```bash
cd packages/dependency_analyzer
pip install -e .[dev]
```

### Verifying Installation

After installation, verify it works:

```bash
dependency-analyzer --help
```

## Quick Start

### 1. Initialize Configuration

```bash
dependency-analyzer init
```

This creates a default configuration file (`dep_analyzer_config.toml`) in your current directory.

### 2. Build a Dependency Graph

```bash
# Build a full dependency graph from PL/SQL analyzer database
dependency-analyzer build full \
  --config dep_analyzer_config.toml \
  --output-fname my_graph \
  --db /path/to/PLSQL_CodeObjects.db
```

### 3. Analyze the Graph

```bash
# Classify nodes by type
dependency-analyzer analyze classify \
  --config dep_analyzer_config.toml \
  --graph-path my_graph.graphml

# Find cycles in the graph
dependency-analyzer analyze cycles \
  --config dep_analyzer_config.toml \
  --graph-path my_graph.graphml
```

### 4. Visualize Dependencies

```bash
# Create a visualization of the full graph
dependency-analyzer visualize graph \
  --config dep_analyzer_config.toml \
  --graph-path my_graph.graphml

# Create a subgraph visualization around a specific node
dependency-analyzer visualize subgraph \
  --config dep_analyzer_config.toml \
  --node-id "schema_app_core.process_payment" \
  --output-image payment_subgraph \
  --upstream-depth 2 \
  --downstream-depth 3
```

### 5. Query Graph Information

```bash
# Find what nodes are reachable from a specific node
dependency-analyzer query reachability \
  --config dep_analyzer_config.toml \
  --graph-path my_graph.graphml \
  --node-id "schema_app_core.process_payment"

# Find paths between two nodes
dependency-analyzer query paths \
  --config dep_analyzer_config.toml \
  --graph-path my_graph.graphml \
  --source-node "schema_app_core.validate_user" \
  --target-node "schema_app_core.process_payment"

# List nodes matching criteria
dependency-analyzer query list \
  --config dep_analyzer_config.toml \
  --graph-path my_graph.graphml \
  --node-type function \
  --package-filter "app_core"
```

## CLI Commands

The dependency analyzer provides a structured CLI with the following command groups:

### `init` - Initialize Configuration
Initialize a new configuration file with default settings.

```bash
dependency-analyzer init [OPTIONS]
```

**Options:**
- `--output-path PATH`: Path where to create the config file (default: current directory)
- `-v, --verbose INTEGER`: Verbosity level (0-3)

### `build` - Build Dependency Graphs

#### `build full` - Build Complete Dependency Graph
Build a full dependency graph from all code objects in the database.

```bash
dependency-analyzer build full [OPTIONS]
```

**Required Options:**
- `--config PATH`: Path to TOML configuration file
- `--output-fname TEXT`: Output filename (without extension)

**Optional Options:**
- `--db, --database PATH`: Path to PL/SQL analyzer database
- `--graph-format [graphml|gpickle|gexf|json]`: Output format
- `--verbose INTEGER`: Verbosity level (0-3)
- `--calculate-complexity BOOL`: Calculate complexity metrics (default: true)

#### `build subgraph` - Build Subgraph
Extract a subgraph around a specific node.

```bash
dependency-analyzer build subgraph [OPTIONS]
```

**Required Options:**
- `--config PATH`: Path to TOML configuration file
- `--input-path PATH`: Path to input graph file
- `--node-id TEXT`: Central node for subgraph
- `--output-fname TEXT`: Output filename

**Optional Options:**
- `--upstream-depth INTEGER`: Levels of callers to include (default: 0)
- `--downstream-depth INTEGER`: Levels of callees to include (default: all)
- `--graph-format [graphml|gpickle|gexf|json]`: Output format
- `--load-with-objects BOOL`: Load with code objects from database

### `analyze` - Analyze Dependency Graphs

#### `analyze classify` - Classify Node Types
Automatically classify nodes into categories (hubs, utilities, orphans, terminals).

```bash
dependency-analyzer analyze classify [OPTIONS]
```

**Required Options:**
- `--config PATH`: Path to TOML configuration file
- `--graph-path PATH`: Path to graph file

**Optional Options:**
- `--output-format [table|json|csv]`: Output format for results
- `--save-results BOOL`: Save classification results to graph

#### `analyze cycles` - Detect Circular Dependencies
Find and analyze cycles in the dependency graph.

```bash
dependency-analyzer analyze cycles [OPTIONS]
```

**Required Options:**
- `--config PATH`: Path to TOML configuration file
- `--graph-path PATH`: Path to graph file

**Optional Options:**
- `--min-cycle-length INTEGER`: Minimum cycle length to report
- `--max-cycle-length INTEGER`: Maximum cycle length to report
- `--output-format [table|json|csv]`: Output format for results
- `--sort-cycles [length|node_count]`: How to sort cycle results

### `visualize` - Generate Visualizations

#### `visualize graph` - Visualize Full Graph
Create a visualization of a complete dependency graph.

```bash
dependency-analyzer visualize graph [OPTIONS]
```

**Required Options:**
- `--config PATH`: Path to TOML configuration file

**Optional Options:**
- `--graph-path PATH`: Path to graph file (can be set in config)
- `--output, -o TEXT`: Output filename (without extension)
- `--graph-format [graphml|gpickle|gexf|json]`: Input graph format
- `--title TEXT`: Title for the visualization

#### `visualize subgraph` - Integrated Subgraph Visualization
Build a full graph, extract a subgraph, and visualize it in one command.

```bash
dependency-analyzer visualize subgraph [OPTIONS]
```

**Required Options:**
- `--config PATH`: Path to TOML configuration file
- `--node-id TEXT`: Central node for subgraph
- `--output-image TEXT`: Base path for output image

**Optional Options:**
- `--db, --database PATH`: Path to PL/SQL analyzer database
- `--upstream-depth INTEGER`: Levels of callers to include (default: 0)
- `--downstream-depth INTEGER`: Levels of callees to include
- `--save-full-graph TEXT`: Optional path to save full graph
- `--save-subgraph TEXT`: Optional path to save subgraph
- `--title TEXT`: Title for the visualization

### `query` - Query Graph Information

#### `query reachability` - Analyze Node Reachability
Find all nodes reachable from a specific node (upstream or downstream).

```bash
dependency-analyzer query reachability [OPTIONS]
```

**Required Options:**
- `--graph-path PATH`: Path to graph file
- `--node-id TEXT`: Node to analyze reachability from
- `--config PATH`: Path to TOML configuration file

**Optional Options:**
- `--downstream BOOL`: Show descendants (default: true)
- `--upstream BOOL`: Show ancestors (default: false)
- `--depth INTEGER`: Maximum depth to traverse

#### `query paths` - Find Paths Between Nodes
Find shortest paths between two nodes in the graph.

```bash
dependency-analyzer query paths [OPTIONS]
```

**Required Options:**
- `--graph-path PATH`: Path to graph file
- `--source-node TEXT`: Starting node
- `--target-node TEXT`: Target node
- `--config PATH`: Path to TOML configuration file

**Optional Options:**
- `--max-paths INTEGER`: Maximum number of paths to find
- `--output-format [table|json|csv]`: Output format for results

#### `query list` - List Nodes with Filtering
List nodes in the graph with various filtering options.

```bash
dependency-analyzer query list [OPTIONS]
```

**Required Options:**
- `--graph-path PATH`: Path to graph file
- `--config PATH`: Path to TOML configuration file

**Optional Options:**
- `--node-type [procedure|function|package|trigger]`: Filter by node type
- `--package-filter TEXT`: Filter by package name pattern
- `--name-filter TEXT`: Filter by node name pattern
- `--limit INTEGER`: Maximum number of results
- `--sort-by [name|type|in_degree|out_degree]`: Sort results by field
- `--output-format [table|json|csv]`: Output format for results
- `--include-node-details BOOL`: Include detailed node information

## Configuration

The dependency analyzer uses TOML configuration files for settings. Initialize a default configuration with:

```bash
dependency-analyzer init
```

### Configuration Sections

#### `[paths]` - File and Directory Paths
```toml
[paths]
# Base directory for all generated artifacts
output_base_dir = "./generated/artifacts"
# Path to the SQLite database containing PL/SQL analysis results
database_path = "./generated/artifacts/PLSQL_CodeObjects.db"
```

#### `[logging]` - Logging Configuration
```toml
[logging]
# Verbosity level for console logging (0=WARNING, 1=INFO, 2=DEBUG, 3=TRACE)
log_verbose_level = 1
```

#### `[graph]` - Graph Settings
```toml
[graph]
# Default format for saving and loading graphs
default_graph_format = "graphml"  # Options: "gpickle", "graphml", "gexf", "json"
```

#### `[visualization]` - Visualization Settings
```toml
[visualization]
# Default engine for visualizing graphs
default_visualization_engine = "graphviz"  # Options: "graphviz"
# Include package names in node labels by default
with_package_name_labels = true
# Show legend showing node type colors in visualizations
show_visualization_legend = true
```

#### `[features]` - Feature Flags
```toml
[features]
# Enable performance profiling
enable_profiler = false
```

#### `[analysis]` - Analysis Parameters
```toml
[analysis]
# Parameters for node classification
hub_degree_percentile = 0.95
hub_betweenness_percentile = 0.95
hub_pagerank_percentile = 0.95
utility_out_degree_percentile = 0.90
utility_max_complexity = 50
orphan_component_max_size = 4
```

## Output Formats

### Graph Formats
- **GraphML** (`.graphml`): XML-based format, good for visualization tools
- **GPickle** (`.gpickle`): Python pickle format, fastest for Python applications
- **GEXF** (`.gexf`): Graph Exchange XML Format, good for Gephi
- **JSON** (`.json`): JSON format, good for web applications

### Visualization Formats
- **Graphviz**: Generates static images (PNG, SVG) and DOT files

### Analysis Output Formats
- **Table**: Formatted console table output
- **JSON**: Machine-readable JSON format
- **CSV**: Spreadsheet-compatible format

## Advanced Usage

### Working with Large Graphs

For large codebases, consider these strategies:

1. **Use Structure-Only Graphs**: Save graphs without code objects for faster loading
```bash
dependency-analyzer build full
```

2. **Extract Focused Subgraphs**: Work with smaller portions of the graph
```bash
dependency-analyzer build subgraph \
  --node-id "critical_function" \
  --upstream-depth 2 \
  --downstream-depth 2
```

3. **Use Efficient Formats**: GPickle is fastest for Python applications
```bash
dependency-analyzer build full --graph-format gpickle
```

### Batch Processing

You can chain commands for batch processing:

```bash
# Build, analyze, and visualize in sequence
dependency-analyzer build full --output-fname main_graph && \
dependency-analyzer analyze classify --graph-path main_graph.graphml && \
dependency-analyzer visualize graph --graph-path main_graph.graphml
```

### Integration with Other Tools

The dependency analyzer integrates seamlessly with:

- **PL/SQL Analyzer**: Consumes its database output
- **NetworkX**: Graphs are NetworkX-compatible
- **Gephi**: Export to GEXF format for advanced network analysis
- **Graphviz**: High-quality static visualizations
- **Jupyter**: Load graphs in notebooks for custom analysis

## Error Handling

The CLI provides detailed error messages with suggestions:

```bash
$ dependency-analyzer build full --config missing.toml
❌ Error: Configuration file not found: missing.toml
💡 Suggestion: Run 'dependency-analyzer init' to create a default configuration file.
```

Common error scenarios and solutions:

1. **Missing Database**: Ensure PL/SQL analyzer has been run first
2. **Invalid Graph Path**: Check file paths and permissions
3. **Configuration Errors**: Validate TOML syntax and required fields
4. **Memory Issues**: Use structure-only graphs for large codebases

## Examples

### Example 1: Basic Workflow
```bash
# 1. Initialize configuration
dependency-analyzer init

# 2. Build full dependency graph
dependency-analyzer build full \
  --config dep_analyzer_config.toml \
  --output-fname project_graph \
  --db ./generated/artifacts/PLSQL_CodeObjects.db

# 3. Classify nodes
dependency-analyzer analyze classify \
  --config dep_analyzer_config.toml \
  --graph-path project_graph.graphml

# 4. Create visualization
dependency-analyzer visualize graph \
  --config dep_analyzer_config.toml \
  --graph-path project_graph.graphml \
  --output project_overview
```

### Example 2: Focused Analysis
```bash
# Extract and visualize a subgraph around a specific function
dependency-analyzer visualize subgraph \
  --config dep_analyzer_config.toml \
  --node-id "schema_app_core.calculate_interest" \
  --output-image interest_calculation \
  --upstream-depth 3 \
  --downstream-depth 2 \
  --title "Interest Calculation Dependencies"
```

### Example 3: Impact Analysis
```bash
# Find all functions that could be affected by changes to a specific function
dependency-analyzer query reachability \
  --graph-path project_graph.graphml \
  --node-id "schema_util.validate_input" \
  --config dep_analyzer_config.toml \
  --downstream true
```

### Example 4: Architecture Analysis
```bash
# Find cycles that might indicate architectural issues
dependency-analyzer analyze cycles \
  --config dep_analyzer_config.toml \
  --graph-path project_graph.graphml \
  --min-cycle-length 3 \
  --output-format json > cycles.json

# List all utility functions
dependency-analyzer query list \
  --graph-path project_graph.graphml \
  --config dep_analyzer_config.toml \
  --node-type function \
  --package-filter "util" \
  --sort-by out_degree
```

## Development

### Running Tests
```bash
cd packages/dependency_analyzer
uv run pytest
```

### Code Structure
- `cli_app.py`: Main CLI application with command groups
- `cli/service.py`: Business logic for CLI operations
- `cli/parameters.py`: Reusable CLI parameter definitions
- `settings.py`: TOML configuration and Pydantic models
- `builder/`: Graph construction components
- `analysis/`: Graph analysis algorithms
- `visualization/`: Visualization engines and exporters
- `persistence/`: Graph storage and loading

## Troubleshooting

### Common Issues

1. **"Database not found" error**
   - Ensure you've run the PL/SQL analyzer first
   - Check the database path in your configuration

2. **"Node not found" error**
   - Verify the node ID exists in the graph
   - Use `query list` to see available nodes

3. **Visualization fails**
   - Check that Graphviz is installed for Graphviz engine
   - Ensure output directory exists and is writable

4. **Memory issues with large graphs**
   - Extract subgraphs instead of working with full graph
   - Consider using GPickle format for better performance

### Getting Help

- Use `--help` with any command for detailed information
- Check the logs in the `generated/artifacts/logs/dependency_analyzer/` directory
- Increase verbosity with `-v 3` for detailed debugging output

## Contributing

The dependency analyzer is part of the CodeMorph project. See the main [CodeMorph README](../../README.md) for contribution guidelines.

## License

This project is licensed under the terms specified in the main CodeMorph project.
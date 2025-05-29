# Configuration Guide

This guide provides comprehensive information about configuring the Dependency Analyzer using TOML configuration files.

## Configuration File Structure

The dependency analyzer uses a TOML configuration file with the following structure:

```toml
[paths]
output_base_dir = "./generated/artifacts"
database_path = "./generated/artifacts/PLSQL_CodeObjects.db"

[logging]
log_verbose_level = 1

[graph]
default_graph_format = "graphml"

[visualization]
default_visualization_engine = "graphviz"
with_package_name_labels = true
show_visualization_legend = true

[visualization.package_colors]
SYS = "lightcoral"
DBMS_ = "lightblue"
# ... more package colors

[features]
enable_profiler = false

[analysis]
hub_degree_percentile = 0.95
hub_betweenness_percentile = 0.95
# ... more analysis parameters
```

## Configuration Sections

### `[paths]` - File and Directory Paths

Controls where the dependency analyzer reads input files and writes output files.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `output_base_dir` | String | `"./generated/artifacts"` | Base directory for all generated artifacts (graphs, visualizations, reports) |
| `database_path` | String | `"./generated/artifacts/PLSQL_CodeObjects.db"` | Path to the SQLite database from PL/SQL analyzer |

**Example:**
```toml
[paths]
output_base_dir = "/home/user/project/analysis"
database_path = "/home/user/project/data/plsql_objects.db"
```

### `[logging]` - Logging Configuration

Controls the verbosity and format of log output.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `log_verbose_level` | Integer | `1` | Logging verbosity level (0=WARNING, 1=INFO, 2=DEBUG, 3=TRACE) |

**Verbosity Levels:**
- `0` (WARNING): Only critical warnings and errors
- `1` (INFO): General progress information (default)
- `2` (DEBUG): Detailed debugging information
- `3` (TRACE): Very detailed tracing information

**Example:**
```toml
[logging]
log_verbose_level = 2  # Enable debug logging
```

### `[graph]` - Graph Settings

Controls how graphs are saved and loaded.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `default_graph_format` | String | `"graphml"` | Default format for saving/loading graphs |

**Supported Graph Formats:**
- `"graphml"`: XML-based format, widely supported
- `"gpickle"`: Python pickle format, fastest for Python applications
- `"gexf"`: Graph Exchange XML Format, good for Gephi
- `"json"`: JSON format, good for web applications

**Example:**
```toml
[graph]
default_graph_format = "gpickle"  # Use fastest format
```

### `[visualization]` - Visualization Settings

Controls how visualizations are generated and styled.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `default_visualization_engine` | String | `"graphviz"` | Engine to use for generating visualizations |
| `with_package_name_labels` | Boolean | `true` | Include package names in node labels |
| `show_visualization_legend` | Boolean | `true` | Show color legend in visualizations |

**Visualization Engines:**
- `"graphviz"`: Produces high-quality static images (PNG, SVG, DOT)

**Example:**
```toml
[visualization]
default_visualization_engine = "graphviz"
with_package_name_labels = false        # Cleaner node labels
show_visualization_legend = true        # Keep legend for clarity
```

### `[visualization.package_colors]` - Package Color Mapping

Defines colors for different packages in visualizations. This helps visually distinguish between different parts of your codebase.

**Default Colors:**
```toml
[visualization.package_colors]
SYS = "lightcoral"              # System packages
DBMS_ = "lightblue"             # Database management packages
UTL_ = "lightgreen"             # Utility packages
STANDARD = "lightgoldenrodyellow" # Standard packages
UNKNOWN = "whitesmoke"          # Unknown/unclassified packages
APP_CORE = "khaki"              # Application core packages
APP_SERVICE = "mediumpurple"    # Application service packages
APP_UTIL = "lightseagreen"      # Application utility packages
```

**Custom Colors:**
You can define colors for your specific package patterns:

```toml
[visualization.package_colors]
# Domain-specific packages
BILLING = "orange"
ACCOUNTING = "yellow"
REPORTING = "purple"
SECURITY = "red"

# Layer-specific packages
DATA_ACCESS = "lightblue"
BUSINESS_LOGIC = "lightgreen"
PRESENTATION = "lightpink"

# Environment-specific packages
TEST_ = "gray"
DEV_ = "lightgray"
```

**Color Values:**
- Named colors: `"red"`, `"blue"`, `"green"`, etc.
- Hex colors: `"#FF0000"`, `"#00FF00"`, etc.
- RGB colors: `"rgb(255,0,0)"`, etc.

### `[features]` - Feature Flags

Controls optional features and performance settings.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enable_profiler` | Boolean | `false` | Enable performance profiling during analysis |

**Example:**
```toml
[features]
enable_profiler = true  # Enable profiling for performance analysis
```

### `[analysis]` - Analysis Parameters

Controls parameters for automated graph analysis features.

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `hub_degree_percentile` | Float | `0.95` | Percentile threshold for identifying hub nodes by degree |
| `hub_betweenness_percentile` | Float | `0.95` | Percentile threshold for identifying hub nodes by betweenness centrality |
| `hub_pagerank_percentile` | Float | `0.95` | Percentile threshold for identifying hub nodes by PageRank |
| `utility_out_degree_percentile` | Float | `0.90` | Percentile threshold for identifying utility nodes by out-degree |
| `utility_max_complexity` | Integer | `50` | Maximum complexity for nodes to be considered utilities |
| `orphan_component_max_size` | Integer | `4` | Maximum size of components to be considered orphaned |

**Node Classification Parameters:**

These parameters control how the `analyze classify` command categorizes nodes:

- **Hub Nodes**: High-centrality nodes that are important connection points
  - Identified by high degree, betweenness centrality, or PageRank
  - Nodes above the specified percentile thresholds are classified as hubs

- **Utility Nodes**: Nodes that are called by many others but have low complexity
  - Identified by high out-degree but low complexity
  - Typically represent shared utility functions

- **Orphan Nodes**: Nodes in small, disconnected components
  - Identified as nodes in components smaller than `orphan_component_max_size`
  - May indicate dead code or integration issues

- **Terminal Nodes**: Leaf nodes with no outgoing dependencies
  - Automatically identified (no configuration needed)

**Example:**
```toml
[analysis]
# More aggressive hub detection
hub_degree_percentile = 0.90
hub_betweenness_percentile = 0.90
hub_pagerank_percentile = 0.90

# More permissive utility detection
utility_out_degree_percentile = 0.85
utility_max_complexity = 100

# Larger orphan component threshold
orphan_component_max_size = 10
```

## Configuration Inheritance and Overrides

### Configuration Priority

Settings are applied in the following order (later sources override earlier ones):

1. Default values (hardcoded in the application)
2. TOML configuration file
3. Command-line arguments (when available)
4. Environment variables (for some settings)

### CLI Overrides

Many settings can be overridden via command-line arguments:

```bash
# Override graph format
dependency-analyzer build full --graph-format gpickle

# Override verbosity
dependency-analyzer build full -v 3

# Override database path
dependency-analyzer build full --db /custom/path/to/database.db
```

### Environment Variables

Some settings can be controlled via environment variables:

```bash
# Set default output directory
export DEPENDENCY_ANALYZER_OUTPUT_DIR="/tmp/analysis"

# Set default database path
export DEPENDENCY_ANALYZER_DB_PATH="/data/plsql_objects.db"
```

## Configuration Validation

The dependency analyzer validates configuration files at startup and provides helpful error messages:

### Common Validation Errors

1. **Invalid graph format:**
```
❌ Error: Invalid graph format 'xyz'. Supported formats: graphml, gpickle, gexf, json
```

2. **Invalid verbosity level:**
```
❌ Error: Verbosity level must be between 0 and 3, got: 5
```

3. **Invalid directory path:**
```
❌ Error: Output directory does not exist: /nonexistent/path
💡 Suggestion: Create the directory or use an existing path
```

4. **Invalid color specification:**
```
❌ Error: Invalid color 'invalid-color' for package 'APP_CORE'
💡 Suggestion: Use named colors (red, blue) or hex colors (#FF0000)
```

## Configuration Examples

### Development Configuration

Optimized for development with detailed logging and fast formats:

```toml
[paths]
output_base_dir = "./dev_artifacts"
database_path = "./dev_data/PLSQL_CodeObjects.db"

[logging]
log_verbose_level = 3  # Detailed tracing

[graph]
default_graph_format = "gpickle"  # Fastest format

[visualization]
default_visualization_engine = "graphviz"
with_package_name_labels = true
show_visualization_legend = true

[features]
enable_profiler = true  # Monitor performance

[analysis]
# More sensitive detection for development
hub_degree_percentile = 0.85
utility_out_degree_percentile = 0.80
orphan_component_max_size = 2
```

### Production Configuration

Optimized for production with efficient formats and minimal logging:

```toml
[paths]
output_base_dir = "/data/analysis/artifacts"
database_path = "/data/plsql/PLSQL_CodeObjects.db"

[logging]
log_verbose_level = 1  # Info level only

[graph]
default_graph_format = "graphml"  # Standard format

[visualization]
default_visualization_engine = "graphviz"  # High-quality static images
with_package_name_labels = false  # Cleaner for large graphs
show_visualization_legend = true

[features]
enable_profiler = false  # No profiling overhead

[analysis]
# Standard detection thresholds
hub_degree_percentile = 0.95
hub_betweenness_percentile = 0.95
hub_pagerank_percentile = 0.95
utility_out_degree_percentile = 0.90
utility_max_complexity = 50
orphan_component_max_size = 4
```

### Large Codebase Configuration

Optimized for handling large codebases:

```toml
[paths]
output_base_dir = "/fast_storage/analysis"
database_path = "/data/large_project/PLSQL_CodeObjects.db"

[logging]
log_verbose_level = 1

[graph]
default_graph_format = "gpickle"  # Fastest for large graphs

[visualization]
default_visualization_engine = "graphviz"  # Better for large graphs
with_package_name_labels = false  # Reduce clutter
show_visualization_legend = true

[features]
enable_profiler = false

[analysis]
# Less aggressive detection for large graphs
hub_degree_percentile = 0.98
hub_betweenness_percentile = 0.98
hub_pagerank_percentile = 0.98
utility_out_degree_percentile = 0.95
utility_max_complexity = 25
orphan_component_max_size = 1
```

## Best Practices

### Directory Structure

Organize your configuration and output:

```
project/
├── config/
│   ├── dev_config.toml
│   ├── prod_config.toml
│   └── test_config.toml
├── analysis/
│   ├── graphs/
│   ├── visualizations/
│   └── reports/
└── data/
    └── PLSQL_CodeObjects.db
```

### Version Control

- **Include configuration files** in version control
- **Exclude output directories** from version control
- Use **environment-specific configurations** for different deployments

### Performance Tuning

1. **Use GPickle format** for frequently accessed graphs
2. **Disable profiling** in production
3. **Adjust analysis thresholds** based on codebase size
4. **Use structure-only graphs** for large codebases when possible

### Security Considerations

- **Protect database paths** containing sensitive information
- **Use relative paths** when possible for portability
- **Review color configurations** for accessibility compliance

## Troubleshooting Configuration

### Configuration File Not Found

```bash
❌ Error: Configuration file not found: config.toml
💡 Suggestion: Run 'dependency-analyzer init' to create a default configuration
```

**Solution:** Create a configuration file using `dependency-analyzer init` or specify an existing file.

### Invalid TOML Syntax

```bash
❌ Error: Invalid TOML syntax in configuration file
💡 Suggestion: Check line 15 for syntax errors
```

**Solution:** Validate your TOML syntax using an online TOML validator or text editor with TOML support.

### Permission Issues

```bash
❌ Error: Permission denied writing to output directory: /protected/path
💡 Suggestion: Check directory permissions or use a different output path
```

**Solution:** Ensure the output directory is writable or change the `output_base_dir` setting.

### Database Connection Issues

```bash
❌ Error: Cannot access database: /path/to/PLSQL_CodeObjects.db
💡 Suggestion: Verify the database exists and was created by plsql-analyzer
```

**Solution:** Run the PL/SQL analyzer first to create the database, or verify the database path.

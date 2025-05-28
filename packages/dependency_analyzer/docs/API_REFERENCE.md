# API Reference

This document provides a comprehensive reference for the Dependency Analyzer CLI commands and their parameters.

## Command Structure

The dependency analyzer CLI follows a hierarchical structure with command groups:

```
dependency-analyzer
├── init                    # Initialize configuration
├── build                   # Build dependency graphs
│   ├── full               # Build complete dependency graph
│   └── subgraph           # Build subgraph around specific node
├── analyze                 # Analyze dependency graphs
│   ├── classify           # Classify node types
│   └── cycles             # Detect cycles
├── visualize              # Generate visualizations
│   ├── graph              # Visualize complete graph
│   └── subgraph           # Integrated subgraph visualization
└── query                   # Query graph information
    ├── reachability       # Analyze node reachability
    ├── paths              # Find paths between nodes
    └── list               # List nodes with filtering
```

## Global Options

These options are available for most commands:

| Option | Short | Type | Description |
|--------|-------|------|-------------|
| `--verbose` | `-v` | Integer | Verbosity level (0-3) |
| `--help` | `-h` | Flag | Show command help |

## Commands Reference

### `init` - Initialize Configuration

Initialize a new configuration file with default settings.

```bash
dependency-analyzer init [OPTIONS]
```

**Options:**

| Option | Type | Default | Required | Description |
|--------|------|---------|----------|-------------|
| `--output-path` | Path | Current directory | No | Path where to create the config file |
| `--verbose` | Integer | 3 | No | Verbosity level (0-3) |

**Examples:**
```bash
# Create config in current directory
dependency-analyzer init

# Create config in specific location
dependency-analyzer init --output-path ./config/

# Create config with minimal logging
dependency-analyzer init --verbose 1
```

**Output:**
- Creates `dep_analyzer_config.toml` in the specified directory
- Displays configuration file location and basic usage instructions

---

### `build` Command Group

Commands for building dependency graphs from PL/SQL analyzer data.

#### `build full` - Build Complete Dependency Graph

Build a full dependency graph from all code objects in the database.

```bash
dependency-analyzer build full [OPTIONS]
```

**Required Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--config` | Path | Path to TOML configuration file |
| `--output-fname` | String | Output filename (without extension) |

**Optional Options:**

| Option | Aliases | Type | Default | Description |
|--------|---------|------|---------|-------------|
| `--db` | `--database` | Path | From config | Path to PL/SQL analyzer database |
| `--graph-format` | | String | From config | Output format (graphml/gpickle/gexf/json) |
| `--verbose` | `-v` | Integer | 1 | Verbosity level (0-3) |
| `--calculate-complexity` | | Boolean | true | Calculate complexity metrics for nodes |

**Examples:**
```bash
# Basic full graph build
dependency-analyzer build full \
  --config config.toml \
  --output-fname project_graph

# Build with custom database and format
dependency-analyzer build full \
  --config config.toml \
  --output-fname project_graph \
  --db /custom/path/PLSQL_CodeObjects.db \
  --graph-format gpickle

# Build without complexity calculation (faster)
dependency-analyzer build full \
  --config config.toml \
  --output-fname project_graph \
  --calculate-complexity false
```

**Output:**
- Graph file in specified format
- Statistics about nodes and edges
- Complexity metrics (if enabled)

#### `build subgraph` - Build Subgraph

Extract a subgraph around a specific node from an existing graph.

```bash
dependency-analyzer build subgraph [OPTIONS]
```

**Required Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--config` | Path | Path to TOML configuration file |
| `--input-path` | Path | Path to input graph file |
| `--node-id` | String | Central node for subgraph |
| `--output-fname` | String | Output filename (without extension) |

**Optional Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--upstream-depth` | Integer | 0 | Levels of callers to include |
| `--downstream-depth` | Integer | All | Levels of callees to include |
| `--graph-format` | String | From config | Output format |
| `--load-with-objects` | Boolean | false | Load with code objects from database |
| `--verbose` | Integer | 1 | Verbosity level (0-3) |

**Examples:**
```bash
# Extract subgraph with specific depths
dependency-analyzer build subgraph \
  --config config.toml \
  --input-path project_graph.graphml \
  --node-id "schema_app_core.process_payment" \
  --output-fname payment_subgraph \
  --upstream-depth 2 \
  --downstream-depth 3

# Extract all downstream dependencies
dependency-analyzer build subgraph \
  --config config.toml \
  --input-path project_graph.graphml \
  --node-id "schema_util.validate_input" \
  --output-fname validation_subgraph \
  --downstream-depth 999
```

**Output:**
- Subgraph file in specified format
- Statistics about included nodes and edges
- Information about depth traversal

---

### `analyze` Command Group

Commands for analyzing dependency graphs to extract insights.

#### `analyze classify` - Classify Node Types

Automatically classify nodes into categories based on graph metrics.

```bash
dependency-analyzer analyze classify [OPTIONS]
```

**Required Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--config` | Path | Path to TOML configuration file |
| `--graph-path` | Path | Path to graph file to analyze |

**Optional Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--output-format` | String | table | Output format (table/json/csv) |
| `--save-results` | Boolean | false | Save classification results to graph |
| `--graph-format` | String | From config | Input graph format |
| `--verbose` | Integer | 1 | Verbosity level (0-3) |

**Node Classifications:**
- **Hub**: High-centrality nodes (connection points)
- **Utility**: Widely-used, low-complexity functions
- **Orphan**: Nodes in small disconnected components
- **Terminal**: Leaf nodes with no dependencies

**Examples:**
```bash
# Basic classification with table output
dependency-analyzer analyze classify \
  --config config.toml \
  --graph-path project_graph.graphml

# Classification with JSON output
dependency-analyzer analyze classify \
  --config config.toml \
  --graph-path project_graph.graphml \
  --output-format json

# Save results back to graph
dependency-analyzer analyze classify \
  --config config.toml \
  --graph-path project_graph.graphml \
  --save-results true
```

**Output:**
- Classification results in specified format
- Statistics for each category
- Optional: Updated graph file with classification attributes

#### `analyze cycles` - Detect Circular Dependencies

Find and analyze cycles (circular dependencies) in the dependency graph.

```bash
dependency-analyzer analyze cycles [OPTIONS]
```

**Required Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--config` | Path | Path to TOML configuration file |
| `--graph-path` | Path | Path to graph file to analyze |

**Optional Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--min-cycle-length` | Integer | 2 | Minimum cycle length to report |
| `--max-cycle-length` | Integer | 10 | Maximum cycle length to report |
| `--output-format` | String | table | Output format (table/json/csv) |
| `--sort-cycles` | String | length | Sort by (length/node_count) |
| `--graph-format` | String | From config | Input graph format |
| `--verbose` | Integer | 1 | Verbosity level (0-3) |

**Examples:**
```bash
# Find all cycles
dependency-analyzer analyze cycles \
  --config config.toml \
  --graph-path project_graph.graphml

# Find only longer cycles
dependency-analyzer analyze cycles \
  --config config.toml \
  --graph-path project_graph.graphml \
  --min-cycle-length 4 \
  --max-cycle-length 20

# Export cycles to CSV
dependency-analyzer analyze cycles \
  --config config.toml \
  --graph-path project_graph.graphml \
  --output-format csv > cycles.csv
```

**Output:**
- List of cycles found
- Cycle statistics (length, nodes involved)
- Suggestions for breaking cycles

---

### `visualize` Command Group

Commands for generating visual representations of dependency graphs.

#### `visualize graph` - Visualize Complete Graph

Create a visualization of a complete dependency graph.

```bash
dependency-analyzer visualize graph [OPTIONS]
```

**Required Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--config` | Path | Path to TOML configuration file |

**Optional Options:**

| Option | Aliases | Type | Default | Description |
|--------|---------|------|---------|-------------|
| `--graph-path` | | Path | From config | Path to graph file |
| `--output` | `-o` | String | Auto-generated | Output filename (without extension) |
| `--graph-format` | | String | From config | Input graph format |
| `--title` | | String | None | Title for the visualization |
| `--verbose` | `-v` | Integer | 1 | Verbosity level (0-3) |

**Examples:**
```bash
# Basic visualization
dependency-analyzer visualize graph \
  --config config.toml \
  --graph-path project_graph.graphml

# Custom output and title
dependency-analyzer visualize graph \
  --config config.toml \
  --graph-path project_graph.graphml \
  --output architecture_overview \
  --title "Project Architecture Overview"

# Visualize with specific format
dependency-analyzer visualize graph \
  --config config.toml \
  --graph-path project_graph.gpickle \
  --graph-format gpickle
```

**Output:**
- Visualization files (PNG, SVG, HTML depending on engine)
- DOT file (for Graphviz engine)
- Generation statistics

#### `visualize subgraph` - Integrated Subgraph Visualization

Build a full graph, extract a subgraph, and visualize it in one integrated command.

```bash
dependency-analyzer visualize subgraph [OPTIONS]
```

**Required Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--config` | Path | Path to TOML configuration file |
| `--node-id` | String | Central node for subgraph |
| `--output-image` | String | Base path for output image (without extension) |

**Optional Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--db` | Path | From config | Path to PL/SQL analyzer database |
| `--upstream-depth` | Integer | 0 | Levels of callers to include |
| `--downstream-depth` | Integer | All | Levels of callees to include |
| `--save-full-graph` | String | None | Optional path to save full graph |
| `--save-subgraph` | String | None | Optional path to save subgraph |
| `--title` | String | Auto-generated | Title for visualization |
| `--graph-format` | String | From config | Graph format for saved files |
| `--verbose` | Integer | 1 | Verbosity level (0-3) |

**Examples:**
```bash
# Quick subgraph visualization
dependency-analyzer visualize subgraph \
  --config config.toml \
  --node-id "schema_app_core.process_payment" \
  --output-image payment_flow

# Comprehensive subgraph with saves
dependency-analyzer visualize subgraph \
  --config config.toml \
  --node-id "schema_app_core.process_payment" \
  --output-image payment_flow \
  --upstream-depth 3 \
  --downstream-depth 4 \
  --save-full-graph full_project_graph \
  --save-subgraph payment_subgraph \
  --title "Payment Processing Flow"

# Custom database and format
dependency-analyzer visualize subgraph \
  --config config.toml \
  --node-id "schema_util.validate_data" \
  --output-image validation_flow \
  --db /custom/path/PLSQL_CodeObjects.db \
  --graph-format gpickle
```

**Output:**
- Visualization files for the subgraph
- Optional: Full graph file
- Optional: Subgraph file
- Processing statistics

---

### `query` Command Group

Commands for querying specific information from dependency graphs.

#### `query reachability` - Analyze Node Reachability

Find all nodes reachable from a specific node (upstream or downstream).

```bash
dependency-analyzer query reachability [OPTIONS]
```

**Required Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--graph-path` | Path | Path to graph file |
| `--node-id` | String | Node to analyze reachability from |
| `--config` | Path | Path to TOML configuration file |

**Optional Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--downstream` | Boolean | true | Show descendants (nodes called by this node) |
| `--upstream` | Boolean | false | Show ancestors (nodes that call this node) |
| `--depth` | Integer | All | Maximum depth to traverse |
| `--graph-format` | String | From config | Input graph format |
| `--verbose` | Integer | 1 | Verbosity level (0-3) |

**Examples:**
```bash
# Find all downstream dependencies
dependency-analyzer query reachability \
  --graph-path project_graph.graphml \
  --node-id "schema_app_core.process_payment" \
  --config config.toml

# Find all upstream dependencies
dependency-analyzer query reachability \
  --graph-path project_graph.graphml \
  --node-id "schema_app_core.process_payment" \
  --config config.toml \
  --upstream true \
  --downstream false

# Limited depth analysis
dependency-analyzer query reachability \
  --graph-path project_graph.graphml \
  --node-id "schema_util.validate_input" \
  --config config.toml \
  --depth 3
```

**Output:**
- List of reachable nodes
- Depth information for each node
- Total count and statistics

#### `query paths` - Find Paths Between Nodes

Find shortest paths between two nodes in the graph.

```bash
dependency-analyzer query paths [OPTIONS]
```

**Required Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--graph-path` | Path | Path to graph file |
| `--source-node` | String | Starting node |
| `--target-node` | String | Target node |
| `--config` | Path | Path to TOML configuration file |

**Optional Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--max-paths` | Integer | 10 | Maximum number of paths to find |
| `--output-format` | String | table | Output format (table/json/csv) |
| `--graph-format` | String | From config | Input graph format |
| `--verbose` | Integer | 1 | Verbosity level (0-3) |

**Examples:**
```bash
# Find paths between two nodes
dependency-analyzer query paths \
  --graph-path project_graph.graphml \
  --source-node "schema_app_core.validate_user" \
  --target-node "schema_app_core.process_payment" \
  --config config.toml

# Find multiple paths with JSON output
dependency-analyzer query paths \
  --graph-path project_graph.graphml \
  --source-node "schema_util.log_activity" \
  --target-node "schema_app_core.finalize_transaction" \
  --config config.toml \
  --max-paths 5 \
  --output-format json
```

**Output:**
- List of paths from source to target
- Path lengths and intermediate nodes
- Alternative routing information

#### `query list` - List Nodes with Filtering

List nodes in the graph with various filtering and sorting options.

```bash
dependency-analyzer query list [OPTIONS]
```

**Required Options:**

| Option | Type | Description |
|--------|------|-------------|
| `--graph-path` | Path | Path to graph file |
| `--config` | Path | Path to TOML configuration file |

**Optional Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--node-type` | String | All | Filter by node type (procedure/function/package/trigger) |
| `--package-filter` | String | All | Filter by package name pattern |
| `--name-filter` | String | All | Filter by node name pattern |
| `--limit` | Integer | 100 | Maximum number of results |
| `--sort-by` | String | name | Sort by (name/type/in_degree/out_degree) |
| `--output-format` | String | table | Output format (table/json/csv) |
| `--include-node-details` | Boolean | false | Include detailed node information |
| `--graph-format` | String | From config | Input graph format |
| `--verbose` | Integer | 1 | Verbosity level (0-3) |

**Examples:**
```bash
# List all functions
dependency-analyzer query list \
  --graph-path project_graph.graphml \
  --config config.toml \
  --node-type function

# List utility package functions
dependency-analyzer query list \
  --graph-path project_graph.graphml \
  --config config.toml \
  --package-filter "util" \
  --node-type function \
  --sort-by out_degree

# Find nodes with specific name pattern
dependency-analyzer query list \
  --graph-path project_graph.graphml \
  --config config.toml \
  --name-filter "*validate*" \
  --include-node-details true

# Export detailed list to CSV
dependency-analyzer query list \
  --graph-path project_graph.graphml \
  --config config.toml \
  --output-format csv \
  --include-node-details true \
  --limit 1000 > nodes.csv
```

**Output:**
- Filtered list of nodes
- Node details (if requested)
- Statistics about the filtered results

## Parameter Types and Validation

### Path Parameters

All path parameters accept:
- Absolute paths: `/full/path/to/file`
- Relative paths: `./relative/path` or `../parent/path`
- Home directory: `~/path/from/home`

Validation:
- File paths must exist (for input files)
- Directory paths must be writable (for output)
- Extensions are validated against expected formats

### String Parameters

String parameters support:
- Plain text: `my_graph`
- Quoted strings: `"my complex name"`
- Special characters: `my-graph_v2.1`

### Pattern Matching

Filter parameters support glob patterns:
- `*`: Matches any characters
- `?`: Matches single character
- `[abc]`: Matches any character in brackets
- `**`: Matches directories recursively

Examples:
- `app_*`: Matches nodes starting with "app_"
- `*util*`: Matches nodes containing "util"
- `schema_[abc]*`: Matches nodes starting with "schema_a", "schema_b", or "schema_c"

### Format Validation

Graph formats are validated against supported types:
- `graphml`: GraphML XML format
- `gpickle`: Python pickle format
- `gexf`: GEXF XML format
- `json`: JSON format

Output formats are validated:
- `table`: Console table output
- `json`: JSON format
- `csv`: CSV format

## Error Handling and Messages

The CLI provides detailed error messages with suggestions:

### Common Error Patterns

1. **File Not Found:**
```bash
❌ Error: Graph file not found: project_graph.graphml
💡 Suggestion: Check the file path or run 'build full' to create a graph
```

2. **Invalid Node ID:**
```bash
❌ Error: Node 'invalid_node' not found in graph
💡 Suggestion: Use 'query list' to see available nodes
```

3. **Configuration Issues:**
```bash
❌ Error: Invalid configuration: missing required field 'output_base_dir'
💡 Suggestion: Run 'init' to create a valid configuration file
```

4. **Format Mismatch:**
```bash
❌ Error: Cannot load graph: expected GraphML format, got pickle
💡 Suggestion: Specify correct format with --graph-format gpickle
```

### Exit Codes

- `0`: Success
- `1`: General error (configuration, file not found, etc.)
- `2`: Invalid arguments or parameters
- `3`: Graph processing error
- `4`: Analysis error

## Performance Considerations

### Large Graphs

For graphs with >10,000 nodes:
- Use `gpickle` format for faster loading
- Consider extracting subgraphs instead of full analysis
- Increase verbosity to monitor progress

### Memory Usage

Commands that load full graphs into memory:
- `analyze classify`
- `analyze cycles`
- `visualize graph`
- All `query` commands

Use structure-only graphs when possible to reduce memory usage.

### Disk Space

Output files can be large:
- GraphML files: ~10x larger than gpickle
- Visualizations: PNG/SVG size depends on graph complexity
- Interactive HTML: Can be very large for complex graphs

## Integration Examples

### Shell Scripting

```bash
#!/bin/bash

# Build and analyze workflow
dependency-analyzer build full \
  --config config.toml \
  --output-fname project_graph || exit 1

dependency-analyzer analyze classify \
  --config config.toml \
  --graph-path project_graph.graphml \
  --output-format json > classification.json

dependency-analyzer analyze cycles \
  --config config.toml \
  --graph-path project_graph.graphml \
  --output-format csv > cycles.csv

echo "Analysis complete. Results saved to classification.json and cycles.csv"
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Analyze Dependencies
  run: |
    dependency-analyzer build full \
      --config .github/config.toml \
      --output-fname ci_graph \
      --verbose 1
    
    dependency-analyzer analyze cycles \
      --config .github/config.toml \
      --graph-path ci_graph.graphml \
      --output-format json > cycles.json
    
    # Fail if cycles found
    if [ -s cycles.json ]; then
      echo "❌ Circular dependencies found!"
      cat cycles.json
      exit 1
    fi
```

### Makefile Integration

```makefile
GRAPH_FILE := project_graph.graphml
CONFIG_FILE := dep_analyzer_config.toml

.PHONY: analyze-deps
analyze-deps: build-graph classify-nodes find-cycles visualize

build-graph:
	dependency-analyzer build full \
		--config $(CONFIG_FILE) \
		--output-fname project_graph

classify-nodes:
	dependency-analyzer analyze classify \
		--config $(CONFIG_FILE) \
		--graph-path $(GRAPH_FILE) \
		--save-results true

find-cycles:
	dependency-analyzer analyze cycles \
		--config $(CONFIG_FILE) \
		--graph-path $(GRAPH_FILE) \
		--output-format json > cycles.json

visualize:
	dependency-analyzer visualize graph \
		--config $(CONFIG_FILE) \
		--graph-path $(GRAPH_FILE) \
		--output architecture_diagram
```

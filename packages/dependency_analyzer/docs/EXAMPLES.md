# Dependency Analyzer Examples

This document provides comprehensive examples of using the Dependency Analyzer for various scenarios in PL/SQL to Java migration projects.

## Table of Contents

- [Basic Workflow](#basic-workflow)
- [Configuration Examples](#configuration-examples)
- [Analysis Scenarios](#analysis-scenarios)
- [Visualization Examples](#visualization-examples)
- [Advanced Use Cases](#advanced-use-cases)
- [Integration Examples](#integration-examples)
- [Troubleshooting Examples](#troubleshooting-examples)

## Basic Workflow

### Complete Analysis Pipeline

This example shows a complete workflow from initialization to visualization:

```bash
# 1. Initialize configuration
dependency-analyzer init

# 2. Build full dependency graph
dependency-analyzer build full \
  --config dep_analyzer_config.toml \
  --output-fname project_graph \
  --db ./generated/artifacts/PLSQL_CodeObjects.db

# 3. Classify nodes to understand architecture
dependency-analyzer analyze classify \
  --config dep_analyzer_config.toml \
  --graph-path project_graph.graphml

# 4. Detect cycles for refactoring planning
dependency-analyzer analyze cycles \
  --config dep_analyzer_config.toml \
  --graph-path project_graph.graphml

# 5. Create overview visualization
dependency-analyzer visualize graph \
  --config dep_analyzer_config.toml \
  --graph-path project_graph.graphml \
  --output project_overview

# 6. Query critical information (find high-degree nodes)
dependency-analyzer query list \
  --config dep_analyzer_config.toml \
  --graph-path project_graph.graphml \
  --sort-by degree \
  --limit 20
```

## Configuration Examples

### Development Environment Configuration

**dev_config.toml:**
```toml
[paths]
output_base_dir = "./dev_output"
database_path = "./test_data/PLSQL_CodeObjects.db"

[logging]
log_verbose_level = 3  # Maximum verbosity for debugging

[graph]
default_graph_format = "gpickle"  # Fastest format for development

[visualization]
default_visualization_engine = "pyvis"  # Interactive exploration
with_package_name_labels = true
show_visualization_legend = true

[features]
enable_profiler = true  # Monitor performance during development

[analysis]
# More sensitive thresholds for detailed analysis
hub_degree_percentile = 0.85
utility_out_degree_percentile = 0.80
orphan_component_max_size = 1
```

**Usage:**
```bash
dependency-analyzer build full --config dev_config.toml --output-fname dev_graph --db ./test_data/PLSQL_CodeObjects.db
```

### Production Environment Configuration

**prod_config.toml:**
```toml
[paths]
output_base_dir = "/data/analysis/artifacts"
database_path = "/data/plsql/PLSQL_CodeObjects.db"

[logging]
log_verbose_level = 1  # Info level only

[graph]
default_graph_format = "graphml"  # Standard format for production

[visualization]
default_visualization_engine = "graphviz"  # High-quality static images
with_package_name_labels = false  # Cleaner for large graphs
show_visualization_legend = true

[features]
enable_profiler = false  # No profiling overhead

[analysis]
# Standard thresholds for production analysis
hub_degree_percentile = 0.95
utility_out_degree_percentile = 0.90
orphan_component_max_size = 4
```

### Large Codebase Configuration

**large_project_config.toml:**
```toml
[paths]
output_base_dir = "/fast_storage/analysis"
database_path = "/data/large_project/PLSQL_CodeObjects.db"

[logging]
log_verbose_level = 1

[graph]
default_graph_format = "gpickle"  # Fastest for large graphs

[visualization]
default_visualization_engine = "graphviz"  # Better performance for large graphs
with_package_name_labels = false  # Reduce visual complexity
show_visualization_legend = true

[features]
enable_profiler = false

[analysis]
# Less aggressive detection for large graphs
hub_degree_percentile = 0.98
utility_out_degree_percentile = 0.95
orphan_component_max_size = 1
```

## Analysis Scenarios

### Scenario 1: Impact Analysis for Critical Component

**Objective:** Understand the impact of modifying a specific procedure.

```bash
# 1. Build the complete graph
dependency-analyzer build full \
  --config config.toml \
  --output-fname full_graph \
  --db ./data/PLSQL_CodeObjects.db

# 2. Find what depends on our target procedure
dependency-analyzer query reachability \
  --config config.toml \
  --graph-path full_graph.graphml \
  --source-node "BILLING_PKG.CALCULATE_INVOICE" \
  --downstream

# 3. Create a subgraph focusing on this component
dependency-analyzer build subgraph \
  --config config.toml \
  --graph-path full_graph.graphml \
  --node-id "BILLING_PKG.CALCULATE_INVOICE" \
  --output-fname impact_analysis \
  --downstream-depth 3

# 4. Visualize the impact
dependency-analyzer visualize subgraph \
  --config config.toml \
  --graph-path full_graph.graphml \
  --node-id "BILLING_PKG.CALCULATE_INVOICE" \
  --output impact_visualization \
  --downstream-depth 3
```

### Scenario 2: Migration Planning - Identifying Independent Modules

**Objective:** Find modules that can be migrated independently.

```bash
# 1. Build and analyze the complete graph
dependency-analyzer build full --config config.toml --output-fname complete_graph --db ./data/PLSQL_CodeObjects.db
dependency-analyzer analyze classify --config config.toml --graph-path complete_graph.graphml

# 2. Find nodes in small components (potential orphans)
dependency-analyzer query list \
  --config config.toml \
  --graph-path complete_graph.graphml \
  --sort-by degree \
  --limit 50

# 3. Analyze each orphaned component
dependency-analyzer build subgraph \
  --config config.toml \
  --graph-path complete_graph.graphml \
  --node-id "REPORTING_PKG.GENERATE_REPORT" \
  --output-fname reporting_module \
  --max-depth 2

# 4. Create visualization for stakeholder review
dependency-analyzer visualize subgraph \
  --config config.toml \
  --graph-path complete_graph.graphml \
  --node-id "REPORTING_PKG.GENERATE_REPORT" \
  --output reporting_module_viz \
  --max-depth 2
```

### Scenario 3: Refactoring Planning - Breaking Circular Dependencies

**Objective:** Identify and plan resolution of circular dependencies.

```bash
# 1. Build graph and detect cycles
dependency-analyzer build full --config config.toml --output-fname project_graph --db ./data/PLSQL_CodeObjects.db
dependency-analyzer analyze cycles --config config.toml --graph-path project_graph.graphml

# 2. Find paths between problematic components
dependency-analyzer query paths \
  --config config.toml \
  --graph-path project_graph.graphml \
  --source-node "ORDERS_PKG.CREATE_ORDER" \
  --target-node "INVENTORY_PKG.RESERVE_ITEMS"

# 3. Create focused visualization of the cycle
dependency-analyzer build subgraph \
  --config config.toml \
  --graph-path project_graph.graphml \
  --node-id "ORDERS_PKG.CREATE_ORDER" \
  --output-fname cycle_analysis \
  --max-depth 2
```

## Visualization Examples

### Example 1: Overview Visualization with Custom Colors

**config.toml:**
```toml
[visualization.package_colors]
BILLING = "orange"
INVENTORY = "lightgreen"
ORDERS = "lightblue"
CUSTOMERS = "pink"
REPORTING = "yellow"
SECURITY = "red"
UTILITIES = "lightgray"
```

**Command:**
```bash
dependency-analyzer visualize graph \
  --config config.toml \
  --graph-path project_graph.graphml \
  --output overview_colored \
  --engine graphviz
```

### Example 2: Interactive Exploration

```bash
# Create interactive visualization for exploration
dependency-analyzer visualize graph \
  --config config.toml \
  --graph-path project_graph.graphml \
  --output interactive_graph \
  --engine pyvis
```

This creates an HTML file that allows interactive exploration of the dependency graph.

### Example 3: Multiple Subgraph Visualizations

```bash
# Create visualizations for different packages
for package in BILLING ORDERS INVENTORY CUSTOMERS; do
  dependency-analyzer visualize subgraph \
    --config config.toml \
    --graph-path project_graph.graphml \
    --node-id "${package}_PKG" \
    --output "${package,,}_module" \
    --max-depth 2
done
```

## Advanced Use Cases

### Use Case 1: Automated CI/CD Integration

**Makefile example:**
```makefile
.PHONY: analyze-dependencies
analyze-dependencies:
	dependency-analyzer build full \
		--config ci_config.toml \
		--output-fname $(BUILD_ID)_graph \
		--db $(DATABASE_PATH)
	
	dependency-analyzer analyze classify \
		--config ci_config.toml \
		--graph-path $(BUILD_ID)_graph.graphml
	
	dependency-analyzer analyze cycles \
		--config ci_config.toml \
		--graph-path $(BUILD_ID)_graph.graphml

.PHONY: generate-reports
generate-reports: analyze-dependencies
	dependency-analyzer visualize graph \
		--config ci_config.toml \
		--graph-path $(BUILD_ID)_graph.graphml \
		--output $(BUILD_ID)_overview
	
	dependency-analyzer query list \
		--config ci_config.toml \
		--graph-path $(BUILD_ID)_graph.graphml \
		--sort-by degree --limit 20 > $(BUILD_ID)_high_degree_nodes.txt
```

### Use Case 2: Batch Processing Multiple Databases

**Shell script example:**
```bash
#!/bin/bash

# Process multiple project databases
PROJECTS=("project_a" "project_b" "project_c")
BASE_CONFIG="base_config.toml"

for project in "${PROJECTS[@]}"; do
    echo "Processing $project..."
    
    # Create project-specific config
    sed "s|DATABASE_PLACEHOLDER|./data/${project}/PLSQL_CodeObjects.db|g" \
        "$BASE_CONFIG" > "${project}_config.toml"
    
    # Build and analyze
    dependency-analyzer build full \
        --config "${project}_config.toml" \
        --output-fname "${project}_graph" \
        --db "./data/${project}/PLSQL_CodeObjects.db"
    
    dependency-analyzer analyze classify \
        --config "${project}_config.toml" \
        --graph-path "${project}_graph.graphml"
    
    # Generate visualization
    dependency-analyzer visualize graph \
        --config "${project}_config.toml" \
        --graph-path "${project}_graph.graphml" \
        --output "${project}_overview"
    
    echo "Completed $project"
done
```

### Use Case 3: Incremental Analysis

```bash
# Compare two versions of the codebase
dependency-analyzer build full --config config.toml --output-fname v1_graph --db ./v1/PLSQL_CodeObjects.db
dependency-analyzer build full --config config.toml --output-fname v2_graph --db ./v2/PLSQL_CodeObjects.db

# Analyze each version
dependency-analyzer analyze classify --config config.toml --graph-path v1_graph.graphml
dependency-analyzer analyze classify --config config.toml --graph-path v2_graph.graphml

# Generate comparison reports
dependency-analyzer query list --config config.toml --graph-path v1_graph.graphml --sort-by degree --limit 20 > v1_high_degree.txt
dependency-analyzer query list --config config.toml --graph-path v2_graph.graphml --sort-by degree --limit 20 > v2_high_degree.txt
diff v1_hubs.txt v2_hubs.txt
```

## Integration Examples

### Integration with Python Scripts

```python
import subprocess
from pathlib import Path

def analyze_project(database_path: Path, output_dir: Path):
    """Analyze a PL/SQL project and generate reports."""
    config_path = output_dir / "analysis_config.toml"
    graph_path = output_dir / "project_graph"
    
    # Build dependency graph
    subprocess.run([
        "dependency-analyzer", "build", "full",
        "--config", str(config_path),
        "--output-fname", str(graph_path.stem),
        "--db", str(database_path)
    ], check=True)
    
    # Perform analysis
    subprocess.run([
        "dependency-analyzer", "analyze", "classify",
        "--config", str(config_path),
        "--graph-path", f"{graph_path}.graphml"
    ], check=True)
    
    # Generate visualization
    subprocess.run([
        "dependency-analyzer", "visualize", "graph",
        "--config", str(config_path),
        "--graph-path", f"{graph_path}.graphml",
        "--output", "project_overview"
    ], check=True)

# Usage
analyze_project(
    database_path=Path("./data/PLSQL_CodeObjects.db"),
    output_dir=Path("./analysis_output")
)
```

### Integration with Data Analysis

```python
import networkx as nx
import pandas as pd

# Load graph for further analysis
G = nx.read_graphml("project_graph.graphml")

# Extract metrics for data analysis
metrics_data = []
for node in G.nodes(data=True):
    node_id, attrs = node
    metrics_data.append({
        'node_id': node_id,
        'package': attrs.get('package', ''),
        'type': attrs.get('type', ''),
        'in_degree': G.in_degree(node_id),
        'out_degree': G.out_degree(node_id),
        'classification': attrs.get('classification', '')
    })

# Create DataFrame for analysis
df = pd.DataFrame(metrics_data)
print(df.groupby('classification').size())
```

## Troubleshooting Examples

### Example 1: Memory Issues with Large Graphs

**Problem:** Out of memory when processing large codebases.

**Solution:**
```bash
# Use structure-only analysis
dependency-analyzer build full \
  --config large_config.toml \
  --output-fname large_graph \
  --db ./large_project/PLSQL_CodeObjects.db

# Use gpickle format for better performance
# Update config.toml:
# [graph]
# default_graph_format = "gpickle"
```

### Example 2: Database Connection Issues

**Problem:** Cannot connect to database.

**Diagnostic:**
```bash
# Verify database exists and is readable
ls -la ./data/PLSQL_CodeObjects.db

# Test with minimal query
dependency-analyzer query list \
  --config config.toml \
  --graph-path existing_graph.graphml \
  --limit 10
```

### Example 3: Configuration Validation Errors

**Problem:** Invalid configuration file.

**Diagnostic:**
```bash
# Initialize new config to see valid format
dependency-analyzer init --config-path debug_config.toml

# Compare with your config
diff debug_config.toml your_config.toml
```

## Performance Optimization Examples

### Large Graph Optimization

```toml
# Optimized config for large graphs
[graph]
default_graph_format = "gpickle"  # 10x faster than GraphML

[visualization]
default_visualization_engine = "graphviz"  # Better for large graphs
with_package_name_labels = false  # Reduce complexity

[features]
enable_profiler = false  # Remove profiling overhead

[analysis]
# Less aggressive detection
hub_degree_percentile = 0.98
orphan_component_max_size = 1
```

### Batch Processing Optimization

```bash
# Process in parallel for multiple analyses
dependency-analyzer build full --config config.toml --output-fname graph1 --db db1.sqlite &
dependency-analyzer build full --config config.toml --output-fname graph2 --db db2.sqlite &
dependency-analyzer build full --config config.toml --output-fname graph3 --db db3.sqlite &
wait

# Sequential analysis
for graph in graph1 graph2 graph3; do
    dependency-analyzer analyze classify --config config.toml --graph-path "${graph}.graphml"
done
```

---

These examples should cover most common usage scenarios for the Dependency Analyzer. For additional help, refer to the [API Reference](API_REFERENCE.md) and [Configuration Guide](CONFIGURATION.md).

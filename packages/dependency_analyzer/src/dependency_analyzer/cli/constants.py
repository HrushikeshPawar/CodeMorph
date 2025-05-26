"""
Constants for CLI commands.

This module contains all constant values used throughout the CLI to ensure
consistency and ease of maintenance.
"""
from __future__ import annotations

# Error message templates
ERROR_MESSAGES = {
    'file_not_found': "File not found: {path}. Please check the path and try again.",
    'graph_not_found': "Graph file not found: {path}. Make sure the file exists and is readable.",
    'invalid_format': "Unsupported format '{format}'. Supported formats: {supported_formats}",
    'node_not_found': "Node '{node_id}' not found in the graph. Use 'query' commands to list available nodes.",
    'database_not_found': "Database file not found: {path}. Run PL/SQL analyzer first to generate the database.",
    'empty_graph': "The graph is empty (no nodes found). Check if the database contains code objects.",
    'load_failed': "Failed to load graph from '{path}' using format '{format}'. {suggestion}",
    'save_failed': "Failed to save graph to '{path}' using format '{format}'. Check write permissions.",
    'invalid_percentile': "Percentile value {value} is invalid. Must be between 0.0 and 1.0.",
    'invalid_depth': "Depth value {value} is invalid. Must be a positive integer.",
    'config_load_error': "Error loading configuration from {path}: {error}",
    'permission_denied': "Permission denied accessing {path}. Check file permissions.",
}

# Success message templates  
SUCCESS_MESSAGES = {
    'graph_saved': "Graph successfully saved to {path} ({nodes} nodes, {edges} edges)",
    'config_created': "Configuration file created at {path}",
    'analysis_complete': "Analysis completed successfully. Results saved to {path}",
    'visualization_complete': "Visualization saved to {path}",
}

# Supported file formats
SUPPORTED_GRAPH_FORMATS = ["gpickle", "graphml", "gexf", "json"]
SUPPORTED_VISUALIZATION_FORMATS = ["svg", "png", "pdf", "dot"]

# Default values
DEFAULT_CONFIG_FILENAME = "dependency_analyzer_config.toml"
DEFAULT_UPSTREAM_DEPTH = 2
DEFAULT_DOWNSTREAM_DEPTH = 3
DEFAULT_MAX_PATHS = 10

# File extensions
GRAPH_EXTENSIONS = {
    '.gpickle': 'gpickle',
    '.graphml': 'graphml', 
    '.gexf': 'gexf',
    '.json': 'json'
}

VISUALIZATION_EXTENSIONS = {
    '.svg': 'svg',
    '.png': 'png', 
    '.pdf': 'pdf',
    '.dot': 'dot'
}

# Validation ranges
PERCENTILE_RANGE = (0.0, 1.0)
VERBOSE_LEVEL_RANGE = (-1, 3)
DEPTH_RANGE = (1, 100)

# Command descriptions
COMMAND_DESCRIPTIONS = {
    'init': "Initialize configuration files and setup workspace",
    'build': "Build dependency graphs from database or existing graphs",
    'analyze': "Perform various analyses on dependency graphs",
    'visualize': "Generate visual representations of graphs",
    'query': "Query specific information from graphs"
}

# Parameter help text with examples
PARAMETER_HELP = {
    'config_file': "Path to configuration file (TOML format). Example: ./config.toml",
    'graph_path': "Path to dependency graph file. Example: ./graphs/main.graphml",
    'output_fname': "Output filename without extension. Example: 'my_graph' -> 'my_graph.graphml'",
    'format': f"Graph format. Options: {', '.join(SUPPORTED_GRAPH_FORMATS)}",
    'verbose': "Logging level: 0=WARNING, 1=INFO, 2=DEBUG, 3=TRACE",
    'depth': "Maximum traversal depth (1-100). Higher values may impact performance.",
    'node_id': "Unique identifier for a graph node. Use quotes if contains spaces.",
    'node_type': "Filter by code object type (PACKAGE, PROCEDURE, FUNCTION, etc.)",
    'package_name': "Filter by package name using substring matching",
    'node_name': "Filter by node name using substring matching",
    'percentile': "Threshold percentile (0.0-1.0). Example: 0.95 = 95th percentile",
    'source_node': "Source node ID for reachability queries. Example: 'pkg1.proc1'",
    'target_node': "Target node ID for reachability queries. Example: 'pkg2.proc2'",
    'sort_by': "Sort nodes by field. Options: name, type, package, degree (default: name)",
    'limit': "Maximum number of nodes to display (default: all)",
    'min_cycle_length': "Minimum cycle length to include (default: 2). Example: --min-length 3",
    'max_cycle_length': "Maximum cycle length to include (default: unlimited). Example: --max-length 10",
    'output_format': "Output format. Options: table, json, csv (default: table)",
    'include_node_details': "Include detailed node information (type, package) in output",
    'sort_cycles': "Sort cycles by criteria. Options: length, nodes, complexity (default: length)",
}

# Suggestions for common errors
ERROR_SUGGESTIONS = {
    'corrupted_graph': "The graph file may be corrupted. Try regenerating it from the database.",
    'format_mismatch': "File extension doesn't match specified format. Let the CLI auto-detect the format.",
    'large_graph': "For large graphs, consider using 'gpickle' format for better performance.",
    'permission_fix': "Try running with appropriate permissions or changing the output directory.",
    'dependency_missing': "Required dependencies may be missing. Check installation requirements.",
}

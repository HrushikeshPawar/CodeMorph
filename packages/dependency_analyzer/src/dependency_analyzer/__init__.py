"""
Dependency Analyzer Package.

This package takes the output from plsql_analyzer (specifically, the
database of parsed PL/SQL code objects) and constructs a dependency graph.
It then performs various analyses on this graph, such as identifying
circular dependencies, unused objects, and can generate visualizations.
"""

from dependency_analyzer.analysis import (
    find_unused_objects,
    find_circular_dependencies,
    generate_subgraph_for_node,
    find_entry_points,
    find_terminal_nodes,
    get_node_degrees,
    find_all_paths,
    get_connected_components,
    calculate_node_complexity_metrics,
    get_descendants,
    get_ancestors,
    trace_downstream_paths,
    classify_nodes
)


__all__ = [
    # Analysis functions
    "find_unused_objects",
    "find_circular_dependencies",
    "generate_subgraph_for_node",
    "find_entry_points",
    "find_terminal_nodes",
    "get_node_degrees",
    "find_all_paths",
    "get_connected_components",
    "calculate_node_complexity_metrics",
    "get_descendants",
    "get_ancestors",
    "trace_downstream_paths",
    "classify_nodes",

    # 
]
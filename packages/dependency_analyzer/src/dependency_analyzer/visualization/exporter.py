# exporter.py
"""
Visualization exporters for dependency graphs.
Exports networkx.DiGraph to Graphviz and Pyvis visualizations.
"""
from __future__ import annotations
import loguru as lg
import networkx as nx
from typing import Optional
import graphviz as gv
from plsql_analyzer.core.code_object import CodeObjectType, PLSQL_CodeObject


def to_graphviz(
    graph: nx.DiGraph,
    logger: lg.Logger,
    with_package_name: bool = False,
    show_legend: bool = True,
) -> gv.Digraph:
    """
    Convert a networkx.DiGraph to a graphviz.Digraph for visualization.
    Args:
        graph: The dependency graph (networkx.DiGraph).
        logger: Logger instance for logging operations.
        with_package_name: If True, include package name in node labels.
        show_legend: If True, include a legend showing node type colors.
    Returns:
        graphviz.Digraph object.
    """
    
    logger = logger.bind(exporter_type="Graphviz")
    logger.debug("Starting Graphviz export.")
    graphviz_dependency_graph = gv.Digraph()
    graphviz_dependency_graph.attr(rankdir="LR")
    graphviz_dependency_graph.attr("node", style="filled", shape="ellipse", fontname="Arial", fontsize="12")

    excluded_node_id = []

    # Define colors and shapes based on CodeObjectType
    type_colors = {
        CodeObjectType.PACKAGE: "#ED7D31",  # Orange
        CodeObjectType.PROCEDURE: "cyan",   # Blue
        CodeObjectType.FUNCTION: "lightblue",    # Light blue
        CodeObjectType.TRIGGER: "#70AD47",   # Green
        CodeObjectType.TYPE: "#FFC000",       # Yellow
        CodeObjectType.UNKNOWN: "lightgray",    # Light gray
    }
    
    # Iterate over nodes to add them to the graph
    logger.debug(f"Adding nodes to Graphviz graph - Total nodes: {len(graph.nodes)}")
    for node in graph.nodes:

        node_data = graph.nodes[node]
        name = node_data["name"]
        object_type = node_data["type"]
        package_name = node_data["package_name"]
        
        # Get color and shape based on CodeObjectType
        color = type_colors.get(object_type, type_colors[CodeObjectType.UNKNOWN])
        shape = "ellipse"
        
        # Set node label
        if with_package_name:
            label = f"{name}\n({package_name})"
        else:
            label = name
        
        # Special handling for UNKNOWN type - dotted border
        if object_type == CodeObjectType.UNKNOWN:
            graphviz_dependency_graph.node(node, label=label, fillcolor=color, shape=shape, style='dashed, filled')
        else:
            graphviz_dependency_graph.node(node, label=label, color=color, shape=shape)
        
        logger.trace(f"Added node '{node}' to Graphviz graph.")

    for (source_node_id, target_node_id) in graph.edges:
        if source_node_id in excluded_node_id or target_node_id in excluded_node_id:
            continue
            
        # Get source node's object type for edge color
        source_obj = graph.nodes[source_node_id].get('object')
        source_code_object: Optional[PLSQL_CodeObject] = source_obj
        source_type = source_code_object.type if source_code_object else CodeObjectType.UNKNOWN
        edge_color = type_colors.get(source_type, type_colors[CodeObjectType.UNKNOWN])
        
        graphviz_dependency_graph.edge(source_node_id, target_node_id, color=edge_color)
        logger.trace(f"Added edge '{source_node_id} -> {target_node_id}' to Graphviz graph.")

    logger.info("Graphviz export completed.")
    
    # Add legend if requested
    if show_legend:
        _add_legend_to_graph(graphviz_dependency_graph, graph, type_colors, logger)
    
    return graphviz_dependency_graph


def _add_legend_to_graph(
    graphviz_graph: gv.Digraph,
    original_graph: nx.DiGraph,
    type_colors: dict,
    logger: lg.Logger
) -> None:
    """
    Add a legend cluster to the Graphviz graph showing node type colors.
    
    Args:
        graphviz_graph: The Graphviz digraph to add legend to.
        original_graph: The original NetworkX graph to analyze for present types.
        type_colors: Dictionary mapping CodeObjectType to colors.
        logger: Logger instance for logging operations.
    """
    logger.debug("Adding legend to Graphviz graph.")
    
    # Determine which CodeObjectTypes are actually present in the graph
    present_types = set()
    for node_data in original_graph.nodes.values():
        object_type = node_data.get("type")
        if object_type:
            present_types.add(object_type)
    
    if not present_types:
        logger.debug("No node types found in graph. Skipping legend creation.")
        return
    
    # Create legend cluster
    with graphviz_graph.subgraph(name='cluster_legend') as legend:
        legend.attr(
            label='Legend - Node Types',
            style='filled,rounded',
            color='gray',
            fillcolor='#f8f8f8',
            fontname='Arial',
            fontsize='14',
            labelloc='t'
        )
        legend.attr('node', fontname='Arial', fontsize='10')
        
        # Sort types for consistent ordering (convert to list and sort by name)
        sorted_types = sorted(present_types, key=lambda t: t.value if hasattr(t, 'value') else str(t))
        
        # Add legend node for each present type
        for object_type in sorted_types:
            color = type_colors.get(object_type, type_colors[CodeObjectType.UNKNOWN])
            legend_node_id = f"legend_{object_type.value if hasattr(object_type, 'value') else str(object_type)}"
            type_name = object_type.value if hasattr(object_type, 'value') else str(object_type)
            
            # Style legend nodes to match main graph nodes
            if object_type == CodeObjectType.UNKNOWN:
                legend.node(
                    legend_node_id, 
                    label=type_name,
                    fillcolor=color,
                    shape='ellipse',
                    style='dashed,filled'
                )
            else:
                legend.node(
                    legend_node_id,
                    label=type_name,
                    fillcolor=color,  # Ensure fill color is set
                    shape='ellipse',
                    style='filled'
                )
        
        # Arrange legend items vertically using invisible edges
        if len(sorted_types) > 1:
            for i in range(len(sorted_types) - 1):
                current_type = sorted_types[i]
                next_type = sorted_types[i + 1]
                current_id = f"legend_{current_type.value if hasattr(current_type, 'value') else str(current_type)}"
                next_id = f"legend_{next_type.value if hasattr(next_type, 'value') else str(next_type)}"
                legend.edge(current_id, next_id, style='invis')
    
    logger.debug(f"Legend added with {len(present_types)} node types: {[t.value if hasattr(t, 'value') else str(t) for t in sorted_types]}")

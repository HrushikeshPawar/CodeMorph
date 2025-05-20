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
    logger:lg.Logger,
    with_package_name: bool = False,
) -> gv.Digraph:
    """
    Convert a networkx.DiGraph to a graphviz.Digraph for visualization.
    Args:
        graph: The dependency graph (networkx.DiGraph).
        with_package_name: If True, include package name in node labels.
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
    return graphviz_dependency_graph

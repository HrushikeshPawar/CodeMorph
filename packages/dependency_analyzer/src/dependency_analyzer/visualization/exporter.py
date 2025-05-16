# exporter.py
"""
Visualization exporters for dependency graphs.
Exports networkx.DiGraph to Graphviz and Pyvis visualizations.
"""
from __future__ import annotations
import loguru as lg
import networkx as nx
from typing import Optional, Dict
import graphviz as gv
from pyvis.network import Network as PyvisNetwork


def to_graphviz(
    graph: nx.DiGraph,
    logger:lg.Logger,
    with_package_name: bool = False,
    package_colors: Optional[Dict[str, str]] = None,
) -> gv.Digraph:
    """
    Convert a networkx.DiGraph to a graphviz.Digraph for visualization.
    Args:
        graph: The dependency graph (networkx.DiGraph).
        with_package_name: If True, include package name in node labels.
        package_colors: Optional dict mapping package names to colors.
    Returns:
        graphviz.Digraph object.
    """
    
    logger = logger.bind(exporter_type="Graphviz")
    logger.debug("Starting Graphviz export.")
    graphviz_dependency_graph = gv.Digraph()
    graphviz_dependency_graph.attr(rankdir="LR")
    graphviz_dependency_graph.attr("node", style="filled", shape="ellipse", fontname="Arial", fontsize="12")

    package_colors = package_colors or {}
    excluded_node_id = []

    def get_package_color(key: str) -> str:
        # Default color if not found
        return package_colors.get(key.upper(), "lightgray")

    for node in graph.nodes:
        node_data = graph.nodes[node]
        if 'object' not in node_data:
            excluded_node_id.append(node)
            logger.warning(f"Node '{node}' missing 'object' attribute. Excluding from visualization.")
            continue
        codeobject = node_data['object']
        package_name = getattr(codeobject, 'package_name', 'UNKNOWN')
        color = get_package_color(package_name)
        if with_package_name:
            label = f"{getattr(codeobject, 'name', node)}\n({package_name})"
        else:
            label = getattr(codeobject, 'name', node)
        if getattr(codeobject, 'source', None):
            graphviz_dependency_graph.node(node, label=label, color=color)
        else:
            graphviz_dependency_graph.node(node, label=label, style='dashed, filled', color=color)
        logger.trace(f"Added node '{node}' to Graphviz graph.")

    for (source_node_id, target_node_id) in graph.edges:
        if source_node_id in excluded_node_id or target_node_id in excluded_node_id:
            continue
        # Try to color edge by package
        try:
            get_package_name = f"{source_node_id.split('.')[0]}.{source_node_id.split('.')[1]}".upper()
        except Exception:
            get_package_name = 'UNKNOWN'
        edge_color = get_package_color(get_package_name)
        graphviz_dependency_graph.edge(source_node_id, target_node_id, color=edge_color)
        logger.trace(f"Added edge '{source_node_id} -> {target_node_id}' to Graphviz graph.")

    logger.info("Graphviz export completed.")
    return graphviz_dependency_graph


def to_pyvis(
    graph: nx.DiGraph,
    logger:lg.Logger,
    with_package_name: bool = False,
    package_colors: Optional[Dict[str, str]] = None,
    notebook: bool = False,
    pyvis_kwargs: Optional[dict] = None,
) -> PyvisNetwork:
    """
    Convert a networkx.DiGraph to a pyvis Network for interactive visualization.
    Args:
        graph: The dependency graph (networkx.DiGraph).
        with_package_name: If True, include package name in node labels.
        package_colors: Optional dict mapping package names to colors.
        notebook: If True, enables notebook mode for inline display.
        pyvis_kwargs: Additional kwargs for pyvis Network constructor.
    Returns:
        pyvis.network.Network object.
    """
    
    logger = logger.bind(exporter_type="Pyvis")
    logger.debug("Starting Pyvis export.")
    pyvis_kwargs = pyvis_kwargs or {}
    net = PyvisNetwork(notebook=notebook, directed=True, **pyvis_kwargs)
    net.barnes_hut()  # Enable physics for better layout

    package_colors = package_colors or {}
    excluded_node_id = []

    def get_package_color(key: str) -> str:
        return package_colors.get(key.upper(), "#D3D3D3")  # lightgray

    for node in graph.nodes:
        node_data = graph.nodes[node]
        if 'object' not in node_data:
            excluded_node_id.append(node)
            logger.warning(f"Node '{node}' missing 'object' attribute. Excluding from Pyvis visualization.")
            continue
        codeobject = node_data['object']
        package_name = getattr(codeobject, 'package_name', 'UNKNOWN')
        color = get_package_color(package_name)
        if with_package_name:
            label = f"{getattr(codeobject, 'name', node)}\n({package_name})"
        else:
            label = getattr(codeobject, 'name', node)
        title = getattr(codeobject, 'signature', '') or label
        net.add_node(
            node,
            label=label,
            color=color,
            title=title,
            shape='ellipse',
            font={"face": "Arial", "size": 16},
        )
        logger.trace(f"Added node '{node}' to Pyvis network.")

    for (source_node_id, target_node_id) in graph.edges:
        if source_node_id in excluded_node_id or target_node_id in excluded_node_id:
            continue
        net.add_edge(source_node_id, target_node_id)
        logger.trace(f"Added edge '{source_node_id} -> {target_node_id}' to Pyvis network.")

    logger.info("Pyvis export completed.")
    return net

# End of exporter.py

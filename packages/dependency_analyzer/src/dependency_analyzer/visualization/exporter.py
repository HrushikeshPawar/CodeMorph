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
from pyvis.network import Network as PyvisNetwork
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
        CodeObjectType.PACKAGE: "#4472C4",   # Blue
        CodeObjectType.PROCEDURE: "#ED7D31",  # Orange
        CodeObjectType.FUNCTION: "#70AD47",   # Green
        CodeObjectType.TRIGGER: "#5B9BD5",    # Light blue
        CodeObjectType.TYPE: "#FFC000",       # Yellow
        CodeObjectType.UNKNOWN: "#D3D3D3",    # Light gray
    }
    
    type_shapes = {
        CodeObjectType.PACKAGE: "box",
        CodeObjectType.PROCEDURE: "ellipse",
        CodeObjectType.FUNCTION: "diamond",
        CodeObjectType.TRIGGER: "hexagon",
        CodeObjectType.TYPE: "parallelogram",
        CodeObjectType.UNKNOWN: "ellipse",    # Default shape but with dotted border
    }

    for node in graph.nodes:
        node_data = graph.nodes[node]
        if 'object' not in node_data:
            excluded_node_id.append(node)
            logger.warning(f"Node '{node}' missing 'object' attribute. Excluding from visualization.")
            continue
        
        code_object: PLSQL_CodeObject = node_data['object']
        object_type = code_object.type
        package_name = code_object.package_name
        
        # Get color and shape based on CodeObjectType
        color = type_colors.get(object_type, type_colors[CodeObjectType.UNKNOWN])
        shape = type_shapes.get(object_type, type_shapes[CodeObjectType.UNKNOWN])
        
        # Set node label
        if with_package_name:
            label = f"{code_object.name}\n({package_name})"
        else:
            label = code_object.name
        
        # Special handling for UNKNOWN type - dotted border
        if object_type == CodeObjectType.UNKNOWN:
            graphviz_dependency_graph.node(node, label=label, color=color, shape=shape, style='dashed, filled')
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


def to_pyvis(
    graph: nx.DiGraph,
    logger:lg.Logger,
    with_package_name: bool = False,
    notebook: bool = False,
    pyvis_kwargs: Optional[dict] = None,
) -> PyvisNetwork:
    """
    Convert a networkx.DiGraph to a pyvis Network for interactive visualization.
    Args:
        graph: The dependency graph (networkx.DiGraph).
        with_package_name: If True, include package name in node labels.
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

    excluded_node_id = []

    # Define colors and shapes based on CodeObjectType
    type_colors = {
        CodeObjectType.PACKAGE: {"background": "#4472C4", "border": "#2A4D7F"},   # Blue
        CodeObjectType.PROCEDURE: {"background": "#ED7D31", "border": "#C05F1A"},  # Orange
        CodeObjectType.FUNCTION: {"background": "#70AD47", "border": "#507B33"},   # Green
        CodeObjectType.TRIGGER: {"background": "#5B9BD5", "border": "#3F6E99"},    # Light blue
        CodeObjectType.TYPE: {"background": "#FFC000", "border": "#CC9B00"},       # Yellow
        CodeObjectType.UNKNOWN: {"background": "#D3D3D3", "border": "#A9A9A9"},    # Light gray
    }
    
    type_shapes = {
        CodeObjectType.PACKAGE: "box",
        CodeObjectType.PROCEDURE: "ellipse",
        CodeObjectType.FUNCTION: "diamond",
        CodeObjectType.TRIGGER: "hexagon",
        CodeObjectType.TYPE: "star",
        CodeObjectType.UNKNOWN: "ellipse",    # Default shape
    }

    for node in graph.nodes:
        node_data = graph.nodes[node]
        if 'object' not in node_data:
            excluded_node_id.append(node)
            logger.warning(f"Node '{node}' missing 'object' attribute. Excluding from Pyvis visualization.")
            continue
        
        code_object: PLSQL_CodeObject = node_data['object']
        object_type = code_object.type
        package_name = code_object.package_name
        
        # Get color and shape based on CodeObjectType
        color_set = type_colors.get(object_type, type_colors[CodeObjectType.UNKNOWN])
        shape = type_shapes.get(object_type, type_shapes[CodeObjectType.UNKNOWN])
        
        # Set node label
        if with_package_name:
            label = f"{code_object.name}\n({package_name})"
        else:
            label = code_object.name
            
        # Use the label as the title since there's no 'signature' attribute in PLSQL_CodeObject
        title = label
        
        # Special handling for UNKNOWN type - dashed border
        if object_type == CodeObjectType.UNKNOWN:
            net.add_node(
                node,
                label=label,
                color=color_set,
                title=title,
                shape=shape,
                font={"face": "Arial", "size": 16},
                borderWidth=2,
                dashes=True  # This makes the border dashed in Pyvis
            )
        else:
            net.add_node(
                node,
                label=label,
                color=color_set,
                title=title,
                shape=shape,
                font={"face": "Arial", "size": 16}
            )
            
        logger.trace(f"Added node '{node}' to Pyvis network.")

    for (source_node_id, target_node_id) in graph.edges:
        if source_node_id in excluded_node_id or target_node_id in excluded_node_id:
            continue
            
        # Get source node's object type for edge color
        source_obj = graph.nodes[source_node_id].get('object')
        source_code_object: Optional[PLSQL_CodeObject] = source_obj
        source_type = source_code_object.type if source_code_object else CodeObjectType.UNKNOWN
        edge_color = type_colors.get(source_type, type_colors[CodeObjectType.UNKNOWN])["border"]
        
        net.add_edge(source_node_id, target_node_id, color=edge_color)
        logger.trace(f"Added edge '{source_node_id} -> {target_node_id}' to Pyvis network.")

    logger.info("Pyvis export completed.")
    return net

# End of exporter.py

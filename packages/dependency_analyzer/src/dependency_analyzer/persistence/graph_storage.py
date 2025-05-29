"""
Graph Storage Module.

Provides functionality to save and load NetworkX graphs in various formats.
Handles graph structure persistence separate from PLSQL_CodeObject storage.
"""
from __future__ import annotations

from pathlib import Path
import networkx as nx
import loguru as lg
from typing import Optional, Union, Dict
import json



class GraphStorage:
    """
    Handles saving and loading NetworkX dependency graphs in various formats.
    
    Supports the following formats:
    - gpickle: Python-specific binary format (fast, Python-only)
    - graphml: XML-based format (interoperable with other tools)
    - gexf: XML-based format (optimized for Gephi visualization)
    - json: JSON node-link format (web-compatible)
    
    Works with structure-only graphs (nodes store attributes like ID, name, type, package, metrics,
    but not full PLSQL_CodeObject instances). Provides rehydration capability for when full
    objects are needed.
    """

    def __init__(self, logger: lg.Logger):
        """
        Initialize the GraphStorage.
        
        Args:
            logger: Logger instance for logging operations.
        """
        self.logger = logger.bind(component="GraphStorage")
        self.logger.debug("GraphStorage instance initialized")

    def save_graph(
        self, graph: nx.DiGraph, output_path: Union[str, Path], format: Optional[str] = None
    ) -> bool:
        """
        Save a NetworkX DiGraph to a file in the specified format.
        
        Args:
            graph: The NetworkX DiGraph to save (already structure-only).
            output_path: Path where the graph will be saved.
            format: Format to use for saving. If None, inferred from the file extension.
                   Valid formats: 'gpickle', 'graphml', 'gexf', 'json'.
        
        Returns:
            bool: True if saving was successful, False otherwise.
        """
        output_path = Path(output_path) if isinstance(output_path, str) else output_path
        self.logger.info(f"Saving graph to {output_path} in {format} format")
        
        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Ensured parent directories exist for '{output_path}'")
        
        # If format is not specified, try to infer it from the file extension
        if format is None:
            format = output_path.suffix.lstrip('.')
            if not format:
                self.logger.error(f"Cannot infer format from '{output_path}'. No file extension provided.")
                return False
        
        format = format.lower()
        self.logger.info(f"Saving graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges to '{output_path}' in '{format}' format")

        # Graph is already structure-only, no need for preprocessing
        
        try:
            if format == 'gpickle':
                import pickle
                with open(output_path, 'wb') as f:
                    pickle.dump(graph, f)
            elif format == 'graphml':
                nx.write_graphml(graph, output_path)
            elif format == 'gexf':
                nx.write_gexf(graph, output_path)
            elif format == 'json' or format == 'node_link':
                data = nx.node_link_data(graph, edges="edges")
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
            else:
                self.logger.error(f"Unsupported graph format: '{format}'. Use 'gpickle', 'graphml', 'gexf', or 'json'.")
                return False
            
            self.logger.info(f"Graph successfully saved to '{output_path}'")
            return True
        
        except Exception as e:
            self.logger.error(f"Error saving graph to '{output_path}' in '{format}' format: {e}", exc_info=True)
            return False

    def load_graph(
        self, input_path: Union[str, Path], format: Optional[str] = None
    ) -> Optional[nx.DiGraph]:
        """
        Load a NetworkX DiGraph from a file.
        
        Args:
            input_path: Path to the file containing the saved graph.
            format: Format of the saved graph. If None, inferred from the file extension.
                   Valid formats: 'gpickle', 'graphml', 'gexf', 'json'.
        
        Returns:
            nx.DiGraph: The loaded graph, or None if loading failed.
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            self.logger.error(f"Graph file not found: '{input_path}'")
            return None
        
        # If format is not specified, try to infer it from the file extension
        if format is None:
            format = input_path.suffix.lstrip('.')
            if not format:
                self.logger.error(f"Cannot infer format from '{input_path}'. No file extension provided.")
                return None
        
        format = format.lower()
        self.logger.info(f"Loading graph from '{input_path}' in '{format}' format")
        
        try:
            if format == 'gpickle':
                import pickle
                with open(input_path, 'rb') as f:
                    graph = pickle.load(f)
            elif format == 'graphml':
                graph = nx.read_graphml(input_path)
            elif format == 'gexf':
                graph = nx.read_gexf(input_path)
            elif format == 'json' or format == 'node_link':
                with open(input_path, 'r') as f:
                    data = json.load(f)
                graph = nx.node_link_graph(data, edges="edges")
            else:
                self.logger.error(f"Unsupported graph format: '{format}'. Use 'gpickle', 'graphml', 'gexf', or 'json'.")
                return None
            
            self.logger.info(f"Graph loaded from '{input_path}' with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")

            for node in graph.nodes:
                if 'node_role' in graph.nodes[node]:
                    # Ensure roles are stored as a set for consistency
                    graph.nodes[node]['node_role'] = graph.nodes[node]['node_role'].split(', ')

            return graph
        
        except Exception as e:
            self.logger.error(f"Error loading graph from '{input_path}' in '{format}' format: {e}", exc_info=True)
            return None

    def rehydrate_graph_with_objects(
        self, 
        graph: nx.DiGraph,
        object_map: Dict[str, object],  # Mapping from node_id to PLSQL_CodeObject
        logger: Optional[lg.Logger] = None
    ) -> nx.DiGraph:
        """
        Rehydrate a structure-only graph with PLSQL_CodeObject instances.

        Args:
            graph: The structure-only NetworkX DiGraph.
            object_map: Dictionary mapping node IDs to PLSQL_CodeObject instances.
            logger: Optional logger instance. If None, uses self.logger.

        Returns:
            nx.DiGraph: The rehydrated graph with 'object' attributes on nodes.
        """
        logger = logger or self.logger
        
        logger.info(f"Rehydrating graph with {len(object_map)} code objects...")
        
        # Create a copy of the graph to avoid modifying the original
        rehydrated_graph = graph.copy()
        
        # Add the code objects to the graph nodes
        nodes_populated = 0
        nodes_without_objects = 0
        
        for node_id in rehydrated_graph.nodes():
            if node_id in object_map:
                rehydrated_graph.nodes[node_id]['object'] = object_map[node_id]
                nodes_populated += 1
            else:
                logger.warning(f"Code object not found for node {node_id}")
                nodes_without_objects += 1
        
        logger.info(f"Graph rehydrated with {nodes_populated} code objects. {nodes_without_objects} nodes could not be populated.")
        return rehydrated_graph

"""
Graph Storage Module.

Provides functionality to save and load NetworkX graphs in various formats.
Handles graph structure persistence separate from PLSQL_CodeObject storage.
"""
from __future__ import annotations

from pathlib import Path
import networkx as nx
import loguru as lg
from typing import Optional, Union
import json

from dependency_analyzer.utils.database_loader import DatabaseLoader



class GraphStorage:
    """
    Handles saving and loading NetworkX dependency graphs in various formats.
    
    Supports the following formats:
    - gpickle: Python-specific binary format (fast, Python-only)
    - graphml: XML-based format (interoperable with other tools)
    - gexf: XML-based format (optimized for Gephi visualization)
    - json: JSON node-link format (web-compatible)
    
    Provides specialized methods for handling graphs with PLSQL_CodeObject data:
    - save_structure_only: Saves only the graph topology (nodes and edges)
    - load_and_populate: Loads a graph and populates it with PLSQL_CodeObjects from a database
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
            graph: The NetworkX DiGraph to save.
            output_path: Path where the graph will be saved.
            format: Format to use for saving. If None, inferred from the file extension.
                   Valid formats: 'gpickle', 'graphml', 'gexf', 'json'.
        
        Returns:
            bool: True if saving was successful, False otherwise.
        """
        output_path = Path(output_path) if isinstance(output_path, str) else output_path
        print(f"Saving graph to {output_path} in {format} format")
        
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

        # Remove all objects from the graph to save only the structure
        # This is important for formats that cannot handle complex Python objects
        graph = self.remove_codeobjects(graph)
        
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

    def load_and_populate(
        self, 
        input_path: Union[str, Path], 
        database_loader: DatabaseLoader,  # Should be DatabaseLoader but avoiding circular imports
        format: Optional[str] = None
    ) -> Optional[nx.DiGraph]:
        """
        Load a graph structure and populate it with PLSQL_CodeObject instances from the database.

        Args:
            input_path: Path to the file containing the saved graph structure.
            database_loader: Instance of DatabaseLoader to fetch PLSQL_CodeObject instances.
            format: Format of the saved graph. If None, inferred from the file extension.
                   Valid formats: 'gpickle', 'graphml', 'gexf', 'json'.

        Returns:
            nx.DiGraph: The loaded and populated graph, or None if loading failed.
        """
        # First, load the structure-only graph
        structure_graph = self.load_graph(input_path, format)
        if structure_graph is None:
            return None
        
        self.logger.info(f"Loaded graph structure with {structure_graph.number_of_nodes()} nodes. Populating with code objects...")
        
        try:
            # Load all code objects from the database
            code_objects = database_loader.load_all_objects()
            if not code_objects:
                self.logger.warning("No code objects loaded from database. Graph nodes will not be populated with object data.")
                return structure_graph
            
            # Create a mapping from object IDs to code objects for quick lookup
            code_object_map = {obj.id: obj for obj in code_objects}
            
            # Populate the graph nodes with the corresponding code objects
            nodes_populated = 0
            nodes_without_objects = 0
            
            for node_id in structure_graph.nodes():
                if 'object_id' in structure_graph.nodes[node_id]:
                    object_id = structure_graph.nodes[node_id]['object_id']
                    if object_id in code_object_map:
                        structure_graph.nodes[node_id]['object'] = code_object_map[object_id]
                        nodes_populated += 1
                    else:
                        self.logger.warning(f"Code object with ID {object_id} not found in database for node {node_id}")
                        nodes_without_objects += 1
            
            self.logger.info(f"Graph populated with {nodes_populated} code objects. {nodes_without_objects} nodes could not be populated.")
            return structure_graph
            
        except Exception as e:
            self.logger.error(f"Error populating graph with code objects: {e}", exc_info=True)
            return structure_graph  # Return the structure graph even if population fails

    def remove_codeobjects(self, graph: nx.DiGraph) -> nx.DiGraph:
        """
        Create a new graph with only the structure (nodes and edges) of the input graph,
        without the PLSQL_CodeObject instances.
        
        This is useful for lightweight graph storage or for exporting to formats that
        can't handle complex Python objects.
        
        Args:
            graph: The NetworkX DiGraph containing PLSQL_CodeObject data
            
        Returns:
            nx.DiGraph: A new graph with the same structure but without PLSQL_CodeObject instances
        """
        self.logger.debug(f"Extracting structure-only graph from graph with {graph.number_of_nodes()} nodes")
        
        # Create a clean graph with only node IDs and basic attributes
        structure_graph = nx.DiGraph()
        
        # Add all nodes without the large code objects
        for node_id in graph.nodes:
            node_data = {}
            
            # Copy basic attributes, filtering out the large PLSQL_CodeObject
            if 'object' in graph.nodes[node_id]:
                # Skip storing the large PLSQL_CodeObject
                # Optionally store very minimal information about the object
                code_obj = graph.nodes[node_id]['object']
                if hasattr(code_obj, 'id') and hasattr(code_obj, 'name') and hasattr(code_obj, 'package_name'):
                    node_data['object_id'] = getattr(code_obj, 'id')
                    node_data['name'] = getattr(code_obj, 'name')
                    node_data['package_name'] = getattr(code_obj, 'package_name')
                    node_data['type'] = getattr(code_obj, 'type').value if hasattr(code_obj, 'type') else None
            
            # Add any other non-object attributes that might be present
            for attr, value in graph.nodes[node_id].items():
                if attr != 'object' and not attr.startswith('_'):
                    node_data[attr] = value
            
            structure_graph.add_node(node_id, **node_data)
        
        # Add all edges with their attributes
        for u, v, data in graph.edges(data=True):
            structure_graph.add_edge(u, v, **data)
            
        return structure_graph

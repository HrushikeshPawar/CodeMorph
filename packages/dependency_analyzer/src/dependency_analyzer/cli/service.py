"""
Service layer for CLI operations.

This module contains the business logic for CLI commands, separated from
the command interface to improve testability and maintainability.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict, Tuple
from contextlib import contextmanager
from rich.console import Console
from rich.table import Table

from dependency_analyzer.settings import DependencyAnalyzerSettings
from dependency_analyzer.utils.logging_setup import configure_logger
from dependency_analyzer.utils.database_loader import DatabaseLoader
from dependency_analyzer.builder.graph_constructor import GraphConstructor
from dependency_analyzer.persistence.graph_storage import GraphStorage
from dependency_analyzer.visualization import exporter
from dependency_analyzer.analysis import analyzer
from dependency_analyzer.cli.utils import (
    CLIError, validate_file_exists, ensure_output_directory,
    generate_output_path, print_success, print_warning, print_info
)
from dependency_analyzer.cli.constants import SUCCESS_MESSAGES, ERROR_MESSAGES

from plsql_analyzer.persistence.database_manager import DatabaseManager


class CLIService:
    """Service class for CLI operations with proper resource management."""
    
    def __init__(self, settings: DependencyAnalyzerSettings):
        self.settings = settings
        self.logger = configure_logger(settings.log_verbose_level, settings.logs_dir)
        self._db_manager: Optional[DatabaseManager] = None
        self._graph_storage: Optional[GraphStorage] = None
    
    @property
    def graph_storage(self) -> GraphStorage:
        """Lazy-loaded graph storage instance."""
        if self._graph_storage is None:
            self._graph_storage = GraphStorage(self.logger)
        return self._graph_storage
    
    @contextmanager
    def database_manager(self):
        """Context manager for database operations."""
        if not self.settings.database_path or not self.settings.database_path.exists():
            raise CLIError(
                ERROR_MESSAGES['database_not_found'].format(path=self.settings.database_path),
                "Run the PL/SQL analyzer first to generate the database."
            )
        
        db_manager = DatabaseManager(self.settings.database_path, self.logger)
        try:
            yield db_manager
        finally:
            # DatabaseManager handles its own cleanup
            pass
    
    def initialize_config(self, output_path: Optional[Path] = None) -> Path:
        """
        Initialize a default configuration file.
        
        Args:
            output_path: Where to save the config file
            
        Returns:
            Path where config was saved
            
        Raises:
            CLIError: If config cannot be created
        """
        if output_path is None:
            output_path = Path.cwd() / self.settings.DEFAULT_CONFIG_FILENAME
        
        try:
            ensure_output_directory(output_path, self.logger)
            self.settings.write_default_config(output_path)
            
            print_success(
                SUCCESS_MESSAGES['config_created'].format(path=output_path),
                {"Size": f"{output_path.stat().st_size} bytes"}
            )
            
            return output_path
            
        except Exception as e:
            raise CLIError(
                f"Failed to create configuration file: {e}",
                "Check write permissions and disk space."
            )
    
    def build_full_graph(
        self, 
        output_fname: str,
        calculate_complexity: bool = True
    ) -> Path:
        """
        Build a complete dependency graph from database.
        
        Args:
            output_fname: Base filename for output
            calculate_complexity: Whether to calculate complexity metrics
            
        Returns:
            Path where graph was saved
            
        Raises:
            CLIError: If graph cannot be built
        """
        self.logger.info("Starting full graph build")
        
        # Ensure output directory exists
        ensure_output_directory(self.settings.graphs_dir, self.logger)
        
        # Generate output path
        output_path = generate_output_path(
            self.settings.graphs_dir,
            output_fname or "full_dependency_graph",
            self.settings.graph_format.value,
            add_timestamp=output_fname is None,
            settings=self.settings
        )
        
        # Load code objects from database
        with self.database_manager() as db_manager:
            loader = DatabaseLoader(db_manager, self.logger)
            code_objects = loader.load_all_objects()
        
        if not code_objects:
            print_warning(
                "No code objects found in database. Graph will be empty.",
                "Check if the PL/SQL analyzer processed any source files."
            )
        else:
            self.logger.info(f"Loaded {len(code_objects)} code objects")
        
        # Build graph
        graph_constructor = GraphConstructor(code_objects, self.logger)
        dependency_graph, out_of_scope_calls = graph_constructor.build_graph()
        
        # Calculate complexity if requested
        if calculate_complexity or self.settings.calculate_complexity_metrics:
            dependency_graph = analyzer.calculate_node_complexity_metrics(dependency_graph, self.logger)
            self.logger.info("Complexity metrics calculated")
        
        # Save graph
        self.logger.info(f"Saving graph to {output_path}")
        if self.graph_storage.save_graph(dependency_graph, output_path, format=self.settings.graph_format.value):
            self.logger.info(
                f"Graph saved successfully: {output_path} ({dependency_graph.number_of_nodes()} nodes, "
                f"{dependency_graph.number_of_edges()} edges)"
            )
            print_success(
                SUCCESS_MESSAGES['graph_saved'].format(
                    path=output_path,
                    nodes=dependency_graph.number_of_nodes(),
                    edges=dependency_graph.number_of_edges()
                ),
                {
                    "Out-of-scope calls": len(out_of_scope_calls),
                    "Format": self.settings.graph_format.value,
                    "File size": f"{output_path.stat().st_size:,} bytes"
                }
            )
        else:
            raise CLIError(
                ERROR_MESSAGES['save_failed'].format(
                    path=output_path,
                    format=self.settings.graph_format.value
                ),
                "Check write permissions and disk space."
            )
        
        return output_path
    
    def build_subgraph(
        self,
        input_path: Path,
        node_id: str,
        output_fname: str,
        upstream_depth: int,
        downstream_depth: Optional[int] = None,
        load_with_objects: bool = False,
    ) -> Path:
        """
        Build a subgraph centered on a specific node.
        
        Args:
            input_path: Path to source graph
            node_id: Central node for subgraph
            output_fname: Where to save subgraph
            upstream_depth: Levels of callers to include
            downstream_depth: Levels of callees to include
            load_with_objects: Whether to populate with full objects
            graph_format: Override format for loading
            
        Returns:
            Path where subgraph was saved
            
        Raises:
            CLIError: If subgraph cannot be built
        """
        validate_file_exists(input_path, "graph")
        ensure_output_directory(self.settings.graphs_dir, self.logger)
        
        self.logger.info(f"Building subgraph for node '{node_id}'")

        # Generate output path
        output_path = generate_output_path(
            self.settings.graphs_dir,
            output_fname or "full_dependency_graph",
            self.settings.graph_format.value,
            add_timestamp=output_fname is None,
            settings=self.settings
        )
        
        # Load the source graph
        if load_with_objects:
            with self.database_manager() as db_manager:
                loader = DatabaseLoader(db_manager, self.logger)
                full_graph = self.graph_storage.load_and_populate(
                    input_path, loader, format=self.settings.graph_format
                )
        else:
            full_graph = self.graph_storage.load_graph(input_path, format=self.settings.graph_format)
        
        if not full_graph:
            raise CLIError(
                ERROR_MESSAGES['load_failed'].format(
                    path=input_path,
                    format=self.settings.graph_format or "auto-detected",
                    suggestion="Check if the file is corrupted"
                )
            )
        
        if node_id not in full_graph:
            raise CLIError(
                ERROR_MESSAGES['node_not_found'].format(node_id=node_id),
                f"Available nodes: {len(full_graph.nodes)}. Use 'query' commands to explore."
            )
        
        # Generate subgraph
        subgraph = analyzer.generate_subgraph_for_node(
            full_graph, node_id, self.logger, upstream_depth, downstream_depth
        )
        
        if subgraph is None:
            raise CLIError(
                f"Failed to generate subgraph for node '{node_id}'",
                "The node may be isolated or parameters may be too restrictive."
            )
        
        # Save subgraph
        if self.graph_storage.save_graph(subgraph, output_path, format=self.settings.graph_format.value):
            print_success(
                SUCCESS_MESSAGES['graph_saved'].format(
                    path=output_path,
                    nodes=subgraph.number_of_nodes(),
                    edges=subgraph.number_of_edges()
                ),
                {
                    "Central node": node_id,
                    "Upstream depth": upstream_depth,
                    "Downstream depth": downstream_depth or "unlimited"
                }
            )
        else:
            raise CLIError(
                ERROR_MESSAGES['save_failed'].format(
                    path=output_path,
                    format=self.settings.graph_format.value
                )
            )
        
        return output_path
    
    def calculate_metrics(self, graph_path: Path, graph_format: Optional[str] = None) -> Path:
        """
        Calculate and store complexity metrics for a graph.
        
        Args:
            graph_path: Path to graph file
            graph_format: Override format for loading
            
        Returns:
            Path where updated graph was saved
            
        Raises:
            CLIError: If metrics cannot be calculated
        """
        validate_file_exists(graph_path, "graph")
        
        self.logger.info(f"Calculating metrics for graph '{graph_path}'")
        
        # Load graph
        graph = self.graph_storage.load_graph(graph_path, format=graph_format)
        if not graph:
            raise CLIError(
                ERROR_MESSAGES['load_failed'].format(
                    path=graph_path,
                    format=graph_format or "auto-detected",
                    suggestion="Check file format and integrity"
                )
            )
        
        # Calculate metrics
        updated_graph = analyzer.calculate_node_complexity_metrics(graph, self.logger)
        
        # Save updated graph
        if self.graph_storage.save_graph(updated_graph, graph_path, format=graph_format):
            print_success(
                f"Metrics calculated and saved to {graph_path}",
                {"Nodes processed": updated_graph.number_of_nodes()}
            )
        else:
            raise CLIError(
                ERROR_MESSAGES['save_failed'].format(
                    path=graph_path,
                    format=graph_format or "auto-detected"
                )
            )
        
        return graph_path
    
    def classify_nodes(
        self,
        graph_path: Path,
        output_fname: str,
        graph_format: Optional[str] = None,
    ) -> Path:
        """
        Classify nodes by architectural roles.
        
        Args:
            graph_path: Path to graph file
            output_fname: Base name for output file
            graph_format: Override format for loading
            **classification_params: Parameters for classification
            
        Returns:
            Path where classified graph was saved
            
        Raises:
            CLIError: If classification fails
        """
        validate_file_exists(graph_path, "graph")
        ensure_output_directory(self.settings.graphs_dir, self.logger)
        
        self.logger.info(f"Classifying nodes in graph '{graph_path}'")
        
        # Load graph
        graph = self.graph_storage.load_graph(graph_path, format=graph_format)
        if not graph:
            raise CLIError(
                ERROR_MESSAGES['load_failed'].format(
                    path=graph_path,
                    format=graph_format or "auto-detected",
                    suggestion="Check file format and integrity"
                )
            )
        
        # Classify nodes
        classified_graph = analyzer.classify_nodes(
            graph, 
            self.logger,
            complexity_metrics_available=self.settings.calculate_complexity_metrics,
            hub_degree_percentile=self.settings.hub_degree_percentile,
            hub_betweenness_percentile= self.settings.hub_betweenness_percentile,
            hub_pagerank_percentile= self.settings.hub_pagerank_percentile,
            utility_out_degree_percentile= self.settings.utility_out_degree_percentile,
            utility_max_complexity= self.settings.utility_max_complexity,
            orphan_component_max_size= self.settings.orphan_component_max_size,
        )
        
        # Generate output path
        output_path = generate_output_path(
            self.settings.graphs_dir,
            output_fname,
            self.settings.graph_format.value
        )
        
        # Save classified graph
        if self.graph_storage.save_graph(classified_graph, output_path, format=self.settings.graph_format.value):
            print_success(
                SUCCESS_MESSAGES['graph_saved'].format(
                    path=output_path,
                    nodes=classified_graph.number_of_nodes(),
                    edges=classified_graph.number_of_edges()
                ),
                {"Classification": "Node roles assigned"}
            )
        else:
            raise CLIError(
                ERROR_MESSAGES['save_failed'].format(
                    path=output_path,
                    format=self.settings.graph_format.value
                )
            )
        
        return output_path
    
    def find_cycles(
        self,
        graph_path: Path,
        output_path: Optional[Path] = None,
        graph_format: Optional[str] = None
    ) -> Tuple[Path, List]:
        """
        Find circular dependencies in a graph.
        
        Args:
            graph_path: Path to graph file
            output_path: Where to save the report
            graph_format: Override format for loading
            
        Returns:
            Tuple of (report_path, cycles_list)
            
        Raises:
            CLIError: If analysis fails
        """
        validate_file_exists(graph_path, "graph")
        
        if output_path is None:
            output_path = generate_output_path(
                self.settings.reports_dir,
                "cycles_report",
                "txt",
                add_timestamp=True,
                settings=self.settings
            )
        
        ensure_output_directory(output_path, self.logger)
        
        self.logger.info(f"Analyzing cycles in graph '{graph_path}'")
        
        # Load graph
        graph = self.graph_storage.load_graph(graph_path, format=graph_format)
        if not graph:
            raise CLIError(
                ERROR_MESSAGES['load_failed'].format(
                    path=graph_path,
                    format=graph_format or "auto-detected",
                    suggestion="Check file format and integrity"
                )
            )
        
        # Find cycles
        cycles = analyzer.find_circular_dependencies(graph, self.logger)
        
        # Write report
        try:
            with open(output_path, 'w') as f:
                f.write("Circular Dependencies Report\n")
                f.write(f"Graph: {graph_path}\n")
                f.write(f"Generated: {self.settings.timestamp_readable}\n")
                f.write(f"Total nodes: {graph.number_of_nodes()}\n")
                f.write(f"Total edges: {graph.number_of_edges()}\n\n")
                
                if cycles:
                    f.write(f"Found {len(cycles)} circular dependencies:\n\n")
                    for i, cycle in enumerate(cycles, 1):
                        f.write(f"Cycle {i} (length {len(cycle)}):\n")
                        for node in cycle:
                            f.write(f"  -> {node}\n")
                        f.write("\n")
                else:
                    f.write("No circular dependencies found.\n")
            
            if cycles:
                print_warning(
                    f"Found {len(cycles)} circular dependencies",
                    f"Review the report at {output_path}"
                )
            else:
                print_success(
                    "No circular dependencies found",
                    {"Graph health": "Good"}
                )
                
        except Exception as e:
            raise CLIError(
                f"Failed to write cycles report: {e}",
                "Check write permissions for the reports directory."
            )
        
        return output_path, cycles
    
    def create_visualization(
        self,
        graph_path: Path,
        output_fname: str,
        title: Optional[str] = None,
        graph_format: Optional[str] = None
    ) -> List[Path]:
        """
        Create visualizations of a graph.
        
        Args:
            graph_path: Path to graph file
            output_fname: Base name for output files
            title: Optional title for visualization
            graph_format: Override format for loading
            
        Returns:
            List of paths where visualizations were saved
            
        Raises:
            CLIError: If visualization fails
        """
        validate_file_exists(graph_path, "graph")
        ensure_output_directory(self.settings.visualizations_dir, self.logger)
        
        self.logger.info(f"Creating visualization for graph '{graph_path}'")
        
        # Load graph
        graph = self.graph_storage.load_graph(graph_path, format=graph_format)
        if not graph:
            raise CLIError(
                ERROR_MESSAGES['load_failed'].format(
                    path=graph_path,
                    format=graph_format or "auto-detected",
                    suggestion="Check file format and integrity"
                )
            )
        
        if graph.number_of_nodes() == 0:
            raise CLIError(
                ERROR_MESSAGES['empty_graph'],
                "Check if the source database contains code objects."
            )
        
        output_paths = []
        
        try:
            if self.settings.default_visualization_engine.value == "graphviz":
                viz_graph = exporter.to_graphviz(
                    graph,
                    self.logger,
                    with_package_name=self.settings.with_package_name_labels
                )
                
                if title:
                    viz_graph.attr(label=title, labelloc="t", fontsize="20")
                
                # Render multiple formats
                for fmt in ["svg", "png"]:
                    output_path = self.settings.visualizations_dir / f"{output_fname}.{fmt}"
                    viz_graph.render(
                        filename=output_fname,
                        directory=self.settings.visualizations_dir,
                        format=fmt,
                        view=False,
                        cleanup=False
                    )
                    
                    output_paths.append(output_path)
                    
                print_success(
                    SUCCESS_MESSAGES['visualization_complete'].format(path=self.settings.visualizations_dir),
                    {
                        "Formats": "SVG, PNG, DOT",
                        "Nodes": graph.number_of_nodes(),
                        "Edges": graph.number_of_edges()
                    }
                )
            
        except ImportError as e:
            raise CLIError(
                f"Visualization engine not available: {e}",
                f"Install the required dependencies for {self.settings.default_visualization_engine.value}"
            )
        except Exception as e:
            raise CLIError(
                f"Failed to create visualization: {e}",
                "Check if the graph is too large or complex for visualization."
            )
        
        return output_paths
    
    def query_reachability(
        self,
        graph_path: Path,
        node_id: str,
        downstream: bool = True,
        upstream: bool = False,
        depth: Optional[int] = None,
        graph_format: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Query reachability for a specific node.
        
        Args:
            graph_path: Path to graph file
            node_id: Node to analyze
            downstream: Include descendants
            upstream: Include ancestors
            depth: Optional depth limit
            graph_format: Override format for loading
            
        Returns:
            Dictionary with reachability results
            
        Raises:
            CLIError: If query fails
        """
        validate_file_exists(graph_path, "graph")
        
        self.logger.info(f"Analyzing reachability for node '{node_id}'")
        
        # Load graph
        graph = self.graph_storage.load_graph(graph_path, format=graph_format)
        if not graph:
            raise CLIError(
                ERROR_MESSAGES['load_failed'].format(
                    path=graph_path,
                    format=graph_format or "auto-detected",
                    suggestion="Check file format and integrity"
                )
            )
        
        if node_id not in graph:
            raise CLIError(
                ERROR_MESSAGES['node_not_found'].format(node_id=node_id),
                f"Graph contains {len(graph.nodes)} nodes. Use 'query' commands to explore."
            )
        
        results = {}
        if downstream:
            descendants = analyzer.get_descendants(graph, node_id, depth_limit=depth)
            results['descendants'] = sorted(descendants) if descendants else []
            print_info(f"Descendants of '{node_id}' (depth={depth}): {len(results['descendants'])} nodes")
        
        if upstream:
            ancestors = analyzer.get_ancestors(graph, node_id, depth_limit=depth)
            results['ancestors'] = sorted(ancestors) if ancestors else []
            print_info(f"Ancestors of '{node_id}' (depth={depth}): {len(results['ancestors'])} nodes")
        
        return results
    
    def query_paths(
        self,
        graph_path: Path,
        source_node: str,
        target_node: str,
        depth: Optional[int] = None,
        graph_format: Optional[str] = None
    ) -> List[List[str]]:
        """
        Find paths between two nodes.
        
        Args:
            graph_path: Path to graph file
            source_node: Starting node
            target_node: Ending node
            depth: Maximum path length
            graph_format: Override format for loading
            
        Returns:
            List of paths (each path is a list of node IDs)
            
        Raises:
            CLIError: If query fails
        """
        validate_file_exists(graph_path, "graph")
        
        self.logger.info(f"Finding paths from '{source_node}' to '{target_node}'")
        
        # Load graph
        graph = self.graph_storage.load_graph(graph_path, format=graph_format)
        if not graph:
            raise CLIError(
                ERROR_MESSAGES['load_failed'].format(
                    path=graph_path,
                    format=graph_format or "auto-detected",
                    suggestion="Check file format and integrity"
                )
            )
        
        # Check if both nodes exist
        for node_id, node_type in [(source_node, "Source"), (target_node, "Target")]:
            if node_id not in graph:
                raise CLIError(
                    f"{node_type} node '{node_id}' not found in graph",
                    f"Graph contains {len(graph.nodes)} nodes. Check the node ID."
                )
        
        # Find paths
        paths = analyzer.find_all_paths(graph, source_node, target_node, self.logger, cutoff=depth)
        
        if not paths:
            print_info(f"No paths found from '{source_node}' to '{target_node}'")
        else:
            print_info(f"Found {len(paths)} paths from '{source_node}' to '{target_node}'")
            for i, path in enumerate(paths[:10], 1):  # Show first 10 paths
                print(f"  Path {i} ({len(path)} steps): {' -> '.join(path)}")
            if len(paths) > 10:
                print(f"  ... and {len(paths) - 10} more paths")
        
        return paths

    def query_list_nodes(
        self,
        input_path: Path,
        node_type: Optional[str] = None,
        package: Optional[str] = None,
        name: Optional[str] = None,
        limit: Optional[int] = None,
        sort_by: str = "name",
        graph_format: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        List all nodes in the graph with optional filtering and sorting.
        
        Args:
            graph_path: Path to graph file
            node_type: Filter by code object type (PACKAGE, PROCEDURE, etc.)
            package: Filter by package name (substring match)
            name: Filter by node name (substring match)
            limit: Maximum number of nodes to return
            sort_by: Sort field ('name', 'type', 'package', 'degree')
            graph_format: Override format for loading
            
        Returns:
            List of node information dictionaries
            
        Raises:
            CLIError: If query fails
        """
        validate_file_exists(input_path, "graph")
        
        self.logger.info(f"Listing nodes from graph '{input_path}' with filters")
        
        # Load graph
        graph = self.graph_storage.load_graph(input_path, format=graph_format)
        if not graph:
            raise CLIError(
                ERROR_MESSAGES['load_failed'].format(
                    path=input_path,
                    format=graph_format or "auto-detected",
                    suggestion="Check file format and integrity"
                )
            )
        
        # Get filtered and sorted nodes
        nodes_info = analyzer.list_nodes(
            graph, 
            self.logger,
            node_type=node_type,
            package=package,
            name=name,
            limit=limit,
            sort_by=sort_by
        )
        
        if not nodes_info:
            print_info("No nodes found matching the specified criteria")
        else:
            total_nodes = len(graph.nodes)
            displayed_count = len(nodes_info)
            
            print_info(f"Found {displayed_count} nodes" + 
                      (f" (filtered from {total_nodes} total)" if displayed_count < total_nodes else ""))
            
            console = Console()
            table = Table(title="Nodes in Graph", show_lines=True)

            for key in nodes_info[0].keys():
                table.add_column(key.capitalize(), justify="left", style="cyan", overflow="fold")
            
            for node_info in nodes_info:
                table.add_row(*[str(x) for x in (node_info.values())])
            console.print(table)
        
        return nodes_info
    
    def analyze_cycles(
        self,
        graph_path: Path,
        min_cycle_length: Optional[int] = None,
        max_cycle_length: Optional[int] = None,
        output_format: str = "table",
        include_node_details: bool = False,
        sort_cycles: str = "length",
        output_fname: Optional[str] = None
    ) -> List[Dict]:
        """
        Analyze circular dependencies in the dependency graph.
        
        Args:
            graph_path: Path to graph file
            min_cycle_length: Filter cycles with minimum length
            max_cycle_length: Filter cycles with maximum length
            output_format: Output format ('table', 'json', 'csv')
            include_node_details: Include detailed node information
            sort_cycles: Sort cycles by 'length', 'nodes', or 'complexity'
            output_fname: Optional output file name
            
        Returns:
            List of cycle information dictionaries
            
        Raises:
            CLIError: If analysis fails
        """
        validate_file_exists(graph_path, "graph")
        
        self.logger.info(f"Analyzing cycles in graph '{graph_path}'")
        
        # Load graph
        graph = self.graph_storage.load_graph(graph_path)
        if not graph:
            raise CLIError(
                ERROR_MESSAGES['load_failed'].format(
                    path=graph_path,
                    format="auto-detected",
                    suggestion="Check file format and integrity"
                )
            )
        
        # Analyze cycles
        cycles_info = analyzer.analyze_cycles_enhanced(
            graph, 
            self.logger,
            min_cycle_length=min_cycle_length,
            max_cycle_length=max_cycle_length,
            sort_by=sort_cycles,
            include_node_details=include_node_details
        )
        
        if not cycles_info:
            print_info("No circular dependencies found matching the specified criteria")
            return []
        
        # Display results
        self._display_cycles_results(cycles_info, output_format, include_node_details)
        
        # Save to file if requested
        if output_fname:
            self._save_cycles_results(cycles_info, output_fname, output_format)
        
        total_nodes = len(graph.nodes)
        print_success(f"Analysis complete: Found {len(cycles_info)} cycles in graph with {total_nodes} nodes")
        
        return cycles_info
    
    def _display_cycles_results(
        self, 
        cycles_info: List[Dict], 
        output_format: str, 
        include_node_details: bool
    ) -> None:
        """Display cycle analysis results in the specified format."""
        console = Console()
        
        if output_format == "table":
            # Summary table
            table = Table(title="Circular Dependencies Analysis", show_lines=True)
            table.add_column("Cycle ID", justify="center", style="cyan")
            table.add_column("Length", justify="center", style="yellow")
            table.add_column("Complexity", justify="center", style="red")
            table.add_column("Cycle Path", justify="left", style="green", overflow="fold")
            
            for cycle in cycles_info:
                table.add_row(
                    str(cycle['cycle_id']),
                    str(cycle['length']),
                    str(cycle['complexity']),
                    cycle['cycle_path']
                )
            
            console.print(table)
            
            # Detailed node information if requested
            if include_node_details:
                for cycle in cycles_info:
                    if 'node_details' in cycle:
                        detail_table = Table(
                            title=f"Cycle {cycle['cycle_id']} - Node Details",
                            show_lines=True
                        )
                        detail_table.add_column("Node ID", style="cyan")
                        detail_table.add_column("Name", style="yellow")
                        detail_table.add_column("Type", style="red")
                        detail_table.add_column("Package", style="green")
                        detail_table.add_column("In Degree", justify="center")
                        detail_table.add_column("Out Degree", justify="center")
                        
                        for node_detail in cycle['node_details']:
                            detail_table.add_row(
                                node_detail['id'],
                                node_detail['name'],
                                node_detail['type'],
                                node_detail['package'],
                                str(node_detail['in_degree']),
                                str(node_detail['out_degree'])
                            )
                        
                        console.print(detail_table)
                        console.print()  # Add spacing
        
        elif output_format == "json":
            import json
            console.print_json(json.dumps(cycles_info, indent=2))
        
        elif output_format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if cycles_info:
                fieldnames = ['cycle_id', 'length', 'complexity', 'cycle_path']
                if include_node_details and 'node_details' in cycles_info[0]:
                    fieldnames.extend(['node_ids', 'node_names', 'node_types', 'node_packages'])
                
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for cycle in cycles_info:
                    row = {
                        'cycle_id': cycle['cycle_id'],
                        'length': cycle['length'],
                        'complexity': cycle['complexity'],
                        'cycle_path': cycle['cycle_path']
                    }
                    
                    if include_node_details and 'node_details' in cycle:
                        node_details = cycle['node_details']
                        row['node_ids'] = ';'.join(nd['id'] for nd in node_details)
                        row['node_names'] = ';'.join(nd['name'] for nd in node_details)
                        row['node_types'] = ';'.join(nd['type'] for nd in node_details)
                        row['node_packages'] = ';'.join(nd['package'] for nd in node_details)
                    
                    writer.writerow(row)
            
            console.print(output.getvalue())
    
    def _save_cycles_results(
        self, 
        cycles_info: List[Dict], 
        output_fname: str, 
        output_format: str
    ) -> None:
        """Save cycle analysis results to file."""
        # Determine file extension
        if output_format == "json":
            file_path = Path(f"{output_fname}.json")
        elif output_format == "csv":
            file_path = Path(f"{output_fname}.csv")
        else:
            file_path = Path(f"{output_fname}.txt")
        
        ensure_output_directory(file_path.parent, self.logger)
        
        try:
            if output_format == "json":
                import json
                with open(file_path, 'w') as f:
                    json.dump(cycles_info, f, indent=2)
            
            elif output_format == "csv":
                import csv
                with open(file_path, 'w', newline='') as f:
                    if cycles_info:
                        fieldnames = ['cycle_id', 'length', 'complexity', 'cycle_path']
                        
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        
                        for cycle in cycles_info:
                            writer.writerow({
                                'cycle_id': cycle['cycle_id'],
                                'length': cycle['length'],
                                'complexity': cycle['complexity'],
                                'cycle_path': cycle['cycle_path']
                            })
            
            else:  # table format as text
                with open(file_path, 'w') as f:
                    f.write("Circular Dependencies Analysis\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for cycle in cycles_info:
                        f.write(f"Cycle {cycle['cycle_id']}:\n")
                        f.write(f"  Length: {cycle['length']}\n")
                        f.write(f"  Complexity: {cycle['complexity']}\n")
                        f.write(f"  Path: {cycle['cycle_path']}\n\n")
            
            print_success(f"Results saved to '{file_path}'")
            
        except Exception as e:
            raise CLIError(f"Failed to save results to '{file_path}': {e}")

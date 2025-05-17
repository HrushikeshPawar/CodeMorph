from __future__ import annotations

from pathlib import Path
from typing import Optional

import cyclopts
from cyclopts import Parameter
# from loguru import logger

from dependency_analyzer import config as da_config
from dependency_analyzer.utils.logging_setup import configure_logger
from dependency_analyzer.utils.database_loader import DatabaseLoader
from dependency_analyzer.builder.graph_constructor import GraphConstructor
from dependency_analyzer.persistence.graph_storage import GraphStorage
from dependency_analyzer.visualization import exporter
from dependency_analyzer.analysis import analyzer # For subgraph and other analyses
from plsql_analyzer.persistence.database_manager import DatabaseManager # For full-build

app = cyclopts.App(help="Dependency Analyzer CLI Tool")

def _setup(verbose_level: int = da_config.LOG_VERBOSE_LEVEL):
    """Shared setup for commands."""
    da_config.ensure_artifact_dirs()
    # The logger instance is returned but also globally configured
    local_logger = configure_logger(verbose_level, da_config.LOGS_DIR)
    return local_logger

@app.command
def full_build(
    db_path: Path = Parameter(da_config.DATABASE_PATH, help="Path to the PL/SQL analyzer SQLite database."),
    output_graph_path: Path = Parameter(da_config.GRAPHS_DIR / f"full_dependency_graph_{da_config.TIMESTAMP}.{da_config.DEFAULT_GRAPH_FORMAT}", help="Path to save the generated dependency graph."),
    graph_format: str = Parameter(da_config.DEFAULT_GRAPH_FORMAT, help=f"Format to save the graph. Options: {da_config.VALID_GRAPH_FORMATS}"),
    save_structure_only: bool = Parameter(True, help="Save only the graph structure without large code objects."),
    calculate_complexity: bool = Parameter(False, help="Calculate and store complexity metrics for each node."),
    verbose_level: int = Parameter(da_config.LOG_VERBOSE_LEVEL, help="Logging verbosity (0-3).")
):
    """
    Builds a full dependency graph from the database and saves it.
    
    When save_structure_only is True (default), only the graph structure (nodes and edges) will be saved
    without the large PLSQL_CodeObject instances, resulting in smaller file sizes and better loading times.
    If calculate_complexity is True, complexity metrics are calculated and stored as node attributes.
    """
    local_logger = _setup(verbose_level)
    local_logger.info(f"Starting full build. DB: '{db_path}', Output: '{output_graph_path}', Format: '{graph_format}'")

    if not db_path.exists():
        local_logger.critical(f"Database file not found at {db_path}. Cannot proceed.")
        return

    db_manager = DatabaseManager(db_path, local_logger)
    loader = DatabaseLoader(db_manager, local_logger)
    code_objects = loader.load_all_objects()

    if not code_objects:
        local_logger.warning("No code objects loaded. Resulting graph will be empty.")
    else:
        local_logger.info(f"Loaded {len(code_objects)} code objects.")

    graph_constructor = GraphConstructor(code_objects, local_logger, verbose=(verbose_level >= 2))
    dependency_graph, out_of_scope_calls = graph_constructor.build_graph()

    if calculate_complexity:
        analyzer.calculate_node_complexity_metrics(dependency_graph, local_logger)
        local_logger.info("Complexity metrics calculated and stored in graph nodes.")

    local_logger.info(
        f"Graph construction complete. Nodes: {dependency_graph.number_of_nodes()}, Edges: {dependency_graph.number_of_edges()}."
    )
    if out_of_scope_calls:
        local_logger.warning(f"Encountered {len(out_of_scope_calls)} out-of-scope calls.")

    graph_storage = GraphStorage(local_logger)
    
    # Use save_structure_only if requested (default), otherwise use the full save_graph
    if save_structure_only:
        if graph_storage.save_structure_only(dependency_graph, output_graph_path, format=graph_format):
            local_logger.info(f"Graph structure saved successfully to {output_graph_path}")
        else:
            local_logger.error(f"Failed to save graph structure to {output_graph_path}")
    else:
        # Legacy mode - save the full graph including large code objects
        if graph_storage.save_graph(dependency_graph, output_graph_path, format=graph_format):
            local_logger.info(f"Full graph saved successfully to {output_graph_path}")
        else:
            local_logger.error(f"Failed to save full graph to {output_graph_path}")
            
    local_logger.info("Full build finished.")

@app.command
def create_subgraph(
    input_graph_path: Path = Parameter(..., help="Path to the full dependency graph file."),
    node_id: str = Parameter(..., help="ID of the central node for the subgraph."),
    output_subgraph_path: Path = Parameter(..., help="Path to save the generated subgraph."),
    graph_format: str = Parameter(da_config.DEFAULT_GRAPH_FORMAT, help=f"Format to save the subgraph. Options: {da_config.VALID_GRAPH_FORMATS}"),
    upstream_depth: int = Parameter(0, help="How many levels of callers (upstream) to include."),
    downstream_depth: Optional[int] = Parameter(None, help="How many levels of callees (downstream) to include (default: all reachable nodes)."),
    save_structure_only: bool = Parameter(True, help="Save only the graph structure without large code objects."),
    load_with_objects: bool = Parameter(False, help="Load the graph with code objects from database (use when input is structure-only)."),
    db_path: Optional[Path] = Parameter(None, help="Path to the PL/SQL analyzer SQLite database (required if load_with_objects=True)."),
    verbose_level: int = Parameter(da_config.LOG_VERBOSE_LEVEL, help="Logging verbosity (0-3).")
):
    """
    Creates a subgraph from a given node in a larger graph and saves it.
    
    This function can work with both full graphs and structure-only graphs:
    - For structure-only input graphs, use load_with_objects=True to populate with code objects from database
    - When save_structure_only=True, the output subgraph will contain only the essential structure
    """
    local_logger = _setup(verbose_level)
    local_logger.info(f"Creating subgraph for node '{node_id}' from '{input_graph_path}'. Output: '{output_subgraph_path}'")

    if not input_graph_path.exists():
        local_logger.critical(f"Input graph file not found: {input_graph_path}")
        return

    graph_storage = GraphStorage(local_logger)
    
    if load_with_objects:
        # If loading with objects, we need a database path
        if not db_path:
            local_logger.critical("Database path required when load_with_objects=True. Cannot proceed.")
            return
        
        if not db_path.exists():
            local_logger.critical(f"Database file not found at {db_path}. Cannot proceed.")
            return
        
        # Setup database loading
        db_manager = DatabaseManager(db_path, local_logger)
        loader = DatabaseLoader(db_manager, local_logger)
        
        # Load structure and populate with objects
        local_logger.info(f"Loading graph structure from {input_graph_path} and populating with objects from database...")
        full_graph = graph_storage.load_and_populate(
            input_graph_path, 
            loader,
            format=Path(input_graph_path).suffix.lstrip('.')
        )
    else:
        # Regular loading without populating from database
        full_graph = graph_storage.load_graph(
            input_graph_path, 
            format=Path(input_graph_path).suffix.lstrip('.')
        )

    if not full_graph:
        local_logger.error(f"Failed to load graph from '{input_graph_path}'.")
        return

    if node_id not in full_graph:
        local_logger.error(f"Node '{node_id}' not found in the loaded graph.")
        return

    # Use downstream_depth=None as default for 'all reachable nodes' if not specified
    subgraph = analyzer.generate_subgraph_for_node(
        full_graph, node_id, local_logger, upstream_depth, downstream_depth
    )
    if subgraph is None:
        local_logger.error(f"Failed to generate subgraph for node '{node_id}'.")
        return
    
    # Save using the appropriate method based on user preference
    if save_structure_only:
        if graph_storage.save_structure_only(subgraph, output_subgraph_path, format=graph_format):
            local_logger.info(f"Subgraph structure saved to '{output_subgraph_path}'.")
        else:
            local_logger.error(f"Failed to save subgraph structure to '{output_subgraph_path}'.")
    else:
        if graph_storage.save_graph(subgraph, output_subgraph_path, format=graph_format):
            local_logger.info(f"Full subgraph saved to '{output_subgraph_path}'.")
        else:
            local_logger.error(f"Failed to save full subgraph to '{output_subgraph_path}'.")
            
    local_logger.info("Subgraph creation finished.")

@app.command
def visualize(
    input_graph_path: Path = Parameter(..., help="Path to the graph file to visualize (full or subgraph)."),
    output_base_path: Path = Parameter(da_config.VISUALIZATIONS_DIR / f"viz_{da_config.TIMESTAMP}", help="Base path and filename for the output visualization (extension will be added)."),
    engine: str = Parameter(da_config.DEFAULT_VISUALIZATION_ENGINE, help="Visualization engine: 'graphviz' or 'pyvis'."),
    with_package_name_labels: bool = Parameter(True, help="Include package names in node labels."),
    title: Optional[str] = Parameter(None, help="Optional title for the visualization."),
    load_with_objects: bool = Parameter(False, help="Load the graph with code objects from database (use when input is structure-only)."),
    db_path: Optional[Path] = Parameter(None, help="Path to the PL/SQL analyzer SQLite database (required if load_with_objects=True)."),
    verbose_level: int = Parameter(da_config.LOG_VERBOSE_LEVEL, help="Logging verbosity (0-3).")
):
    """
    Generates a visualization of a given graph file.
    
    This function can work with both full graphs and structure-only graphs:
    - For structure-only input graphs, use load_with_objects=True to populate with code objects from database
      before visualization if you need the detailed object information.
    """
    local_logger = _setup(verbose_level)
    local_logger.info(f"Visualizing graph '{input_graph_path}' using '{engine}'. Output base: '{output_base_path}'")

    if not input_graph_path.exists():
        local_logger.critical(f"Input graph file not found: {input_graph_path}")
        return

    graph_storage = GraphStorage(local_logger)
    
    if load_with_objects:
        # If loading with objects, we need a database path
        if not db_path:
            local_logger.critical("Database path required when load_with_objects=True. Cannot proceed.")
            return
        
        if not db_path.exists():
            local_logger.critical(f"Database file not found at {db_path}. Cannot proceed.")
            return
        
        # Setup database loading
        db_manager = DatabaseManager(db_path, local_logger)
        loader = DatabaseLoader(db_manager, local_logger)
        
        # Load structure and populate with objects
        local_logger.info(f"Loading graph structure from {input_graph_path} and populating with objects from database...")
        graph_to_viz = graph_storage.load_and_populate(
            input_graph_path, 
            loader,
            format=Path(input_graph_path).suffix.lstrip('.')
        )
    else:
        # Regular loading without populating from database
        graph_to_viz = graph_storage.load_graph(
            input_graph_path, 
            format=Path(input_graph_path).suffix.lstrip('.')
        )

    if not graph_to_viz:
        local_logger.error(f"Failed to load graph from {input_graph_path} for visualization.")
        return
    
    if graph_to_viz.number_of_nodes() == 0:
        local_logger.warning(f"Graph for '{input_graph_path}' is empty. Skipping visualization.")
        return

    output_base_path.parent.mkdir(parents=True, exist_ok=True) # Ensure output directory exists

    try:
        if engine == "graphviz":
            viz_graph = exporter.to_graphviz(
                graph_to_viz,
                local_logger,
                with_package_name=with_package_name_labels
            )
            if title:
                viz_graph.attr(label=title, labelloc="t", fontsize="20")
            
            output_path_png = output_base_path.with_suffix(".png")
            output_path_dot = output_base_path.with_suffix(".dot")
            # Ensure render saves .dot correctly
            viz_graph.render(outfile=output_path_png, format="png", view=False, cleanup=False)
            # Check if .dot was created as expected, rename if render added .png.dot
            temp_dot_path = output_base_path.parent / (output_path_png.name + ".dot") # Common pattern for graphviz render
            if temp_dot_path.exists() and temp_dot_path != output_path_dot:
                 temp_dot_path.rename(output_path_dot)
            elif not output_path_dot.exists() and (output_base_path.parent / output_base_path.name).exists(): # if render saved it as output_base_path without extension
                 (output_base_path.parent / output_base_path.name).rename(output_path_dot)


            local_logger.info(f"Graphviz visualization saved to {output_path_png} (and .dot source: {output_path_dot}).")

        elif engine == "pyvis":
            pyvis_net = exporter.to_pyvis(
                graph_to_viz,
                local_logger,
                with_package_name=with_package_name_labels,
                pyvis_kwargs={'height': '800px', 'width': '100%', 'heading': title or output_base_path.name}
            )
            output_path_html = output_base_path.with_suffix(".html")
            pyvis_net.save_graph(str(output_path_html))
            local_logger.info(f"Pyvis interactive visualization saved to {output_path_html}.")
        else:
            local_logger.error(f"Unsupported visualization engine: {engine}")
    except ImportError as ie:
        local_logger.error(f"ImportError for visualization engine '{engine}': {ie}. Ensure it's installed.")
    except Exception as e:
        local_logger.error(f"Error generating or saving {engine} visualization: {e}", exc_info=True)
    local_logger.info("Visualization finished.")

@app.command
def analyze_metrics(
    graph_path: Path = Parameter(..., help="Path to the dependency graph file (full or subgraph)."),
    graph_format: str = Parameter(da_config.DEFAULT_GRAPH_FORMAT, help=f"Format of the graph file. Options: {da_config.VALID_GRAPH_FORMATS}"),
    verbose_level: int = Parameter(da_config.LOG_VERBOSE_LEVEL, help="Logging verbosity (0-3)."),
):
    """
    Calculates and stores complexity metrics for each node in an existing dependency graph file.
    Metrics include LOC, number of parameters, outgoing calls, and approximate cyclomatic complexity (ACC).
    The graph is updated in-place and saved back to the same file.
    """
    local_logger = _setup(verbose_level)
    local_logger.info(f"Analyzing metrics for graph '{graph_path}'...")

    if not graph_path.exists():
        local_logger.critical(f"Graph file not found: {graph_path}")
        return

    graph_storage = GraphStorage(local_logger)
    graph = graph_storage.load_graph(graph_path, format=graph_format)
    if not graph:
        local_logger.error(f"Failed to load graph from '{graph_path}'.")
        return

    analyzer.calculate_node_complexity_metrics(graph, local_logger)
    # Save the updated graph (structure-only, as metrics are node attributes)
    if graph_storage.save_structure_only(graph, graph_path, format=graph_format):
        local_logger.info(f"Metrics calculated and graph updated at '{graph_path}'.")
    else:
        local_logger.error(f"Failed to save updated graph with metrics to '{graph_path}'.")

if __name__ == "__main__": # To make cli.py runnable directly for development
    app()
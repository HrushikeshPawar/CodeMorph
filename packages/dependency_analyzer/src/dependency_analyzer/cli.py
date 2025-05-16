from __future__ import annotations

from pathlib import Path
from typing import Optional

import cyclopts
from cyclopts import Parameter
from loguru import logger

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
    verbose_level: int = Parameter(da_config.LOG_VERBOSE_LEVEL, help="Logging verbosity (0-3).")
):
    """
    Builds a full dependency graph from the database and saves it.
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

    local_logger.info(
        f"Graph construction complete. Nodes: {dependency_graph.number_of_nodes()}, Edges: {dependency_graph.number_of_edges()}."
    )
    if out_of_scope_calls:
        local_logger.warning(f"Encountered {len(out_of_scope_calls)} out-of-scope calls.")

    graph_storage = GraphStorage(local_logger)
    if graph_storage.save_graph(dependency_graph, output_graph_path, format=graph_format):
        local_logger.info(f"Graph saved successfully to {output_graph_path}")
    else:
        local_logger.error(f"Failed to save graph to {output_graph_path}")
    local_logger.info("Full build finished.")

@app.command
def create_subgraph(
    input_graph_path: Path = Parameter(..., help="Path to the full dependency graph file."),
    node_id: str = Parameter(..., help="ID of the central node for the subgraph."),
    output_subgraph_path: Path = Parameter(..., help="Path to save the generated subgraph."),
    graph_format: str = Parameter(da_config.DEFAULT_GRAPH_FORMAT, help=f"Format to save the subgraph. Options: {da_config.VALID_GRAPH_FORMATS}"),
    upstream_depth: int = Parameter(0, help="How many levels of callers (upstream) to include."),
    downstream_depth: int = Parameter(999, help="How many levels of callees (downstream) to include (default: full)."), # 999 as a proxy for "all"
    verbose_level: int = Parameter(da_config.LOG_VERBOSE_LEVEL, help="Logging verbosity (0-3).")
):
    """
    Creates a subgraph from a given node in a larger graph and saves it.
    """
    local_logger = _setup(verbose_level)
    local_logger.info(f"Creating subgraph for node '{node_id}' from '{input_graph_path}'. Output: '{output_subgraph_path}'")

    if not input_graph_path.exists():
        local_logger.critical(f"Input graph file not found: {input_graph_path}")
        return

    graph_storage = GraphStorage(local_logger)
    full_graph = graph_storage.load_graph(input_graph_path, format=Path(input_graph_path).suffix.lstrip('.')) # Infer format from extension

    if not full_graph:
        local_logger.error(f"Failed to load graph from {input_graph_path}")
        return

    if node_id not in full_graph:
        local_logger.error(f"Node ID '{node_id}' not found in the loaded graph.")
        return

    subgraph = analyzer.generate_subgraph_for_node(
        full_graph, node_id, local_logger, upstream_depth, downstream_depth
    )

    if subgraph and subgraph.number_of_nodes() > 0:
        if graph_storage.save_graph(subgraph, output_subgraph_path, format=graph_format):
            local_logger.info(f"Subgraph saved successfully to {output_subgraph_path}")
        else:
            local_logger.error(f"Failed to save subgraph to {output_subgraph_path}")
    elif subgraph: # Empty subgraph
        local_logger.info(f"Generated subgraph for '{node_id}' is empty. Nothing to save.")
    else:
        local_logger.error(f"Failed to generate subgraph for '{node_id}'.")
    local_logger.info("Subgraph creation finished.")

@app.command
def visualize(
    input_graph_path: Path = Parameter(..., help="Path to the graph file to visualize (full or subgraph)."),
    output_base_path: Path = Parameter(da_config.VISUALIZATIONS_DIR / f"viz_{da_config.TIMESTAMP}", help="Base path and filename for the output visualization (extension will be added)."),
    engine: str = Parameter(da_config.DEFAULT_VISUALIZATION_ENGINE, help="Visualization engine: 'graphviz' or 'pyvis'."),
    with_package_name_labels: bool = Parameter(True, help="Include package names in node labels."),
    title: Optional[str] = Parameter(None, help="Optional title for the visualization."),
    verbose_level: int = Parameter(da_config.LOG_VERBOSE_LEVEL, help="Logging verbosity (0-3).")
):
    """
    Generates a visualization of a given graph file.
    """
    local_logger = _setup(verbose_level)
    local_logger.info(f"Visualizing graph '{input_graph_path}' using '{engine}'. Output base: '{output_base_path}'")

    if not input_graph_path.exists():
        local_logger.critical(f"Input graph file not found: {input_graph_path}")
        return

    graph_storage = GraphStorage(local_logger)
    graph_to_viz = graph_storage.load_graph(input_graph_path, format=Path(input_graph_path).suffix.lstrip('.'))

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
                with_package_name=with_package_name_labels,
                package_colors=da_config.PACKAGE_COLORS_DEFAULT
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
                package_colors=da_config.PACKAGE_COLORS_DEFAULT,
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

if __name__ == "__main__": # To make cli.py runnable directly for development
    app()
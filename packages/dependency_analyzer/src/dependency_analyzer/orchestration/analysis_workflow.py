"""
AnalysisWorkflow for the Dependency Analyzer.

This module orchestrates various analysis tasks on a constructed dependency graph,
such as finding unused objects, circular dependencies, generating subgraphs,
and producing visualizations.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Set, List, Optional

import networkx as nx
import loguru as lg

# Local application/library specific imports
from dependency_analyzer.analysis import analyzer
from dependency_analyzer.visualization import exporter

if TYPE_CHECKING:
    from dependency_analyzer import config as da_config # Use 'da_config' to avoid conflict if 'config' is a var name
    from dependency_analyzer.persistence.graph_storage import GraphStorage


class AnalysisWorkflow:
    """
    Orchestrates the dependency analysis process.

    This class takes a constructed dependency graph and applies various
    analysis functions to it, logs the results, and can generate
    visualizations and reports.
    """

    def __init__(
        self,
        config_module: da_config, # Pass the config module itself
        logger: lg.Logger,
        graph: nx.DiGraph,
        graph_storage: GraphStorage,
    ):
        """
        Initializes the AnalysisWorkflow.

        Args:
            config_module: The dependency_analyzer configuration module.
            logger: A Loguru logger instance.
            graph: The NetworkX DiGraph representing code dependencies.
            graph_storage: An instance of GraphStorage for saving/loading graphs.
        """
        self.config = config_module
        self.logger = logger.bind(class_name=self.__class__.__name__)
        self.graph = graph
        self.graph_storage = graph_storage
        self.logger.info("AnalysisWorkflow initialized.")

    def run_standard_analyses(self) -> None:
        """
        Runs a predefined set of standard analyses on the graph.
        """
        self.logger.info("Starting standard analyses...")

        if not self.graph or self.graph.number_of_nodes() == 0:
            self.logger.warning("Graph is empty or not provided. Skipping analyses.")
            return

        # 1. Find Unused Objects (Potential Entry Points or Dead Code)
        self.logger.info("-" * 30)
        unused_objects: Set[str] = analyzer.find_unused_objects(self.graph, self.logger)
        self.logger.info(f"Found {len(unused_objects)} unused objects (in-degree 0).")
        if unused_objects:
            self.logger.info("Unused objects list (first 10):")
            for i, obj_id in enumerate(list(unused_objects)[:10]):
                self.logger.info(f"  - {obj_id}")
            if len(unused_objects) > 10:
                self.logger.info(f"  ... and {len(unused_objects) - 10} more.")
        
        # 2. Find Circular Dependencies
        self.logger.info("-" * 30)
        circular_deps: List[List[str]] = analyzer.find_circular_dependencies(self.graph, self.logger)
        self.logger.info(f"Found {len(circular_deps)} circular dependencies (cycles).")
        if circular_deps:
            self.logger.info("Circular dependencies list (first 5 cycles):")
            for i, cycle in enumerate(circular_deps[:5]):
                self.logger.info(f"  Cycle {i+1}: {' -> '.join(cycle)} -> {cycle[0]}")
            if len(circular_deps) > 5:
                self.logger.info(f"  ... and {len(circular_deps) - 5} more cycles.")

        # 3. Find Terminal Nodes (Objects that don't call anything else in scope)
        self.logger.info("-" * 30)
        terminal_nodes: Set[str] = analyzer.find_terminal_nodes(self.graph, self.logger, exclude_placeholders=True)
        self.logger.info(f"Found {len(terminal_nodes)} terminal nodes (out-degree 0, excluding placeholders).")
        if terminal_nodes:
            self.logger.info("Terminal nodes list (first 10):")
            for i, obj_id in enumerate(list(terminal_nodes)[:10]):
                self.logger.info(f"  - {obj_id}")
            if len(terminal_nodes) > 10:
                self.logger.info(f"  ... and {len(terminal_nodes) - 10} more.")

        # 4. Identify Entry Points (alias for unused_objects, semantically different)
        self.logger.info("-" * 30)
        entry_points: Set[str] = analyzer.find_entry_points(self.graph, self.logger) # Reuses find_unused_objects
        self.logger.info(f"Identified {len(entry_points)} potential entry points (in-degree 0).")
        # Logging details already done by find_unused_objects if called directly.

        self.logger.info("Standard analyses completed.")


    def generate_and_save_visualization(
        self,
        graph_to_viz: nx.DiGraph,
        base_filename: str,
        engine: str = "graphviz", # "graphviz" or "pyvis"
        title: Optional[str] = None,
        with_package_name_labels: bool = True,
    ) -> None:
        """
        Generates a visualization of the given graph and saves it.

        Args:
            graph_to_viz: The graph to visualize.
            base_filename: The base name for the output file (without extension).
            engine: The visualization engine to use ("graphviz" or "pyvis").
            title: Optional title for the visualization.
            with_package_name_labels: Whether to include package names in node labels.
        """
        if not graph_to_viz or graph_to_viz.number_of_nodes() == 0:
            self.logger.warning(f"Graph for '{base_filename}' is empty. Skipping visualization.")
            return

        self.logger.info(f"Generating '{engine}' visualization for '{base_filename}'...")

        try:
            if engine == "graphviz":
                viz_graph = exporter.to_graphviz(
                    graph_to_viz,
                    self.logger,
                    with_package_name=with_package_name_labels,
                    package_colors=self.config.PACKAGE_COLORS_DEFAULT
                )
                if title:
                    viz_graph.attr(label=title, labelloc="t", fontsize="20")
                
                # Save as PNG and DOT source
                output_path_png = self.config.VISUALIZATIONS_DIR / f"{base_filename}.png"
                output_path_dot = self.config.VISUALIZATIONS_DIR / f"{base_filename}.dot"
                viz_graph.render(outfile=output_path_png, format="png", cleanup=False) # Keep .dot
                # viz_graph.save(output_path_dot) # render already saves .dot if cleanup=False
                if output_path_dot.exists() and output_path_dot.name != f"{base_filename}.png.dot": # render might add .png before .dot
                    output_path_dot.rename(self.config.VISUALIZATIONS_DIR / f"{base_filename}.dot")


                self.logger.info(f"Graphviz visualization saved to {output_path_png} (and .dot source).")

            elif engine == "pyvis":
                pyvis_net = exporter.to_pyvis(
                    graph_to_viz,
                    self.logger,
                    with_package_name=with_package_name_labels,
                    package_colors=self.config.PACKAGE_COLORS_DEFAULT,
                    pyvis_kwargs={'height': '800px', 'width': '100%', 'heading': title or base_filename}
                )
                output_path_html = self.config.VISUALIZATIONS_DIR / f"{base_filename}.html"
                pyvis_net.save_graph(str(output_path_html))
                self.logger.info(f"Pyvis interactive visualization saved to {output_path_html}.")

            else:
                self.logger.error(f"Unsupported visualization engine: {engine}")
                return

        except ImportError as ie:
            self.logger.error(f"ImportError for visualization engine '{engine}': {ie}. Please ensure it's installed.")
            if engine == "graphviz":
                self.logger.error("Try: pip install graphviz")
            if engine == "pyvis":
                self.logger.error("Try: pip install pyvis")
        except Exception as e:
            self.logger.error(f"Error generating or saving {engine} visualization for '{base_filename}': {e}", exc_info=True)


    def generate_subgraph_visualizations(
            self,
            node_ids: List[str],
            upstream_depth: int = 1,
            downstream_depth: int = 1,
            engine: str = "graphviz"
        ) -> None:
        """
        Generates and saves visualizations for subgraphs around specified nodes.
        """
        self.logger.info(f"Generating subgraph visualizations for {len(node_ids)} nodes (depth U:{upstream_depth}, D:{downstream_depth}).")
        if not self.graph:
            self.logger.warning("Main graph not available. Cannot generate subgraphs.")
            return

        for node_id in node_ids:
            subgraph = analyzer.generate_subgraph_for_node(
                self.graph, node_id, self.logger, upstream_depth, downstream_depth
            )
            if subgraph and subgraph.number_of_nodes() > 0 :
                # Sanitize node_id for use in filename
                safe_node_id_filename = node_id.replace('.', '_').replace(':', '_')
                base_filename = f"subgraph_{safe_node_id_filename}_U{upstream_depth}_D{downstream_depth}"
                title = f"Subgraph for {node_id} (Upstream: {upstream_depth}, Downstream: {downstream_depth})"
                self.generate_and_save_visualization(subgraph, base_filename, engine=engine, title=title)
            elif subgraph and subgraph.number_of_nodes() == 0:
                 self.logger.info(f"Subgraph for '{node_id}' is empty (contains only the node itself or no connections at specified depth). Skipping visualization.")
            else:
                self.logger.warning(f"Could not generate subgraph for node '{node_id}'. Skipping visualization.")


    def run(self) -> None:
        """
        Executes the full analysis and visualization workflow.
        """
        self.logger.info("Starting full analysis workflow...")

        if not self.graph or self.graph.number_of_nodes() == 0:
            self.logger.error("Graph is empty. Aborting analysis workflow.")
            return

        # 1. Run standard analyses (logs results to console/file)
        self.run_standard_analyses()

        # 2. Generate and save visualization of the full graph
        self.logger.info("-" * 30)
        self.logger.info("Generating visualization for the full dependency graph...")
        full_graph_filename_base = f"full_dependency_graph_{self.config.TIMESTAMP}"
        self.generate_and_save_visualization(
            self.graph,
            full_graph_filename_base,
            engine=self.config.DEFAULT_VISUALIZATION_ENGINE,
            title="Full Dependency Graph"
        )
        # Optionally, generate with the other engine too if desired
        # alt_engine = "pyvis" if self.config.DEFAULT_VISUALIZATION_ENGINE == "graphviz" else "graphviz"
        # self.generate_and_save_visualization(
        #     self.graph,
        #     f"{full_graph_filename_base}_{alt_engine}",
        #     engine=alt_engine,
        #     title=f"Full Dependency Graph ({alt_engine})"
        # )


        # 3. Example: Generate subgraphs for a few key entry points or interesting nodes
        self.logger.info("-" * 30)
        entry_points = analyzer.find_entry_points(self.graph, self.logger)
        if entry_points:
            # Limit to a few examples to avoid too many files
            nodes_for_subgraph_viz = list(entry_points)[:3] # Take first 3 entry points
            if nodes_for_subgraph_viz:
                self.logger.info(f"Generating subgraph visualizations for example entry points: {nodes_for_subgraph_viz}")
                self.generate_subgraph_visualizations(
                    nodes_for_subgraph_viz,
                    upstream_depth=0, # Entry points have no upstream in-scope
                    downstream_depth=2,
                    engine=self.config.DEFAULT_VISUALIZATION_ENGINE
                )
            else:
                self.logger.info("No specific entry points selected for example subgraph visualization.")
        else:
            self.logger.info("No entry points found to generate example subgraph visualizations.")
        
        # Example: Subgraph for a node involved in a cycle (if any)
        cycles = analyzer.find_circular_dependencies(self.graph, self.logger)
        if cycles:
            first_cycle_node = cycles[0][0] # Take the first node of the first cycle
            self.logger.info(f"Generating subgraph visualization for a node in a cycle: {first_cycle_node}")
            self.generate_subgraph_visualizations(
                [first_cycle_node],
                upstream_depth=1,
                downstream_depth=1,
                engine=self.config.DEFAULT_VISUALIZATION_ENGINE
            )


        self.logger.info("Analysis workflow completed.")


if __name__ == "__main__":
    # This is an example of how to use the AnalysisWorkflow.
    # It requires a pre-constructed graph or loads one.

    # --- Setup for example ---
    from pathlib import Path
    project_root_example = Path(__file__).resolve().parent.parent.parent.parent.parent
    
    import sys
    if str(project_root_example) not in sys.path:
        sys.path.insert(0, str(project_root_example))

    try:
        from dependency_analyzer import config as da_config_module # Alias to avoid var name 'config'
        from dependency_analyzer.utils.logging_setup import configure_logger as da_configure_logger
        from dependency_analyzer.persistence.graph_storage import GraphStorage
        # For creating a mock graph if not loading
        from plsql_analyzer.core.code_object import PLSQL_CodeObject, CodeObjectType
    except ImportError as e:
        print(f"Could not import dependency_analyzer components: {e}. Ensure PYTHONPATH or run from project root.")
        sys.exit(1)

    # 1. Configure Logger
    da_config_module.ensure_artifact_dirs()
    example_logger = da_configure_logger(da_config_module.LOG_VERBOSE_LEVEL, da_config_module.LOGS_DIR)
    example_logger.info("--- AnalysisWorkflow Example ---")

    # 2. Prepare Graph and GraphStorage
    example_graph_storage = GraphStorage(example_logger)
    
    # Option A: Load an existing graph
    # graph_file_to_load = da_config_module.GRAPHS_DIR / "your_graph_file.gpickle" # Change to an actual file
    # example_graph = example_graph_storage.load_graph(graph_file_to_load, format="gpickle")

    # Option B: Create a mock graph for demonstration
    example_graph = nx.DiGraph()
    obj_a = PLSQL_CodeObject(name="proc_a", package_name="pkg1", type=CodeObjectType.PROCEDURE)
    obj_a.id = "pkg1.proc_a"
    obj_b = PLSQL_CodeObject(name="func_b", package_name="pkg1", type=CodeObjectType.FUNCTION)
    obj_b.id = "pkg1.func_b"
    obj_c = PLSQL_CodeObject(name="proc_c", package_name="pkg2", type=CodeObjectType.PROCEDURE)
    obj_c.id = "pkg2.proc_c"
    obj_d_unused = PLSQL_CodeObject(name="unused_d", package_name="pkg1", type=CodeObjectType.PROCEDURE)
    obj_d_unused.id = "pkg1.unused_d"
    
    example_graph.add_node(obj_a.id, object=obj_a)
    example_graph.add_node(obj_b.id, object=obj_b)
    example_graph.add_node(obj_c.id, object=obj_c)
    example_graph.add_node(obj_d_unused.id, object=obj_d_unused)
    
    example_graph.add_edges_from([(obj_a.id, obj_b.id), (obj_b.id, obj_c.id), (obj_c.id, obj_a.id)]) # Cycle A->B->C->A
    example_logger.info(f"Created a mock graph with {example_graph.number_of_nodes()} nodes and {example_graph.number_of_edges()} edges.")


    if not example_graph:
        example_logger.error("Failed to load or create a graph for the example. Exiting.")
    else:
        # 3. Initialize AnalysisWorkflow
        workflow = AnalysisWorkflow(
            config_module=da_config_module,
            logger=example_logger,
            graph=example_graph,
            graph_storage=example_graph_storage
        )

        # 4. Run the workflow
        workflow.run()

    example_logger.info("--- AnalysisWorkflow Example Finished ---")
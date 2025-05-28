"""
Structured CLI commands for the Dependency Analyzer package.

This module implements a comprehensive CLI interface using cyclopts with
command groups that provide a more intuitive user experience:
- init: Initialize configuration
- build: Build dependency graphs  
- analyze: Analyze dependency graphs
- visualize: Generate visualizations
- query: Query specific information from graphs

The CLI follows these principles:
- Clear error messages with suggestions
- Consistent parameter handling
- Progress feedback for long operations
- Proper resource management
- Comprehensive validation
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Annotated, List
from loguru import logger

from cyclopts import App, Parameter
from dependency_analyzer.settings import DependencyAnalyzerSettings, GraphFormat
from dependency_analyzer.cli.service import CLIService
from dependency_analyzer.cli.utils import handle_cli_error, CLIError
from dependency_analyzer.cli.parameters import (
    config_file_param, graph_path_param, output_fname_param, graph_format_param,
    verbose_param, depth_param, node_id_param, output_path_param, source_node_param,
    target_node_param, node_type_filter_param, package_filter_param,
    name_filter_param, limit_param, sort_by_param, input_path_param,
    min_cycle_length_param, max_cycle_length_param, output_format_param,
    include_node_details_param, sort_cycles_param
)
from dependency_analyzer.cli.constants import COMMAND_DESCRIPTIONS

# Main application
app = App(
    help="🔍 Dependency Analyzer CLI Tool\n\n"
         "Analyze and visualize code dependencies from PL/SQL codebases.\n"
         "Use subcommands to perform different operations on dependency graphs.\n\n"
         "Examples:\n"
         "  dependency-analyzer init                    # Initialize configuration\n"
         "  dependency-analyzer build full -o my_graph # Build full dependency graph\n"
         "  dependency-analyzer analyze classify        # Classify node types\n"
         "  dependency-analyzer visualize graph.gpickle # Generate visualization\n"
         "  dependency-analyzer query paths A B         # Find paths between nodes"
)

# Command groups
build_app = App(name="build", help=COMMAND_DESCRIPTIONS["build"])
analyze_app = App(name="analyze", help=COMMAND_DESCRIPTIONS["analyze"])
visualize_app = App(name="visualize", help=COMMAND_DESCRIPTIONS["visualize"])
query_app = App(name="query", help=COMMAND_DESCRIPTIONS["query"])

app.command(build_app)
app.command(analyze_app)
app.command(visualize_app)
app.command(query_app)


# =============================================================================
# INIT COMMAND
# =============================================================================

@app.command(name="init")
def init(
    output_path: Annotated[Optional[Path], output_path_param()] = None,
    verbose: Annotated[int, verbose_param()] = 3
):
    """Initialize configuration file with default settings."""
    try:
        service =  CLIService(DependencyAnalyzerSettings(log_verbose_level=verbose))
        service.initialize_config(output_path)
    except CLIError as e:
        handle_cli_error(e, logger)
        sys.exit(1)
    except Exception as e:
        handle_cli_error(CLIError(f"Unexpected error during initialization: {e}"), logger)
        sys.exit(1)


# =============================================================================
# BUILD COMMANDS
# =============================================================================

@build_app.command(name="full")
def build_full(
    config_file: Annotated[Path, config_file_param(True)],
    output_fname: Annotated[str, output_fname_param()],
    db_path: Annotated[Optional[Path], Parameter(help="Path to the PL/SQL analyzer SQLite database.", name=["--db", "--database"])] = None,
    graph_format: Annotated[Optional[str], graph_format_param()] = None,
    verbose: Annotated[int, verbose_param()] = 1,
    calculate_complexity: Annotated[bool, Parameter(help="Calculate and store complexity metrics for nodes.")] = True
):
    """Build a full dependency graph from the PL/SQL analyzer database."""
    try:
        
        settings = DependencyAnalyzerSettings.from_toml(config_file)
        if db_path:
            settings.database_path = db_path
        
        if graph_format:
            settings.graph_format = graph_format

        settings.log_verbose_level = verbose

        service =  CLIService(settings)
        service.build_full_graph(output_fname, calculate_complexity)
    except CLIError as e:
        handle_cli_error(e, logger)
        sys.exit(1)
    except Exception as e:
        handle_cli_error(CLIError(f"Unexpected error during full build: {e}"), logger)
        sys.exit(1)


@build_app.command(name="subgraph")
def build_subgraph(
    input_path: Annotated[Path, input_path_param()],
    node_id: Annotated[str, node_id_param()],
    config_file: Annotated[Path, config_file_param(True)],
    output_fname: Annotated[Optional[str], output_fname_param()]=None,
    upstream_depth: Annotated[int, Parameter(
        help="How many levels of callers (upstream) to include.",
        name=["--upstream", "-u"]
    )]=0,
    downstream_depth: Annotated[Optional[int], Parameter(
        help="How many levels of callees (downstream) to include.",
        name=["--downstream", "-d"]
    )] = None,
    graph_format: Annotated[Optional[str], graph_format_param()] = None,
    load_with_objects: Annotated[bool, Parameter(
        help="Load graph with objects from database."
    )] = False,
    verbose: Annotated[int, verbose_param()] = 1,
):
    """Extract a subgraph centered around a specific node."""
    try:
        settings = DependencyAnalyzerSettings.from_toml(config_file)
        
        if graph_format:
            settings.graph_format = graph_format

        settings.log_verbose_level = verbose

        if output_fname is None:
            output_fname = f"subgraph-{node_id.replace('.', '-')}"

        service =  CLIService(settings)
        service.build_subgraph(
            input_path=input_path,
            node_id=node_id,
            output_fname=output_fname,
            upstream_depth=upstream_depth,
            downstream_depth=downstream_depth,
            load_with_objects=load_with_objects
        )
    except CLIError as e:
        handle_cli_error(e, logger)
        sys.exit(1)
    except Exception as e:
        handle_cli_error(CLIError(f"Unexpected error during subgraph build: {e}"), logger)
        sys.exit(1)


# =============================================================================
# ANALYZE COMMANDS
# =============================================================================

@analyze_app.command(name="classify")
def analyze_classify(
    graph_path: Annotated[Path, graph_path_param()],
    config_file: Annotated[Path, config_file_param(True)],
    output_fname: Annotated[str, output_fname_param()],
    verbose: Annotated[int, verbose_param()] = 1,
    graph_format: Annotated[Optional[str], graph_format_param()] = None,
):
    """Classify nodes in the dependency graph by their role."""
    try:
        settings = DependencyAnalyzerSettings.from_toml(config_file)
        
        if graph_format:
            settings.graph_format = graph_format

        settings.log_verbose_level = verbose

        service = CLIService(settings)
        service.classify_nodes(
            graph_path=graph_path,
            output_fname=output_fname,
            graph_format=graph_format
        )
    except CLIError as e:
        handle_cli_error(e, logger)
        sys.exit(1)
    except Exception as e:
        handle_cli_error(CLIError(f"Unexpected error during node classification: {e}"), logger)
        sys.exit(1)


@analyze_app.command(name="cycles")
def analyze_cycles(
    graph_path: Annotated[Path, graph_path_param()],
    config_file: Annotated[Path, config_file_param(True)],
    verbose: Annotated[int, verbose_param()] = 1,
    min_cycle_length: Annotated[Optional[int], min_cycle_length_param()] = None,
    max_cycle_length: Annotated[Optional[int], max_cycle_length_param()] = None,
    output_format: Annotated[str, output_format_param()] = "table",
    include_node_details: Annotated[bool, include_node_details_param()] = False,
    sort_cycles: Annotated[str, sort_cycles_param()] = "length",
    output_fname: Annotated[Optional[str], Parameter(help="Save results to file (extension auto-added based on format).", name=["--output", "-o"])] = None,
):
    """Find and analyze circular dependencies in the dependency graph."""
    try:
        settings = DependencyAnalyzerSettings.from_toml(config_file)
        settings.log_verbose_level = verbose

        service = CLIService(settings)
        service.analyze_cycles(
            graph_path=graph_path,
            min_cycle_length=min_cycle_length,
            max_cycle_length=max_cycle_length,
            output_format=output_format,
            include_node_details=include_node_details,
            sort_cycles=sort_cycles,
            output_fname=output_fname
        )
    except CLIError as e:
        handle_cli_error(e, logger)
        sys.exit(1)
    except Exception as e:
        handle_cli_error(CLIError(f"Unexpected error during cycle analysis: {e}"), logger)
        sys.exit(1)


# =============================================================================
# VISUALIZE COMMANDS
# =============================================================================

@visualize_app.command(name="graph")
def visualize_graph(
    config_file: Annotated[Path, config_file_param(True)],
    graph_path: Annotated[Optional[Path], graph_path_param()],
    output_fname: Annotated[Optional[str], Parameter(help="Output filename (without extension).", name=["--output", "-o"])] = None,
    verbose: Annotated[int, verbose_param()] = 1,
    graph_format: Annotated[Optional[str], graph_format_param()] = None,
    title: Annotated[Optional[str], Parameter(help="Title for the visualization.")] = None
):
    """Generate a visualization from a dependency graph file."""
    try:
        settings = DependencyAnalyzerSettings.from_toml(config_file)

        if graph_path:
            settings.graph_path = graph_path
        
        if graph_format:
            settings.graph_format = graph_format

        settings.log_verbose_level = verbose

        service = CLIService(settings)
        service.create_visualization(
            graph_path=settings.graph_path,
            graph_format=settings.graph_format,
            output_fname=output_fname,
            title=title,

        )
    except CLIError as e:
        handle_cli_error(e, logger)
        sys.exit(1)
    except Exception as e:
        handle_cli_error(CLIError(f"Unexpected error during visualization: {e}"), logger)
        sys.exit(1)


@app.command(name="visualize-subgraph")
def visualize_subgraph(
    config_file: Annotated[Path, config_file_param(True)],
    node_id: Annotated[str, node_id_param()],
    output_image: Annotated[str, Parameter(help="Base path for output image (without extension).", name=["--output-image"])],
    db_path: Annotated[Optional[Path], Parameter(help="Path to the PL/SQL analyzer SQLite database.", name=["--db", "--database"])] = None,
    upstream_depth: Annotated[int, Parameter(help="Levels of callers to include", name=["--upstream-depth"])] = 0,
    downstream_depth: Annotated[Optional[int], Parameter(help="Levels of callees to include", name=["--downstream-depth"])] = None,
    save_full_graph: Annotated[Optional[str], Parameter(help="Optional path to save full graph.", name=["--save-full-graph"])] = None,
    save_subgraph: Annotated[Optional[str], Parameter(help="Optional path to save subgraph.", name=["--save-subgraph"])] = None,
    title: Annotated[Optional[str], Parameter(help="Title for the visualization.")] = None,
    verbose: Annotated[int, verbose_param()] = 1,
    graph_format: Annotated[Optional[str], graph_format_param()] = None,
):
    """Integrated command to build full graph, extract subgraph, and visualize it."""
    try:
        settings = DependencyAnalyzerSettings.from_toml(config_file)
        if db_path:
            settings.database_path = db_path
        if graph_format:
            settings.graph_format = graph_format
        settings.log_verbose_level = verbose
        
        service = CLIService(settings)
        service.visualize_subgraph_integrated(
            node_id=node_id,
            output_image=output_image,
            upstream_depth=upstream_depth,
            downstream_depth=downstream_depth,
            save_full_graph=save_full_graph,
            save_subgraph=save_subgraph,
            title=title
        )
    except CLIError as e:
        handle_cli_error(e, logger)
        sys.exit(1)
    except Exception as e:
        handle_cli_error(CLIError(f"Unexpected error during visualize-subgraph: {e}"), logger)
        sys.exit(1)


# =============================================================================
# QUERY COMMANDS
# =============================================================================

@query_app.command(name="reachability")
def query_reachability(
    graph_path: Annotated[Path, graph_path_param(True)],
    node_id: Annotated[str, node_id_param()],
    config_file: Annotated[Path, config_file_param(True)],
    verbose: Annotated[int, verbose_param()] = 1,
    graph_format: Annotated[Optional[GraphFormat], graph_format_param()] = None,
    downstream: Annotated[bool, Parameter(
        help="Show descendants (downstream reachability)."
    )] = True,
    upstream: Annotated[bool, Parameter(
        help="Show ancestors (upstream reachability)."
    )] = False,
    depth: Annotated[Optional[int], depth_param()] = None
):
    """Analyze reachability (upstream/downstream nodes) for a specific node."""
    try:
        settings = DependencyAnalyzerSettings.from_toml(config_file)

        if graph_path:
            settings.graph_path = graph_path
        
        if graph_format:
            settings.graph_format = graph_format

        settings.log_verbose_level = verbose

        service = CLIService(settings)

        
        service.query_reachability(
            graph_path=graph_path,
            node_id=node_id,
            graph_format=graph_format,
            downstream=downstream,
            upstream=upstream,
            depth=depth
        )
    except CLIError as e:
        handle_cli_error(e)
        sys.exit(1)
    except Exception as e:
        handle_cli_error(CLIError(f"Unexpected error during reachability query: {e}"))
        sys.exit(1)


@query_app.command(name="paths")
def query_paths(
    graph_path: Annotated[Path, graph_path_param(True)],
    source_node: Annotated[str, source_node_param(True)],
    target_node: Annotated[str, target_node_param(True)],
    config_file: Annotated[Path, config_file_param(True)],
    verbose: Annotated[int, verbose_param()] = 1,
    graph_format: Annotated[Optional[str], graph_format_param()] = None,
    depth: Annotated[Optional[int], depth_param()] = None
):
    """Find all paths between two nodes in the dependency graph."""
    try:
        settings = DependencyAnalyzerSettings.from_toml(config_file)
        
        if graph_format:
            settings.graph_format = graph_format

        settings.log_verbose_level = verbose
        service = CLIService(settings)
        service.query_paths(
            graph_path=graph_path,
            source_node=source_node,
            target_node=target_node,
            graph_format=graph_format,
            depth=depth
        )
    except CLIError as e:
        handle_cli_error(e)
        sys.exit(1)
    except Exception as e:
        handle_cli_error(CLIError(f"Unexpected error during path query: {e}"))
        sys.exit(1)


@query_app.command(name="list")
def query_list(
    input_path: Annotated[Path, input_path_param()],
    config_file: Annotated[Path, config_file_param(True)],
    verbose: Annotated[int, verbose_param()] = 1,
    graph_format: Annotated[Optional[str], graph_format_param()] = None,
    node_type: Annotated[List[str], node_type_filter_param()] = [],
    package: Annotated[List[str], package_filter_param()] = [],
    name: Annotated[Optional[str], name_filter_param()] = None,
    limit: Annotated[Optional[int], limit_param()] = None,
    sort_by: Annotated[str, sort_by_param()] = "name"
):
    """List all available nodes in the dependency graph with optional filtering."""
    try:
        settings = DependencyAnalyzerSettings.from_toml(config_file)
        
        if graph_format:
            settings.graph_format = graph_format

        settings.log_verbose_level = verbose

        service = CLIService(settings)
        service.query_list_nodes(
            input_path=input_path,
            graph_format=graph_format,
            filter_node_type=node_type,
            filter_packages=package,
            filter_name_substr=name,
            limit=limit,
            sort_by=sort_by
        )
    except CLIError as e:
        handle_cli_error(e, logger)
        sys.exit(1)
    except Exception as e:
        handle_cli_error(CLIError(f"Unexpected error during node listing: {e}"), logger)
        sys.exit(1)


def main():
    """Main entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        handle_cli_error(CLIError(f"Unexpected error: {e}"))
        sys.exit(1)


if __name__ == "__main__":
    main()

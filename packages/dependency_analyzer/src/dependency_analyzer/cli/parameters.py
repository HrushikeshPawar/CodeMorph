"""
Reusable parameter definitions for CLI commands.

This module provides factory functions and common parameter definitions
to ensure consistency across commands and reduce duplication.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Annotated, Sequence

import cyclopts
from cyclopts import Parameter, Token

from dependency_analyzer.cli.constants import PARAMETER_HELP, VERBOSE_LEVEL_RANGE
from dependency_analyzer.settings import GraphFormat


def convert_to_path(_, path_str: Sequence[Token]) -> Optional[Path]:
    """Convert string to Path object."""
    return Path(path_str[0].value) if path_str else None


def validate_path_exists(_, path: Optional[Path]):
    """Validate that a path exists."""
    if path and not path.exists():
        raise cyclopts.ValidationError(f"Path does not exist: {path}")


def validate_verbose_level(_, level: int):
    """Validate verbose level is in range."""
    if not (VERBOSE_LEVEL_RANGE[0] <= level <= VERBOSE_LEVEL_RANGE[1]):
        raise cyclopts.ValidationError(
            f"Verbose level must be between {VERBOSE_LEVEL_RANGE[0]} and {VERBOSE_LEVEL_RANGE[1]}"
        )

def convert_to_graph_format(_, format_str: Sequence[Token]) -> GraphFormat:
    """Convert string to GraphFormat enum."""
    if format_str is None:
        return GraphFormat.GRAPHML
        
    try:
        return GraphFormat[format_str[0].value.upper()]
    except KeyError:
        raise cyclopts.ValidationError(f"Invalid graph format: {format_str[0].value}. Must be one of: {', '.join(GraphFormat._member_names_)}")
    


# Common parameter factories
def config_file_param(required: bool = False):
    """Create a config file parameter."""
    return Parameter(
        name=["--config", "-c"],
        help=PARAMETER_HELP['config_file'],
        converter=convert_to_path,
        validator=validate_path_exists if required else None
    )


def graph_path_param(required: bool = False):
    """Create a graph path parameter.""" 
    return Parameter(
        help=PARAMETER_HELP['graph_path'],
        converter=convert_to_path,
        validator=validate_path_exists if required else None
    )

def input_path_param():
    """Create an input path parameter."""
    return Parameter(
        name=["--input", "-i"],
        help="Path to the full dependency graph file.",
        converter=convert_to_path,
        validator=validate_path_exists
    )

def source_node_param(required: bool = False):
    """Create a source node parameter."""
    return Parameter(
        name=["--source", "-s"],
        help=PARAMETER_HELP['source_node'],
        validator=validate_path_exists if required else None
    )

def target_node_param(required: bool = False):
    """Create a target node parameter."""
    return Parameter(
        name=["--target", "-t"],
        help=PARAMETER_HELP['target_node'],
        validator=validate_path_exists if required else None
    )


def output_path_param():
    """Create an output path parameter."""
    return Parameter(
        help="Path where output will be saved",
        converter=convert_to_path
    )


def output_fname_param():
    """Create an output filename parameter."""
    return Parameter(
        name=["--out", "-o"],
        help=PARAMETER_HELP['output_fname']
    )


def graph_format_param():
    """Create a graph format parameter."""
    return Parameter(
        name=["--format", "-f"],
        help=PARAMETER_HELP['format'],
        converter=convert_to_graph_format,
        # validator=lambda _, fmt: fmt.casefold() in [x.casefold() for x in GraphFormat._member_names_ if fmt]  # Validate against enum names
    )


def verbose_param():
    """Create a verbose level parameter."""
    return Parameter(
        name=["--verbose", "-v"],
        help=PARAMETER_HELP['verbose'],
        validator=validate_verbose_level
    )


def depth_param(help_text: str = None):
    """Create a depth parameter."""
    return Parameter(
        help=help_text or PARAMETER_HELP['depth']
    )


def node_id_param():
    """Create a node ID parameter."""
    return Parameter(
        help=PARAMETER_HELP['node_id']
    )


def node_type_filter_param():
    """Create a node type filter parameter."""
    return Parameter(
        name=["--type", "-t"],
        help="Filter nodes by type. Multiple types can be specified. Options: PACKAGE, PROCEDURE, FUNCTION, TRIGGER, TYPE, UNKNOWN",
        consume_multiple=True,
    )


def package_filter_param():
    """Create a package filter parameter."""
    return Parameter(
        name=["--package", "-p"], 
        help="Filter nodes by package name (case-insensitive substring match)",
        consume_multiple=True,
    )


def name_filter_param():
    """Create a name filter parameter."""
    return Parameter(
        name=["--name", "-n"],
        help="Filter nodes by name (case-insensitive substring match)"
    )


def limit_param():
    """Create a limit parameter."""
    return Parameter(
        name=["--limit", "-l"],
        help="Maximum number of nodes to display (default: all)"
    )


def sort_by_param():
    """Create a sort by parameter."""
    return Parameter(
        name=["--sort", "-s"],
        help="Sort nodes by field. Options: name, type, package, degree (default: name)"
    )


def percentile_param(param_name: str):
    """Create a percentile parameter."""
    return Parameter(
        help=f"{param_name} {PARAMETER_HELP['percentile']}"
    )


def min_cycle_length_param():
    """Create a minimum cycle length parameter for cycle analysis."""
    return Parameter(
        name=["--min-length", "--min"],
        help=PARAMETER_HELP['min_cycle_length']
    )


def max_cycle_length_param():
    """Create a maximum cycle length parameter for cycle analysis."""
    return Parameter(
        name=["--max-length", "--max"],
        help=PARAMETER_HELP['max_cycle_length']
    )


def output_format_param():
    """Create an output format parameter."""
    return Parameter(
        name=["--format", "-f"],
        help=PARAMETER_HELP['output_format']
    )


def include_node_details_param():
    """Create a parameter to include detailed node information."""
    return Parameter(
        name=["--details", "-d"],
        help=PARAMETER_HELP['include_node_details']
    )


def sort_cycles_param():
    """Create a parameter to sort cycles by different criteria."""
    return Parameter(
        name=["--sort-cycles", "--sort"],
        help=PARAMETER_HELP['sort_cycles']
    )


# Common parameter type annotations for reuse
ConfigFileParam = Annotated[Optional[Path], config_file_param(required=False)]
RequiredConfigFileParam = Annotated[Path, config_file_param(required=True)]
GraphPathParam = Annotated[Optional[Path], graph_path_param(required=False)]
RequiredGraphPathParam = Annotated[Path, graph_path_param(required=True)]
OutputPathParam = Annotated[Optional[Path], output_path_param()]
OutputFnameParam = Annotated[str, output_fname_param()]
GraphFormatParam = Annotated[Optional[str], graph_format_param()]
VerboseParam = Annotated[Optional[int], verbose_param()]
DepthParam = Annotated[Optional[int], depth_param()]
NodeIdParam = Annotated[str, node_id_param()]

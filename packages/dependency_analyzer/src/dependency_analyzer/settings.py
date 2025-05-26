"""
Pydantic-based configuration for the Dependency Analyzer package.

This module provides a centralized, type-safe configuration management
using Pydantic's BaseModel. It replaces the previous config.py approach
with a more structured, validated configuration system.

It supports loading configuration from TOML files and environment variables.
"""
from __future__ import annotations

import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Union, ClassVar

import tomlkit
from loguru import logger
from pydantic import BaseModel, Field, field_validator, computed_field


class GraphFormat(str, Enum):
    """Valid graph storage formats."""
    GPICKLE = "gpickle"  # Python-specific, fast
    GRAPHML = "graphml"  # XML, interoperable
    GEXF = "gexf"        # XML, for Gephi
    JSON = "json"        # Node-link format for web


class VisualizationEngine(str, Enum):
    """Available visualization engines."""
    GRAPHVIZ = "graphviz"
    # PYVIS = "pyvis"


class LogLevel(int, Enum):
    """Log verbosity levels mapped to standard logging levels."""
    WARNING = 0
    INFO = 1
    DEBUG = 2
    TRACE = 3


class DependencyAnalyzerSettings(BaseModel):
    """
    Settings for the Dependency Analyzer package.
    
    This Pydantic model serves as the single source of truth for all
    configuration settings, providing type safety, validation, and
    centralized management of application settings.
    
    Settings are loaded with the following precedence (highest to lowest):
    1. CLI arguments
    2. TOML configuration file
    3. Environment variables
    4. Default values
    """
    # Class variables for config file handling
    DEFAULT_CONFIG_FILENAME: ClassVar[str] = "dep_analyzer_config.toml"
    DEFAULT_CONFIG_PATHS: ClassVar[list[Path]] = [
        Path(os.getcwd()) / DEFAULT_CONFIG_FILENAME, 
        Path.home() / ".config" / DEFAULT_CONFIG_FILENAME,
        Path(__file__).parent / DEFAULT_CONFIG_FILENAME,
    ]
    
    # Base output directory
    output_base_dir: Path = Field(
        default=Path(__file__).resolve().parent.parent.parent.parent.parent / "generated" / "artifacts",
        description="Base directory for all generated artifacts"
    )
    
    # Database configuration
    database_path: Optional[Path] = Field(
        default=None,
        description="Path to the SQLite database containing PL/SQL analysis results"
    )
    
    # Logging configuration
    log_verbose_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Verbosity level for console logging (0=WARNING, 1=INFO, 2=DEBUG, 3=TRACE)"
    )
    
    # Graph storage configuration
    graph_format: GraphFormat = Field(
        default=GraphFormat.GRAPHML,
        description="Default format for saving and loading graphs"
    )

    # Graph path - Used for loading graphs
    graph_path: Optional[Path] = Field(
        default=None,
        description="Path to the graph file for loading"
    )
    
    # Visualization configuration
    default_visualization_engine: VisualizationEngine = Field(
        default=VisualizationEngine.GRAPHVIZ,
        description="Default engine for visualizing graphs"
    )
    # Include package names in node labels
    with_package_name_labels: bool = Field(
        default=True,
        description="Include package names in node labels"
    )
    
    # Package color mapping for visualization
    package_colors: Dict[str, str] = Field(
        default={
            "SYS": "lightcoral",
            "DBMS_": "lightblue",
            "UTL_": "lightgreen",
            "STANDARD": "lightgoldenrodyellow",
            "UNKNOWN": "whitesmoke",  # For placeholder nodes
            "APP_CORE": "khaki",
            "APP_SERVICE": "mediumpurple",
            "APP_UTIL": "lightseagreen",
        },
        description="Color mapping for packages in visualizations"
    )
    
    # Feature flags
    enable_profiler: bool = Field(
        default=False, 
        description="Enable performance profiling"
    )
    calculate_complexity_metrics: bool = Field(
        default=True,
        description="Calculate complexity metrics during graph building"
    )
    
    # Timestamp for unique filenames
    timestamp: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"),
        description="Timestamp for unique filenames"
    )

    # Model configuration
    model_config = {
        "validate_default": True,
        "arbitrary_types_allowed": True,
    }
    
    @field_validator("output_base_dir", "database_path", mode="before")
    @classmethod
    def expand_path(cls, v: Optional[Union[str, Path]]):
        """Expand and resolve paths."""
        if v is None:
            return v
        if isinstance(v, str):
            expanded_path_str = Path(v).expanduser()
            expanded_path_str = os.path.expandvars(expanded_path_str)
        
        if isinstance(v, Path):
            expanded_path_str = v.expanduser()
            expanded_path_str = os.path.expandvars(expanded_path_str)

        return Path(expanded_path_str).resolve()
            
    @computed_field
    @property
    def logs_dir(self) -> Path:
        """Directory for log files."""
        return self.output_base_dir / "logs" / "dependency_analyzer"
        
    @computed_field
    @property
    def graphs_dir(self) -> Path:
        """Directory for graph files."""
        return self.output_base_dir / "graphs"
        
    @computed_field
    @property
    def visualizations_dir(self) -> Path:
        """Directory for visualization outputs."""
        return self.output_base_dir / "visualizations"
        
    @computed_field
    @property
    def reports_dir(self) -> Path:
        """Directory for analysis reports."""
        return self.output_base_dir / "reports"
        
    @computed_field
    @property
    def timestamp_readable(self) -> str:
        """Human-readable timestamp format."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Analysis parameters
    hub_degree_percentile: float = Field(
        default=0.95,
        description="Percentile threshold for hub nodes based on degree"
    )
    hub_betweenness_percentile: float = Field(
        default=0.95,
        description="Percentile threshold for hub nodes based on betweenness centrality"
    )
    hub_pagerank_percentile: float = Field(
        default=0.95,
        description="Percentile threshold for hub nodes based on PageRank"
    )
    utility_out_degree_percentile: float = Field(
        default=0.90,
        description="Percentile threshold for utility nodes based on out-degree"
    )
    utility_max_complexity: int = Field(
        default=50,
        description="Maximum complexity for a utility node"
    )
    orphan_component_max_size: int = Field(
        default=4,
        description="Maximum size for an orphan component"
    )

    def ensure_artifact_dirs(self) -> None:
        """
        Creates necessary artifact directories if they don't already exist.
        """
        dirs_to_create = [self.logs_dir, self.graphs_dir, self.visualizations_dir]
        for dir_path in dirs_to_create:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.trace(f"Directory created: {dir_path}")
            except OSError as e:
                error_msg = f"Error creating directory {dir_path}: {e}"
                try:
                    logger.error(error_msg)
                except Exception:  # Fallback if logger is not available/configured
                    print(f"ERROR: {error_msg}")
    
    @classmethod
    def from_toml(cls, config_path: Union[str, Path]) -> "DependencyAnalyzerSettings":
        """
        Create settings from a TOML config file.
        
        Args:
            config_path: Path to the TOML configuration file
            
        Returns:
            DependencyAnalyzerSettings instance with values from the TOML file
            
        Raises:
            FileNotFoundError: If the config file does not exist
            ValueError: If the config file is invalid
        """
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            config_data = tomlkit.loads(config_path.read_text())
            
            # Flatten nested dictionaries
            flat_config = {}
            
            # Handle [paths] section
            if "paths" in config_data:
                for key, value in config_data["paths"].items():
                    flat_config[key] = value
            
            # Handle [logging] section
            if "logging" in config_data:
                for key, value in config_data["logging"].items():
                    flat_config[key] = value
            
            # Handle [graph] section
            if "graph" in config_data:
                for key, value in config_data["graph"].items():
                    flat_config[key] = value
                    
            # Handle [visualization] section
            if "visualization" in config_data:
                for key, value in config_data["visualization"].items():
                    if key != "package_colors":
                        flat_config[key] = value
                
                # Handle package colors separately
                if "package_colors" in config_data["visualization"]:
                    flat_config["package_colors"] = config_data["visualization"]["package_colors"]
            
            # Handle [features] section
            if "features" in config_data:
                for key, value in config_data["features"].items():
                    flat_config[key] = value
                    
            # Handle [analysis] section
            if "analysis" in config_data:
                for key, value in config_data["analysis"].items():
                    flat_config[key] = value
            
            # Replace any None values with sentinel values
            for key, value in flat_config.items():
                if value == "None":
                    flat_config[key] = None
            
            # Drop any keys with None values
            flat_config = {k: v for k, v in flat_config.items() if v is not None}
            
            # Create settings object with the flattened config
            return cls(**flat_config)
            
        except Exception as e:
            raise ValueError(f"Error loading configuration from {config_path}: {e}")
    
    def write_default_config(self, path: Optional[Path] = None) -> Path:
        """
        Write a default configuration file.
        
        Args:
            path: Optional path where to write the file.
                 If not provided, writes to the current directory.
                 
        Returns:
            Path to the written config file
            
        Raises:
            OSError: If the file cannot be written
        """
        if path is None:
            path = Path.cwd() / self.DEFAULT_CONFIG_FILENAME
            
        # Organize config in sections
        config = {
            "paths": {
                "output_base_dir": str(self.output_base_dir),
                "database_path": str(self.database_path) if self.database_path else None,
            },
            "logging": {
                "log_verbose_level": int(self.log_verbose_level),
            },
            "graph": {
                "graph_format": self.graph_format,
            },
            "visualization": {
                "default_visualization_engine": self.default_visualization_engine,
                "with_package_name_labels": self.with_package_name_labels,
                "package_colors": self.package_colors,
            },
            "features": {
                "enable_profiler": self.enable_profiler,
                "calculate_complexity_metrics": self.calculate_complexity_metrics,
            },
            "analysis": {
                "hub_degree_percentile": self.hub_degree_percentile,
                "hub_betweenness_percentile": self.hub_betweenness_percentile,
                "hub_pagerank_percentile": self.hub_pagerank_percentile,
                "utility_out_degree_percentile": self.utility_out_degree_percentile,
                "utility_max_complexity": self.utility_max_complexity,
                "orphan_component_max_size": self.orphan_component_max_size,
            }
        }

        # Replace any None values with sentinel values
        for section, values in config.items():
            for key, value in values.items():
                if value is None:
                    config[section][key] = "None"
                elif isinstance(value, Path):
                    config[section][key] = str(value)
        
        try:
            with open(path, "w") as f:
                tomlkit.dump(config, f)
            return path
        except Exception as e:
            raise OSError(f"Failed to write config file to {path}: {e}")


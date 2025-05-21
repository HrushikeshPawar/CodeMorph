"""
Pydantic-based configuration for the Dependency Analyzer package.

This module provides a centralized, type-safe configuration management
using Pydantic's BaseModel. It replaces the previous config.py approach
with a more structured, validated configuration system.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

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
    PYVIS = "pyvis"


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
    """
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
    default_graph_format: GraphFormat = Field(
        default=GraphFormat.GRAPHML,
        description="Default format for saving and loading graphs"
    )
    
    # Visualization configuration
    default_visualization_engine: VisualizationEngine = Field(
        default=VisualizationEngine.GRAPHVIZ,
        description="Default engine for visualizing graphs"
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
    def expand_path(cls, v):
        """Expand and resolve paths."""
        if v is None:
            return v
        if isinstance(v, str):
            v = Path(v).expanduser()
        return v.resolve()
            
    @computed_field
    def logs_dir(self) -> Path:
        """Directory for log files."""
        return self.output_base_dir / "logs" / "dependency_analyzer"
        
    @computed_field
    def graphs_dir(self) -> Path:
        """Directory for graph files."""
        return self.output_base_dir / "graphs"
        
    @computed_field
    def visualizations_dir(self) -> Path:
        """Directory for visualization outputs."""
        return self.output_base_dir / "visualizations"
    
    def ensure_artifact_dirs(self) -> None:
        """
        Creates necessary artifact directories if they don't already exist.
        """
        dirs_to_create = [self.logs_dir, self.graphs_dir, self.visualizations_dir]
        for dir_path in dirs_to_create:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                error_msg = f"Error creating directory {dir_path}: {e}"
                try:
                    logger.error(error_msg)
                except Exception:  # Fallback if logger is not available/configured
                    print(f"ERROR: {error_msg}")


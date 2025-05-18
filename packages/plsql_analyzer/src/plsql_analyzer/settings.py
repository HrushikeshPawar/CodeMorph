from pathlib import Path
from typing import List
from pydantic import BaseModel, Field, field_validator
import os

class AppConfig(BaseModel):
    """
    Centralized application configuration using Pydantic for type safety and validation.
    """
    # Core configuration fields
    source_code_root_dir: Path = Field(..., description="Root directory containing source code to analyze.")
    output_base_dir: Path = Field(
        default=Path("generated/artifacts"),
        description="Base directory for all generated artifacts, logs, and outputs."
    )
    log_verbose_level: int = Field(
        default=1,
        ge=0,
        le=3,
        description="Verbosity level for logging (0=ERROR, 1=INFO, 2=DEBUG, 3=TRACE)."
    )
    log_file_prefix: str = Field(
        default="dependency_debug_",
        description="Prefix for log files."
    )
    log_trace_file_prefix: str = Field(
        default="dependency_trace_",
        description="Prefix for trace log files."
    )
    database_filename: str = Field(
        default="dependency_graph.db",
        description="Filename for the SQLite database storing analysis results."
    )
    include_patterns: List[str] = Field(
        default_factory=lambda: ["*.sql", "*.pls"],
        description="Glob patterns for files to include in analysis."
    )
    exclude_dirs: List[str] = Field(
        default_factory=lambda: ["__pycache__", ".git", "tests", "logs"],
        description="Directory names to exclude from analysis."
    )
    enable_profiler: bool = Field(
        default=False,
        description="Enable or disable profiling during analysis."
    )

    @property
    def artifacts_dir(self) -> Path:
        return self.output_base_dir

    @property
    def logs_dir(self) -> Path:
        return self.output_base_dir / "logs"

    @property
    def database_path(self) -> Path:
        return self.output_base_dir / self.database_filename

    def ensure_artifact_dirs(self) -> None:
        """Create necessary output directories if they do not exist."""
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @field_validator('source_code_root_dir', 'output_base_dir', mode='before')
    @classmethod
    def expand_and_resolve_path(cls, v):
        if isinstance(v, Path):
            v = str(v)
        v = os.path.expanduser(v)
        v = os.path.expandvars(v)
        return Path(v).resolve()

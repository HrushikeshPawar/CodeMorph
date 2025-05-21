"""
Tests for the DependencyAnalyzerSettings Pydantic model.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from types import NoneType

import pytest
from pydantic import ValidationError

from dependency_analyzer.settings import (
    DependencyAnalyzerSettings, GraphFormat, VisualizationEngine, LogLevel
)


class TestDependencyAnalyzerSettings:
    """Test cases for DependencyAnalyzerSettings."""

    def test_default_initialization(self):
        """Test initialization with default values."""
        settings = DependencyAnalyzerSettings()
        
        # Check that default values are set correctly
        assert isinstance(settings.output_base_dir, Path)
        assert settings.database_path is None
        assert settings.log_verbose_level == LogLevel.INFO
        assert settings.default_graph_format == GraphFormat.GRAPHML
        assert settings.default_visualization_engine == VisualizationEngine.GRAPHVIZ
        assert not settings.enable_profiler
        assert len(settings.package_colors) > 0
        
    def test_custom_initialization(self):
        """Test initialization with custom values."""
        custom_output_dir = Path("/tmp/custom_output")
        custom_settings = DependencyAnalyzerSettings(
            output_base_dir=custom_output_dir,
            log_verbose_level=LogLevel.DEBUG,
            default_graph_format=GraphFormat.GRAPHML,
            default_visualization_engine=VisualizationEngine.PYVIS,
            enable_profiler=True
        )
        
        assert custom_settings.output_base_dir == custom_output_dir
        assert custom_settings.log_verbose_level == LogLevel.DEBUG
        assert custom_settings.default_graph_format == GraphFormat.GRAPHML
        assert custom_settings.default_visualization_engine == VisualizationEngine.PYVIS
        assert custom_settings.enable_profiler is True
        
    def test_computed_directories(self):
        """Test that computed directories are derived correctly from output_base_dir."""
        base_dir = Path("/tmp/test_base_dir")
        settings = DependencyAnalyzerSettings(output_base_dir=base_dir)
        
        assert settings.logs_dir == base_dir / "logs" / "dependency_analyzer"
        assert settings.graphs_dir == base_dir / "graphs"
        assert settings.visualizations_dir == base_dir / "visualizations"
        
    def test_path_expansion(self):
        """Test that paths are properly expanded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "expanded_path"
            settings = DependencyAnalyzerSettings(output_base_dir=str(temp_path))
            assert settings.output_base_dir == temp_path

    def test_ensure_artifact_dirs(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = DependencyAnalyzerSettings(output_base_dir=temp_dir)
            settings.ensure_artifact_dirs()
            
            assert settings.logs_dir.exists()
            assert settings.graphs_dir.exists()
            assert settings.visualizations_dir.exists()
    
    def test_invalid_graph_format(self):
        """Test validation for invalid graph format."""
        with pytest.raises(ValidationError):
            DependencyAnalyzerSettings(default_graph_format="invalid_format")


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

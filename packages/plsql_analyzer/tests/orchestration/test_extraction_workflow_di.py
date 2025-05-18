from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest
from pathlib import Path

from plsql_analyzer.settings import AppConfig, CALL_EXTRACTOR_KEYWORDS_TO_DROP
from plsql_analyzer.orchestration.extraction_workflow import ExtractionWorkflow

@pytest.fixture
def mock_app_config():
    """Create a mock AppConfig with basic test values"""
    config = AppConfig(
        source_code_root_dir=Path("/test/source"),
        output_base_dir=Path("/test/output"),
        file_extensions_to_include=["sql"],
        exclude_names_from_processed_path=["Bulk Download"],
        call_extractor_keywords_to_drop=CALL_EXTRACTOR_KEYWORDS_TO_DROP[:10]  # Just use the first 10 keywords
    )
    return config

@pytest.fixture
def mock_extraction_components(test_logger):
    """Create mock components for ExtractionWorkflow"""
    db_manager = MagicMock()
    structural_parser = MagicMock()
    signature_parser = MagicMock()
    call_extractor = MagicMock()
    file_helpers = MagicMock()
    
    return {
        "logger": test_logger,
        "db_manager": db_manager,
        "structural_parser": structural_parser,
        "signature_parser": signature_parser, 
        "call_extractor": call_extractor,
        "file_helpers": file_helpers
    }

def test_extraction_workflow_init_with_app_config(mock_app_config, mock_extraction_components):
    """Test that ExtractionWorkflow initializes correctly with an AppConfig instance"""
    
    # Create the workflow with mock components and config
    workflow = ExtractionWorkflow(
        config=mock_app_config,
        **mock_extraction_components
    )
    
    # Verify that the workflow was initialized with the correct config
    assert workflow.config is mock_app_config
    assert workflow.config.source_code_root_dir == Path("/test/source")
    assert workflow.config.file_extensions_to_include == ["sql"]
    assert workflow.logger is not None
    
    # Check that metrics counters were initialized
    assert workflow.total_files_processed == 0
    assert workflow.total_objects_extracted == 0

@patch("plsql_analyzer.orchestration.extraction_workflow.Path")
def test_extraction_workflow_run_uses_config(mock_path_class, mock_app_config, mock_extraction_components):
    """Test that the run method uses the config correctly"""
    
    # Setup mock to simulate directory existence check
    mock_path_instance = MagicMock()
    mock_path_instance.is_dir.return_value = True
    mock_path_instance.rglob.return_value = []  # No files to process
    mock_path_class.return_value = mock_path_instance
    
    # Create the workflow
    workflow = ExtractionWorkflow(
        config=mock_app_config,
        **mock_extraction_components
    )
    
    # Run the workflow
    workflow.run()
    
    # Verify config was used to check source directory
    mock_path_class.assert_called_once_with(mock_app_config.source_code_root_dir)
    
    # Verify file extensions from config were used
    mock_path_instance.rglob.assert_called_with(f"*.{mock_app_config.file_extensions_to_include[0]}")

def test_extraction_workflow_process_single_file_uses_config(mock_app_config, mock_extraction_components):
    """Test that _process_single_file uses the config correctly"""
    
    # Setup mocks
    mock_extraction_components["file_helpers"].get_processed_fpath.return_value = "processed/path.sql"
    mock_extraction_components["file_helpers"].compute_file_hash.return_value = "mockhash123"
    mock_extraction_components["db_manager"].get_file_hash.return_value = None  # File not in DB
    
    # Create a mock for open() to avoid actual file reading
    mock_file = MagicMock()
    mock_file.__enter__.return_value.read.return_value = "-- Test SQL\nSELECT * FROM dual;"
    
    # Create the workflow
    workflow = ExtractionWorkflow(
        config=mock_app_config,
        **mock_extraction_components
    )
    
    # Call _process_single_file with a mock path
    test_file_path = Path("/test/path.sql")
    
    with patch("builtins.open", return_value=mock_file):
        workflow._process_single_file(test_file_path)
    
    # Verify the config's exclude_names_from_processed_path was used
    mock_extraction_components["file_helpers"].get_processed_fpath.assert_called_once_with(
        test_file_path, mock_app_config.exclude_names_from_processed_path
    )

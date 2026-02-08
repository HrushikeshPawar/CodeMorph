from __future__ import annotations
import loguru as lg

# Additional imports for testing the ExtractionWorkflow class
from pathlib import Path
from unittest.mock import MagicMock, patch
from plsql_analyzer.orchestration.extraction_workflow import ExtractionWorkflow

# Note: All clean_code_and_map_literals tests have been moved to tests/utils/test_code_cleaner.py

def test_extraction_workflow_force_reprocess(test_logger: lg.Logger):
    """Test that force_reprocess from the PLSQLAnalyzerSettings is correctly handled in _process_single_file."""
    
    mock_db_manager = MagicMock()
    mock_db_manager.get_file_hash.return_value = "current_hash_123"
    
    mock_file_helpers = MagicMock()
    mock_file_helpers.get_processed_fpath.return_value = "processed/path/file.sql"
    mock_file_helpers.compute_file_hash.return_value = "current_hash_123"
    mock_file_helpers.escape_angle_brackets = lambda x: x  # Simple passthrough
    
    # Other mocks needed for the workflow
    mock_structural_parser = MagicMock()
    mock_structural_parser.parse.return_value = ("", {})
    mock_signature_parser = MagicMock()
    mock_call_extractor = MagicMock()
    
    # Create two workflow instances with different configs
    # Config for normal processing
    mock_config_normal = MagicMock()
    mock_config_normal.force_reprocess = []
    
    # Config for forced reprocessing
    mock_config_force = MagicMock()
    mock_config_force.force_reprocess = ["/path/to/file.sql", "processed/path/file.sql"]
    
    workflow_normal = ExtractionWorkflow(
        config=mock_config_normal,
        logger=test_logger,
        db_manager=mock_db_manager,
        structural_parser=mock_structural_parser,
        signature_parser=mock_signature_parser,
        call_extractor=mock_call_extractor,
        file_helpers=mock_file_helpers
    )
    
    workflow_force = ExtractionWorkflow(
        config=mock_config_force,
        logger=test_logger,
        db_manager=mock_db_manager,
        structural_parser=mock_structural_parser,
        signature_parser=mock_signature_parser,
        call_extractor=mock_call_extractor,
        file_helpers=mock_file_helpers
    )
    
    # Test cases
    test_file_path = Path("/path/to/file.sql")
    
    # Case 1: Normal workflow with matching hash should skip processing
    with patch('builtins.open'):  # Prevent actual file opening
        workflow_normal._process_single_file(test_file_path)
    
    # Verify skipped due to hash match
    assert workflow_normal.total_files_skipped_unchanged == 1
    assert workflow_normal.total_files_processed == 0
    assert workflow_normal.total_files_force_reprocessed == 0
    
    # Case 2: Force workflow with matching hash should continue processing
    # We need to patch functions that would be called by _process_single_file after the hash check
    with patch('builtins.open', MagicMock()):
        with patch.object(workflow_force, 'db_manager') as mock_db:
            # Override update_file_hash to avoid needing to mock all subsequent code
            mock_db.update_file_hash.return_value = "current_hash_123"
            workflow_force._process_single_file(test_file_path)
    
    # Verify processing was forced despite hash match
    assert workflow_force.total_files_skipped_unchanged == 0
    assert workflow_force.total_files_force_reprocessed == 1
    assert workflow_force.total_files_processed == 1
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
def test_extraction_workflow_signature_raw_text(test_logger: lg.Logger):
    """Test that signature raw text is correctly extracted and passed to the CodeObject."""

    mock_db_manager = MagicMock()
    # Mock hash to ensure processing proceeds (file changed or new)
    mock_db_manager.get_file_hash.return_value = "old_hash"
    mock_db_manager.update_file_hash.return_value = True
    mock_db_manager.add_codeobject.return_value = True

    mock_file_helpers = MagicMock()
    mock_file_helpers.get_processed_fpath.return_value = "processed/path/file.sql"
    mock_file_helpers.compute_file_hash.return_value = "new_hash_456"
    mock_file_helpers.escape_angle_brackets = lambda x: x
    mock_file_helpers.derive_package_name_from_path.return_value = "PKG_A"

    # Mock Structural Parser to return one object
    mock_structural_parser = MagicMock()
    # Returns (package_name, objects_dict)
    # Object dict: { "OBJ_NAME": [ {start: 1, end: 5, type: "PROCEDURE", name_raw: "OBJ_NAME"} ] }
    mock_structural_parser.parse.return_value = (
        "PKG_A",
        {
            "MY_PROC": [
                {"start": 1, "end": 5, "type": "PROCEDURE", "name_raw": "MY_PROC"}
            ]
        }
    )

    # Mock Signature Parser to return raw_text
    mock_signature_parser = MagicMock()
    expected_raw_text = "PROCEDURE my_proc (p_val IN NUMBER) IS"
    mock_signature_parser.parse.return_value = {
        "proc_name": "my_proc",
        "params": [],
        "return_type": None,
        "raw_text": expected_raw_text
    }

    mock_call_extractor = MagicMock()
    mock_call_extractor.extract_calls_with_details.return_value = []

    mock_config = MagicMock()
    mock_config.exclude_names_from_processed_path = []
    mock_config.force_reprocess = []
    mock_config.file_extensions_to_include = ["sql"]
    mock_config.exclude_names_for_package_derivation = []
    mock_config.allow_parameterless_calls = False

    workflow = ExtractionWorkflow(
        config=mock_config,
        logger=test_logger,
        db_manager=mock_db_manager,
        structural_parser=mock_structural_parser,
        signature_parser=mock_signature_parser,
        call_extractor=mock_call_extractor,
        file_helpers=mock_file_helpers
    )

    test_file_path = Path("/path/to/file.sql")

    # Mock open to provide dummy code content
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        mock_file = MagicMock()
        # 5 lines of code to satisfy structural parser indices
        mock_file.read.return_value = "line1\nline2\nline3\nline4\nline5\n"
        mock_open.return_value.__enter__.return_value = mock_file

        workflow._process_single_file(test_file_path)

    # Verify db_manager.add_codeobject was called
    assert mock_db_manager.add_codeobject.called

    # Inspect the CodeObject passed to add_codeobject
    # call_args[0] contains positional args. The first arg is the code object.
    call_args = mock_db_manager.add_codeobject.call_args
    code_obj = call_args[0][0]

    from plsql_analyzer.core.code_object import PLSQL_CodeObject
    assert isinstance(code_obj, PLSQL_CodeObject)
    assert code_obj.signature_raw_text == expected_raw_text
    assert code_obj.name == "my_proc"

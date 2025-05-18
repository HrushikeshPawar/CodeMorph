from __future__ import annotations
import loguru as lg
import pytest
from plsql_analyzer.orchestration.extraction_workflow import clean_code_and_map_literals

# Additional imports for testing the ExtractionWorkflow class
from pathlib import Path
from unittest.mock import MagicMock, patch
from plsql_analyzer.orchestration.extraction_workflow import ExtractionWorkflow

# --- Test Cases ---
@pytest.mark.parametrize("input_code, expected_cleaned_code, expected_mapping", [
    # Basic Cases
    ("", "", {}),
    ("SELECT 1 FROM DUAL;", "SELECT 1 FROM DUAL;", {}),
    # Inline Comments
    ("SELECT 1; -- comment", "SELECT 1; ", {}),
    ("SELECT 1; -- comment\nSELECT 2;", "SELECT 1; \nSELECT 2;", {}),
    ("SELECT 1; --no_space_comment", "SELECT 1; ", {}),
    ("-- পুরো লাইন মন্তব্য\nSELECT 3;", "\nSELECT 3;", {}),
    ("SELECT 1; --", "SELECT 1; ", {}), # Comment marker at EOF
    # Multiline Comments
    ("/* comment */SELECT 1;", "SELECT 1;", {}),
    ("SELECT /* comment */ 1;", "SELECT  1;", {}),
    ("SELECT 1 /* comment \n on two lines */ FROM DUAL;", "SELECT 1  FROM DUAL;", {}),
    ("/* comment */", "", {}),
    ("SELECT 1; /**/", "SELECT 1; ", {}), # Empty multiline comment
    ("SELECT 1; /* unclosed", "SELECT 1; ", {}), # Unclosed multiline comment
    # String Literals
    ("v_var := 'text';", "v_var := '<LITERAL_0>';", {"<LITERAL_0>": "text"}),
    ("v_var := '';", "v_var := '<LITERAL_0>';", {"<LITERAL_0>": ""}),
    ("v_var := 'It''s a test';", "v_var := '<LITERAL_0>';", {"<LITERAL_0>": "It''s a test"}),
    ("v_var := 'two '''' quotes';", "v_var := '<LITERAL_0>';", {"<LITERAL_0>": "two '''' quotes"}),
    ("v_first := 'one'; v_second := 'two';", "v_first := '<LITERAL_0>'; v_second := '<LITERAL_1>';", {"<LITERAL_0>": "one", "<LITERAL_1>": "two"}),
    ("v_unclosed := 'text", "v_unclosed := '<LITERAL_0>", {"<LITERAL_0>": "text"}), # Unclosed literal
    # Mixed Scenarios
    ("SELECT '--not a comment--' FROM DUAL; -- but this is", "SELECT '<LITERAL_0>' FROM DUAL; ", {"<LITERAL_0>": "--not a comment--"}),
    ("SELECT '/*not a comment*/' FROM DUAL; /* but this is */", "SELECT '<LITERAL_0>' FROM DUAL; ", {'<LITERAL_0>': '/*not a comment*/'}),
    ("/* comment 'with quote' */ v_text := 'literal --with comment like sequence' ; -- final comment", " v_text := '<LITERAL_0>' ; ", {'<LITERAL_0>': 'literal --with comment like sequence'}),
    ("code -- comment 'literal in comment'\n more_code 'actual literal' -- another comment", "code \n more_code '<LITERAL_0>' ", {'<LITERAL_0>': 'actual literal'}),
    # Edge Cases
    ("--", "", {}), # Just a comment marker
    ("/*", "", {}), # Just a multiline comment start
    ("'", "'<LITERAL_0>", {"<LITERAL_0>": ""}), # Single quote (interpreted as start of unclosed literal)
    ("'''", "'<LITERAL_0>", {"<LITERAL_0>": "''"}), # Triple single quote ('', then unclosed ')
    # ("''''", "'<LITERAL_0>''<LITERAL_1>'", {"<LITERAL_0>": "", "<LITERAL_1>": ""}), # Quadruple single quote ('', then '') Not sure how this should be
    ("v := 'a'--comment\n||'b';", "v := '<LITERAL_0>'\n||'<LITERAL_1>';", {"<LITERAL_0>": "a", "<LITERAL_1>": "b"}),
    ("v := 'a'/*comment*/||'b';", "v := '<LITERAL_0>'||'<LITERAL_1>';", {"<LITERAL_0>": "a", "<LITERAL_1>": "b"}),
    ("SELECT 1 --comment\n", "SELECT 1 \n", {}),
    ("SELECT 1 /*comment*/\n", "SELECT 1 \n", {}),
    ("SELECT 'text'--comment", "SELECT '<LITERAL_0>'", {'<LITERAL_0>': 'text'}),
    ("SELECT 'text'/*comment*/", "SELECT '<LITERAL_0>'", {'<LITERAL_0>': 'text'}),
    ("SELECT 'text' /* comment */ -- another comment", "SELECT '<LITERAL_0>'  ", {'<LITERAL_0>': 'text'}),
    ("---- A line that looks like a separator", "", {}), # Multiple dashes start a comment
    # ("/*/**/*/", "", {}), # Nested-like multiline comment markers (outer wins) Nested not supported in PLSQL
    ("'/''*''/'", "'<LITERAL_0>'", {"<LITERAL_0>": "/''*''/"}), # Comment markers inside a string
    ("foo := 'bar' -- baz\nnext_line := 'qux';", "foo := '<LITERAL_0>' \nnext_line := '<LITERAL_1>';", {"<LITERAL_0>": "bar", "<LITERAL_1>": "qux"}),
    ("foo := 'bar' /* baz */\nnext_line := 'qux';", "foo := '<LITERAL_0>' \nnext_line := '<LITERAL_1>';", {"<LITERAL_0>": "bar", "<LITERAL_1>": "qux"}),

    # From real life
    ("FUNCTION open_document RETURN CLOB IS\n        l_xml CLOB;\nBEGIN\n         l_xml := '<?xml version=\"1.0\" ?>' || g_endchar;\n         l_xml := l_xml || '<autofax>' || g_endchar;\n    RETURN l_xml;\nEXCEPTION\n   WHEN OTHERS THEN\n      dbms_output.put_line(SUBSTR('open_document: '||SQLERRM,1,200));\n      RETURN(NULL);\nEND;", "FUNCTION open_document RETURN CLOB IS\n        l_xml CLOB;\nBEGIN\n         l_xml := '<LITERAL_0>' || g_endchar;\n         l_xml := l_xml || '<LITERAL_1>' || g_endchar;\n    RETURN l_xml;\nEXCEPTION\n   WHEN OTHERS THEN\n      dbms_output.put_line(SUBSTR('<LITERAL_2>'||SQLERRM,1,200));\n      RETURN(NULL);\nEND;",
        {
            "<LITERAL_0>": "<?xml version=\"1.0\" ?>",
            "<LITERAL_1>": "<autofax>",
            "<LITERAL_2>": "open_document: "
        })
])
def test_clean_code_and_map_literals(test_logger:lg.Logger, input_code, expected_cleaned_code, expected_mapping):
    cleaned_code, mapping = clean_code_and_map_literals(input_code, test_logger)
    assert cleaned_code == expected_cleaned_code
    assert mapping == expected_mapping

@pytest.mark.skip(reason="Q-quoted string handling to be implemented in the future.")
def test_q_quoted_strings_not_specially_handled(test_logger):
    # Current logic does not support q-quoting, treats q as a normal character
    # and ' as the delimiter. This test documents current behavior.
    code = "v_val := q'[Hello ' World]';"
    # Expected: q is normal char, [Hello  is literal, ] is normal, ; is normal
    # ' after q is start, ' after Hello is end.
    expected_cleaned_code = "v_val := q'<LITERAL_0>' World]';"
    expected_mapping = {"<LITERAL_0>": "[Hello "}
    cleaned_code, mapping = clean_code_and_map_literals(code, test_logger)
    assert cleaned_code == expected_cleaned_code
    assert mapping == expected_mapping

    code_2 = "v_val := Q'{text '' in q}'"
    expected_cleaned_2 = "v_val := Q'<LITERAL_0>'"
    expected_mapping_2 = {"<LITERAL_0>": "{text '' in q}"} # The inner '' are part of the literal content
    cleaned_code_2, mapping_2 = clean_code_and_map_literals(code_2, test_logger)
    assert cleaned_code_2 == expected_cleaned_2
    assert mapping_2 == expected_mapping_2

def test_extraction_workflow_force_reprocess(test_logger):
    """Test that force_reprocess from the AppConfig is correctly handled in _process_single_file."""
    
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
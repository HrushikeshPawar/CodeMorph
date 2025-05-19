"""
Tests for the code_cleaner.py utility module.
"""
from __future__ import annotations
import sys
import pytest
import loguru as lg

from plsql_analyzer.utils.code_cleaner import clean_code_and_map_literals

# Set up logger for tests
logger = lg.logger
logger.remove()
logger.add(
    sink=sys.stderr,
    level="TRACE",
    colorize=True,
    format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

@pytest.fixture
def test_logger() -> lg.Logger:
    """Return a logger instance for tests."""
    return logger

# Code moved from `test_extraction_workflow.py`
# --- Test _preprocess_code --- #
def test_preprocess_simple(test_logger):
    code = "BEGIN\n  my_proc('hello'); -- comment\nEND;"
    expected_clean_code = "BEGIN\n  my_proc('<LITERAL_0>'); \nEND;"
    expected_literals = {"<LITERAL_0>": "hello"}
    clean_code, literal_map = clean_code_and_map_literals(code, test_logger)
    assert clean_code == expected_clean_code
    assert literal_map == expected_literals

def test_preprocess_multiline_comment(test_logger):
    code = "/* Multi\nline\ncomment */\nmy_func(1);"
    expected_clean_code = "\nmy_func(1);"
    expected_literals = {}
    clean_code, literal_map = clean_code_and_map_literals(code, test_logger)
    assert clean_code == expected_clean_code
    assert literal_map == expected_literals

def test_preprocess_escaped_quotes(test_logger):
    code = "call_me('O''Malley');"
    expected_clean_code = "call_me('<LITERAL_0>');"
    expected_literals = {"<LITERAL_0>": "O''Malley"}
    clean_code, literal_map = clean_code_and_map_literals(code, test_logger)
    assert clean_code == expected_clean_code
    assert literal_map == expected_literals

def test_preprocess_no_literals_or_comments(test_logger):
    code = "a := b + c;"
    expected_clean_code = "a := b + c;"
    expected_literals = {}
    clean_code, literal_map = clean_code_and_map_literals(code, test_logger)
    assert clean_code == expected_clean_code
    assert literal_map == expected_literals

def test_preprocess_empty_string(test_logger):
    code = ""
    expected_clean_code = ""
    expected_literals = {}
    clean_code, literal_map = clean_code_and_map_literals(code, test_logger)
    assert clean_code == expected_clean_code
    assert literal_map == expected_literals

def test_preprocess_only_comments(test_logger):
    code = "-- line comment\n/* block comment */"
    expected_clean_code = "\n" # Newline remains from line comment
    expected_literals = {}
    clean_code, literal_map = clean_code_and_map_literals(code, test_logger)
    assert clean_code == expected_clean_code
    assert literal_map == expected_literals


# Code moved from `test_call_extraction.py`
# --- Tests for Preprocessing --- #
@pytest.mark.parametrize(
    "code, expected_cleaned_contains, expected_cleaned_not_contains, expected_literals_count, expected_literal_values",
    [
        ("simple code", ["simple code"], ["--", "/*", "<LITERAL_"], 0, []),
        ("-- comment\ncode", ["code"], ["-- comment", "<LITERAL_"], 0, []),
        ("/* block */code", ["code"], ["/* block */", "<LITERAL_"], 0, []),
        ("code 'literal'", ["code '<LITERAL_0>'"], ["'literal'"], 1, ["literal"]),
        ("code 'lit''eral'", ["code '<LITERAL_0>'"], ["'lit''eral'"], 1, ["lit''eral"]),
        ("code 'lit1' -- comment 'lit2'\n 'lit3'", ["code '<LITERAL_0>'", "<LITERAL_1>"], ["'lit1'", "'lit2'", "'lit3'", "-- comment"], 2, ["lit1", "lit3"]),
        ("code /* 'lit_in_comment' */ 'lit_after'", ["code", "'<LITERAL_0>'"], ["'lit_in_comment'", "'lit_after'", "/*"], 1, ["lit_after"]),
        # ("q'#delimited string#'", ["q'#delimited string#'"], [], 0, []), # Assuming q-quoting isn't handled yet
    ],
    ids=["plain", "inline_comment", "block_comment", "simple_literal", "escaped_literal", "mixed_comment_literal", "literal_in_block"] #, "q_quote_unhandled"]
)
def test_preprocess_code(code: str, expected_cleaned_contains: list[str], expected_cleaned_not_contains: list[str], expected_literals_count: int, expected_literal_values: list[str], test_logger):
    """Tests the _preprocess_code method directly."""
    
    clean_code, literal_map = clean_code_and_map_literals(code, test_logger)

    for item in expected_cleaned_contains:
        assert item in clean_code
    for item in expected_cleaned_not_contains:
        assert item not in clean_code

    assert len(literal_map) == expected_literals_count
    # Compare values without the outer quotes added by the preprocessor
    assert sorted(literal_map.values()) == sorted(expected_literal_values)


@pytest.mark.parametrize("input_code, expected_cleaned_code, expected_mapping", [
    # Simple case with single quotes
    ("SELECT 'foo' FROM dual", "SELECT '<LITERAL_0>' FROM dual", {"<LITERAL_0>": "foo"}),
    
    # Multiple literals
    ("CALL proc('foo', 'bar')", "CALL proc('<LITERAL_0>', '<LITERAL_1>')",
     {"<LITERAL_0>": "foo", "<LITERAL_1>": "bar"}),
    
    # Single quote within literal (escaped with another single quote)
    ("SELECT 'don''t' FROM dual", "SELECT '<LITERAL_0>' FROM dual", {"<LITERAL_0>": "don''t"}),
    
    # Comments removal (inline)
    ("SELECT 'foo' FROM dual -- Comment here", "SELECT '<LITERAL_0>' FROM dual ", {"<LITERAL_0>": "foo"}),
    
    # Comments removal (multi-line)
    ("SELECT 'foo' /* Multi-line\ncomment */ FROM dual", "SELECT '<LITERAL_0>'  FROM dual", {"<LITERAL_0>": "foo"}),
    
    # Complete function example with multiple literals and comments
    ("FUNCTION open_document RETURN CLOB IS\n        l_xml CLOB;\nBEGIN\n         l_xml := '<?xml version=\"1.0\" ?>' || g_endchar;\n         l_xml := l_xml || '<autofax>' || g_endchar;\n    RETURN l_xml;\nEXCEPTION\n   WHEN OTHERS THEN\n      dbms_output.put_line(SUBSTR('open_document: '||SQLERRM,1,200));\n      RETURN(NULL);\nEND;", 
     "FUNCTION open_document RETURN CLOB IS\n        l_xml CLOB;\nBEGIN\n         l_xml := '<LITERAL_0>' || g_endchar;\n         l_xml := l_xml || '<LITERAL_1>' || g_endchar;\n    RETURN l_xml;\nEXCEPTION\n   WHEN OTHERS THEN\n      dbms_output.put_line(SUBSTR('<LITERAL_2>'||SQLERRM,1,200));\n      RETURN(NULL);\nEND;",
        {
            "<LITERAL_0>": "<?xml version=\"1.0\" ?>",
            "<LITERAL_1>": "<autofax>",
            "<LITERAL_2>": "open_document: "
        })
])
def test_clean_code_and_map_literals(test_logger:lg.Logger, input_code, expected_cleaned_code, expected_mapping):
    """Tests the main clean_code_and_map_literals function."""
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
    # Similar expectation, ' after Q is start, first ' in text is end (even though actual q-quote would not end there)
    expected_cleaned_code_2 = "v_val := Q'<LITERAL_0>' in q}'"
    expected_mapping_2 = {"<LITERAL_0>": "{text "}
    cleaned_code_2, mapping_2 = clean_code_and_map_literals(code_2, test_logger)
    assert cleaned_code_2 == expected_cleaned_code_2
    assert mapping_2 == expected_mapping_2

from __future__ import annotations
import loguru as lg
import pytest
from plsql_analyzer.orchestration.extraction_workflow import clean_code_and_map_literals


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
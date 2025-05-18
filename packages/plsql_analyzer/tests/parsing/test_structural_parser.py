from __future__ import annotations
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch
import loguru as lg

from plsql_analyzer.orchestration.extraction_workflow import clean_code_and_map_literals
from plsql_analyzer.parsing.structural_parser import PlSqlStructuralParser, OBJECT_NAME_REGEX, PACKAGE_NAME_REGEX, END_CHECK_REGEX, KEYWORDS_REQUIRING_END_REGEX, KEYWORDS_REQUIRING_END_ONE_LINE_REGEX

# Relative import for the class to be tested

# # Configure a simple logger for tests
# test_logger.remove()
# test_logger.add(lambda _: None, level="INFO") # Suppress output during tests, or configure as needed


@pytest.fixture
def basic_parser(test_logger) -> PlSqlStructuralParser:
    """Provides a basic PlSqlStructuralParser instance for testing."""
    # Minimal code, as most methods operate on current_line_content or specific state
    parser = PlSqlStructuralParser(logger=test_logger, verbose_lvl=0)
    parser.reset_state() # Ensure clean state
    return parser

# --- Test Regular Expressions ---

@pytest.mark.parametrize("text, expected_match, expected_groups", [
    ("PROCEDURE my_proc IS", True, ("PROCEDURE", "my_proc")),
    ("FUNCTION my_func RETURN VARCHAR2 AS", True, ("FUNCTION", "my_func")),
    ("  procedure  \"My.Proc\" ( p_param IN VARCHAR2 ) is", True, ("procedure", "\"My.Proc\"")),
    ("function func_name(a number) return boolean is", True, ("function", "func_name")),
    ("FUNCTION schema.pkg.func RETURN T_TYPE IS", True, ("FUNCTION", "schema.pkg.func")),
    ("PROCEDURE p1;", True, ("PROCEDURE", "p1")), # Missing IS/AS
    ("CREATE PROCEDURE my_proc IS", True, ("PROCEDURE", "my_proc")), # CREATE is not part of this regex
    ("TYPE my_type IS RECORD", False, None),
    ("PROCEDURE\nmy_proc\nIS", True, ("PROCEDURE", "my_proc")), # Regex expects name on same line as keyword for basic match
    ("FUNCTION f_test RETURN NUMBER; -- fwd decl", True, ("FUNCTION", "f_test")),
    ("PROCEDURE p_test(a IN NUMBER); -- fwd decl", True, ("PROCEDURE", "p_test")),
])
def test_object_name_regex(text, expected_match, expected_groups):
    match = OBJECT_NAME_REGEX.search(text)
    if expected_match:
        assert match is not None
        assert match.groups()[:2] == expected_groups
    else:
        assert match is None

@pytest.mark.parametrize("text, expected_match, expected_name", [
    ("CREATE OR REPLACE PACKAGE BODY my_package IS", True, "my_package"),
    ("CREATE PACKAGE BODY \"MyPackage\" AS", True, "\"MyPackage\""),
    ("CREATE PACKAGE BODY \"My Package\" AS", True, "\"My"), # Space inside package name not handled
    ("CREATE NONEDITIONABLE PACKAGE BODY schema.pkg_name AS", True, "schema.pkg_name"),
    ("CREATE PACKAGE BODY pkg1 IS", True, "pkg1"),
    ("CREATE OR REPLACE EDITIONABLE PACKAGE BODY pkg_name IS", True, "pkg_name"),
    ("PACKAGE BODY my_package IS", False, None), # Missing CREATE
    ("CREATE OR REPLACE PACKAGE my_package IS", False, None), # Missing BODY
])
def test_package_name_regex(text, expected_match, expected_name):
    match = PACKAGE_NAME_REGEX.search(text)
    if expected_match:
        assert match is not None
        assert match.group(1).strip() == expected_name
    else:
        assert match is None

@pytest.mark.parametrize("text, expected_match", [
    ("END;", True),
    ("  END IF;", True),
    ("END LOOP;", True),
    ("PENDING", False),
    ("MY_VARIABLE_ENDING", False),
])
def test_end_check_regex(text, expected_match):
    match = END_CHECK_REGEX.search(text)
    if expected_match:
        assert match is not None
        assert match.group(1).upper() == "END"
    else:
        assert match is None

@pytest.mark.parametrize("text, expected_keywords", [
    ("IF condition THEN", ["IF"]),
    ("FOR i IN 1..10 LOOP", ["FOR", "LOOP"]), # This regex finds individual keywords
    ("WHILE x > 0 LOOP", ["WHILE", "LOOP"]),
    ("CASE var WHEN 1 THEN BEGIN", ["CASE", "BEGIN"]),
    ("END IF;", []), # END is not matched by this
    ("  if a then loop_var := 1; end if;", ["IF"]), # Only the first if
    ("SELECT * FROM my_table;", []),
    ("  begin execute immediate 'foo'; end;", ["BEGIN"]),
])
def test_keywords_requiring_end_regex(text, expected_keywords):
    matches = KEYWORDS_REQUIRING_END_REGEX.findall(text)
    assert [m.upper() for m in matches] == expected_keywords


@pytest.mark.parametrize("text, expected_match, expected_keyword", [
    ("IF condition THEN statement; END IF;", True, "IF"),
    ("FOR i IN 1..10 LOOP statement; END LOOP;", True, "FOR"), # This regex finds the block
    ("BEGIN statement; END;", True, "BEGIN"),
    ("IF condition THEN", False, None), # Not a one-liner
    ("  if a then b(); end if; -- comment", True, "if"),
    ("  if a then b(); end loop; -- mismatch", True, "if"), # Mismatched END type not checked by regex itself: TODO
])
def test_keywords_requiring_end_one_line_regex(text, expected_match, expected_keyword):
    match = KEYWORDS_REQUIRING_END_ONE_LINE_REGEX.search(text)
    if expected_match:
        assert match is not None
        assert match.group(1).upper() == expected_keyword.upper()
    else:
        assert match is None

# --- Test Class Methods ---

def test_parser_initialization(basic_parser: PlSqlStructuralParser):
    assert basic_parser.code == ""
    assert basic_parser.lines == []
    assert basic_parser.logger is not None
    assert basic_parser.verbose_lvl == 0
    # Check reset_state values
    assert basic_parser.line_num == 0
    assert basic_parser.current_line_content == ""
    assert basic_parser.processed_line_content == ""
    assert not basic_parser.inside_quote
    assert not basic_parser.inside_multiline_comment
    assert basic_parser.multiline_object_name_pending is None
    assert basic_parser.package_name is None
    assert basic_parser.collected_code_objects == {}
    assert basic_parser.block_stack == []
    assert basic_parser.scope_stack == []
    assert not basic_parser.is_awaiting_loop_for_for
    assert not basic_parser.is_awaiting_loop_for_while
    assert basic_parser.forward_decl_candidate is None

def test_reset_state(basic_parser: PlSqlStructuralParser):
    # Modify some state
    basic_parser.line_num = 10
    basic_parser.inside_quote = True
    basic_parser.package_name = "test_pkg"
    basic_parser.block_stack.append((5, "IF"))
    basic_parser.scope_stack.append((1, ("PACKAGE", "test_pkg"), {}))
    basic_parser.collected_code_objects["proc1"] = [{"start": 2, "end": 9, "type": "PROCEDURE"}]

    basic_parser.reset_state()

    assert basic_parser.line_num == 0
    assert not basic_parser.inside_quote
    assert basic_parser.package_name is None
    assert basic_parser.block_stack == []
    assert basic_parser.scope_stack == []
    assert basic_parser.collected_code_objects == {}
    assert basic_parser.logger is not None # Logger should persist

@pytest.mark.parametrize("line, initial_quote_state, expected_processed_line, expected_final_quote_state", [
    ("simple line", False, "simple line", False),
    ("line with -- comment", False, "line with ", False),
    ("line with 'string'", False, "line with ''", False), # String content is kept
    ("line with 'string' -- comment", False, "line with '' ", False),
    ("line with 'don''t break'", False, "line with ''", False),
    ("select 'string with -- inside' from dual;", False, "select '' from dual;", False),
    ("select q'[multi-line ' string]' from dual;", False, "select q'' string]'", True), # q-quotes are treated as normal strings by this simplified logic
    ("text 'unterminated string", False, "text '", True),
    (" rest of string'", True, "'", False), # Continuing a string
    (" -- comment on continued string line'", True, "'", False), # Comment not  respected if inside string part
    ("text -- 'commented out string'", False, "text ", False),
    ("text 'escaped '' quote' and normal text", False, "text '' and normal text", False),
    ("text 'string1' and 'string2'", False, "text '' and ''", False),
    ("", False, "", False),
    ("-- entire line comment", False, "", False),
    ("  -- leading space comment", False, "  ", False),
    ("line_before_quote 'str", False, "line_before_quote '", True),
    ("ing_after_quote'", True, "'", False),
    ("first 'part'; second_part -- comment", False, "first ''; second_part ", False),

    # Added After real files evals
    ("v_stgrec.RX_REFILL_NUM := TO_NUMBER(REPLACE(v_val,',',''));", False, "v_stgrec.RX_REFILL_NUM := TO_NUMBER(REPLACE(v_val,'',''));", False)
])
def test_remove_strings_and_inline_comments(basic_parser: PlSqlStructuralParser, line, initial_quote_state, expected_processed_line, expected_final_quote_state):
    processed_line, final_quote_state = basic_parser._remove_strings_and_inline_comments(line, initial_quote_state)
    assert processed_line == expected_processed_line
    assert final_quote_state == expected_final_quote_state

def test_push_pop_scope(basic_parser: PlSqlStructuralParser):
    basic_parser._push_scope(1, "PACKAGE", "my_pkg", is_package=True)
    assert len(basic_parser.scope_stack) == 1
    assert basic_parser.scope_stack[0] == (1, ("PACKAGE", "my_pkg"), {"has_seen_begin": False, "is_package": True})
    assert "my_pkg" not in basic_parser.collected_code_objects # Packages not added by default

    basic_parser._push_scope(5, "PROCEDURE", "my_proc")
    assert len(basic_parser.scope_stack) == 2
    assert basic_parser.scope_stack[1] == (5, ("PROCEDURE", "my_proc"), {"has_seen_begin": False, "is_package": False})
    assert "my_proc" in basic_parser.collected_code_objects
    assert basic_parser.collected_code_objects["my_proc"] == [{"start": 5, "end": -1, "type": "PROCEDURE"}]

    # Test forward decl candidate logic (simplified)
    basic_parser.processed_line_content = "PROCEDURE my_proc;" # Simulate line that might trigger candidate
    basic_parser._push_scope(10, "PROCEDURE", "fwd_proc_test")
    # _check_for_forward_decl_candidate is called inside _push_scope
    # We'd need to mock/verify its call or check parser.forward_decl_candidate if it was set

    popped_proc = basic_parser._pop_scope()
    assert popped_proc[1] == ("PROCEDURE", "fwd_proc_test")
    assert len(basic_parser.scope_stack) == 2 # my_proc and my_pkg left

    popped_proc2 = basic_parser._pop_scope()
    assert popped_proc2[1] == ("PROCEDURE", "my_proc")
    assert len(basic_parser.scope_stack) == 1

    popped_pkg = basic_parser._pop_scope()
    assert popped_pkg[1] == ("PACKAGE", "my_pkg")
    assert len(basic_parser.scope_stack) == 0

    with pytest.raises(IndexError):
        basic_parser._pop_scope()

def test_push_pop_block(basic_parser: PlSqlStructuralParser):
    basic_parser._push_block(1, "IF")
    assert basic_parser.block_stack == [(1, "IF")]
    basic_parser._push_block(2, "LOOP")
    assert basic_parser.block_stack == [(1, "IF"), (2, "LOOP")]

    popped_loop = basic_parser._pop_block()
    assert popped_loop == (2, "LOOP")
    assert basic_parser.block_stack == [(1, "IF")]

    popped_if = basic_parser._pop_block()
    assert popped_if == (1, "IF")
    assert basic_parser.block_stack == []

    with pytest.raises(IndexError):
        basic_parser._pop_block()

@pytest.mark.parametrize("code_lines, scope_line, scope_type, scope_name, processed_line_at_scope, expect_candidate", [
    (["PROCEDURE p_fwd;\n"], 1, "PROCEDURE", "p_fwd", "PROCEDURE p_fwd;", True),
    (["FUNCTION f_fwd RETURN NUMBER;\n"], 1, "FUNCTION", "f_fwd", "FUNCTION f_fwd RETURN NUMBER;", True),
    (["PROCEDURE p_normal IS\n", "BEGIN\n", "NULL;\n", "END;\n"], 1, "PROCEDURE", "p_normal", "PROCEDURE p_normal IS", False), # IS present
    (["FUNCTION f_normal RETURN NUMBER IS\n", "BEGIN\n", "RETURN 1;\n", "END;\n"], 1, "FUNCTION", "f_normal", "FUNCTION f_normal RETURN NUMBER IS", False), # IS present
    (["PROCEDURE p_lang AS LANGUAGE C NAME \"c_proc\";\n"], 1, "PROCEDURE", "p_lang", "PROCEDURE p_lang AS LANGUAGE C NAME \"c_proc\";", True),
    # Test with current line being different from scope line
    (["PROCEDURE p_multi_fwd\n", "(param1 VARCHAR2);\n"], 1, "PROCEDURE", "p_multi_fwd", "PROCEDURE p_multi_fwd", False), # Initial line
    (["PROCEDURE p_multi_fwd\n", "(param1 VARCHAR2);\n"], 1, "PROCEDURE", "p_multi_fwd", "(param1 VARCHAR2);", True), # Second line confirms
])
def test_check_for_forward_decl_candidate(basic_parser: PlSqlStructuralParser, code_lines, scope_line, scope_type, scope_name, processed_line_at_scope, expect_candidate):
    basic_parser.lines = code_lines
    basic_parser.line_num = code_lines.index(f"{processed_line_at_scope}\n") + 1 # Simulate being at the end of the provided lines for check
    basic_parser.processed_line_content = processed_line_at_scope # This is the line content when check is made

    # Manually set up the state as if _push_scope just happened
    # basic_parser.scope_stack.append((scope_line, (scope_type, scope_name), {"has_seen_begin": False, "is_package": False}))
    # basic_parser.collected_code_objects[scope_name.casefold()] = [{"start": scope_line, "end": -1, "type": scope_type}]

    basic_parser._check_for_forward_decl_candidate(processed_line_at_scope, scope_line, scope_type, scope_name)

    if expect_candidate:
        assert basic_parser.forward_decl_candidate == (scope_line, (scope_type, scope_name))
    else:
        assert basic_parser.forward_decl_candidate is None

def test_clear_forward_decl_candidate(basic_parser: PlSqlStructuralParser):
    basic_parser.forward_decl_candidate = (1, ("PROCEDURE", "p_test"))
    basic_parser.forward_decl_check_end_line = 2
    basic_parser._clear_forward_decl_candidate("reason test")
    assert basic_parser.forward_decl_candidate is None
    assert basic_parser.forward_decl_check_end_line is None

    # Test clearing when already None (should not fail)
    basic_parser._clear_forward_decl_candidate("reason test 2")
    assert basic_parser.forward_decl_candidate is None

def test_handle_forward_declaration(basic_parser: PlSqlStructuralParser):
    scope_line, scope_type, scope_name = 1, "PROCEDURE", "fwd_proc"
    basic_parser.forward_decl_candidate = (scope_line, (scope_type, scope_name))
    basic_parser.forward_decl_check_end_line = 1 # or some line number
    
    # Simulate state before handling
    basic_parser.scope_stack.append((scope_line, (scope_type, scope_name), {"has_seen_begin": False, "is_package": False}))
    obj_key = scope_name.casefold()
    basic_parser.collected_code_objects[obj_key] = [{"start": scope_line, "end": -1, "type": scope_type}]
    
    basic_parser.line_num = basic_parser.forward_decl_check_end_line # Set current line for logging

    basic_parser._handle_forward_declaration()

    assert basic_parser.forward_decl_candidate is None
    assert basic_parser.forward_decl_check_end_line is None
    assert len(basic_parser.scope_stack) == 0
    assert obj_key not in basic_parser.collected_code_objects

def test_handle_forward_declaration_no_candidate(basic_parser: PlSqlStructuralParser):
    basic_parser.forward_decl_candidate = None
    # Mock logger to check for warning (optional)
    with patch.object(basic_parser.logger, 'warning') as mock_warning:
        basic_parser._handle_forward_declaration()
        mock_warning.assert_called_once()
    assert basic_parser.scope_stack == [] # Should remain unchanged
    assert basic_parser.collected_code_objects == {}


# --- Tests for _process_line (examples for different scenarios) ---
# These tests will set up parser state, then call _process_line with a specific line

def test_process_line_multiline_comment_handling(basic_parser: PlSqlStructuralParser):
    # Scenario 1: Inside a multiline comment
    basic_parser.inside_multiline_comment = True
    basic_parser.current_line_content = "this line is inside a comment\n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert basic_parser.processed_line_content == "" # Should be skipped

    # Scenario 2: End of a multiline comment
    basic_parser.reset_state()
    basic_parser.inside_multiline_comment = True
    basic_parser.current_line_content = "end of comment */ code after\n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert not basic_parser.inside_multiline_comment
    assert basic_parser.processed_line_content.strip() == "code after"

    # Scenario 3: Start of a multiline comment
    basic_parser.reset_state()
    basic_parser.current_line_content = "code before /* start of comment\n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert basic_parser.inside_multiline_comment
    assert basic_parser.processed_line_content.strip() == "code before"

    # Scenario 4: Single-line block comment
    basic_parser.reset_state()
    basic_parser.current_line_content = "code /* comment */ more code\n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert not basic_parser.inside_multiline_comment
    assert basic_parser.processed_line_content.strip() == "code  more code" # Note: comment content removed

def test_process_line_empty_after_processing(basic_parser: PlSqlStructuralParser):
    # basic_parser.reset_state()
    basic_parser.current_line_content = clean_code_and_map_literals("  \n", basic_parser.logger)[0] # Whitespace only
    basic_parser.line_num = 1
    print(basic_parser.current_line_content)
    basic_parser._process_line()
    assert basic_parser.processed_line_content == "" # Stays as is, but strip() is empty
    # No changes to stacks expected
    # Verify no structural changes occurred
    assert basic_parser.block_stack == []
    assert basic_parser.scope_stack == []
    assert basic_parser.package_name is None

    basic_parser.current_line_content = clean_code_and_map_literals("-- only a comment\n", basic_parser.logger)[0]
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert basic_parser.processed_line_content == "" # Becomes empty
    # No changes to stacks expected
    # Verify no structural changes occurred
    assert basic_parser.block_stack == []
    assert basic_parser.scope_stack == []
    assert basic_parser.package_name is None

def test_process_line_package_declaration(basic_parser: PlSqlStructuralParser):
    basic_parser.current_line_content = "CREATE OR REPLACE PACKAGE BODY my_test_pkg IS\n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert basic_parser.package_name == "my_test_pkg"
    assert len(basic_parser.scope_stack) == 1
    assert basic_parser.scope_stack[0][1] == ("PACKAGE", "my_test_pkg")

def test_process_line_procedure_declaration(basic_parser: PlSqlStructuralParser):
    basic_parser.current_line_content = "PROCEDURE do_something (p_param IN NUMBER) IS\n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert len(basic_parser.scope_stack) == 1
    assert basic_parser.scope_stack[0][1] == ("PROCEDURE", "do_something")
    assert "do_something" in basic_parser.collected_code_objects
    assert basic_parser.collected_code_objects["do_something"][0]["start"] == 1

def test_process_line_function_declaration(basic_parser: PlSqlStructuralParser):
    basic_parser.current_line_content = "FUNCTION get_value RETURN VARCHAR2 AS\n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert len(basic_parser.scope_stack) == 1
    assert basic_parser.scope_stack[0][1] == ("FUNCTION", "get_value")
    assert "get_value" in basic_parser.collected_code_objects

def test_process_line_multiline_object_pending(basic_parser: PlSqlStructuralParser):
    basic_parser.current_line_content = "FUNCTION \n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert basic_parser.multiline_object_name_pending == "FUNCTION"

    basic_parser.current_line_content = "  my_multiline_func RETURN BOOLEAN IS\n"
    basic_parser.line_num = 2
    basic_parser._process_line()
    assert basic_parser.multiline_object_name_pending is None
    assert len(basic_parser.scope_stack) == 1
    assert basic_parser.scope_stack[0][1] == ("FUNCTION", "my_multiline_func")
    assert "my_multiline_func" in basic_parser.collected_code_objects

def test_process_line_end_keyword_closes_block(basic_parser: PlSqlStructuralParser):
    basic_parser._push_block(1, "IF")
    basic_parser.current_line_content = "END IF;\n"
    basic_parser.line_num = 2
    basic_parser._process_line()
    assert len(basic_parser.block_stack) == 0

def test_process_line_end_keyword_closes_scope(basic_parser: PlSqlStructuralParser):
    basic_parser._push_scope(1, "PROCEDURE", "test_proc")
    basic_parser.current_line_content = "END test_proc;\n" # Name optional for END in PL/SQL but good practice
    basic_parser.line_num = 10
    basic_parser._process_line()
    assert len(basic_parser.scope_stack) == 0
    assert basic_parser.collected_code_objects["test_proc"][0]["end"] == 10

def test_process_line_begin_keyword_scope(basic_parser: PlSqlStructuralParser):
    basic_parser._push_scope(1, "PROCEDURE", "proc_with_begin")
    basic_parser.current_line_content = "BEGIN\n"
    basic_parser.line_num = 2
    basic_parser._process_line()
    assert basic_parser.scope_stack[0][2]["has_seen_begin"] is True
    assert len(basic_parser.block_stack) == 0 # BEGIN for scope doesn't push to block_stack

def test_process_line_begin_keyword_standalone_block(basic_parser: PlSqlStructuralParser):
    # First, a scope that has already seen its BEGIN
    basic_parser._push_scope(1, "PROCEDURE", "outer_proc")
    basic_parser.scope_stack[0][2]["has_seen_begin"] = True
    
    basic_parser.current_line_content = "BEGIN -- nested anonymous block\n"
    basic_parser.line_num = 5
    basic_parser._process_line()
    assert len(basic_parser.block_stack) == 1
    assert basic_parser.block_stack[0] == (5, "BEGIN")

def test_process_line_if_block(basic_parser: PlSqlStructuralParser):
    basic_parser.current_line_content = "IF condition THEN\n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert len(basic_parser.block_stack) == 1
    assert basic_parser.block_stack[0] == (1, "IF")

def test_process_line_for_loop_block(basic_parser: PlSqlStructuralParser):
    basic_parser.current_line_content = "FOR i IN 1..10 LOOP\n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert len(basic_parser.block_stack) == 1
    assert basic_parser.block_stack[0] == (1, "FOR") # FOR is pushed
    assert not basic_parser.is_awaiting_loop_for_for # LOOP was on same line

def test_process_line_for_awaiting_loop(basic_parser: PlSqlStructuralParser):
    basic_parser.current_line_content = "FOR rec IN (SELECT * FROM DUAL)\n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert len(basic_parser.block_stack) == 1
    assert basic_parser.block_stack[0] == (1, "FOR")
    assert basic_parser.is_awaiting_loop_for_for

    basic_parser.current_line_content = "LOOP\n"
    basic_parser.line_num = 2
    basic_parser._process_line()
    # LOOP itself doesn't add to block_stack when awaited
    assert len(basic_parser.block_stack) == 1 # Still the FOR block
    assert not basic_parser.is_awaiting_loop_for_for

def test_process_line_while_loop_block(basic_parser: PlSqlStructuralParser):
    basic_parser.current_line_content = "WHILE TRUE LOOP\n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert len(basic_parser.block_stack) == 1
    assert basic_parser.block_stack[0] == (1, "WHILE")
    assert not basic_parser.is_awaiting_loop_for_while

def test_process_line_one_liner_if_block(basic_parser: PlSqlStructuralParser):
    basic_parser.current_line_content = "IF x > 0 THEN y := 1; END IF;\n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert len(basic_parser.block_stack) == 0 # Should be self-contained

def test_process_line_one_liner_begin_end_scope(caplog, basic_parser: PlSqlStructuralParser):
    basic_parser._push_scope(1, "PROCEDURE", "one_line_proc")
    basic_parser.current_line_content = "BEGIN NULL; END;\n" # This is the BEGIN for the procedure
    basic_parser.line_num = 1 # Assume IS/AS was on previous line, now this is the BEGIN line
    
    with caplog.at_level(0):
        basic_parser._process_line()
        
        assert "L1: Found BEGIN for one_line_proc (Scope Start: L1)" in caplog.text
        assert "L1-1: END PROCEDURE one_line_proc" in caplog.text
        assert "L1-1: Self-contained block (begin) on line." in caplog.text
    
    assert len(basic_parser.scope_stack) == 0
    assert len(basic_parser.block_stack) == 0 # Block stack not used for scope's BEGIN/END
    # The END on this line would close the procedure if it was the *scope's* end.
    # This specific test focuses on the BEGIN part of the one-liner.
    # A full one-line proc `PROCEDURE p IS BEGIN NULL; END;` would be more complex.

def test_process_line_forward_decl_procedure_confirmation(basic_parser: PlSqlStructuralParser):
    # Setup: A procedure was pushed and is a candidate
    basic_parser.lines = ["PROCEDURE fwd_p (a NUMBER);\n"] # This is the line that _check_for_forward_decl_candidate would see
    basic_parser.line_num = 1
    basic_parser.processed_line_content = "PROCEDURE fwd_p (a NUMBER);" # This is the current processed line
    
    # Manually push the scope and set it as candidate
    basic_parser._push_scope(1, "PROCEDURE", "fwd_p") # This calls _check_for_forward_decl_candidate
    assert basic_parser.forward_decl_candidate == (1, ("PROCEDURE", "fwd_p"))
    
    # Now, the _process_line should see the obj_match and then handle the forward declaration
    # Re-simulate _process_line for the same line, as if it's being re-evaluated after candidate set
    # This is a bit artificial, normally _check_for_forward_decl_candidate is called within _push_scope
    # and _handle_forward_declaration is called if obj_match happens on a *subsequent* line
    # or if the obj_match itself confirms it (like a simple ';').

    # Let's test the scenario where the *same line* confirms it via OBJECT_NAME_REGEX
    # and the forward_decl_candidate was already set (e.g. by a prior _check_for_forward_decl_candidate call)
    basic_parser.reset_state()
    basic_parser.lines = ["PROCEDURE fwd_p;\n", "PROCEDURE bwd_p;\n"]
    basic_parser.line_num = 2
    basic_parser.current_line_content = "PROCEDURE bwd_p;"
    
    # Simulate _push_scope without the internal _check_for_forward_decl_candidate for this specific test flow
    # to isolate the _handle_forward_declaration call within _process_line
    with patch.object(basic_parser, '_check_for_forward_decl_candidate'):
        basic_parser._push_scope(1, "PROCEDURE", "fwd_p") # Pushes to scope_stack & collected_objects
    
    # Manually set the candidate, as if a previous check on this line (or part of it) determined it
    basic_parser.forward_decl_candidate = (1, ("PROCEDURE", "fwd_p"))
    basic_parser.forward_decl_check_end_line = 1 # Mark that the check passed on this line

    # Now _process_line will find "PROCEDURE fwd_p;" via OBJECT_NAME_REGEX
    # and since forward_decl_candidate is set, it should call _handle_forward_declaration
    basic_parser._process_line()

    assert basic_parser.forward_decl_candidate == (2, ('PROCEDURE', 'bwd_p')) # New Candidate
    assert "fwd_p" not in basic_parser.collected_code_objects # Removed
    assert len(basic_parser.scope_stack) == 1 # Popped

def test_process_line_for_update_ignored(basic_parser: PlSqlStructuralParser):
    basic_parser.current_line_content = "CURSOR c1 IS SELECT * FROM employees FOR UPDATE;\n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert not basic_parser.block_stack  # 'FOR' in 'FOR UPDATE' should not create a block
    assert not basic_parser.is_awaiting_loop_for_for

def test_process_line_open_for_ignored(basic_parser: PlSqlStructuralParser):
    basic_parser.current_line_content = "OPEN cur_name FOR SELECT * FROM other_table;\n"
    basic_parser.line_num = 1
    basic_parser._process_line()
    assert not basic_parser.block_stack # 'FOR' in 'OPEN cur FOR' should not create a block
    assert not basic_parser.is_awaiting_loop_for_for


# Define the path to your test data directory
TEST_DATA_ROOT = Path(__file__).parent.parent / "test_data" # Assuming tests/parsing/test_structural_parser.py
STRUCTURAL_PARSER_TEST_DATA_DIR = TEST_DATA_ROOT / "structural_parser"

# Define a directory for test logs
TEST_LOGS_DIR = Path(__file__).parent.parent / "logs" / "structural_parser"
TEST_LOGS_DIR.mkdir(parents=True, exist_ok=True) # Ensure the log directory exists

TEST_INFO_FPATH = TEST_DATA_ROOT / "parse_method_test_cases.json"
if TEST_INFO_FPATH.is_file():
    with open(TEST_INFO_FPATH, 'r') as f:
        PARSE_METHOD_TEST_CASES = json.load(f)
else:
    PARSE_METHOD_TEST_CASES = []
@pytest.mark.parametrize("sql_file_path, expected_json_file_name", PARSE_METHOD_TEST_CASES)
def test_parse_method_with_real_files(test_logger:lg.Logger, sql_file_path, expected_json_file_name):

    sql_file_name = sql_file_path[-1]
    sql_file_path = Path(STRUCTURAL_PARSER_TEST_DATA_DIR, "input", *sql_file_path)
    expected_json_path = Path(STRUCTURAL_PARSER_TEST_DATA_DIR, "output", expected_json_file_name)

    assert sql_file_path.is_file(), f"Test SQL file not found: {sql_file_path}"
    assert expected_json_path.is_file(), f"Expected JSON output file not found: {expected_json_path}"

    sql_content = sql_file_path.read_text()

    # --- Configure File Logging for this specific test case ---
    log_file_base_name = Path(sql_file_name).stem # e.g., "my_package_example"
    
    info_log_path = TEST_LOGS_DIR / f"{log_file_base_name}_info.log"
    debug_log_path = TEST_LOGS_DIR / f"{log_file_base_name}_debug.log"
    trace_log_path = TEST_LOGS_DIR / f"{log_file_base_name}_trace.log"

    # Delete Log files, if already present
    if info_log_path.exists():
        info_log_path.unlink()
    if debug_log_path.exists():
        debug_log_path.unlink()
    if trace_log_path.exists():
        trace_log_path.unlink()


    # Add file handlers. It's good practice to store their IDs to remove them later.
    # Use a fresh logger instance or ensure the passed 'test_logger' can be configured per test.
    # If 'test_logger' is session-scoped and shared, adding/removing handlers might affect other tests
    # if not managed carefully. For per-test logs, creating a new logger instance or
    # cloning/reconfiguring the existing one for the scope of this test is safer.

    # For simplicity, let's assume test_logger can have handlers added and removed.
    # If test_logger is from a fixture that already has handlers, you might want to
    # create a new logger instance here or use logger.bind() to create a child logger.

    # Let's clear any existing handlers from the test_logger for this specific test run
    # to avoid duplicate messages if the fixture is reused.
    # This depends on how your 'test_logger' fixture is set up.
    # If it's a fresh logger each time, this might not be needed.
    # For a session-scoped logger, this is important.
    # test_logger.remove() # Potentially remove all handlers if you want full control here

    test_logger.remove() # Remove any default handlers
    test_logger.add(
        sys.stderr,
        level="INFO", # Set to TRACE to see all logs during tests
        colorize=True,
        format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    handler_id_info = test_logger.add(
        info_log_path, 
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    handler_id_debug = test_logger.add(
        debug_log_path, 
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
    )
    handler_id_trace = test_logger.add(
        trace_log_path, 
        level="TRACE",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[parser_type]} | {name}:{function}:{line} - {message}"
    )

    
    # Initialize the parser
    # Use a low verbose_lvl for tests to avoid progress bar output unless debugging
    parser = PlSqlStructuralParser(logger=test_logger, verbose_lvl=0) 
    
    try:
        test_logger.info(f"Starting parse test for {sql_file_name}")
        # Call the parse method
        clean_code, _ = clean_code_and_map_literals(sql_content, test_logger)
        actual_package_name, actual_collected_objects = parser.parse(code=clean_code)

        # Load expected results from JSON
        expected_data:dict = json.loads(expected_json_path.read_text())
        expected_package_name = expected_data.get("package_name")
        expected_collected_objects = expected_data.get("collected_code_objects", {})

        # Assertions
        assert actual_package_name == expected_package_name, \
            f"Package name mismatch for {sql_file_path}"
        assert actual_collected_objects == expected_collected_objects, \
            f"Collected code objects mismatch for {sql_file_path}"

        test_logger.info(f"Successfully completed parse test for {sql_file_name}")

    finally:
        # --- Remove the file handlers to clean up ---
        test_logger.remove(handler_id_info)
        test_logger.remove(handler_id_debug)
        test_logger.remove(handler_id_trace)

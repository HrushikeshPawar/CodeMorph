"""
Tests for the text utility functions in plsql_analyzer.utils.text_utils
"""
import pytest
from plsql_analyzer.utils.text_utils import escape_angle_brackets


def test_escape_angle_brackets_string():
    """Test that angle brackets in strings are properly escaped."""
    # Test with a string containing angle brackets
    test_str = "function test<T>(a: T): T < 10"
    expected = "function test\\<T>(a: T): T \\< 10"
    assert escape_angle_brackets(test_str) == expected


def test_escape_angle_brackets_empty_string():
    """Test that empty strings are handled correctly."""
    assert escape_angle_brackets("") == ""


def test_escape_angle_brackets_no_brackets():
    """Test that strings without angle brackets remain unchanged."""
    test_str = "function test(a, b)"
    assert escape_angle_brackets(test_str) == test_str


def test_escape_angle_brackets_list():
    """Test that lists are converted to strings with escaped brackets."""
    test_list = ["a<b", "c>d"]
    assert "\\<" in escape_angle_brackets(test_list)


def test_escape_angle_brackets_dict():
    """Test that dictionaries are converted to strings with escaped brackets."""
    test_dict = {"key<1": "value>2"}
    assert "\\<" in escape_angle_brackets(test_dict)


def test_escape_angle_brackets_nested():
    """Test that nested structures are handled correctly."""
    test_nested = {"outer": ["inner<value>", {"key<": "value>"}]}
    result = escape_angle_brackets(test_nested)
    assert "\\<" in result

# Moved from `test_structural_parser.py`
@pytest.mark.parametrize("text, expected", [
    ("text with < brackets >", "text with \\< brackets >"),
    ("no brackets", "no brackets"),
    ("<>", "\\<>"),
    ("", ""),
])
def test_escape_angle_brackets(text, expected):
    assert escape_angle_brackets(text) == expected

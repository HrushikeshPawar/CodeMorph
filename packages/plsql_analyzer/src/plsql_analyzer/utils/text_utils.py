"""
Text utility functions for the plsql_analyzer package.
Contains common text manipulation functions used across modules.
"""
from typing import Union


def escape_angle_brackets(text: Union[str, list, dict]) -> str:
    """
    Escape angle brackets in text to prevent loguru from interpreting them as tags.
    Handles strings, lists, and dictionaries.
    
    Args:
        text: The text to escape. Can be a string, list, or dictionary.
        
    Returns:
        str: The escaped text as a string.
    """

    return str(text).replace("<", "\\<")

"""
Code cleaning utilities for PL/SQL code.

This module provides functions for preprocessing PL/SQL code, including:
- Removing comments
- Handling string literals by replacing them with placeholders
- Creating a mapping between placeholders and original literals
"""
from __future__ import annotations
import loguru as lg
from typing import Tuple, Dict


def clean_code_and_map_literals(code: str, logger: lg.Logger) -> Tuple[str, Dict[str, str]]:
    """
    Removes comments and replaces string literals with placeholders.
    Returns the cleaned code and a mapping of placeholders to original literals.
    
    Args:
        code: The PL/SQL code to be processed
        logger: A logger instance for logging operations
        
    Returns:
        A tuple containing:
        - cleaned_code: The processed code with comments removed and literals replaced
        - literal_mapping: A dictionary mapping placeholder strings to original literals
    """
    logger.debug("Cleaning code: removing comments and string literals.")
    literal_mapping: Dict[str, str] = {}
    inside_quote = False
    inside_inline_comment = False
    inside_multiline_comment = False

    idx = 0
    clean_code_chars = [] 
    current_literal_chars = []

    while idx < len(code):
        current_char = code[idx]
        next_char = code[idx + 1] if (idx + 1) < len(code) else None

        if inside_inline_comment:
            if current_char == "\n":
                inside_inline_comment = False
                clean_code_chars.append('\n')
            idx += 1
            continue

        if inside_multiline_comment:
            if f"{current_char}{next_char}" == "*/":
                inside_multiline_comment = False
                idx += 2
            else:
                idx += 1
            continue
        
        if f"{current_char}{next_char}" == "/*" and not inside_quote:
            inside_multiline_comment = True
            idx += 2
            continue

        if f"{current_char}{next_char}" == "--" and not inside_quote:
            inside_inline_comment = True
            idx += 1 
            continue
        
        if inside_quote and current_char == "'" and next_char == "'":
            current_literal_chars.append("''") 
            idx += 2
            continue

        if current_char == "'":
            inside_quote = not inside_quote

            if not inside_quote: 
                literal_name = f"<LITERAL_{len(literal_mapping)}>"
                literal_mapping[literal_name] = "".join(current_literal_chars)
                current_literal_chars = []
                clean_code_chars.append(literal_name) 
                clean_code_chars.append("'")
            
            else:
                clean_code_chars.append("'")

            idx += 1
            continue
        
        if inside_quote:
            current_literal_chars.append(current_char)
        else:
            clean_code_chars.append(current_char)
        
        idx += 1
    
    # Handle unclosed string literal at end of code
    if inside_quote:
        literal_name = f"<LITERAL_{len(literal_mapping)}>"
        literal_mapping[literal_name] = "".join(current_literal_chars)
        current_literal_chars = []
        clean_code_chars.append(literal_name)
    
    cleaned_code_str = "".join(clean_code_chars)
    logger.debug(f"Code cleaning complete. Original Code Length: {len(code)}, Cleaned code length: {len(cleaned_code_str)}, Literals found: {len(literal_mapping)}")
    return cleaned_code_str, literal_mapping

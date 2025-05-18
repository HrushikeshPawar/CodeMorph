# plsql_analyzer/parsing/signature_parser.py
from __future__ import annotations
import json
import loguru as lg
import pyparsing as pp # Ensure pyparsing is installed: pip install pyparsing

from typing import Dict, Optional
from plsql_analyzer.utils.text_utils import escape_angle_brackets

# Pyparsing setup for better performance (call once if parser is instantiated once)
pp.ParserElement.enablePackrat()
pp.ParserElement.setDefaultWhitespaceChars(" \t\r\n")


class PLSQLSignatureParser:
    def __init__(self, logger: lg.Logger):
        self.logger = logger.bind(parser_type="Signature")
        self._setup_pyparsing_parser()
        # Enable packrat for the instance of the parser
        self.proc_or_func_signature.enable_packrat(cache_size_limit=1024, force=True)

    # _escape_angle_brackets method has been removed and replaced with
    # the centralized version from utils.text_utils

    def _process_parameter(self, s: str, loc: int, toks: pp.ParseResults) -> Dict[str, str|bool]:
        # toks[0] is the Group containing parameter details
        p_dict = toks[0].as_dict()
        self.logger.trace(f"Raw param toks: {escape_angle_brackets(p_dict)}")

        raw_mode = p_dict.get("param_mode_raw")
        mode = "IN" # Default
        if isinstance(raw_mode, str): # "IN" or "OUT"
            mode = raw_mode.upper()
        elif isinstance(raw_mode, pp.ParseResults) and len(raw_mode) > 0 : # Could be "IN OUT"
            # raw_mode might be a list like ['IN', 'OUT'] or just ['IN']
            # Combine will make it a single string "IN OUT"
            mode = " ".join(raw_mode).upper()
        
        param_info = {
            "name": p_dict["param_name"].strip(),
            "type": p_dict["param_type"].strip(), # type might have spaces, e.g. "VARCHAR2 (100)"
            "mode": mode.strip(),
            "default_value": p_dict.get("default_value", "").strip() or None, # Ensure empty string becomes None
            # "has_nocopy": "has_nocopy" in p_dict # True if NOCOPY was present
        }
        self.logger.trace(f"Processed param: {escape_angle_brackets(param_info)}")
        return param_info

    def _setup_pyparsing_parser(self):
        # Basic Keywords
        CREATE, OR, REPLACE, EDITIONABLE, NONEDITIONABLE, PROCEDURE, FUNCTION, IS, AS, RETURN, IN, OUT, DEFAULT, NOCOPY = map(
            pp.CaselessKeyword,
            "CREATE OR REPLACE EDITIONABLE NONEDITIONABLE PROCEDURE FUNCTION IS AS RETURN IN OUT DEFAULT NOCOPY".split()
        )

        # Delimiters and Operators (suppressed from output)
        LPAR, RPAR, COMMA, SEMI, PLUS = map(pp.Suppress, "(),;+")
        ASSIGN = pp.Suppress(":=")
        # DOT for qualified identifiers needs to be a Literal, not Suppress, if part of combine=True
        DOT = pp.Literal('.')

        # Identifiers
        # Allowing dot in identifier for schema.name, but qualified_identifier handles it better.
        # Added '#' and '$' commonly found in Oracle identifiers.
        identifier = pp.Word(pp.alphas + "_", pp.alphanums + "_#$") | pp.QuotedString('"', esc_char='""', unquote_results=False)
        
        # Qualified identifier: schema.package.name or package.name or name
        # combine=True makes it a single string
        qualified_identifier = pp.DelimitedList(identifier, delim=DOT, combine=True)

        # Parameter Mode
        # Order Matters: Check "IN OUT" first
        param_mode = pp.Combine(IN + OUT, adjacent=False, join_string=" ")  | IN | OUT 

        # Parameter Type attribute
        type_attribute = pp.CaselessLiteral("%TYPE") | pp.CaselessLiteral("%ROWTYPE")

        # Parameter Type: identifier optionally with type_attribute or (value) for size like VARCHAR2(100)
        # This needs to be more robust to capture things like "VARCHAR2 (2000 BYTE)" or "TABLE OF some_type"
        # Using originalTextFor to capture complex types as a single string
        # A simple approach: anything until the next keyword (DEFAULT, NOCOPY, COMMA, RPAR)
        # This might be too greedy. Let's try a more defined one.
        
        # Basic types, qualified types, types with attributes
        # A general type expression can be complex, e.g. `pkg.type%ROWTYPE` or `TABLE OF another.type`
        # `pp.SkipTo` is often useful for complex, less-structured parts.
        # However, for types, they are somewhat structured.
        
        # For param_type, let's try to capture common patterns:
        # 1. simple_type (e.g., VARCHAR2, NUMBER, DATE)
        # 2. qualified_type (e.g., schema.table.column%TYPE, pkg.custom_type)
        # 3. type_with_size (e.g., VARCHAR2(100), NUMBER(10,2))
        # 4. collection_type (e.g., TABLE OF some_type, VARRAY(10) OF other_type) - More complex

        # Let's use a simpler combined approach for now and refine if needed.
        # `Combine` is good for piecing together parts that should be one token.
        param_type_base = qualified_identifier.copy()
        param_type_with_attr = pp.Combine(param_type_base + type_attribute)
        # For types like VARCHAR2(100) or NUMBER(5,0)
        # Need to capture content within parentheses that isn't a parameter list.
        # Regex for typical size/precision specifier
        size_specifier = pp.Regex(r"\(\s*\d+(\s*,\s*\d+)?\s*(?:CHAR|BYTE)?\s*\)")
        param_type_with_size = pp.Combine(param_type_base + pp.Optional(size_specifier), adjacent=False, join_string="")

        # Final param_type, order matters for matching
        param_type = pp.original_text_for(param_type_with_attr | param_type_with_size | param_type_base | pp.Combine(qualified_identifier + pp.Optional(LPAR + PLUS + RPAR) + pp.Optional(type_attribute)))

        # Default Value Expression: Capture everything until the next comma or closing parenthesis
        # original_text_for is good here as default values can be complex expressions
        default_value_expr = pp.original_text_for(pp.SkipTo(COMMA | RPAR))
        default_clause = (DEFAULT | ASSIGN) + default_value_expr("default_value")

        # Single Parameter structure
        parameter = pp.Group(
            identifier("param_name") +
            pp.Optional(param_mode)("param_mode_raw") + # Captures mode like "IN" or ["IN","OUT"]
            pp.Optional(NOCOPY)("has_nocopy") + # Presence indicates true
            param_type("param_type") +
            pp.Optional(default_clause)
        )
        parameter.set_parse_action(self._process_parameter)

        # Optional: Parameter list
        parameter_list = pp.Optional(LPAR + pp.delimited_list(parameter)("params") + RPAR)

        # Procedure header
        # Optional "CREATE OR REPLACE [EDITIONABLE|NONEDITIONABLE]" prefix
        optional_create_prefix = pp.Optional(
            CREATE + pp.Optional(OR + REPLACE) + pp.Optional(EDITIONABLE | NONEDITIONABLE)
        )
        proc_header = (
            optional_create_prefix +
            PROCEDURE + qualified_identifier("proc_name") +
            parameter_list +
            pp.Optional(IS | AS) # End of signature before body
        )

        # Function Header
        # Return type for function is similar to param_type
        return_type_spec = param_type.copy() # Reuse param_type definition
        return_clause = RETURN + return_type_spec("return_type")
        
        func_header = (
            optional_create_prefix +
            FUNCTION + qualified_identifier("func_name") +
            parameter_list +
            return_clause + # RETURN clause is mandatory for function syntax after params
            pp.Optional(IS | AS) # End of signature before body
        )

        # Combined parser for either a procedure or a function signature
        # We are interested in parsing the signature part, so we don't need the full body.
        # The input to this parser should ideally be just the signature line(s).
        # Adding Optional(SEMI) to consume a trailing semicolon if the signature is extracted standalone.
        self.proc_or_func_signature = (proc_header | func_header) + pp.Optional(SEMI)

    def _clean_code_for_signature_v1(self, signature_text: str) -> str:
        # Remove C-style comments /* ... */ and SQL-style -- comments
        # Pyparsing's built-in comment definitions are good.
        sql_comment = pp.cppStyleComment | pp.dblSlashComment | ("--" + pp.restOfLine)
        
        # Remove comments first
        code_no_comments = sql_comment.suppress().transform_string(signature_text)
        
        # Replace multiple whitespaces with a single space for normalization, handle newlines
        normalized_code = " ".join(code_no_comments.split())
        return normalized_code
    
    def _clean_code_for_signature(self, signature_text: str) -> str:
        cleaned_chars = []
        idx = 0
        text_len = len(signature_text)

        while idx < text_len:
            char = signature_text[idx]

            # Skip C-style comments /* ... */
            if char == '/' and idx + 1 < text_len and signature_text[idx + 1] == '*':
                comment_end_idx = idx + 2 # Start after "/*"
                while comment_end_idx < text_len:
                    if signature_text[comment_end_idx] == '*' and \
                       comment_end_idx + 1 < text_len and \
                       signature_text[comment_end_idx + 1] == '/':
                        idx = comment_end_idx + 2 # Move past "*/"
                        break
                    comment_end_idx += 1
                else: # Unterminated comment, skip rest of string
                    idx = text_len
                continue

            # Skip SQL-style comments -- ...
            elif char == '-' and idx + 1 < text_len and signature_text[idx + 1] == '-':
                comment_end_idx = idx + 2 # Start after "--"
                while comment_end_idx < text_len and signature_text[comment_end_idx] != '\n':
                    comment_end_idx += 1

                idx = comment_end_idx
                if idx < text_len and signature_text[idx] == '\n': # Also consume the newline
                    idx += 1
                continue
            
            # Process non-comment characters for whitespace normalization
            if char.isspace():
                # Add a single space if cleaned_chars is not empty
                # and the last character added wasn't already a space.
                if cleaned_chars and cleaned_chars[-1] != ' ':
                    cleaned_chars.append(' ')
            else: # Non-whitespace character
                cleaned_chars.append(char)
            
            idx += 1

        # Join the characters and strip leading/trailing whitespace
        # to mimic the behavior of " ".join(str.split()).
        final_str = "".join(cleaned_chars)
        if not final_str: # Handle case where input was empty or only comments/whitespace
            return ""
        
        # If the string effectively starts or ends with a space due to original content,
        # strip it. e.g. " text " -> "text", "text " -> "text"
        return final_str.strip()

    def parse(self, signature_text: str) -> Optional[Dict[str, Optional[str]]]:
        """
        Parses a PL/SQL procedure or function signature string.
        Args:
            signature_text: The string containing the signature.
                            e.g., "PROCEDURE my_proc (p_param1 IN VARCHAR2, p_param2 OUT NUMBER) IS"
                               or "FUNCTION my_func (p_id IN NUMBER) RETURN BOOLEAN AS"
        Returns:
            A dictionary with parsed components or None if parsing fails.
        """
        if not signature_text.strip():
            self.logger.warning("Attempted to parse an empty signature string.")
            return None

        # The structural parser might give us more than just the signature line.
        # We need to find the core signature. A simple heuristic:
        # Take up to " IS " or " AS " or the first semicolon.
        # This is a bit fragile. Ideally, the input is already well-defined.
        
        # # Let's assume signature_text is reasonably clean (e.g., one object's declaration part)
        # # Clean comments from the input text specifically for signature parsing
        # clean_signature_text = self._clean_code_for_signature(signature_text)
        # print(self._clean_code_for_signature(signature_text))
        clean_signature_text = signature_text

        # The parser definition includes IS/AS, so the input can contain them.
        # Let's try parsing directly first. The parser is defined to handle optional CREATE OR REPLACE etc.
        
        # The pyparsing grammar expects the signature. If the input `signature_text`
        # includes the body, `SkipTo(IS|AS)` might be needed before this parser.
        # However, the grammar is defined up to IS/AS.

        self.logger.debug(f"Attempting to parse signature: {escape_angle_brackets(clean_signature_text[:200])}...") # Log snippet
        
        try:
            # The parser needs to handle the entire object definition line typically
            # e.g. "FUNCTION get_name (p_id NUMBER) RETURN VARCHAR2 IS"
            # If the input `signature_text` is the *full* source of a proc/func,
            # this parser will only match the header part. This is intended.
            
            # We might need to scan for the start of the signature if `signature_text` is a large block.
            # For now, assume `signature_text` starts with or near the signature.
            
            # `scan_string` might be better if the signature is embedded.
            # `parse_string` expects the whole string to match.
            # Let's try parse_string with `parseAll=False` implicitly by not specifying it.
            
            # Test with a simple parse first. If the input has leading non-signature text, it will fail.
            # result = self.proc_or_func_signature.parse_string(clean_signature_text)
            
            # Using scan_string to find the first match of a signature
            best_match = None
            best_match_len = 0
            for toks, start, end in self.proc_or_func_signature.scan_string(clean_signature_text):
                new_len = end - start
                
                if new_len >= best_match_len:
                    best_match = toks # Take the first (and likely only, for a single object's source)
                    self.logger.trace(f"Found Signature match from {start} to {end}: {escape_angle_brackets(toks.as_dict())}")

            # parsed_dict = self.proc_or_func_signature.parse_string(clean_signature_text).as_dict()
            # # Ensure 'params' is always a list, even if empty
            # if "params" not in parsed_dict:
            #     parsed_dict["params"] = []

            # self.logger.debug(f"Successfully parsed signature. Name: {parsed_dict.get('proc_name') or parsed_dict.get('func_name')}, Param: {json.dumps(parsed_dict["params"], indent=0)}")
            # return parsed_dict
            
            if best_match:
                parsed_dict = best_match.as_dict()

                # Strip whitespace from string values in the parsed dictionary
                for key, value in parsed_dict.items():
                    if isinstance(value, str):
                        parsed_dict[key] = value.strip()
                    # Note: 'params' is handled separately as it's a list of dicts
                    # The stripping for param details happens in _process_parameter

                self.logger.debug(f"Successfully parsed signature. Name: {escape_angle_brackets(parsed_dict.get('proc_name') or parsed_dict.get('func_name'))}, Param: {escape_angle_brackets(json.dumps(parsed_dict.get('params', {}), indent=0))}")
                # Ensure 'params' is always a list, even if empty
                if "params" not in parsed_dict:
                    parsed_dict["params"] = []
                return parsed_dict
            else:
                self.logger.warning(f"No PL/SQL signature found or matched in the provided text: {escape_angle_brackets(signature_text[:200])}...")
                return None

        except pp.ParseException as pe:
            self.logger.error(f"Failed to parse PL/SQL signature. Error: {pe}")
            self.logger.debug(f"ParseException at L{pe.lineno} C{pe.col}: {pe.line}")
            self.logger.debug(f"Problematic text (context): '{escape_angle_brackets(signature_text[max(0,pe.loc-30):pe.loc+30])}'")
            return None
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during signature parsing: {e}")
            self.logger.exception(e)
            return None

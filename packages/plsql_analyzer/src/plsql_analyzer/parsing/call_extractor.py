# plsql_analyzer/parsing/call_extractor.py
from __future__ import annotations
import re
import loguru as lg
import pyparsing as pp
from typing import List, Tuple, Dict, NamedTuple

from plsql_analyzer.utils.text_utils import escape_angle_brackets

# Define the named tuple for extracted calls at the module level
class ExtractedCallTuple(NamedTuple):
    call_name: str
    line_no: int    # Line number within the input code_string for this call
    start_idx: int  # Start char index in the input code_string
    end_idx: int    # End char index (exclusive) of the call_name in input code_string

class CallParameterTuple(NamedTuple):
    """Stores extracted positional and named parameters for a call."""
    positional_params: List[str]
    named_params: Dict[str, str]

class CallDetailsTuple(NamedTuple):
    """Stores comprehensive details of an extracted call, including parameters."""
    call_name: str
    line_no: int    # Line number where the call occurs in the cleaned code
    start_idx: int  # Start char index of the call_name in the cleaned code
    end_idx: int    # End char index (exclusive) of the call_name in the cleaned code
    positional_params: List[str] # List of positional parameters, with literals restored
    named_params: Dict[str, str]   # Dictionary of named parameters, with literals restored


class CallDetailExtractor:
    def __init__(self, logger: lg.Logger, keywords_to_drop:List[str]):
        self.logger = logger.bind(parser_type="CallDetailExtractor")
        self.keywords_to_drop = {kw.upper() for kw in keywords_to_drop}
        self.temp_extracted_calls_list: List[Tuple[str, int]] = []
        self.code_string_for_parsing = "" # Renamed for clarity
        self.cleaned_code = ""
        self.allow_parameterless_config: bool = False # Default to False
        self._setup_parser()

    def _reset_internal_state(self):
        """Resets internal state before parsing a new code block."""
        self.logger.trace("Resetting internal parser state.")
        self.temp_extracted_calls_list = []
        self.cleaned_code = ""
        self.literal_mapping = {}
    
    # _escape_angle_brackets method has been removed and replaced with
    # the centralized version from utils.text_utils

    def _record_call(self, s:str, loc:int, toks:pp.ParseResults) -> pp.ParseResults:
       # This method uses self.code_string_for_parsing for line number calculation
        if isinstance(toks[0], pp.ParseResults):
            call_name_token:str = toks[0].get("call_name", None)
        elif isinstance(toks, pp.ParseResults):
            call_name_token:str = toks.get("call_name", None)

        if call_name_token.upper() in self.keywords_to_drop:
            return toks

        # Ensure code_string_for_parsing is set before scan_string is called
        lineno = self.cleaned_code.count('\n', 0, loc) + 1
        self.temp_extracted_calls_list.append((call_name_token, lineno))
        return toks

    def _setup_parser(self):
        # Suppress delimiters commonly found around or in calls, but not part of the name
        LPAR, RPAR, COMMA, SEMI, ASSIGN_OP, ARROW_OP = map(pp.Suppress, ["(", ")", ",", ";", ":=", "=>"])
        DOT = pp.Literal('.') # Keep dots for qualified names

        # Identifier: standard PL/SQL identifiers, can be quoted
        identifier = pp.Word(pp.alphas + "_", pp.alphanums + "_#$") | pp.QuotedString('"', esc_char='""', unquote_results=False)
        
        # Qualified identifier (e.g., package.procedure, schema.package.procedure)
        # combine=True makes it a single string token
        self.qualified_identifier_call = pp.DelimitedList(identifier, delim=DOT, combine=True)("call_name")

        # A call is a qualified_identifier followed by an opening parenthesis or a semicolon (for parameter-less calls)
        # or if it's an assignment target (though this parser focuses on callable units)
        # We are looking for "name(" or "name;" patterns.
        # The original also matched assignments "name :=", but this is more for variable assignment.
        # Let's stick to actual calls.
        
        # Pattern for a call: qualified_identifier followed by LPAR or SEMI
        # SEMI is for parameterless procedures called like `my_proc;`
        # LPAR is for procedures/functions called like `my_func()` or `my_proc(a,b)`
        # The grammar should ignore calls that are part of DDL/DML like INSERT, UPDATE, SELECT
        # or keywords like IF(), LOOP(). This is handled by `keywords_to_drop`.

        # Define what a call looks like. It must be followed by ( or ;
        # to distinguish from variable names.
        self.codeobject_call_pattern = self.qualified_identifier_call + (LPAR | SEMI)

        # Record original positions for reporting
        self.codeobject_call_pattern.set_parse_action(self._record_call)

    def _extract_base_calls(self) -> List[ExtractedCallTuple]:
        """
        Extracts potential procedure/function calls from a block of PL/SQL code.
        Args:
            code_string: The PL/SQL code as a string.
            keywords_to_drop: A list of uppercase keywords to ignore as calls (e.g., "IF", "LOOP").
        Returns:
            A list of ExtractedCallTuple objects.
        """
        extracted_calls_list: List[ExtractedCallTuple] =  []
        if not self.cleaned_code.strip():
            return []

        # TODO: Need to check why this is slow
        # # Comments and string literals should be ignored during parsing for calls.
        # # Pyparsing's default comment ignores can be useful here.
        # sql_comment = pp.cppStyleComment | ("--" + pp.restOfLine)
        # single_quoted_string = pp.QuotedString("'", esc_quote="''", multiline=True)
        
        parser_to_scan = self.codeobject_call_pattern.copy()
        # parser_to_scan.ignore(sql_comment)
        # parser_to_scan.ignore(single_quoted_string)
        # # Also ignore PL/SQL block comments /* ... */
        # parser_to_scan.ignore(pp.cStyleComment)

        self.logger.trace(f"Scanning for calls in code block (length {len(self.cleaned_code)}).")

        # scan_string yields (tokens, start_loc_match, end_loc_match)
        # temp_extracted_calls_list is populated by _record_call
        # We iterate through scan_string to get precise start/end of the name itself.
        
        # We need to map items from temp_extracted_calls_list (populated by parse action)
        # to the more detailed start/end indices from scan_string.
        
        # Ensure temp_extracted_calls_list matches scan_results after filtering
        # This is a bit tricky because keywords_to_drop happens in _record_call
        # Let's refine this: _record_call will add to temp_extracted_calls_list
        # Then we iterate scan_results and if the call_name matches one not dropped, we use its indices.

        processed_temp_idx = 0
        for tokens, start_loc, end_loc in parser_to_scan.parse_with_tabs().scan_string(self.cleaned_code):
            assert isinstance(tokens, pp.ParseResults), f"Type: {type(tokens)}, {tokens}"

            if isinstance(tokens[0], pp.ParseResults):
                call_name_token:str = tokens[0].get("call_name", None) # This is the combined qualified identifier
            elif isinstance(tokens, pp.ParseResults):
                call_name_token:str = tokens.get("call_name", None) # This is the combined qualified identifier

            if not call_name_token:
                self.logger.warning(f"Token 'call_name' not found in parsed tokens: {tokens.dump()} at {start_loc}-{end_loc}")
                continue
            
            current_call_name = call_name_token.strip()
            self.logger.trace(f"Processing potential call: '{current_call_name}' at {start_loc}-{end_loc}")

            # Filter out common SQL keywords or specified keywords
            if current_call_name.upper() in self.keywords_to_drop:
                self.logger.trace(f"Dropping potential call '{current_call_name}' as it's in keywords_to_drop.")
                continue
            
            # Find the corresponding entry in temp_extracted_calls_list
            # This assumes _record_call and this loop process in the same order for non-dropped items.
            if processed_temp_idx >= len(self.temp_extracted_calls_list):
                self.logger.error(f"Mismatch between scan_results and temp_extracted_calls_list for '{current_call_name}'. Temp list exhausted.")
                break 
                
            temp_call_name, temp_line_no = self.temp_extracted_calls_list[processed_temp_idx]
            # assert current_call_name == temp_call_name, f"`{current_call_name}` not in {self.temp_extracted_calls_list[processed_temp_idx]}"
            if current_call_name != temp_call_name:
                # This can happen if _record_call's logic for stripping/handling differs slightly, or if a bug exists.
                self.logger.warning(f"Name mismatch: scan_string gave '{current_call_name}', _record_call gave '{temp_call_name}'. Using scan_string's name. Check logic.")
                # Potentially, resync or log more details. For now, proceed with scan_string's name.
            

            # The `end_loc` from scan_string is for the whole match (e.g., "my_call(").
            # We want the end_loc of just the `call_name`.
            # `start_loc` is the start of `call_name`.
            # `len(call_name)` gives its length.
            end_loc = start_loc + len(current_call_name)

            extracted_call = ExtractedCallTuple(
                call_name=current_call_name,
                line_no=temp_line_no,
                start_idx=start_loc,
                end_idx=end_loc 
            )
            
            extracted_calls_list.append(extracted_call)
            self.logger.trace(f"Base Extracted Call: {extracted_call}")
            processed_temp_idx += 1
        
        if processed_temp_idx != len(self.temp_extracted_calls_list):
             self.logger.warning(f"Processed {processed_temp_idx} calls, but temp_extracted_calls_list has {len(self.temp_extracted_calls_list)} items. Mismatch occurred.")

            
        self.logger.debug(f"Found {len(extracted_calls_list)} potential calls in code block.")
        return extracted_calls_list

    def _extract_call_params(self, call_info: ExtractedCallTuple) -> CallParameterTuple:
        """
        Extracts parameters for a given call from the cleaned code.
        Based on the user-provided `extract_call_params` function.
        `call_info.end_idx` points to the character *after* the call name.
        """
        self.logger.trace(f"Extracting parameters for call '{call_info.call_name}' (L{call_info.line_no}:{call_info.start_idx}-{call_info.end_idx}) from cleaned code.")
        
        param_nested_lvl = 0 # Start at 0, becomes 1 when '(' is encountered.
        positional_params = []
        named_params = {}
        is_named_param = False
        param_name_collector = []
        param_value_collector = []
        
        # Start searching for parameters right after the call name's end_idx
        # This index should point to '(', or whitespace then '(', or ';'
        current_idx = call_info.end_idx 

        # Skip initial whitespace before parameters start (if any)
        while current_idx < len(self.cleaned_code) and self.cleaned_code[current_idx].isspace():
            current_idx += 1

        if current_idx >= len(self.cleaned_code) or self.cleaned_code[current_idx] != '(':
            # No opening parenthesis found, likely a parameter-less call (e.g., my_proc; or USER)
            # Or a call like SYSDATE (which might not have `()` in all contexts but pyparsing matched `SEMI` implicitly or explicitly)
            if not self.allow_parameterless_config:
                self.logger.trace(f"No opening parenthesis found for '{call_info.call_name}' at index {current_idx} and allow_parameterless is False. Skipping call.")
                return None # Indicate skipping this call
            else:
                self.logger.trace(f"No opening parenthesis found for '{call_info.call_name}' at index {current_idx}. Assuming parameter-less as allow_parameterless is True.")
                return CallParameterTuple([], {})

        # We found '(', so start parsing parameters
        param_nested_lvl = 1 # We are inside the first level of parentheses
        current_idx += 1 # Move past '('

        while current_idx < len(self.cleaned_code) and param_nested_lvl > 0:
            current_char = self.cleaned_code[current_idx]
            next_char = self.cleaned_code[current_idx + 1] if (current_idx + 1) < len(self.cleaned_code) else None

            if current_char == '(':
                param_nested_lvl += 1
                param_value_collector.append(current_char)
            
            elif current_char == ')':
                param_nested_lvl -= 1
                if param_nested_lvl > 0: # Closing a nested parenthesis
                    param_value_collector.append(current_char)
                # Else: this is the closing parenthesis of the parameter list, handled by loop condition
            
            elif current_char == ";" and param_nested_lvl <= 1:
                param_value_collector = []
                break
            
            elif current_char == ',' and param_nested_lvl == 1: # Parameter separator
                if is_named_param:
                    param_name_str = "".join(param_name_collector).strip()
                    param_value_str = "".join(param_value_collector).strip()
                    if param_name_str: # Ensure param name is not empty
                         named_params[param_name_str] = param_value_str
                         self.logger.trace(f"Found named param: `{param_name_str}` => `{escape_angle_brackets(param_value_str)}`")
                    else:
                        self.logger.warning(f"Empty parameter name found for call '{call_info.call_name}' with value '{param_value_str}'.")
                else:
                    param_value_str = "".join(param_value_collector).strip()
                    if param_value_str:
                        positional_params.append(param_value_str)
                        self.logger.trace(f"Found positional param: `{escape_angle_brackets(param_value_str)}`")
                
                param_value_collector = []
                param_name_collector = []
                is_named_param = False

            elif current_char == '=' and next_char == '>' and param_nested_lvl == 1 and not is_named_param: # Named parameter assignment
                is_named_param = True
                # Current param_value_collector has the name
                param_name_collector.extend(param_value_collector)
                param_value_collector = []
                current_idx += 1 # Skip the '>' as well (current_char is '=')

            else: # Character is part of a parameter name or value
                param_value_collector.append(current_char)
            
            current_idx += 1

        # Add the last parameter if any
        if param_value_collector:
            if is_named_param:
                param_name_str = "".join(param_name_collector).strip()
                param_value_str = "".join(param_value_collector).strip()
                if param_name_str:
                    named_params[param_name_str] = param_value_str
                    self.logger.trace(f"Found last named param: `{param_name_str}` => `{escape_angle_brackets(param_value_str)}`")
                else:
                    self.logger.warning(f"Empty parameter name for last param for call '{call_info.call_name}' with value '{escape_angle_brackets(param_value_str)}'.")
            else:
                param_value_str = "".join(param_value_collector).strip()
                if param_value_str:
                    positional_params.append(param_value_str)
                    self.logger.trace(f"Found last positional param: `{escape_angle_brackets(param_value_str)}`")

        if param_nested_lvl != 0:
            self.logger.warning(f"Parameter parsing for '{call_info.call_name}' ended with unbalanced parentheses. Nesting level: {param_nested_lvl}. Results might be incomplete.")

        # Restore literals
        restored_positional_params = [re.sub(r'<LITERAL_\d+>', lambda match: self.literal_mapping.get(match.group(0), match.group(0)), p) for p in positional_params]
        restored_named_params = {
            name: re.sub(r'<LITERAL_\d+>', lambda match: self.literal_mapping.get(match.group(0), match.group(0)), val)
            for name, val in named_params.items()
        }
        
        self.logger.trace(f"Parameters for '{escape_angle_brackets(call_info.call_name)}': Positional={escape_angle_brackets(restored_positional_params)}, Named={escape_angle_brackets(restored_named_params)}")

        return CallParameterTuple(restored_positional_params, restored_named_params)

    def extract_calls_with_details(self, cleaned_plsql_code: str, literal_mapping: Dict[str, str], allow_parameterless: bool = True) -> List[CallDetailsTuple]:
        """
        Main public method to extract all procedure/function calls with their parameters.
        
        Args:
            cleaned_plsql_code: Pre-cleaned code with literals replaced with placeholders
            literal_mapping: Mapping of literal placeholders to their original values
            allow_parameterless: If False, calls without parentheses (e.g. `my_proc;`) will be skipped. Defaults to True.
            
        Returns:
            List of CallDetailsTuple objects representing all extracted calls
        """
        self.logger.info("Starting extraction of calls with parameters from PL/SQL code.")
        
        # Reset Parser
        self._reset_internal_state()

        self.allow_parameterless_config = allow_parameterless # Store the config
        
        self.cleaned_code = cleaned_plsql_code
        self.literal_mapping = literal_mapping
        if not self.cleaned_code.strip():
            self.logger.info("No content in code after preprocessing. No calls to extract.")
            return []

        # ExtractedCallTuple instances will have coordinates relative to cleaned_code
        base_calls: List[ExtractedCallTuple] = self._extract_base_calls()

        detailed_calls_list: List[CallDetailsTuple] = []
        if not base_calls:
            self.logger.info("No base calls identified in the cleaned code.")
            return []

        for call_info in base_calls:
            # call_info contains name, line_no, start_idx, end_idx relative to cleaned_code
            # call_info.end_idx is the index *after* the call name in cleaned_code.
            
            parameter_tuple = self._extract_call_params(call_info)

            if parameter_tuple is None: # This call should be skipped
                self.logger.trace(f"Skipping call '{call_info.call_name}' due to parameter extraction result (None).")
                continue
            
            detailed_calls_list.append(
                CallDetailsTuple(
                    call_name=call_info.call_name,
                    line_no=call_info.line_no,
                    start_idx=call_info.start_idx,
                    end_idx=call_info.end_idx,
                    positional_params=parameter_tuple.positional_params,
                    named_params=parameter_tuple.named_params
                )
            )
        
        self.logger.info(f"Extraction complete. Found {len(detailed_calls_list)} calls with parameter details.")
        return detailed_calls_list

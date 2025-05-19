# plsql_analyzer/parsing/structural_parser.py
from __future__ import annotations
import re
from pprint import pformat
import loguru as lg # Assuming logger is passed
from typing import List, Tuple, Optional, Dict, Any
from tqdm.auto import tqdm # For progress bar
from plsql_analyzer.utils.text_utils import escape_angle_brackets

# --- Regular Expressions --- #
OBJECT_NAME_REGEX = re.compile(
    pattern=r"""\b(PROCEDURE|FUNCTION)\b\s+         # Matches the keyword PROCEDURE or FUNCTION as a whole word (due to \b word boundaries),
                                                    # followed by one or more whitespace characters (\s+).
                ([A-Za-z0-9_"/.]+)\s*               # Captures the object's name. This group allows:
                                                    #   A-Z, a-z: uppercase and lowercase letters.
                                                    #   0-9: digits.
                                                    #   _: underscore.
                                                    #   ": double quotes, for quoted identifiers (e.g., "My Procedure").
                                                    #   /: forward slash, sometimes seen in Oracle object names.
                                                    #   .: dot, for qualified names (e.g., package_name.procedure_name).
                                                    # The '+' means one or more of these characters.
                                                    # \s* matches zero or more trailing whitespace characters after the name.
                (?:\bRETURN\s+\S+(?:[^\S\n]*)?)?    # Optionally matches a function's RETURN clause. This is a non-capturing group (?:...).
                                                    #   \bRETURN\b: Matches the keyword RETURN as a whole word.
                                                    #   \s+: Followed by one or more whitespace characters.
                                                    #   \S+: Matches the return type (one or more non-whitespace characters).
                                                    #   (?:[^\S\n]*)?: Optionally matches any trailing spaces on the same line (zero or more whitespace characters that are not newlines).
                (?:\(|\bIS\b|\bAS\b)?               # Optionally matches characters or keywords that typically follow the name/signature. This is a non-capturing group.
                                                    #   \( : Matches an opening parenthesis, often starting a parameter list.
                                                    #   |  : OR operator.
                                                    #   \bIS\b : Matches the keyword IS as a whole word.
                                                    #   |  : OR operator.
                                                    #   \bAS\b : Matches the keyword AS as a whole word.
                (?:(?:.*)(\bEND\b))?                # Optionally matches if the line contains an 'END' keyword further along. This is a non-capturing group for the outer structure.
                                                    #   (?:.*): A non-capturing group that matches any character (except newline) zero or more times, consuming characters before 'END'.
                                                    #   (\bEND\b): A capturing group for the keyword 'END' as a whole word. This allows checking if the object definition ends on the same line.
                (?:[^\S\n]*\n)?                     # Optionally matches trailing horizontal whitespace (spaces, tabs) and a newline character. This is a non-capturing group.
                                                    #   [^\S\n]* : Matches zero or more whitespace characters that are NOT newlines.
                                                    #   \n : Matches a newline character.
            """,
    flags= re.IGNORECASE | re.VERBOSE
)

PACKAGE_NAME_REGEX = re.compile(r"""
    CREATE\s+                               # Matches the keyword "CREATE" followed by one or more whitespace characters.
    (?:OR\s+REPLACE\s+)?                    # Optionally matches "OR REPLACE " (non-capturing group).
                                            #   (?: ... )? makes the whole group optional.
                                            #   OR\s+REPLACE matches "OR" then whitespace, then "REPLACE".
                                            #   \s+ ensures one or more whitespace characters after REPLACE.
    (?:(?:NON)?EDITIONABLE\s+)?             # Optionally matches "EDITIONABLE " or "NONEDITIONABLE " (non-capturing group).
                                            #   (?: ... )? makes the outer group optional.
                                            #   (?:NON)? optionally matches "NON".
                                            #   EDITIONABLE matches the literal "EDITIONABLE".
                                            #   \s+ ensures one or more whitespace characters after.
    PACKAGE\s+BODY\s+                       # Matches the keywords "PACKAGE BODY" each followed by one or more whitespace characters.
    (                                       # Start of capturing group 1 (for the package name).
        [A-Za-z0-9_"\.]+?                   # Matches the package name itself.
                                            #   [ ... ] defines a character set:
                                            #     A-Za-z: uppercase and lowercase letters.
                                            #     0-9: digits.
                                            #     _: underscore.
                                            #     ": double quote (for quoted identifiers).
                                            #     \.: literal dot (for schema.package_name).
                                            #     REMOVED: \s: (Note: space character explicitly included) matches a space.
                                            #   +? means one or more characters, matched non-greedily.
                                            #      This is important if the name might contain spaces and
                                            #      we want to stop before the next required keyword (IS/AS).
    )                                       # End of capturing group 1.
    \s+                                     # Matches one or more whitespace characters after the package name.
    (?:IS|AS)?                              # Optionally matches the keyword "IS" or "AS" (non-capturing group).
                                            #   (?: ... )? makes the group optional.
                                            #   IS|AS matches either "IS" or "AS".
    """, re.IGNORECASE | re.VERBOSE
)

END_CHECK_REGEX = re.compile(r"""
    \b      # Matches a word boundary, ensuring "END" is matched as a whole word.
    (END)   # Capturing group 1: Matches the literal string "END".
    \b      # Matches another word boundary.
    """,
    flags=re.IGNORECASE | re.VERBOSE
)

KEYWORDS_REQUIRING_END = [x.casefold() for x in ["IF", "LOOP", "FOR", "WHILE", "BEGIN", "CASE"]]

# Dynamically constructs a regex string like: (?<!END\s)\b(if|loop|for|while|begin|case)\b
KEYWORDS_REQUIRING_END_REGEX = re.compile(rf"""
    (?<!END\s)              # Negative lookbehind assertion:
                            # Ensures that the current position is NOT preceded by "END" followed by a whitespace character.
                            # This helps avoid matching keywords within an "END <KEYWORD>" construct (e.g., "END IF").
    \b                      # Matches a word boundary before the keyword.
    (                       # Start of capturing group 1:
        {'|'.join(KEYWORDS_REQUIRING_END)}  # Dynamically inserts the keywords separated by OR (|).
                                            # Example: (if|loop|for|while|begin|case)
    )                       # End of capturing group 1.
    \b                      # Matches a word boundary after the keyword.
    """,
    flags=re.IGNORECASE | re.VERBOSE # Added re.VERBOSE for consistency with multi-line format
)

# Dynamically constructs a regex string for identifying single-line blocks
# Example: \b(?<!END\s)(if|loop|...)\b.*(?:\bTHEN\b)?.*\bEND\b
KEYWORDS_REQUIRING_END_ONE_LINE_REGEX =  re.compile(rf"""
    \b                          # Matches a word boundary before the keyword.
    (?<!END\s)                  # Negative lookbehind: ensures not preceded by "END ".
    (                           # Start of capturing group 1 (the opening keyword):
        {'|'.join(KEYWORDS_REQUIRING_END)}      # Dynamically inserts the keywords.
    )                           # End of capturing group 1.
    \b                          # Matches a word boundary after the opening keyword.
    .*                          # Matches any character (except newline) zero or more times.
                                # This accounts for any code between the opening keyword and an optional THEN.
    (?:\bTHEN\b)?               # Optional non-capturing group for the "THEN" keyword.
                                #   (?: ... ) denotes a non-capturing group.
                                #   \bTHEN\b matches "THEN" as a whole word.
                                #   ? makes this group optional.
    .*                          # Matches any character (except newline) zero or more times.
                                # This accounts for any code between THEN (if present) and the final END.
    \bEND\b                     # Matches the keyword "END" as a whole word, signifying the end of the one-line block.
    """,
    flags=re.IGNORECASE | re.VERBOSE # Added re.VERBOSE
)

class PlSqlStructuralParser:
    
    def __init__(self, logger:lg.Logger, verbose_lvl:int):

        self.logger = logger.bind(parser_type="Structural")
        self.verbose_lvl = verbose_lvl

        # Parsing State (initialized in reset_state)
        self.line_num = 0
        self.current_line_content = ""
        self.processed_line_content = ""
        self.inside_quote = False
        self.inside_multiline_comment = False
        self.multiline_object_name_pending = None

        # Collected Data
        self.package_name: Optional[str] = None
        self.collected_code_objects: Dict[str, List[Dict[str, Any]]] = {}
        
        # Stacks for tracking blocks and scopes
        # block_stack holds keywords like IF, LOOP, CASE, BEGIN
        # scope_stack holds PACKAGE, PROCEDURE, FUNCTION scopes
        self.block_stack: List[Tuple[int, str]] = []
        self.scope_stack: List[Tuple[int, Tuple[str, str], Dict[str, Any]]] = [] # (line, (type, name), state_dict)

        # State specific to loops (to handle FOR/WHILE needing LOOP)
        self.is_awaiting_loop_for_for = False
        self.is_awaiting_loop_for_while = False

        # State for forward declaration detection
        self.forward_decl_candidate: Optional[Tuple[int, Tuple[str, str]]] = None # (scope_line, (type, name))
        self.forward_decl_check_end_line: Optional[int] = None # Line where check was triggered

        # self.reset_state() # Initialize state

    def reset_state(self):
        """Resets the parser state for a new run or initialization."""
        self.code = ""
        self.lines = self.code.splitlines(keepends=True)
        self.line_num = 0
        self.current_line_content = ""
        self.processed_line_content = ""
        self.inside_quote = False
        self.inside_multiline_comment = False
        self.multiline_object_name_pending = None
        self.package_name = None
        self.collected_code_objects = {}
        self.block_stack = []
        self.scope_stack = []
        self.is_awaiting_loop_for_for = False
        self.is_awaiting_loop_for_while = False
        self.forward_decl_candidate = None
        self.forward_decl_check_end_line = None
        self.is_forward_decl = False
        self.logger.trace("StructuralParser state reset.")

    def _remove_strings_and_inline_comments(self, line: str, current_inside_quote_state: bool) -> Tuple[str, bool]:
        new_line = ""
        idx = 0
        # Propagate quote state from previous line
        is_inside_quote = current_inside_quote_state 

        while idx < len(line):
            current_char = line[idx]
            next_char = line[idx + 1] if (idx + 1) < len(line) else None

            if is_inside_quote:

                # Check for escaped quote
                if next_char and current_char + next_char == "''":
                    # new_line += "''"
                    idx += 1
                
                # Close Quotes
                elif current_char == "'" and next_char != "'":
                    new_line += current_char
                    is_inside_quote = False
                
                # Else - Just skip over
            
            # If not inside quotes
            else:

                # Check start of quotes
                if current_char == "'":
                    new_line += current_char
                    is_inside_quote = True
                
                # Check for inline comments
                elif next_char and current_char + next_char == "--":
                    break

                else:
                    new_line += current_char
            
            idx += 1



        return new_line, is_inside_quote

    def _push_scope(self, line_num: int, scope_type: str, scope_name: str, is_package: bool = False):
        """Pushes a new scope (Package, Procedure, Function) onto the stack."""
        scope_name_cleaned = scope_name.replace("\"", "") # Remove quotes for internal tracking
        scope_tuple = (scope_type.upper(), scope_name_cleaned)
        state_info = {"has_seen_begin": False, "is_package": is_package}

        self.scope_stack.append((line_num, scope_tuple, state_info))
        self.logger.debug(f"L{line_num}: PUSH SCOPE: {scope_tuple}")

        if not is_package:
            # Add to collected objects immediately, end line updated later
            obj_key = scope_name_cleaned.casefold()

            if obj_key not in self.collected_code_objects:
                self.collected_code_objects[obj_key] = []

            self.collected_code_objects[obj_key].append({
                "start": line_num,
                "end": -1, # Placeholder
                "type": scope_type.upper()
            })

            # Prepare for potential forward declaration check ONLY for PROC/FUNC
            # self.forward_decl_candidate = (line_num, scope_tuple)
            self._check_for_forward_decl_candidate(self.processed_line_content, line_num, *scope_tuple)

        else:
            # Clear any pending forward decl candidate when package starts
            self._clear_forward_decl_candidate(reason="Package scope started")

    def _push_block(self, line_num: int, block_type: str):
        """Pushes a block keyword (IF, LOOP, etc.) onto the stack."""
        self.block_stack.append((line_num, block_type.upper()))
        self.logger.debug(f"L{line_num}: PUSH BLOCK: {block_type.upper()}")

    def _pop_scope(self, reason:str) -> Tuple[int, Tuple[str, str], Dict[str, Any]]:
        """Pops the current scope from the stack."""
        if not self.scope_stack:
            self.logger.error(f"L{self.line_num}: Attempted to pop scope, but scope stack is empty! (pop reason: {reason})")
            
            # Decide how to handle this - raise error or return dummy? Raising is safer.
            raise IndexError("Attempted to pop from empty scope stack")
    
        popped = self.scope_stack.pop()
        self.logger.debug(f"L{self.line_num}: POP SCOPE : {popped[1]} (Started L{popped[0]}) (pop reason: {reason})")
        
        # Clear forward decl candidate if we are popping its scope
        if self.forward_decl_candidate and self.forward_decl_candidate[0] == popped[0]:
            self._clear_forward_decl_candidate(reason="Scope ended normally before confirmation")

        return popped

    def _pop_block(self) -> Tuple[int, str]:
        """Pops the latest block keyword from the stack."""
        
        if not self.block_stack:
            self.logger.error(f"L{self.line_num}: Attempted to pop block, but block stack is empty!")
            raise IndexError("Attempted to pop from empty block stack")
        
        popped = self.block_stack.pop()
        self.logger.debug(f"L{self.line_num}: POP BLOCK : {popped[1]} (Started L{popped[0]})")
        
        return popped

    def _check_for_forward_decl_candidate(self, processed_line:str, scope_line:int, scope_type:str, scope_name:str):
        # scope_line, (scope_type, scope_name) = self.forward_decl_candidate
        self.logger.trace(f"L{scope_line}: Checking Candidate for Forward Decl: {(scope_type, scope_name)}")

        # Check for patterns indicating a forward declaration is confirmed
        if scope_type == "PROCEDURE":
            # Check code block since definition for more complex patterns if needed
            # (Simplified check here based on original logic)
            code_block_since_def = "".join(self.lines[scope_line-1 : self.line_num])
            self.logger.trace(f"L{scope_line}-{self.line_num}: Code Block from Def: `{escape_angle_brackets(repr(code_block_since_def.strip()))}`")

            if re.search(rf"PROCEDURE\s+{scope_name.replace('.', r'\.')}\s*\(((?!(\bIS\b|\bAS\b)).)*;", code_block_since_def, re.DOTALL|re.IGNORECASE):
                # forward_dec_detected = True
                self.forward_decl_candidate = (scope_line, (scope_type, scope_name))
            
            elif re.search(rf"PROCEDURE\s+{scope_name.replace('.', r'\.')}\s*(?!(\(|\bAS\b|\bIS\b).)\s*;", code_block_since_def, re.DOTALL|re.IGNORECASE):
                self.forward_decl_candidate = (scope_line, (scope_type, scope_name))
            
            # Pattern 1: Specific "AS LANGUAGE" pattern
            elif re.search(rf"PROCEDURE\s+{re.escape(scope_name)}\s*(:?\(.*?\))?\s+\bAS\b\s+\blanguage\b.*?;", code_block_since_def, re.DOTALL|re.IGNORECASE):
                # self.is_forward_decl = True
                self.forward_decl_candidate = (scope_line, (scope_type, scope_name))
        
        # Pattern 3: Function return clause ending with semicolon
        if scope_type == "FUNCTION":
            code_block_since_def = "".join(self.lines[scope_line-1 : self.line_num])
            self.logger.trace(f"L{scope_line}-{self.line_num}: Code Block from Def: `{escape_angle_brackets(repr(code_block_since_def.strip()))}`")
            # Check if RETURN type is defined and line ends with ;
            # if re.search(rf"FUNCTION\s+{re.escape(scope_name)}.*?\s*\bRETURN\b\s+\S+\s*;", code_block_since_def, re.IGNORECASE|re.DOTALL):
            #     self.is_forward_decl = True
            if re.search(r"\bRETURN\b\s+(.*?)\s*;", processed_line, re.IGNORECASE):
                self.forward_decl_candidate = (scope_line, (scope_type, scope_name))

        if self.forward_decl_candidate:
            self.forward_decl_check_end_line = None
            self.logger.trace(f"L{scope_line}: Candidate Selected for Forward Decl: {(scope_type, scope_name)}")

    def _clear_forward_decl_candidate(self, reason: str):
        if self.forward_decl_candidate:
            self.logger.trace(f"L{self.line_num}: Candidate dropped for Forward Decl check: {self.forward_decl_candidate[1]} - Reason: {reason}")
            self.forward_decl_candidate = None
            self.forward_decl_check_end_line = None

    def _handle_forward_declaration(self):
        """Handles confirmed forward declaration by removing it."""
        if not self.forward_decl_candidate:
            self.logger.warning(f"L{self.line_num}: _handle_forward_declaration called but no candidate exists.")
            return

        scope_line, (scope_type, scope_name) = self.forward_decl_candidate
        check_line = self.forward_decl_check_end_line or self.line_num # Use check line if available

        self.logger.info(f"L{scope_line}-{check_line}: Confirmed Forward Declaration for `{scope_name}` ({scope_type}). Removing.")

        # Find and remove from scope stack (should be the last one)
        found_on_stack = False
        if self.scope_stack and self.scope_stack[-1][0] == scope_line and self.scope_stack[-1][1] == (scope_type, scope_name):
            self._pop_scope(reason="Forward Declaration confirmed") # Pop it using the method to ensure logging consistency
            found_on_stack = True
            self.logger.trace(f"Removed forward decl {scope_name} from scope stack.")

        # Remove from collected_code_objects
        obj_key = scope_name.casefold()
        removed_from_collected = False
        if obj_key in self.collected_code_objects:

            # Find the specific entry by start line and remove it
            entries = self.collected_code_objects[obj_key]
            for i in range(len(entries) - 1, -1, -1):
                if entries[i]['start'] == scope_line and entries[i]['type'] == scope_type:
                    entries.pop(i)
                    removed_from_collected = True
                    self.logger.trace(f"Removed forward decl {scope_name} from collected objects.")
                    break

            if not entries:  # Remove key if list becomes empty
                del self.collected_code_objects[obj_key]
                self.logger.trace(f"Removed empty key '{obj_key}' from collected objects.")

        if not found_on_stack or not removed_from_collected:
             self.logger.warning(f"L{self.line_num}: Could not fully remove forward decl candidate {scope_name} (found_on_stack={found_on_stack}, removed_from_collected={removed_from_collected})")

        self.forward_decl_candidate = None
        self.forward_decl_check_end_line = None

    def _process_line(self):
        """Processes a single line of code. Uses self.logger for output."""
        line = self.current_line_content
        self.logger.trace(f"L{self.line_num}: Raw Line: {escape_angle_brackets(repr(line))}")

        # 1. Handle Multiline Comments
        if self.inside_multiline_comment:
            if "*/" in line:
                self.inside_multiline_comment = False
                line = line.split("*/", 1)[1]
                self.logger.trace(f"L{self.line_num}: Multiline comment ends. Remaining: `{escape_angle_brackets(line.strip())}`")
                
                if not line.strip():
                    return # Nothing left on line

            else:
                self.logger.trace(f"L{self.line_num}: Skipping line inside multi-line comment.")
                return # Skip rest of processing for this line

        # Must handle comments *before* string/inline comment removal
        # Handle start of multiline comment `/*` potentially after some code
        if "/*" in line:
            before_comment, _, after_comment = line.partition("/*")
            if "*/" in after_comment: # Starts and ends on the same line
                # Handle comment contained entirely within the line
                line_without_block_comment = before_comment + after_comment.split("*/", 1)[1]
                self.logger.trace(f"L{self.line_num}: Handled single-line block comment. Remaining: `{escape_angle_brackets(line_without_block_comment.strip())}`")
                line = line_without_block_comment
                
                if not line.strip():
                    return
             
            else:
                # Multiline comment starts here
                self.inside_multiline_comment = True
                line = before_comment
                self.logger.trace(f"L{self.line_num}: Multiline comment starts. Processing before: `{escape_angle_brackets(line.strip())}`")
                # Continue processing 'line'

        # Skip empty lines after potential comment removal
        if not line.strip():
            self.logger.trace(f"L{self.line_num}: Line empty after multiline comment handling.")
            return

        # # 2. Remove Strings and Inline Comments
        # # This modifies self.inside_quote state
        # processed_line, next_inside_quote = self._remove_strings_and_inline_comments(line, self.inside_quote)

        # if self.inside_quote != next_inside_quote:
        #     self.logger.trace(f"L{self.line_num}: Quote state changed to: {next_inside_quote}")
        #     self.inside_quote = next_inside_quote
        processed_line = line
        self.processed_line_content = processed_line
        self.logger.trace(f"L{self.line_num}: Processed Line: {escape_angle_brackets(repr(processed_line))}")
        
        # Skip lines that become empty after string/comment removal
        if not processed_line.strip():
            self.logger.trace(f"L{self.line_num}: Line empty after string/inline comment removal.")
            return

        # --- Check for Forward Declaration Confirmation Pattern --- #
        # This needs to happen *before* checking for new objects/blocks on the *current* line,
        # but *after* comment/string removal as ';' might be hidden.
        # Only check if the candidate is still the top scope and hasn't seen 'BEGIN'
        current_scope_obj = self.scope_stack[-1] if self.scope_stack else None
        if current_scope_obj and not current_scope_obj[2].get("has_seen_begin") and self.forward_decl_candidate is None:
            self._check_for_forward_decl_candidate(processed_line, current_scope_obj[0], *current_scope_obj[1])
        
                # --- Check for Package --- #
        
        # Needs to be checked *before* PROCEDURE/FUNCTION as they can appear inside package spec/body declarations
        package_match = PACKAGE_NAME_REGEX.search(processed_line)
        if package_match:
            if self.package_name:
                self.logger.error(f"L{self.line_num}: Multiple PACKAGE BODY declarations found! Previous: {self.package_name}")
                # Depending on desired behavior, maybe raise Exception(..) or just log and overwrite
            
            # .strip() to remove potential trailing spaces captured by ([A-Za-z0-9_\"\. ]+?)
            self.package_name = package_match.group(1).strip().replace("\"", "")
            self.logger.info(f"L{self.line_num}: Found PACKAGE BODY {self.package_name}")
            self._push_scope(self.line_num, "PACKAGE", self.package_name, is_package=True)

            # Package definition line likely doesn't contain other blocks, maybe return?
            # Decide if other keywords can follow on this line. Assuming not for now.
            # return

        # --- Check for Object (Procedure/Function) --- #
        # Handle pending object name from previous line
        line_to_check_object = processed_line
        if self.multiline_object_name_pending:
            line_to_check_object = f"{self.multiline_object_name_pending} {line_to_check_object}"
            self.logger.trace(f"L{self.line_num}: Combined pending '{self.multiline_object_name_pending}' with current line for object check.")
            self.multiline_object_name_pending = None # Reset pending name

        obj_match = OBJECT_NAME_REGEX.search(line_to_check_object)# or OBJECT_NAME_REGEX_V2.search(line_to_check_object)
        if obj_match:

            if self.forward_decl_candidate:
                self.forward_decl_check_end_line = self.line_num # Record line where check passed
                self.logger.trace(f"L{self.line_num}: Forward Declaration pattern matched for {self.forward_decl_candidate[1][1]}: `{escape_angle_brackets(processed_line.strip())}`")
                self._handle_forward_declaration()

                # Since the forward declaration is handled, we might not need to process the rest of this line?
                # Or maybe the ';' line just ends the forward decl, and we continue?
                # Assuming the line ONLY contains the end of the forward decl. If code follows ';', this needs adjustment.
                # return # Assume line only confirmed forward decl - Stop processing this line after handling fwd decl confirmation

            obj_type, obj_name, has_end = obj_match.groups() # Ensure only first two groups are taken - Extract type and name
            obj_name = obj_name.replace("\"", "") # Clean name
            self.logger.info(f"L{self.line_num}: Found {obj_type.upper()} {obj_name}")

            self._clear_forward_decl_candidate(reason=f"New object '{obj_name}' found")
            self._push_scope(self.line_num, obj_type, obj_name)

            # if has_end and self.scope_stack:
            #     start_idx, (ended_type, ended_name), scope_state = self._pop_scope(reason="END for codeobject found on same line")

            #     # Update end line in collected objects
            #     if not scope_state.get("is_package"): # Don't track end for package itself? Or do? Decide.
            #         obj_key = ended_name.casefold()
            #         if obj_key in self.collected_code_objects:

            #             # Find the corresponding entry (usually the last one for this key) and update end line
            #             for entry in reversed(self.collected_code_objects[obj_key]):

            #                 # Match on start line to be certain, although usually last is correct
            #                 if entry['start'] == start_idx and entry['end'] == -1:
            #                     entry['end'] = self.line_num
            #                     self.logger.trace(f"Updated end line for {ended_name} to {self.line_num}")
            #                     break

            #     log_level = "INFO" if ended_type in ["PACKAGE", "PROCEDURE", "FUNCTION"] else "DEBUG"
            #     self.logger.log(log_level, f"L{start_idx}-{self.line_num}: END {ended_type} {ended_name}")

            # Don't return yet, need to check for block keywords on the same line
            # Continue processing line for keywords like IS/AS/BEGIN

        # Handle case where PROCEDURE/FUNCTION keyword is on one line, name on the next
        elif re.search(r"\b(FUNCTION|PROCEDURE)\b", processed_line.strip(), re.IGNORECASE):

            # Check if it looks like just the keyword, e.g., ends with it or only whitespace after
            m = re.search(r"\b(FUNCTION|PROCEDURE)\s*$", processed_line.strip(), re.IGNORECASE)

            if m:
                self.multiline_object_name_pending = m.group(1)
                self.logger.trace(f"L{self.line_num}: Object definition keyword '{self.multiline_object_name_pending}' found, name potentially on next line.")
                return # Expect name on the next line

        # --- Check for Keywords Requiring END (One Line) --- #
        # Needs to be checked before individual keywords like BEGIN/END
        one_line_match = KEYWORDS_REQUIRING_END_ONE_LINE_REGEX.search(processed_line)
        if one_line_match:

            # Count keywords vs ENDs on the line
            keywords = [keyword.casefold() for keyword in KEYWORDS_REQUIRING_END_REGEX.findall(processed_line)]
            ends = END_CHECK_REGEX.findall(processed_line)
            self.logger.trace(f"L{self.line_num}: Found one-line block(s). Keywords: {keywords}, ENDs: {ends}.")

            if len(ends) > len(keywords):
                self.logger.error(f"L{self.line_num}: Excess END found on one-line block, but no block to close.")

            # Log the self-contained blocks
            num_closed = min(len(keywords), len(ends))
            for _ in range(num_closed):
                self_contained_keyword = keywords.pop(-1)

                if self_contained_keyword == 'begin':
                    if self.scope_stack and not self.scope_stack[-1][2].get("has_seen_begin"):
                        scope_line, (_, scope_name), scope_state = self.scope_stack[-1]
                        self.logger.debug(f"L{self.line_num}: Found BEGIN for {scope_name} (Scope Start: L{scope_line})")
                        scope_state["has_seen_begin"] = True

                        # Finding BEGIN means the current scope is *not* a forward declaration
                        self._clear_forward_decl_candidate(reason="BEGIN found")

                        if self.scope_stack:
                            start_idx, (ended_type, ended_name), scope_state = self._pop_scope(reason="END for keyword found on same line")
                            
                            # Update end line in collected objects
                            if not scope_state.get("is_package"): # Don't track end for package itself? Or do? Decide.
                                obj_key = ended_name.casefold()
                                if obj_key in self.collected_code_objects:

                                    # Find the corresponding entry (usually the last one for this key) and update end line
                                    for entry in reversed(self.collected_code_objects[obj_key]):

                                        # Match on start line to be certain, although usually last is correct
                                        if entry['start'] == start_idx and entry['end'] == -1:
                                            entry['end'] = self.line_num
                                            self.logger.trace(f"Updated end line for {ended_name} to {self.line_num}")
                                            break

                            log_level = "INFO" if ended_type in ["PACKAGE", "PROCEDURE", "FUNCTION"] else "DEBUG"
                            self.logger.log(log_level, f"L{start_idx}-{self.line_num}: END {ended_type} {ended_name}")

                self.logger.debug(f"L{self.line_num}-{self.line_num}: Self-contained block ({self_contained_keyword}) on line.")
            
            # Implicitly consume loop if also found by regex
            while ('loop' in keywords) and ('for' in keywords or 'while' in keywords):
                keywords.remove('loop')

            # Handle scope BEGIN on same line
            # If BEGIN is involved, check if it's the scope's BEGIN
            for keyword in keywords:
                keyword_upper = keyword.upper()

                # Special handling for BEGIN: Associate with current scope if it hasn't seen one
                if keyword == 'begin':
                    if self.scope_stack and not self.scope_stack[-1][2].get("has_seen_begin"):
                        scope_line, (_, scope_name), scope_state = self.scope_stack[-1]
                        self.logger.debug(f"L{self.line_num}: Found BEGIN for {scope_name} (Scope Start: L{scope_line})")
                        scope_state["has_seen_begin"] = True

                        # Finding BEGIN means the current scope is *not* a forward declaration
                        self._clear_forward_decl_candidate(reason="BEGIN found")
                    else:
                        # Standalone BEGIN block
                        self._push_block(self.line_num, keyword_upper)

                # Handling FOR loop start
                elif keyword == 'for':
                     
                    # Ignore 'FOR UPDATE' and 'OPEN cursor FOR query'
                    if re.search(r"\bFOR\s+UPDATE\b", processed_line, re.IGNORECASE) or re.search(r"\bOPEN\s+\S+\s+FOR\b", processed_line, re.IGNORECASE):
                        self.logger.trace(f"L{self.line_num}: Ignoring 'FOR' as part of UPDATE or OPEN statement.")
                        continue # Skip this keyword

                    # Check if LOOP is on the same line
                    if re.search(r"\bFOR\b.*\bLOOP\b", processed_line, re.IGNORECASE):
                        self.logger.trace(f"L{self.line_num}: FOR with LOOP on same line.")
                        self._push_block(self.line_num, keyword_upper)

                    else:
                        self.logger.trace(f"L{self.line_num}: FOR found without LOOP on same line. Awaiting LOOP.")
                        self._push_block(self.line_num, keyword_upper)
                        self.is_awaiting_loop_for_for = True

                # Handling WHILE loop start
                elif keyword == 'while':
                    # Check if LOOP is on the same line
                    if re.search(r"\bWHILE\b.*\bLOOP\b", processed_line, re.IGNORECASE):
                        self.logger.trace(f"L{self.line_num}: WHILE with LOOP on same line.")
                        self._push_block(self.line_num, keyword_upper)
                    else:
                        self.logger.trace(f"L{self.line_num}: WHILE found without LOOP on same line. Awaiting LOOP.")
                        self._push_block(self.line_num, keyword_upper)
                        self.is_awaiting_loop_for_while = True

                # Handle LOOP keyword (only if not consumed by FOR/WHILE logic above)
                elif keyword == 'loop':
                    # Only push if not consumed above and not awaiting
                    if not self.is_awaiting_loop_for_for and not self.is_awaiting_loop_for_while:
                        self.logger.trace(f"L{self.line_num}: Standalone LOOP keyword found.")
                        self._push_block(self.line_num, keyword_upper)
                    # else: implicitly handled by FOR/WHILE logic finding it

                # Other keywords (IF, CASE)
                elif keyword in ['if', 'case']:
                    self._push_block(self.line_num, keyword_upper)

            return # Handled one-liner

        # --- Check for END Keyword --- #
        if END_CHECK_REGEX.search(processed_line):
            ends_found = len(END_CHECK_REGEX.findall(processed_line))
            self.logger.trace(f"L{self.line_num}: Found {ends_found} 'END' keyword(s) on the line.")
            for _ in range(ends_found):
                if self.block_stack:
                    start_idx, ended_keyword = self._pop_block()
                    if ended_keyword == "FOR":
                        assert not self.is_awaiting_loop_for_for, f"L{self.line_num}: END FOR before LOOP found"

                    if ended_keyword == "WHILE":
                        assert not self.is_awaiting_loop_for_while, f"L{self.line_num}: END WHILE before LOOP found"

                    self.logger.debug(f"L{start_idx}-{self.line_num}: END {ended_keyword}")
                
                # If no blocks, close the current scope (PROC, FUNC, PACKAGE)
                elif self.scope_stack:
                    start_idx, (ended_type, ended_name), scope_state = self._pop_scope(reason="END found")
                    
                    # Update end line in collected objects
                    if not scope_state.get("is_package"): # Don't track end for package itself? Or do? Decide.
                        obj_key = ended_name.casefold()
                        if obj_key in self.collected_code_objects:

                            # Check if the object has begun
                            if not scope_state.get("has_seen_begin"):
                                self.logger.error(f"L{self.line_num}: Found END for {ended_type} {ended_name} but it hasn't seen a BEGIN yet!")

                            # Find the corresponding entry (usually the last one for this key) and update end line
                            for entry in reversed(self.collected_code_objects[obj_key]):

                                # Match on start line to be certain, although usually last is correct
                                if entry['start'] == start_idx and entry['end'] == -1:
                                    entry['end'] = self.line_num
                                    self.logger.trace(f"Updated end line for {ended_name} to {self.line_num}")
                                    break

                    log_level = "INFO" if ended_type in ["PACKAGE", "PROCEDURE", "FUNCTION"] else "DEBUG"
                    self.logger.log(log_level, f"L{start_idx}-{self.line_num}: END {ended_type} {ended_name}")
                else:
                    self.logger.error(f"L{self.line_num}: Found 'END' keyword but no open block or scope!")
            return # Handled END

        # --- Check for Block Starting Keywords --- #
        # Use findall to catch multiple keywords on one line (e.g. IF condition THEN IF ...)
        keywords_found = KEYWORDS_REQUIRING_END_REGEX.findall(processed_line)
        if keywords_found:
            current_keywords = [kw.casefold() for kw in keywords_found]
            self.logger.trace(f"L{self.line_num}: Keywords requiring END found: {current_keywords}")

            # Handle awaited LOOPs
            if self.is_awaiting_loop_for_for and 'loop' in current_keywords:
                self.logger.trace(f"L{self.line_num}: LOOP found, matching pending FOR.")
                current_keywords.remove('loop')
                self.is_awaiting_loop_for_for = False

            if self.is_awaiting_loop_for_while and 'loop' in current_keywords:
                self.logger.trace(f"L{self.line_num}: LOOP found, matching pending WHILE.")
                current_keywords.remove('loop')
                self.is_awaiting_loop_for_while = False

            # Process remaining keywords
            for keyword in current_keywords:
                keyword_upper = keyword.upper()

                # Special handling for BEGIN: Associate with current scope if it hasn't seen one
                if keyword == 'begin':
                    if self.scope_stack and not self.scope_stack[-1][2].get("has_seen_begin"):
                        scope_line, (_, scope_name), scope_state = self.scope_stack[-1]
                        self.logger.debug(f"L{self.line_num}: Found BEGIN for {scope_name} (Scope Start: L{scope_line})")
                        scope_state["has_seen_begin"] = True

                        # Finding BEGIN means the current scope is *not* a forward declaration
                        self._clear_forward_decl_candidate(reason="BEGIN found")
                    else:
                        # Standalone BEGIN block
                        self._push_block(self.line_num, keyword_upper)

                # Handling FOR loop start
                elif keyword == 'for':
                     
                    # Ignore 'FOR UPDATE' and 'OPEN cursor FOR query'
                    if re.search(r"\bFOR\s+UPDATE\b", processed_line, re.IGNORECASE) or re.search(r"\bOPEN\s+\S+\s+FOR\b", processed_line, re.IGNORECASE):
                        self.logger.trace(f"L{self.line_num}: Ignoring 'FOR' as part of UPDATE or OPEN statement.")
                        continue # Skip this keyword

                    # Check if LOOP is on the same line
                    if re.search(r"\bFOR\b.*\bLOOP\b", processed_line, re.IGNORECASE):
                        self.logger.trace(f"L{self.line_num}: FOR with LOOP on same line.")
                        self._push_block(self.line_num, keyword_upper)
                        # Implicitly consume loop if also found by regex
                        if 'loop' in current_keywords:
                            current_keywords.remove('loop')
                    else:
                        self.logger.trace(f"L{self.line_num}: FOR found without LOOP on same line. Awaiting LOOP.")
                        self._push_block(self.line_num, keyword_upper)
                        self.is_awaiting_loop_for_for = True

                # Handling WHILE loop start
                elif keyword == 'while':
                    # Check if LOOP is on the same line
                    if re.search(r"\bWHILE\b.*\bLOOP\b", processed_line, re.IGNORECASE):
                        self.logger.trace(f"L{self.line_num}: WHILE with LOOP on same line.")
                        self._push_block(self.line_num, keyword_upper)

                        # Consume the LOOP implicitly
                        if 'loop' in current_keywords:
                            current_keywords.remove('loop')
                    else:
                        self.logger.trace(f"L{self.line_num}: WHILE found without LOOP on same line. Awaiting LOOP.")
                        self._push_block(self.line_num, keyword_upper)
                        self.is_awaiting_loop_for_while = True

                # Handle LOOP keyword (only if not consumed by FOR/WHILE logic above)
                elif keyword == 'loop':
                    # Only push if not consumed above and not awaiting
                    if not self.is_awaiting_loop_for_for and not self.is_awaiting_loop_for_while:
                        self.logger.trace(f"L{self.line_num}: Standalone LOOP keyword found.")
                        self._push_block(self.line_num, keyword_upper)
                    # else: implicitly handled by FOR/WHILE logic finding it

                # Other keywords (IF, CASE)
                elif keyword in ['if', 'case']:
                    self._push_block(self.line_num, keyword_upper)
            return # Handled block starters

        # --- Default Case --- #
        # No return means no major structural keyword was fully handled on this line
        self.logger.trace(f"L{self.line_num}: No specific structural keywords processed.")

    def parse(self, code:str) -> Tuple[Optional[str], Dict]:
        """Parses the entire PL/SQL code, logs progress and details."""
        self.reset_state() # Ensure clean state before parsing
        self.logger.info("Starting PL/SQL code parsing...")

        self.code = code
        self.lines = code.splitlines(keepends=True)

        # Wrap lines iteration with tqdm for progress bar
        line_iterator = tqdm(enumerate(self.lines),
                             total=len(self.lines),
                             desc="Parsing lines",
                             unit=" lines",
                             disable=self.verbose_lvl <= 1) # Disable tqdm if self.logger level is higher than INFO

        for i, line in line_iterator:
            self.line_num = i + 1
            self.current_line_content = line
            try:
                self._process_line()
            except Exception as e:
                self.logger.critical(f"Critical error processing line L{self.line_num}: `{escape_angle_brackets(line.strip())}`")
                self.logger.exception(e) # Log stack trace
                # Re-raise to stop parsing immediately on critical error
                raise

        # --- Final Checks ---
        self.logger.info("Parsing finished. Performing final checks...")
        if self.inside_multiline_comment:
             self.logger.error("Code ended while still inside a multi-line comment.")
        if self.inside_quote:
             self.logger.error("Code ended while still inside a string literal.")
        if self.block_stack:
             self.logger.error(f"Code ended with unclosed blocks: {self.block_stack}")
        if self.scope_stack:
            # Check if only the main package scope remains (which is OK)
            # Only error if non-package scopes remain
            non_package_scopes = [s for s in self.scope_stack if not s[2].get("is_package")]
            if non_package_scopes:
                self.logger.error(f"Code ended with unclosed scopes: {non_package_scopes}")
            elif self.scope_stack: # Only package scope left
                self.logger.info(f"Package scope '{self.scope_stack[0][1][1]}' implicitly closed by end of file.")
        if self.is_awaiting_loop_for_for:
            self.logger.error("Code ended while awaiting LOOP for a FOR statement.")
        if self.is_awaiting_loop_for_while:
            self.logger.error("Code ended while awaiting LOOP for a WHILE statement.")

        self.logger.info("Final checks complete.")
        # Use pprint for nice formatting in logs if possible, or simple dict log
        self.logger.debug(f"\n--- Collected Objects ---\n{pformat(self.collected_code_objects, sort_dicts=False)}\n--- End Collected Objects ---")

        return self.package_name, self.collected_code_objects


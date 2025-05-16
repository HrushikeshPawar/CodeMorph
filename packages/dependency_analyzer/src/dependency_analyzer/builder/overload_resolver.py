from __future__ import annotations
from typing import List, Dict, Optional, Any
import loguru as lg
import sys # For example usage logger

# Assuming these are accessible, adjust import paths as necessary
# from plsql_analyzer.core.code_object import PLSQL_CodeObject # Circular dep if in same package root
# from plsql_analyzer.parsing.call_extractor import CallDetailsTuple # Same here

# To avoid circular dependencies if these modules are part of the same top-level package
# and plsql_analyzer is a sibling, we might need to define simplified versions or
# ensure proper package structuring. For now, assuming they can be imported or
# will be passed such that type hints work.
# If PLSQL_CodeObject and CallDetailsTuple are defined in plsql_analyzer.core and plsql_analyzer.parsing respectively:
from plsql_analyzer.core.code_object import PLSQL_CodeObject
from plsql_analyzer.parsing.call_extractor import CallDetailsTuple


def resolve_overloaded_call(
    candidate_objects: List[PLSQL_CodeObject],
    call_details: CallDetailsTuple,
    logger: lg.Logger
) -> Optional[PLSQL_CodeObject]:
    """
    Resolves an overloaded call by matching provided call parameters against candidate signatures.

    Args:
        candidate_objects: A list of PLSQL_CodeObject instances representing potential
                           overloaded candidates.
        call_details: A CallDetailsTuple containing the parsed positional and named
                      parameters of the actual call.
        logger: A Loguru logger instance.

    Returns:
        The resolved PLSQL_CodeObject if a single unambiguous match is found,
        otherwise None.
    """
    logger.trace(f"Attempting to resolve overload for call '{call_details.call_name}' "
                 f"with {len(call_details.positional_params)} positional args, "
                 f"{len(call_details.named_params)} named args. "
                 f"Candidates: {[c.id for c in candidate_objects]}")

    matching_candidates: List[PLSQL_CodeObject] = []

    for candidate in candidate_objects:
        logger.trace(f"Evaluating candidate: {candidate.id} (Name: {candidate.name}, Pkg: {candidate.package_name})")
        candidate_formal_params: List[Dict[str, Any]] = candidate.parsed_parameters
        
        # Create a mutable copy of formal params to track supplied status
        # and map by lowercase name for case-insensitive matching of named args
        formal_params_status: List[Dict[str, Any]] = []
        for p in candidate_formal_params:
            param_copy = p.copy()
            param_copy['_supplied'] = False # Track if supplied by call
            param_copy['_name_lower'] = p.get('name', '').lower()
            formal_params_status.append(param_copy)

        valid_candidate = True

        # 1. Process Named Parameters from the call
        # Store which formal params were matched by a named arg from the call
        called_named_params_lower = {name.lower(): value for name, value in call_details.named_params.items()}

        for formal_param_info in formal_params_status:
            formal_param_name_lower = formal_param_info['_name_lower']
            if formal_param_name_lower in called_named_params_lower:
                if formal_param_info['_supplied']: # Should not happen if logic is sound (e.g. supplied by another named param - impossible)
                    logger.warning(f"Candidate {candidate.id}: Formal param '{formal_param_name_lower}' seems supplied multiple times by name. Skipping.")
                    valid_candidate = False
                    break
                formal_param_info['_supplied'] = True
                logger.trace(f"Candidate {candidate.id}: Param '{formal_param_name_lower}' supplied by named arg.")
        
        if not valid_candidate:
            continue

        # Check if all called named parameters actually exist in the candidate
        for called_name_lower in called_named_params_lower.keys():
            if not any(fp['_name_lower'] == called_name_lower for fp in formal_params_status):
                logger.trace(f"Candidate {candidate.id}: Called named parameter '{called_name_lower}' not found in signature. Invalid match.")
                valid_candidate = False
                break
        if not valid_candidate:
            continue
            
        # 2. Process Positional Parameters from the call
        num_positional_args_call = len(call_details.positional_params)
        
        # Find the first N available (not yet supplied by name) formal parameters
        available_for_positional_idx = 0
        for i in range(num_positional_args_call):
            # Find the next available formal parameter for this positional argument
            found_formal_for_positional = False
            while available_for_positional_idx < len(formal_params_status):
                formal_param_info = formal_params_status[available_for_positional_idx]
                if not formal_param_info['_supplied']: # If not already supplied by a named argument
                    formal_param_info['_supplied'] = True
                    logger.trace(f"Candidate {candidate.id}: Positional arg {i+1} maps to formal param '{formal_param_info.get('name')}'.")
                    available_for_positional_idx += 1
                    found_formal_for_positional = True
                    break 
                available_for_positional_idx += 1 # Move to next formal param
            
            if not found_formal_for_positional:
                # Not enough available formal parameters for the given positional arguments
                logger.trace(f"Candidate {candidate.id}: Too many positional arguments provided ({num_positional_args_call}) "
                             f"for available formal parameters. Invalid match.")
                valid_candidate = False
                break
        
        if not valid_candidate:
            continue

        # 3. Check for unsupplied parameters and ensure they have defaults
        for formal_param_info in formal_params_status:
            if not formal_param_info['_supplied']:
                # Parameter was not supplied by the call (neither positionally nor by name)
                # It must have a default value.
                # Assuming `param_info.get('default_value')` or `param_info.get('default')` exists and is not None
                # or a specific boolean flag like `param_info.get('has_default')`.
                # Let's check for a 'default_value' key, and assume its non-None presence means a default exists.
                # Or, if `dummy.py` used `param['default'] is not None`, we adapt to that.
                # Let's assume `parsed_parameters` has a field like `default_exists: bool` or `default_value: Optional[str]`
                # For this example, we'll check if a 'default_value' key exists and is not a specific "no default" marker
                # or rely on a hypothetical 'has_default' boolean field.
                # Based on `dummy.py`'s `current_candidate[param]['default'] is not None`,
                # we expect a 'default' key in the param dict.
                if formal_param_info.get('default') is None: # Or more robustly, a specific flag
                    logger.trace(f"Candidate {candidate.id}: Formal parameter '{formal_param_info.get('name')}' "
                                 f"is not supplied and has no default value. Invalid match.")
                    valid_candidate = False
                    break
                else:
                    logger.trace(f"Candidate {candidate.id}: Formal param '{formal_param_info.get('name')}' not supplied, using default.")

        if not valid_candidate:
            continue

        # 4. Final check: if any named parameters from the call were not used to supply a formal param
        #    (This should have been caught earlier if a called named param didn't exist in signature)
        #    This is more about ensuring all parts of the call make sense for the candidate.
        #    This check is largely covered by step 1's iteration over `called_named_params_lower`.

        if valid_candidate:
            logger.debug(f"Candidate {candidate.id} is a valid match for call '{call_details.call_name}'.")
            matching_candidates.append(candidate)

    # 5. Determine Winner
    if not matching_candidates:
        logger.warning(f"Overload resolution for '{call_details.call_name}': No matching candidates found. "
                       f"Call details: Positional={call_details.positional_params}, Named={call_details.named_params}")
        return None
    
    if len(matching_candidates) == 1:
        resolved_obj = matching_candidates[0]
        logger.info(f"Overload resolution for '{call_details.call_name}': Unambiguously resolved to {resolved_obj.id}")
        return resolved_obj

    # More than 1 match - ambiguity
    # TODO: Implement tie-breaking rules if necessary (e.g., prefer fewer defaults, more specific types)
    # For now, consider it ambiguous.
    logger.warning(f"Overload resolution for '{call_details.call_name}': Ambiguous. "
                   f"{len(matching_candidates)} candidates match: {[c.id for c in matching_candidates]}. "
                   f"Call details: Positional={call_details.positional_params}, Named={call_details.named_params}")
    return None

# Example (Illustrative - requires PLSQL_CodeObject and CallDetailsTuple to be defined and populated)
if __name__ == '__main__':
    # Setup a basic logger for the example
    example_logger = lg.logger
    example_logger.remove()
    example_logger.add(
        sys.stderr,
        level="TRACE",
        colorize=True,
        format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
    )
    example_logger.info("Running Overload Resolver example...")

    # Mock PLSQL_CodeObject and CallDetailsTuple for the sake of example
    # In a real scenario, these would be properly defined and imported.
    from typing import NamedTuple
    
    class MockExtractedCallTuple(NamedTuple): # Simplified for this example
        call_name: str
        line_no: int
        start_idx: int
        end_idx: int

    class MockCallDetailsTuple(NamedTuple): # Simplified
        call_name: str
        line_no: int
        start_idx: int
        end_idx: int
        positional_params: List[str]
        named_params: Dict[str, str]

    class MockPLSQLCodeObject:
        def __init__(self, id: str, name: str, package_name: str, parsed_parameters: List[Dict[str, Any]]):
            self.id = id
            self.name = name
            self.package_name = package_name
            self.parsed_parameters = parsed_parameters # List of dicts like {'name': 'p1', 'type': 'T', 'default': None or value}
            self.overloaded = True # For this context

        def __repr__(self):
            return f"MockPLSQLCodeObject(id='{self.id}')"

    # Candidate Signatures
    cand1_params = [
        {'name': 'p_text', 'type': 'VARCHAR2', 'default': None},
        {'name': 'p_num', 'type': 'NUMBER', 'default': 100}
    ]
    candidate1 = MockPLSQLCodeObject("pkg.proc_v1", "proc", "pkg", cand1_params)

    cand2_params = [
        {'name': 'p_text', 'type': 'VARCHAR2', 'default': None}
    ]
    candidate2 = MockPLSQLCodeObject("pkg.proc_v2", "proc", "pkg", cand2_params)
    
    cand3_params = [ # Different name
        {'name': 'p_data', 'type': 'VARCHAR2', 'default': None},
    ]
    candidate3 = MockPLSQLCodeObject("pkg.proc_v3_data", "proc", "pkg", cand3_params)

    cand4_params = [ # All defaults
        {'name': 'p_a', 'type': 'NUMBER', 'default': 1},
        {'name': 'p_b', 'type': 'NUMBER', 'default': 2},
    ]
    candidate4 = MockPLSQLCodeObject("pkg.proc_v4_defaults", "proc", "pkg", cand4_params)


    all_candidates = [candidate1, candidate2, candidate3, candidate4]

    # Test Case 1: Exact match for candidate2 (positional)
    call1 = MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=['hello_world'], named_params={})
    example_logger.info(f"\n--- Test Case 1: {call1} ---")
    resolved1 = resolve_overloaded_call(all_candidates, call1, example_logger)
    example_logger.info(f"Resolved to: {resolved1.id if resolved1 else 'None'} (Expected: {candidate2.id})")

    # Test Case 2: Match for candidate1 (positional + default)
    call2 = MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=['test_text'], named_params={})
    # This is ambiguous between cand1 (using default for p_num) and cand2 (exact match)
    # Our current logic might pick both, then declare ambiguity.
    # A more sophisticated system might prefer cand2 due to exact param count match.
    # For now, let's see. If cand2 is chosen, it means it prioritizes exact positional matches.
    example_logger.info(f"\n--- Test Case 2 (Ambiguity Expected or cand2): {call2} ---")
    resolved2 = resolve_overloaded_call(all_candidates, call2, example_logger)
    example_logger.info(f"Resolved to: {resolved2.id if resolved2 else 'None'} (Expected: {candidate2.id} or None if ambiguous with cand1)")


    # Test Case 3: Match for candidate1 (named parameters)
    call3 = MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=[], named_params={'p_text': 'named_text'})
    # This should also be ambiguous between cand1 (using default for p_num) and cand2 (exact match for p_text)
    example_logger.info(f"\n--- Test Case 3 (Ambiguity Expected or cand2): {call3} ---")
    resolved3 = resolve_overloaded_call(all_candidates, call3, example_logger)
    example_logger.info(f"Resolved to: {resolved3.id if resolved3 else 'None'} (Expected: {candidate2.id} or None if ambiguous with cand1)")

    # Test Case 4: Match for candidate1 (all params named)
    call4 = MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=[], named_params={'p_text': 'full', 'p_num': '123'})
    example_logger.info(f"\n--- Test Case 4: {call4} ---")
    resolved4 = resolve_overloaded_call(all_candidates, call4, example_logger)
    example_logger.info(f"Resolved to: {resolved4.id if resolved4 else 'None'} (Expected: {candidate1.id})")

    # Test Case 5: No match (wrong named parameter)
    call5 = MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=[], named_params={'p_wrong_name': 'test'})
    example_logger.info(f"\n--- Test Case 5 (No match): {call5} ---")
    resolved5 = resolve_overloaded_call(all_candidates, call5, example_logger)
    example_logger.info(f"Resolved to: {resolved5.id if resolved5 else 'None'} (Expected: None)")

    # Test Case 6: Too many positional arguments
    call6 = MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=['arg1', 'arg2', 'arg3'], named_params={})
    example_logger.info(f"\n--- Test Case 6 (No match - too many positional): {call6} ---")
    resolved6 = resolve_overloaded_call(all_candidates, call6, example_logger)
    example_logger.info(f"Resolved to: {resolved6.id if resolved6 else 'None'} (Expected: None)")
    
    # Test Case 7: Match for candidate4 (no args, all defaults)
    call7 = MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=[], named_params={})
    # This will be ambiguous with cand2 (if p_text has default) or cand1 (if p_text and p_num have defaults)
    # Let's assume cand2.p_text does NOT have a default. cand1.p_num has a default.
    # So this call should match cand4.
    example_logger.info(f"\n--- Test Case 7 (Match cand4 by all defaults): {call7} ---")
    resolved7 = resolve_overloaded_call(all_candidates, call7, example_logger) # Ambiguous with cand1 if p_text has default
    example_logger.info(f"Resolved to: {resolved7.id if resolved7 else 'None'} (Expected: {candidate4.id} if others require params)")

    # Test Case 8: Positional then named
    call8 = MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=['pos_text'], named_params={'p_num': '99'})
    example_logger.info(f"\n--- Test Case 8 (Positional then named for cand1): {call8} ---")
    resolved8 = resolve_overloaded_call(all_candidates, call8, example_logger)
    example_logger.info(f"Resolved to: {resolved8.id if resolved8 else 'None'} (Expected: {candidate1.id})")
    
    example_logger.info("\nOverload Resolver example finished.")

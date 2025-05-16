from __future__ import annotations
from typing import List, Dict, Any, NamedTuple, Optional
import pytest
from dependency_analyzer.builder.overload_resolver import resolve_overloaded_call
# Assuming PLSQL_CodeObject and CallDetailsTuple are accessible for mocking
# If they are in plsql_analyzer, adjust import paths or use simplified mocks as below.

# Simplified Mocks for testing if actual classes are complex or have many dependencies
class MockPLSQLCodeObject:
    def __init__(self, id: str, name: str, package_name: str, parsed_parameters: List[Dict[str, Any]]):
        self.id = id
        self.name = name
        self.package_name = package_name
        self.parsed_parameters = parsed_parameters  # e.g., [{'name': 'p1', 'type': 'T', 'default': None or value}]
        self.overloaded = True # Indicates it's part of an overload set

    def __repr__(self):
        return f"MockPLSQLCodeObject(id='{self.id}')"

class MockCallDetailsTuple(NamedTuple):
    call_name: str
    line_no: int
    start_idx: int
    end_idx: int
    positional_params: List[str]
    named_params: Dict[str, str]

# Test Candidates Setup
# PROC1: (p_a NUMBER, p_b VARCHAR2 DEFAULT 'default_b')
cand_proc1_p1 = MockPLSQLCodeObject("pkg.proc_v1", "proc", "pkg", [
    {'name': 'p_a', 'type': 'NUMBER', 'default': None},
    {'name': 'p_b', 'type': 'VARCHAR2', 'default': 'default_b'}
])

# PROC2: (p_a NUMBER)
cand_proc1_p2 = MockPLSQLCodeObject("pkg.proc_v2", "proc", "pkg", [
    {'name': 'p_a', 'type': 'NUMBER', 'default': None}
])

# PROC3: (p_x VARCHAR2)
cand_proc1_p3 = MockPLSQLCodeObject("pkg.proc_v3", "proc", "pkg", [
    {'name': 'p_x', 'type': 'VARCHAR2', 'default': None}
])

# PROC_NO_PARAMS: ()
cand_proc_no_params = MockPLSQLCodeObject("pkg.proc_no_params_v1", "proc_no_params", "pkg", [])

# PROC_ALL_DEFAULTS: (p_c NUMBER DEFAULT 1, p_d VARCHAR2 DEFAULT 'd')
cand_proc_all_defaults = MockPLSQLCodeObject("pkg.proc_all_defaults_v1", "proc_all_defaults", "pkg", [
    {'name': 'p_c', 'type': 'NUMBER', 'default': 1},
    {'name': 'p_d', 'type': 'VARCHAR2', 'default': 'd'}
])

# PROC_MIXED_ORDER: (p_req1 VARCHAR2, p_opt1 NUMBER DEFAULT 0, p_req2 DATE)
cand_proc_mixed_order = MockPLSQLCodeObject("pkg.proc_mixed_order_v1", "proc_mixed_order", "pkg", [
    {'name': 'p_req1', 'type': 'VARCHAR2', 'default': None},
    {'name': 'p_opt1', 'type': 'NUMBER', 'default': 0},
    {'name': 'p_req2', 'type': 'DATE', 'default': None}
])

# For case insensitivity tests
cand_proc_case = MockPLSQLCodeObject("pkg.proc_case_v1", "proc_case", "pkg", [
    {'name': 'ParamOne', 'type': 'NUMBER', 'default': None},
    {'name': 'paramTwo', 'type': 'VARCHAR2', 'default': 'two'}
])

# Candidates from the example in overload_resolver.py
ex_cand1_params = [
    {'name': 'p_text', 'type': 'VARCHAR2', 'default': None},
    {'name': 'p_num', 'type': 'NUMBER', 'default': 100}
]
ex_candidate1 = MockPLSQLCodeObject("pkg.proc_ex_v1", "proc", "pkg", ex_cand1_params)

ex_cand2_params = [
    {'name': 'p_text', 'type': 'VARCHAR2', 'default': None}
]
ex_candidate2 = MockPLSQLCodeObject("pkg.proc_ex_v2", "proc", "pkg", ex_cand2_params)

# Note: Original example had id="pkg.proc_v3_data", name="proc". Call is "pkg.proc".
# This candidate will be considered if candidate.name is "proc" and candidate.package_name is "pkg".
ex_cand3_params = [
    {'name': 'p_data', 'type': 'VARCHAR2', 'default': None},
]
ex_candidate3 = MockPLSQLCodeObject("pkg.proc_ex_v3_data", "proc", "pkg", ex_cand3_params)

# Note: Original example had id="pkg.proc_v4_defaults", name="proc".
ex_cand4_params = [
    {'name': 'p_a', 'type': 'NUMBER', 'default': 1},
    {'name': 'p_b', 'type': 'NUMBER', 'default': 2},
]
ex_candidate4 = MockPLSQLCodeObject("pkg.proc_ex_v4_defaults", "proc", "pkg", ex_cand4_params)

example_candidates_set = [ex_candidate1, ex_candidate2, ex_candidate3, ex_candidate4]


all_test_candidates = [
    cand_proc1_p1, cand_proc1_p2, cand_proc1_p3,
    cand_proc_no_params, cand_proc_all_defaults,
    cand_proc_mixed_order, cand_proc_case
]

# Test Cases
@pytest.mark.parametrize("test_name, candidates, call_details, expected_id, description", [
    # Basic Scenarios
    ("Exact match (positional)", [cand_proc1_p2], MockCallDetailsTuple("pkg.proc", 1,0,0, ['val_a'], {}), "pkg.proc_v2", "Exact positional match."),
    ("Exact match (named)", [cand_proc1_p2], MockCallDetailsTuple("pkg.proc", 1,0,0, [], {'p_a': 'val_a'}), "pkg.proc_v2", "Exact named match."),
    ("Match with default (positional)", [cand_proc1_p1], MockCallDetailsTuple("pkg.proc", 1,0,0, ['val_a'], {}), "pkg.proc_v1", "Positional match using a default for the second param."),
    ("Match with default (named)", [cand_proc1_p1], MockCallDetailsTuple("pkg.proc", 1,0,0, [], {'p_a': 'val_a'}), "pkg.proc_v1", "Named match using a default for the second param."),
    ("Full match (all params provided, positional)", [cand_proc1_p1], MockCallDetailsTuple("pkg.proc", 1,0,0, ['val_a', 'val_b'], {}), "pkg.proc_v1", "All params provided positionally."),
    ("Full match (all params provided, named)", [cand_proc1_p1], MockCallDetailsTuple("pkg.proc", 1,0,0, [], {'p_a': 'val_a', 'p_b': 'val_b'}), "pkg.proc_v1", "All params provided by name."),
    ("Full match (all params provided, mixed)", [cand_proc1_p1], MockCallDetailsTuple("pkg.proc", 1,0,0, ['val_a'], {'p_b': 'val_b'}), "pkg.proc_v1", "All params provided, mixed positional and named."),

    # No Candidates
    ("No candidates", [], MockCallDetailsTuple("pkg.proc", 1,0,0, ['val_a'], {}), None, "No candidates provided."),

    # No Parameters
    ("Call with no params, candidate with no params", [cand_proc_no_params], MockCallDetailsTuple("pkg.proc_no_params", 1,0,0, [], {}), "pkg.proc_no_params_v1", "Successful call to a procedure with no parameters."),
    ("Call with params, candidate with no params", [cand_proc_no_params], MockCallDetailsTuple("pkg.proc_no_params", 1,0,0, ['val_a'], {}), None, "Call with positional arg to a no-param procedure."),
    ("Call with named params, candidate with no params", [cand_proc_no_params], MockCallDetailsTuple("pkg.proc_no_params", 1,0,0, [], {'p_a':'val_a'}), None, "Call with named arg to a no-param procedure."),

    # All Defaults
    ("Call with no params, candidate with all defaults", [cand_proc_all_defaults], MockCallDetailsTuple("pkg.proc_all_defaults", 1,0,0, [], {}), "pkg.proc_all_defaults_v1", "Call to proc with all defaults, no args given."),
    ("Call with some params (pos), candidate with all defaults", [cand_proc_all_defaults], MockCallDetailsTuple("pkg.proc_all_defaults", 1,0,0, [10], {}), "pkg.proc_all_defaults_v1", "Call to proc with all defaults, first arg given positionally."),
    ("Call with some params (named), candidate with all defaults", [cand_proc_all_defaults], MockCallDetailsTuple("pkg.proc_all_defaults", 1,0,0, [], {'p_d': 'new_d'}), "pkg.proc_all_defaults_v1", "Call to proc with all defaults, second arg given by name."),

    # Case Insensitivity for Named Parameters
    ("Named param case insensitivity (lowercase call)", [cand_proc_case], MockCallDetailsTuple("pkg.proc_case", 1,0,0, [], {'paramone': 123}), "pkg.proc_case_v1", "Named param 'ParamOne' called as 'paramone'."),
    ("Named param case insensitivity (uppercase call for mixed case param)", [cand_proc_case], MockCallDetailsTuple("pkg.proc_case", 1,0,0, [123], {'PARAMTWO': 'new_val'}), "pkg.proc_case_v1", "Named param 'paramTwo' called as 'PARAMTWO'."),
    ("Named param case insensitivity (mixed call)", [cand_proc_case], MockCallDetailsTuple("pkg.proc_case", 1,0,0, [], {'ParamOne': 1, 'paramtwo': 'val'}), "pkg.proc_case_v1", "Named params with mixed casing in call."),

    # Ambiguity
    ("Ambiguous: two candidates match (pos)", [cand_proc1_p1, cand_proc1_p2], MockCallDetailsTuple("pkg.proc", 1,0,0, ['val_a'], {}), None, "Ambiguous: cand1 (p_a, p_b default) and cand2 (p_a) both match positional call."),
    ("Ambiguous: two candidates match (named)", [cand_proc1_p1, cand_proc1_p2], MockCallDetailsTuple("pkg.proc", 1,0,0, [], {'p_a': 'val_a'}), None, "Ambiguous: cand1 (p_a, p_b default) and cand2 (p_a) both match named call."),
    
    # Unambiguous due to required parameters
    ("Unambiguous: one requires more params (pos)", [cand_proc1_p1, cand_proc1_p2], MockCallDetailsTuple("pkg.proc", 1,0,0, ['val_a', 'val_b'], {}), "pkg.proc_v1", "Unambiguous: cand1 matches with two positional args, cand2 does not."),
    ("Unambiguous: one requires more params (named)", [cand_proc1_p1, cand_proc1_p2], MockCallDetailsTuple("pkg.proc", 1,0,0, [], {'p_a': 'val_a', 'p_b': 'val_b'}), "pkg.proc_v1", "Unambiguous: cand1 matches with two named args, cand2 does not."),

    # Mismatch Scenarios
    ("Mismatch: too many positional args", [cand_proc1_p2], MockCallDetailsTuple("pkg.proc", 1,0,0, ['val_a', 'val_b'], {}), None, "Too many positional arguments for cand_proc1_p2."),
    ("Mismatch: unknown named parameter", [cand_proc1_p2], MockCallDetailsTuple("pkg.proc", 1,0,0, [], {'p_x': 'val_x'}), None, "Unknown named parameter 'p_x' for cand_proc1_p2."),
    ("Mismatch: required param not supplied", [cand_proc1_p3], MockCallDetailsTuple("pkg.proc", 1,0,0, [], {}), None, "Required parameter 'p_x' for cand_proc1_p3 not supplied."),
    
    # Mixed positional and named arguments
    ("Mixed args: positional then named, valid", [cand_proc_mixed_order], MockCallDetailsTuple("pkg.proc_mixed_order", 1,0,0, ["req1_val"], {'p_req2': "date_val"}), "pkg.proc_mixed_order_v1", "p_req1 by pos, p_opt1 default, p_req2 by name."),
    ("Mixed args: positional fills optional, then named for required", [cand_proc_mixed_order], MockCallDetailsTuple("pkg.proc_mixed_order", 1,0,0, ["req1_val", 99], {'p_req2': "date_val"}), "pkg.proc_mixed_order_v1", "p_req1, p_opt1 by pos, p_req2 by name."),

    # # TODO
    # ("Mixed args: named arg supplied that would have been taken by positional", [cand_proc1_p1], MockCallDetailsTuple("pkg.proc", 1,0,0, ["pos_val_for_a"], {'p_a': "named_val_for_a"}), None, "Named arg p_a supplied, but also a positional arg that would map to p_a. This is invalid PL/SQL but current resolver might allow if named processed first."),
    # The above test case "Mixed args: named arg supplied that would have been taken by positional" is tricky.
    # PL/SQL itself would raise an error if a parameter is effectively supplied twice.
    # Current resolver logic: named args mark params as '_supplied'. Then positional args fill remaining unsupplied.
    # If p_a is supplied by name, the first positional arg would then try to map to p_b.
    # Let's refine this test to check correct mapping:
    ("Mixed args: named arg for later param, positional for earlier", [cand_proc1_p1], MockCallDetailsTuple("pkg.proc", 1,0,0, ["val_for_pa"], {'p_b': "val_for_pb"}), "pkg.proc_v1", "p_a by pos, p_b by name. Valid."),

    # Edge cases with defaults and supplied values
    ("Supplied value for param with default", [cand_proc1_p1], MockCallDetailsTuple("pkg.proc", 1,0,0, [], {'p_a': 'val_a', 'p_b': 'override_default_b'}), "pkg.proc_v1", "Value supplied for p_b, overriding its default."),
    
    # More complex ambiguity
    # Cand A: (p1, p2 def)
    # Cand B: (p1)
    # Cand C: (p1, p2, p3 def)
    # Call (val1) -> Ambiguous A, B. C fails (needs p2).
    # Call (val1, val2) -> A matches. C matches (p3 default). Ambiguous.
    # Call (val1, val2, val3) -> C matches.
    (
        "Complex Ambiguity 1", 
        [
            MockPLSQLCodeObject("complex.vA", "complex", "pkg", [{'name':'p1', 'default':None}, {'name':'p2', 'default':'def2'}]),
            MockPLSQLCodeObject("complex.vB", "complex", "pkg", [{'name':'p1', 'default':None}]),
            MockPLSQLCodeObject("complex.vC", "complex", "pkg", [{'name':'p1', 'default':None}, {'name':'p2', 'default':None}, {'name':'p3', 'default':'def3'}])
        ], 
        MockCallDetailsTuple("complex.proc", 1,0,0, ["v1"], {}), 
        None, # Expect ambiguity between vA and vB
        "Call with one arg, matches vA (p2 default) and vB. vC needs p2."
    ),
    (
        "Complex Ambiguity 2", 
        [
            MockPLSQLCodeObject("complex.vA", "complex", "pkg", [{'name':'p1', 'default':None}, {'name':'p2', 'default':'def2'}]),
            MockPLSQLCodeObject("complex.vB", "complex", "pkg", [{'name':'p1', 'default':None}]), # vB won't match
            MockPLSQLCodeObject("complex.vC", "complex", "pkg", [{'name':'p1', 'default':None}, {'name':'p2', 'default':None}, {'name':'p3', 'default':'def3'}])
        ], 
        MockCallDetailsTuple("complex.proc", 1,0,0, ["v1", "v2"], {}), 
        None, # Expect ambiguity between vA and vC
        "Call with two args, matches vA and vC (p3 default)."
    ),
    (
        "Complex Unambiguous", 
        [
            MockPLSQLCodeObject("complex.vA", "complex", "pkg", [{'name':'p1', 'default':None}, {'name':'p2', 'default':'def2'}]),
            MockPLSQLCodeObject("complex.vB", "complex", "pkg", [{'name':'p1', 'default':None}]),
            MockPLSQLCodeObject("complex.vC", "complex", "pkg", [{'name':'p1', 'default':None}, {'name':'p2', 'default':None}, {'name':'p3', 'default':'def3'}])
        ], 
        MockCallDetailsTuple("complex.proc", 1,0,0, ["v1", "v2", "v3"], {}), 
        "complex.vC", # Only vC matches
        "Call with three args, only vC matches."
    ),
     (
        "Named args out of order",
        [cand_proc1_p1],
        MockCallDetailsTuple("pkg.proc", 1,0,0, [], {'p_b': 'val_b', 'p_a': 'val_a'}),
        "pkg.proc_v1",
        "Named arguments provided in a different order than defined."
    ),
    (
        "Fewer positional args than a candidate that has defaults for the remainder",
        [cand_proc_mixed_order], # (p_req1, p_opt1 def 0, p_req2)
        MockCallDetailsTuple("pkg.proc_mixed_order", 1,0,0, ["val_req1"], {}),
        None, # Fails because p_req2 is not supplied and has no default
        "Call with only first of three args, second has default, third is required but not supplied."
    ),
     (
        "Positional argument after a named argument (Not directly testable here, as CallDetailsTuple pre-sorts)",
        # This scenario depends on how CallDetailsTuple is constructed.
        # If mixed mode (pos then named) is enforced by parser, this is fine.
        # If CallDetailsTuple could represent `(named_arg=X, pos_arg)`, PL/SQL forbids it.
        # The resolver itself doesn't see the original call string order, only the parsed CallDetailsTuple.
        # Assuming CallDetailsTuple correctly represents a valid PL/SQL call structure.
        [cand_proc1_p1],
        MockCallDetailsTuple("pkg.proc", 1,0,0, ["val_for_a"], {'p_b': "val_for_b"}), # This is fine: pos, then named
        "pkg.proc_v1",
        "Standard mixed: positional followed by named."
    ),

    # === Tests converted from overload_resolver.py example ===
    (
        "Example TC1: Ambiguous match with one positional arg",
        example_candidates_set,
        MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=['hello_world'], named_params={}),
        None,
        "Example TC1: Call ('hello_world') matches ex_cand1, ex_cand2, ex_cand3, and ex_cand4, leading to ambiguity."
    ),
    ("Example TC2: Ambiguous (ex_cand1 default vs ex_cand2 exact pos)", example_candidates_set, MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=['test_text'], named_params={}), None, "Example TC2: Ambiguous between ex_cand1 (p_num default) and ex_cand2 (exact positional)"),
    ("Example TC3: Ambiguous (ex_cand1 default vs ex_cand2 exact named)", example_candidates_set, MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=[], named_params={'p_text': 'named_text'}), None, "Example TC3: Ambiguous between ex_cand1 (p_num default) and ex_cand2 (exact named)"),
    ("Example TC4: Match for ex_cand1 (all params named)", example_candidates_set, MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=[], named_params={'p_text': 'full', 'p_num': '123'}), ex_candidate1.id, "Example TC4: Match for ex_cand1 (all params named)"),
    ("Example TC5: No match (wrong named parameter)", example_candidates_set, MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=[], named_params={'p_wrong_name': 'test'}), None, "Example TC5: No match (wrong named parameter)"),
    ("Example TC6: No match (too many positional arguments)", example_candidates_set, MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=['arg1', 'arg2', 'arg3'], named_params={}), None, "Example TC6: No match (too many positional arguments)"),
    ("Example TC7: Match ex_cand4 by all defaults (call with no args)", example_candidates_set, MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=[], named_params={}), ex_candidate4.id, "Example TC7: Match ex_cand4 by all defaults. ex_cand1 and ex_cand2 require p_text."),
    ("Example TC8: Positional then named for ex_cand1", example_candidates_set, MockCallDetailsTuple("pkg.proc", 1, 0, 0, positional_params=['pos_text'], named_params={'p_num': '99'}), ex_candidate1.id, "Example TC8: Positional then named for ex_cand1"),
    # === End of tests converted from example ===

])
def test_resolve_overloaded_call(
    test_name: str,
    candidates: List[MockPLSQLCodeObject],
    call_details: MockCallDetailsTuple,
    expected_id: Optional[str],
    description: str,
    da_test_logger # Fixture from dependency_analyzer/tests/conftest.py
):
    """
    Tests various scenarios for resolve_overloaded_call.
    """
    da_test_logger.info(f"Running test: {test_name} - {description}")
    
    # Filter all_test_candidates to only include those whose IDs are in the `candidates` list for this param set,
    # or use the candidates directly if they are fully formed MockPLSQLCodeObject instances.
    active_candidates: List[MockPLSQLCodeObject]
    if all(isinstance(c, str) for c in candidates): # If candidates are specified by ID
        name_to_object = {obj.id: obj for obj in all_test_candidates}
        active_candidates = [name_to_object[id_] for id_ in candidates if id_ in name_to_object]
    else: # If candidates are direct MockPLSQLCodeObject instances
        active_candidates = candidates

    resolved_obj = resolve_overloaded_call(active_candidates, call_details, da_test_logger)

    if expected_id is None:
        assert resolved_obj is None, f"{test_name}: Expected no resolution (None), but got {resolved_obj.id if resolved_obj else 'None'}"
    else:
        assert resolved_obj is not None, f"{test_name}: Expected resolution to {expected_id}, but got None"
        assert resolved_obj.id == expected_id, f"{test_name}: Expected {expected_id}, but got {resolved_obj.id}"


from __future__ import annotations
import pytest
import networkx as nx
import loguru as lg
from typing import List, Dict, Any

from dependency_analyzer.builder.graph_constructor import GraphConstructor
from plsql_analyzer.core.code_object import PLSQL_CodeObject, CodeObjectType
from plsql_analyzer.parsing.call_extractor import CallDetailsTuple
# Assuming conftest.py with da_test_logger is in ../../conftest.py or discoverable by pytest

# --- Mocks & Test Data ---

class MockPLSQLCodeObject(PLSQL_CodeObject):
    # Override init to allow easier mock creation if PLSQL_CodeObject has complex setup
    def __init__(
        self,
        name: str,
        package_name: str | None,
        type: CodeObjectType,
        clean_code: str | None = "BEGIN null; END;", # Default clean_code
        parsed_parameters: List[Dict[str, Any]] | None = None,
        extracted_calls: List[CallDetailsTuple] | None = None,
        overloaded: bool = False,
        id: str | None = None,
        **kwargs
    ):
        super().__init__(name=name, package_name=package_name, type=type, clean_code=clean_code, **kwargs)
        # Override fields after super init for test purposes
        self.parsed_parameters = parsed_parameters if parsed_parameters is not None else []
        self.extracted_calls = extracted_calls if extracted_calls is not None else []
        self.overloaded = overloaded
        if id: # Allow explicit ID setting for predictable test outcomes
            self.id = id
        else: # Ensure ID is generated if not provided
            self.generate_id()

    # Helper to easily add a call
    def add_call(self, call_name: str, line_no: int = 1, pos_params: List[str] | None = None, named_params: Dict[str, str] | None = None):
        if self.extracted_calls is None:
            self.extracted_calls = []
        self.extracted_calls.append(
            CallDetailsTuple(
                call_name=call_name,
                line_no=line_no,
                start_idx=0, # Dummy value
                end_idx=0,   # Dummy value
                positional_params=pos_params if pos_params is not None else [],
                named_params=named_params if named_params is not None else {}
            )
        )

# --- Fixtures ---

@pytest.fixture
def basic_code_objects() -> List[MockPLSQLCodeObject]:
    obj1 = MockPLSQLCodeObject(name="proc1", package_name="pkg1", type=CodeObjectType.PROCEDURE, id="pkg1.proc1")
    obj2 = MockPLSQLCodeObject(name="proc2", package_name="pkg1", type=CodeObjectType.PROCEDURE, id="pkg1.proc2")
    obj3 = MockPLSQLCodeObject(name="func1", package_name="pkg2", type=CodeObjectType.FUNCTION, id="pkg2.func1")
    obj1.add_call("pkg1.proc2")
    obj2.add_call("pkg2.func1")
    return [obj1, obj2, obj3]

@pytest.fixture
def overloaded_code_objects() -> List[MockPLSQLCodeObject]:
    # Caller
    caller = MockPLSQLCodeObject(name="caller_proc", package_name="pkg_over", type=CodeObjectType.PROCEDURE, id="pkg_over.caller_proc")

    # Overloaded candidates for "over_proc"
    over_proc_v1 = MockPLSQLCodeObject(
        name="over_proc", package_name="pkg_over", type=CodeObjectType.PROCEDURE, overloaded=True,
        parsed_parameters=[{'name': 'p_text', 'type': 'VARCHAR2', 'default': None}],
        id="pkg_over.over_proc_v1_sig" # Predictable ID
    )
    over_proc_v2 = MockPLSQLCodeObject(
        name="over_proc", package_name="pkg_over", type=CodeObjectType.PROCEDURE, overloaded=True,
        parsed_parameters=[
            {'name': 'p_num', 'type': 'NUMBER', 'default': None},
            {'name': 'p_flag', 'type': 'BOOLEAN', 'default': True}
        ],
        id="pkg_over.over_proc_v2_sig" # Predictable ID
    )
    # Another overloaded procedure in a different package or standalone
    other_over_proc = MockPLSQLCodeObject(
        name="another_over", package_name=None, type=CodeObjectType.PROCEDURE, overloaded=True,
        parsed_parameters=[{'name': 'p_date', 'type': 'DATE'}],
        id="another_over_v1_sig"
    )
    # Calls from caller_proc
    caller.add_call("pkg_over.over_proc", named_params={"p_text": "some_text_val"}) # Should match v1
    caller.add_call("pkg_over.over_proc")  # Should ambiguous and match both v1 and v2
    caller.add_call("pkg_over.over_proc", pos_params=["text_for_v1", "extra_param"]) # Should be un-ambiguous and match for existing v2
    caller.add_call("another_over", pos_params=["SYSDATE"]) # Should match another_over_v1

    return [caller, over_proc_v1, over_proc_v2, other_over_proc]


# --- Test Cases ---
def test_graph_constructor_empty_input(da_test_logger: lg.Logger):
    constructor = GraphConstructor(code_objects=[], logger=da_test_logger)
    graph, out_of_scope = constructor.build_graph()
    assert isinstance(graph, nx.DiGraph)
    assert graph.number_of_nodes() == 0
    assert graph.number_of_edges() == 0
    assert len(out_of_scope) == 0

def test_graph_constructor_nodes_only(da_test_logger: lg.Logger):
    obj_no_calls1 = MockPLSQLCodeObject(name="proc_a", package_name="pkg_a", type=CodeObjectType.PROCEDURE, id="pkg_a.proc_a")
    obj_no_calls2 = MockPLSQLCodeObject(name="func_b", package_name="pkg_b", type=CodeObjectType.FUNCTION, id="pkg_b.func_b")
    objects = [obj_no_calls1, obj_no_calls2]
    constructor = GraphConstructor(code_objects=objects, logger=da_test_logger)
    graph, out_of_scope = constructor.build_graph()

    assert graph.number_of_nodes() == 2
    assert "pkg_a.proc_a" in graph
    assert "pkg_b.func_b" in graph
    assert graph.number_of_edges() == 0
    assert len(out_of_scope) == 0

def test_simple_direct_call(basic_code_objects, da_test_logger):
    constructor = GraphConstructor(code_objects=basic_code_objects, logger=da_test_logger)
    graph, out_of_scope = constructor.build_graph()

    assert graph.number_of_nodes() == 3
    assert graph.has_node("pkg1.proc1")
    assert graph.has_node("pkg1.proc2")
    assert graph.has_node("pkg2.func1")

    assert graph.number_of_edges() == 2
    assert graph.has_edge("pkg1.proc1", "pkg1.proc2")
    assert graph.has_edge("pkg1.proc2", "pkg2.func1")
    assert len(out_of_scope) == 0

def test_package_local_call_resolution(da_test_logger: lg.Logger):
    # pkg_x.proc_alpha calls proc_beta (which is pkg_x.proc_beta)
    # pkg_y.proc_beta exists but should not be chosen
    obj_xa = MockPLSQLCodeObject(name="proc_alpha", package_name="pkg_x", type=CodeObjectType.PROCEDURE, id="pkg_x.proc_alpha")
    obj_xb = MockPLSQLCodeObject(name="proc_beta", package_name="pkg_x", type=CodeObjectType.PROCEDURE, id="pkg_x.proc_beta")
    obj_yb = MockPLSQLCodeObject(name="proc_beta", package_name="pkg_y", type=CodeObjectType.PROCEDURE, id="pkg_y.proc_beta") # Same simple name, diff package

    obj_xa.add_call("proc_beta") # Call is not fully qualified

    objects = [obj_xa, obj_xb, obj_yb]
    constructor = GraphConstructor(code_objects=objects, logger=da_test_logger)
    graph, out_of_scope = constructor.build_graph()

    assert graph.has_edge("pkg_x.proc_alpha", "pkg_x.proc_beta")
    assert not graph.has_edge("pkg_x.proc_alpha", "pkg_y.proc_beta")
    assert len(out_of_scope) == 0

def test_out_of_scope_call_creates_placeholder(da_test_logger: lg.Logger):
    obj1 = MockPLSQLCodeObject(name="caller", package_name="mypkg", type=CodeObjectType.PROCEDURE, id="mypkg.caller")
    obj1.add_call("external_pkg.non_existent_proc")
    obj1.add_call("completely_unknown_proc") # Non-qualified

    constructor = GraphConstructor(code_objects=[obj1], logger=da_test_logger)
    graph, out_of_scope = constructor.build_graph()

    assert graph.number_of_nodes() == 2 # caller + one placeholder for qualified call
    assert graph.has_node("mypkg.caller")
    assert graph.has_node("external_pkg.non_existent_proc") # Placeholder for qualified
    
    # Check placeholder node attributes in structure-only mode
    placeholder_node_data = graph.nodes["external_pkg.non_existent_proc"]
    assert placeholder_node_data['name'] == "non_existent_proc"
    assert placeholder_node_data['package_name'] == "external_pkg"
    assert placeholder_node_data['type'] == "UNKNOWN"

    assert graph.has_edge("mypkg.caller", "external_pkg.non_existent_proc")
    
    # Check out_of_scope_calls set
    assert "external_pkg.non_existent_proc" in out_of_scope
    assert "completely_unknown_proc" in out_of_scope # Non-qualified unknown is also out of scope

def test_self_loop_skipped(da_test_logger: lg.Logger):
    obj_self = MockPLSQLCodeObject(name="self_caller", package_name="pkg_self", type=CodeObjectType.PROCEDURE, id="pkg_self.self_caller")
    obj_self.add_call("pkg_self.self_caller") # Calls itself

    constructor = GraphConstructor(code_objects=[obj_self], logger=da_test_logger)
    graph, _ = constructor.build_graph()
    assert graph.number_of_nodes() == 1
    assert graph.number_of_edges() == 0 # No self-loop edge


# --- Tests for _register_globally (and its interaction with _initialize_lookup_structures) ---

def test_register_globally_packaged_object_fqn_only(da_test_logger: lg.Logger):
    """Test that only FQN of packaged objects are registered globally."""
    obj_pkg = MockPLSQLCodeObject(name="proc1", package_name="pkg1", type=CodeObjectType.PROCEDURE)
    constructor = GraphConstructor(code_objects=[obj_pkg], logger=da_test_logger)
    constructor._initialize_lookup_structures() # This calls _register_globally internally

    assert "pkg1.proc1" in constructor._code_object_call_names
    assert constructor._code_object_call_names["pkg1.proc1"] == obj_pkg
    assert "proc1" not in constructor._code_object_call_names # Simple name of packaged obj NOT global
    da_test_logger.info("Passed: test_register_globally_packaged_object_fqn_only")

def test_register_globally_non_packaged_object_simple_name(da_test_logger: lg.Logger):
    """Test that simple name of non-packaged (global) objects are registered globally."""
    obj_global = MockPLSQLCodeObject(name="global_proc", package_name=None, type=CodeObjectType.PROCEDURE)
    constructor = GraphConstructor(code_objects=[obj_global], logger=da_test_logger)
    constructor._initialize_lookup_structures()

    assert "global_proc" in constructor._code_object_call_names
    assert constructor._code_object_call_names["global_proc"] == obj_global
    da_test_logger.info("Passed: test_register_globally_non_packaged_object_simple_name")

def test_register_globally_conflict_normal_vs_overloaded(da_test_logger: lg.Logger):
    """Test conflict when a normal and overloaded object share a global call name."""
    obj_normal = MockPLSQLCodeObject(name="conflict_proc", package_name=None, type=CodeObjectType.PROCEDURE, id="normal_conflict")
    obj_overload = MockPLSQLCodeObject(name="conflict_proc", package_name=None, type=CodeObjectType.PROCEDURE, overloaded=True, id="overload_conflict")
    
    # Order 1: Normal then Overloaded
    constructor1 = GraphConstructor(code_objects=[obj_normal, obj_overload], logger=da_test_logger)
    constructor1._initialize_lookup_structures()
    assert "conflict_proc" in constructor1._skip_call_names
    assert "conflict_proc" not in constructor1._code_object_call_names
    assert "conflict_proc" not in constructor1._overloaded_code_object_call_names

    # Order 2: Overloaded then Normal
    constructor2 = GraphConstructor(code_objects=[obj_overload, obj_normal], logger=da_test_logger)
    constructor2._initialize_lookup_structures()
    assert "conflict_proc" in constructor2._skip_call_names
    assert "conflict_proc" not in constructor2._code_object_call_names
    assert "conflict_proc" not in constructor2._overloaded_code_object_call_names
    da_test_logger.info("Passed: test_register_globally_conflict_normal_vs_overloaded")

def test_register_globally_ambiguous_normal_objects(da_test_logger: lg.Logger):
    """Test ambiguity when two different normal objects would map to the same global call name."""
    obj1 = MockPLSQLCodeObject(name="amb_proc", package_name=None, type=CodeObjectType.PROCEDURE, id="amb1")
    obj2 = MockPLSQLCodeObject(name="amb_proc", package_name=None, type=CodeObjectType.PROCEDURE, id="amb2")
    constructor = GraphConstructor([obj1, obj2], da_test_logger)
    constructor._initialize_lookup_structures()

    assert "amb_proc" in constructor._skip_call_names
    assert "amb_proc" not in constructor._code_object_call_names
    da_test_logger.info("Passed: test_register_globally_ambiguous_normal_objects")

def test_register_globally_overloaded_set_correctly_formed(da_test_logger: lg.Logger):
    """Test that a set of overloaded objects is correctly formed under their FQN."""
    obj_o1 = MockPLSQLCodeObject(name="my_over", package_name="pkg_o", type=CodeObjectType.PROCEDURE, overloaded=True, parsed_parameters=[{'name':'p1'}], id="pkg_o.my_over_v1")
    obj_o2 = MockPLSQLCodeObject(name="my_over", package_name="pkg_o", type=CodeObjectType.PROCEDURE, overloaded=True, parsed_parameters=[{'name':'p2'}], id="pkg_o.my_over_v2")
    constructor = GraphConstructor([obj_o1, obj_o2], da_test_logger)
    constructor._initialize_lookup_structures()

    assert "pkg_o.my_over" in constructor._overloaded_code_object_call_names
    assert len(constructor._overloaded_code_object_call_names["pkg_o.my_over"]) == 2
    assert obj_o1 in constructor._overloaded_code_object_call_names["pkg_o.my_over"]
    assert obj_o2 in constructor._overloaded_code_object_call_names["pkg_o.my_over"]
    assert "my_over" not in constructor._overloaded_code_object_call_names # Simple name of packaged overload not global
    da_test_logger.info("Passed: test_register_globally_overloaded_set_correctly_formed")

# --- Tests for _initialize_lookup_structures (Validation Part) ---

def test_init_lookup_invalid_overload_set_reclassification(da_test_logger: lg.Logger):
    """Test reclassification of an 'overloaded' object that is alone."""
    # Marked overloaded but is the only one with this FQN
    obj_invalid_overload = MockPLSQLCodeObject(name="solo_over", package_name="pkg_val", type=CodeObjectType.PROCEDURE, overloaded=True, id="pkg_val.solo_over_invalid")
    constructor = GraphConstructor([obj_invalid_overload], da_test_logger)
    constructor._initialize_lookup_structures()

    assert "pkg_val.solo_over" not in constructor._overloaded_code_object_call_names # Should be removed
    assert "pkg_val.solo_over" in constructor._code_object_call_names     # Should be moved to normal
    assert constructor._code_object_call_names["pkg_val.solo_over"] == obj_invalid_overload
    da_test_logger.info("Passed: test_init_lookup_invalid_overload_set_reclassification")

def test_init_lookup_invalid_overload_reclassification_conflict(da_test_logger: lg.Logger):
    """Test conflict during reclassification of an invalid overload."""
    obj_invalid_overload = MockPLSQLCodeObject(name="reclass_conflict", package_name="pkg_rc", type=CodeObjectType.PROCEDURE, overloaded=True, id="pkg_rc.reclass_conflict_io")
    obj_normal_same_name = MockPLSQLCodeObject(name="reclass_conflict", package_name="pkg_rc", type=CodeObjectType.PROCEDURE, id="pkg_rc.reclass_conflict_normal")
    
    constructor = GraphConstructor([obj_invalid_overload, obj_normal_same_name], da_test_logger)
    constructor._initialize_lookup_structures()

    # The FQN "pkg_rc.reclass_conflict" should end up in _skip_call_names
    # because obj_invalid_overload (size 1 set) tries to move to normal, where obj_normal_same_name already exists for that FQN.
    assert "pkg_rc.reclass_conflict" in constructor._skip_call_names
    assert "pkg_rc.reclass_conflict" not in constructor._overloaded_code_object_call_names
    assert "pkg_rc.reclass_conflict" not in constructor._code_object_call_names
    da_test_logger.info("Passed: test_init_lookup_invalid_overload_reclassification_conflict")

# --- Tests for _initialize_lookup_structures ---
def test_lookup_initialization_basic(basic_code_objects, da_test_logger):
    constructor = GraphConstructor(code_objects=basic_code_objects, logger=da_test_logger)
    constructor._initialize_lookup_structures() # Call directly for focused test

    # Global names
    assert "pkg1.proc1" in constructor._code_object_call_names
    assert constructor._code_object_call_names["pkg1.proc1"].id == "pkg1.proc1"
    assert "proc1" not in constructor._code_object_call_names # Assuming proc1 alone is not globally unique if pkg1.proc1 exists
    
    # Check one level up package name
    assert "proc2" not in constructor._code_object_call_names # pkg1.proc2 exists
    assert "pkg1.proc2" in constructor._code_object_call_names

    # Package-wise names
    assert "pkg1" in constructor._package_wise_code_object_names
    assert "proc1" in constructor._package_wise_code_object_names["pkg1"]["normal"]
    assert constructor._package_wise_code_object_names["pkg1"]["normal"]["proc1"].id == "pkg1.proc1"

    assert "pkg2" in constructor._package_wise_code_object_names
    assert "func1" in constructor._package_wise_code_object_names["pkg2"]["normal"]
    assert constructor._package_wise_code_object_names["pkg2"]["normal"]["func1"].id == "pkg2.func1"

def test_lookup_ambiguous_non_overloaded_global(da_test_logger: lg.Logger):
    # obj_dup1 = MockPLSQLCodeObject(name="dup_proc", package_name="pkg_a", type=CodeObjectType.PROCEDURE, id="pkg_a.dup_proc")
    # obj_dup2 = MockPLSQLCodeObject(name="dup_proc", package_name="pkg_b", type=CodeObjectType.PROCEDURE, id="pkg_b.dup_proc") # Same simple name
    # This creates an ambiguous global name "dup_proc" if packages are not considered part of the shortest unique name
    # However, the current logic generates pkg_a.dup_proc, a.dup_proc, dup_proc and pkg_b.dup_proc, b.dup_proc, dup_proc
    # So "dup_proc" will be ambiguous.

    # Let's make it more direct:
    obj_gdup1 = MockPLSQLCodeObject(name="global_dup", package_name=None, type=CodeObjectType.PROCEDURE, id="global_dup_1")
    obj_gdup2 = MockPLSQLCodeObject(name="global_dup", package_name=None, type=CodeObjectType.PROCEDURE, id="global_dup_2")


    constructor = GraphConstructor(code_objects=[obj_gdup1, obj_gdup2], logger=da_test_logger)
    constructor._initialize_lookup_structures()

    assert "global_dup" in constructor._skip_call_names
    assert "global_dup" not in constructor._code_object_call_names
    assert "global_dup" not in constructor._overloaded_code_object_call_names

def test_lookup_conflict_non_overloaded_with_overloaded(da_test_logger: lg.Logger):
    obj_normal = MockPLSQLCodeObject(name="conflict_proc", package_name="pkg_c", type=CodeObjectType.PROCEDURE, id="pkg_c.conflict_proc_normal")
    obj_overload = MockPLSQLCodeObject(name="conflict_proc", package_name="pkg_c", type=CodeObjectType.PROCEDURE, overloaded=True, id="pkg_c.conflict_proc_overload")

    # Order matters for this test based on current implementation
    constructor1 = GraphConstructor(code_objects=[obj_normal, obj_overload], logger=da_test_logger)
    constructor1._initialize_lookup_structures()
    # If normal is processed first, then overloaded with same name, it should become skipped.
    # If overloaded is processed first, then normal with same name, it should become skipped.
    assert "pkg_c.conflict_proc" in constructor1._skip_call_names
    assert "pkg_c.conflict_proc" not in constructor1._code_object_call_names
    assert "pkg_c.conflict_proc" not in constructor1._overloaded_code_object_call_names

    constructor2 = GraphConstructor(code_objects=[obj_overload, obj_normal], logger=da_test_logger)
    constructor2._initialize_lookup_structures()
    assert "pkg_c.conflict_proc" in constructor2._skip_call_names
    assert "pkg_c.conflict_proc" not in constructor2._code_object_call_names
    assert "pkg_c.conflict_proc" not in constructor2._overloaded_code_object_call_names

# --- Tests for Overload Resolution Integration ---
def test_overloaded_call_successful_resolution(overloaded_code_objects, da_test_logger):
    constructor = GraphConstructor(code_objects=overloaded_code_objects, logger=da_test_logger)
    graph, out_of_scope = constructor.build_graph()

    caller_id = "pkg_over.caller_proc"
    over_proc_v1_id = "pkg_over.over_proc_v1_sig"
    over_proc_v2_id = "pkg_over.over_proc_v2_sig"
    another_over_id = "another_over_v1_sig"

    assert graph.has_edge(caller_id, over_proc_v1_id) # Call with pos_params=["some_text_val"]
    assert graph.has_edge(caller_id, over_proc_v2_id) # Call with pos_params=["text_for_v1", "extra_param"]
    assert graph.has_edge(caller_id, another_over_id) # Call with pos_params=["SYSDATE"]
    
    # The call ("pkg_over.over_proc", pos_params=["text_for_v1", "extra_param"]) should fail or be ambiguous
    # and thus added to out_of_scope
    failed_overload_call_sig = "pkg_over.over_proc (overloaded, resolution_failed: CallDetailsTuple(call_name='pkg_over.over_proc', line_no=1, start_idx=0, end_idx=0, positional_params=[], named_params={}))"
    assert any(failed_overload_call_sig.strip('"') in item for item in out_of_scope), f"Expected failed overload not in out_of_scope. Got: {out_of_scope}"

def test_overloaded_call_no_matching_signature(da_test_logger: lg.Logger):
    caller = MockPLSQLCodeObject(name="caller", package_name="pkg", type=CodeObjectType.PROCEDURE, id="pkg.caller")
    over_cand1 = MockPLSQLCodeObject(name="my_over_proc", package_name="pkg", type=CodeObjectType.PROCEDURE, overloaded=True,
                                   parsed_parameters=[{'name': 'p1', 'type': 'NUMBER'}], id="pkg.my_over_proc_num")
    over_cand2 = MockPLSQLCodeObject(name="my_over_proc", package_name="pkg", type=CodeObjectType.PROCEDURE, overloaded=True,
                                   parsed_parameters=[{'name': 'p2', 'type': 'NUMBER'}], id="pkg.my_over_proc_num")
    caller.add_call("pkg.my_over_proc", pos_params=[]) # No Param

    constructor = GraphConstructor(code_objects=[caller, over_cand1, over_cand2], logger=da_test_logger)
    _, out_of_scope = constructor.build_graph()
    
    expected_oos_detail = "CallDetailsTuple(call_name='pkg.my_over_proc', line_no=1, start_idx=0, end_idx=0, positional_params=[], named_params={})"
    expected_oos_entry_part = f"pkg.my_over_proc (overloaded, resolution_failed: {expected_oos_detail})"
    
    assert any(expected_oos_entry_part in item for item in out_of_scope), f"Expected unresolved overload not in out_of_scope. Got: {out_of_scope}"

def test_object_with_no_clean_code_handling(da_test_logger: lg.Logger):
    obj_no_code = MockPLSQLCodeObject(name="no_code_proc", package_name="pkg_test", type=CodeObjectType.PROCEDURE, clean_code=None, id="pkg_test.no_code_proc")
    # Add calls that would require parameter parsing if clean_code was present
    obj_no_code.add_call("some_pkg.some_overloaded_proc", pos_params=["arg1"]) 
    obj_no_code.add_call("another_call")

    # Add a potential target for the overloaded call to see it's not resolved
    target_overload = MockPLSQLCodeObject(name="some_overloaded_proc", package_name="some_pkg", type=CodeObjectType.PROCEDURE, overloaded=True,
                                          parsed_parameters=[{'name':'p1', 'type':'VARCHAR2'}], id="some_pkg.some_overloaded_proc_v1")


    constructor = GraphConstructor(code_objects=[obj_no_code, target_overload], logger=da_test_logger)
    graph, out_of_scope = constructor.build_graph()

    assert graph.number_of_nodes() == 2 # obj_no_code and target_overload
    assert not graph.has_edge("pkg_test.no_code_proc", "some_pkg.some_overloaded_proc_v1")
    
    # The calls should be added to out_of_scope with a specific reason
    assert "some_pkg.some_overloaded_proc (overloaded, source_unavailable)" in out_of_scope or \
           "some_pkg.some_overloaded_proc (source_unavailable_for_params)" in out_of_scope # Check for either log message variant
    
    # The non-overloaded call "another_call" will also be out of scope as it's not defined
    assert "another_call (source_unavailable_for_params)" in out_of_scope

def test_call_to_skipped_name(da_test_logger: lg.Logger):
    # Setup: global_dup1 and global_dup2 create an ambiguous "global_dup"
    obj_gdup1 = MockPLSQLCodeObject(name="global_dup", package_name=None, type=CodeObjectType.PROCEDURE, id="global_dup_1")
    obj_gdup2 = MockPLSQLCodeObject(name="global_dup", package_name=None, type=CodeObjectType.PROCEDURE, id="global_dup_2")
    
    caller = MockPLSQLCodeObject(name="caller_of_dup", package_name="any_pkg", type=CodeObjectType.PROCEDURE, id="any_pkg.caller_of_dup")
    caller.add_call("global_dup")

    constructor = GraphConstructor(code_objects=[obj_gdup1, obj_gdup2, caller], logger=da_test_logger)
    graph, out_of_scope = constructor.build_graph()

    assert "global_dup" in constructor._skip_call_names # Ensure it was skipped
    assert not graph.has_edge("any_pkg.caller_of_dup", "global_dup_1")
    assert not graph.has_edge("any_pkg.caller_of_dup", "global_dup_2")
    # The call 'global_dup' from caller_of_dup should be in out_of_scope because 'global_dup' is ambiguous
    assert "global_dup" in out_of_scope

def test_skip_ambiguous_intermediate_names_and_resolution(da_test_logger: lg.Logger):
    """
    When two non-overloaded objects share the same intermediate qualified name, it should be skipped
    and calls to that intermediate name become out-of-scope.
    """
    # Two procs in pkg.sub.proc with different IDs (same simple name -> same intermediate)
    obj1 = MockPLSQLCodeObject(name="proc", package_name="pkg.sub", type=CodeObjectType.PROCEDURE, id="pkg.sub.proc1")
    obj2 = MockPLSQLCodeObject(name="proc", package_name="pkg.sub", type=CodeObjectType.PROCEDURE, id="pkg.sub.proc2")
    constructor = GraphConstructor(code_objects=[obj1, obj2], logger=da_test_logger)
    constructor._initialize_lookup_structures()
    # Intermediate "sub.proc" under parent "pkg" should be marked ambiguous
    skip_set = constructor._skip_intermediate_names.get("pkg", set())
    assert "sub.proc" in skip_set
    # The intermediate should not be registered
    normal_map = constructor._package_wise_code_object_names.get("pkg", {}).get("normal", {})
    assert "sub.proc" not in normal_map

    # Now resolution: a caller in pkg calling "sub.proc" should not resolve
    caller = MockPLSQLCodeObject(name="caller", package_name="pkg", type=CodeObjectType.PROCEDURE, id="pkg.caller")
    caller.add_call("sub.proc")
    graph, out_of_scope = GraphConstructor(code_objects=[obj1, obj2, caller], logger=da_test_logger).build_graph()
    assert "sub.proc" in out_of_scope
    # No edge created for ambiguous intermediate
    assert not graph.has_edge("pkg.caller", "pkg.sub.proc1")
    assert not graph.has_edge("pkg.caller", "pkg.sub.proc2")

# --- Tests for build_graph (incorporating _resolve_and_add_dependencies_for_call) ---

def test_build_graph_empty(da_test_logger: lg.Logger):
    constructor = GraphConstructor([], da_test_logger)
    graph, out_of_scope = constructor.build_graph()
    assert graph.number_of_nodes() == 0 and graph.number_of_edges() == 0
    assert not out_of_scope

def test_build_graph_nodes_no_calls(da_test_logger: lg.Logger):
    obj1 = MockPLSQLCodeObject(name="p1", package_name="pkg", type=CodeObjectType.PROCEDURE)
    obj2 = MockPLSQLCodeObject(name="g1", package_name=None, type=CodeObjectType.FUNCTION)
    constructor = GraphConstructor([obj1, obj2], da_test_logger)
    graph, out_of_scope = constructor.build_graph()
    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 0
    assert obj1.id in graph and obj2.id in graph
    assert not out_of_scope

def test_build_graph_fqn_call_to_packaged_object(da_test_logger: lg.Logger):
    caller = MockPLSQLCodeObject(name="caller", package_name="pkg_a", type=CodeObjectType.PROCEDURE)
    target = MockPLSQLCodeObject(name="target", package_name="pkg_b", type=CodeObjectType.PROCEDURE)
    caller.add_call("pkg_b.target")
    constructor = GraphConstructor([caller, target], da_test_logger)
    graph, _ = constructor.build_graph()
    assert graph.has_edge(caller.id, target.id)
    da_test_logger.info("Passed: test_build_graph_fqn_call_to_packaged_object")

def test_build_graph_simple_call_within_same_package(da_test_logger: lg.Logger):
    caller = MockPLSQLCodeObject(name="caller", package_name="pkg_s", type=CodeObjectType.PROCEDURE)
    target = MockPLSQLCodeObject(name="local_target", package_name="pkg_s", type=CodeObjectType.PROCEDURE)
    caller.add_call("local_target") # Simple name call
    constructor = GraphConstructor([caller, target], da_test_logger)
    graph, _ = constructor.build_graph()
    assert graph.has_edge(caller.id, target.id)
    da_test_logger.info("Passed: test_build_graph_simple_call_within_same_package")

def test_build_graph_call_to_global_non_packaged_object(da_test_logger: lg.Logger):
    caller = MockPLSQLCodeObject(name="caller", package_name="pkg_g", type=CodeObjectType.PROCEDURE)
    target_global = MockPLSQLCodeObject(name="global_target", package_name=None, type=CodeObjectType.FUNCTION)
    caller.add_call("global_target")
    constructor = GraphConstructor([caller, target_global], da_test_logger)
    graph, _ = constructor.build_graph()
    assert graph.has_edge(caller.id, target_global.id)
    da_test_logger.info("Passed: test_build_graph_call_to_global_non_packaged_object")

def test_build_graph_contextual_fqn_resolution_normal(da_test_logger: lg.Logger):
    """Call 'sub.proc' from 'pkg' should resolve to 'pkg.sub.proc' if it exists globally."""
    caller = MockPLSQLCodeObject(name="main_proc", package_name="pkg", type=CodeObjectType.PROCEDURE)
    target = MockPLSQLCodeObject(name="proc", package_name="pkg.sub", type=CodeObjectType.PROCEDURE, id="pkg.sub.proc") # Target is pkg.sub.proc
    caller.add_call("sub.proc") # Call is relative-like
    constructor = GraphConstructor([caller, target], da_test_logger)
    graph, out_of_scope = constructor.build_graph()
    assert not out_of_scope, f"Out of scope calls: {out_of_scope}"
    assert graph.has_edge(caller.id, target.id)
    da_test_logger.info("Passed: test_build_graph_contextual_fqn_resolution_normal")

def test_build_graph_contextual_fqn_resolution_overloaded(da_test_logger: lg.Logger):
    """Call 'sub.over' from 'pkg' should resolve to 'pkg.sub.over' (overloaded set)."""
    caller = MockPLSQLCodeObject(name="main_proc", package_name="pkg", type=CodeObjectType.PROCEDURE)
    target_v1 = MockPLSQLCodeObject(name="over", package_name="pkg.sub", type=CodeObjectType.PROCEDURE, overloaded=True, parsed_parameters=[{'name':'p1'}], id="pkg.sub.over_v1")
    target_v2 = MockPLSQLCodeObject(name="over", package_name="pkg.sub", type=CodeObjectType.PROCEDURE, overloaded=True, parsed_parameters=[{'name':'p2'}], id="pkg.sub.over_v2")
    caller.add_call("sub.over", named_params={"p1": "val_for_p1"}) # This call should match target_v1
    
    constructor = GraphConstructor([caller, target_v1, target_v2], da_test_logger)
    graph, out_of_scope = constructor.build_graph()

    assert not out_of_scope, f"Out of scope calls: {out_of_scope}"
    assert graph.has_edge(caller.id, target_v1.id)
    assert not graph.has_edge(caller.id, target_v2.id)
    da_test_logger.info("Passed: test_build_graph_contextual_fqn_resolution_overloaded")

def test_build_graph_out_of_scope_and_placeholder(da_test_logger: lg.Logger):
    caller = MockPLSQLCodeObject(name="p", package_name="pkg", type=CodeObjectType.PROCEDURE)
    caller.add_call("unknown_pkg.unknown_proc") # Qualified out-of-scope
    caller.add_call("local_unknown")          # Unqualified out-of-scope
    constructor = GraphConstructor([caller], da_test_logger)
    graph, out_of_scope = constructor.build_graph()

    assert "unknown_pkg.unknown_proc" in out_of_scope
    assert "local_unknown" in out_of_scope
    assert graph.has_node("unknown_pkg.unknown_proc") # Placeholder created
    assert graph.nodes["unknown_pkg.unknown_proc"]['type'] == "UNKNOWN"
    assert graph.has_edge(caller.id, "unknown_pkg.unknown_proc")

def test_initialize_lookup_structures_intermediate_names(da_test_logger: lg.Logger):
    """
    Test that intermediate qualified names (e.g., 'sub.proc') are registered under parent package context.
    """
    # Object in nested package pkg.sub.proc
    nested_obj = MockPLSQLCodeObject(
        name="proc", package_name="pkg.sub", type=CodeObjectType.PROCEDURE, id="pkg.sub.proc"
    )
    constructor = GraphConstructor(code_objects=[nested_obj], logger=da_test_logger)
    constructor._initialize_lookup_structures()

    # Simple name under its own context
    assert "proc" in constructor._package_wise_code_object_names.get("pkg.sub", {}).get("normal", {})
    # Intermediate name under parent context
    parent_map = constructor._package_wise_code_object_names.get("pkg", {}).get("normal", {})
    assert "sub.proc" in parent_map, f"Expected 'sub.proc' in pkg.normal map, got {parent_map.keys()}"
    assert parent_map["sub.proc"].id == nested_obj.id

def test_intermediate_name_resolution(da_test_logger: lg.Logger):
    """
    Test resolution of calls using intermediate qualified names in package-local lookup.
    """
    # Caller in pkg, target in pkg.sub.proc
    
    caller = MockPLSQLCodeObject(name="main", package_name="pkg", type=CodeObjectType.PROCEDURE, id="pkg.main")
    target = MockPLSQLCodeObject(name="proc", package_name="pkg.sub", type=CodeObjectType.PROCEDURE, id="pkg.sub.proc")
    caller.add_call("sub.proc")  # Call using intermediate qualified name
    constructor = GraphConstructor(code_objects=[caller, target], logger=da_test_logger)
    graph, out_of_scope = constructor.build_graph()
    assert not out_of_scope, f"Intermediate name resolution failed, out_of_scope: {out_of_scope}"
    assert graph.has_edge(caller.id, target.id)

def test_build_graph_call_to_skipped_name_is_out_of_scope(da_test_logger: lg.Logger):
    # Setup a skipped name
    obj_gdup1 = MockPLSQLCodeObject(name="global_dup", package_name=None, type=CodeObjectType.PROCEDURE, id="global_dup_1")
    obj_gdup2 = MockPLSQLCodeObject(name="global_dup", package_name=None, type=CodeObjectType.PROCEDURE, id="global_dup_2")
    caller = MockPLSQLCodeObject(name="caller_of_dup", package_name="any_pkg", type=CodeObjectType.PROCEDURE)
    caller.add_call("global_dup")

    constructor = GraphConstructor([obj_gdup1, obj_gdup2, caller], da_test_logger)
    graph, out_of_scope = constructor.build_graph()

    assert "global_dup" in constructor._skip_call_names
    assert "global_dup" in out_of_scope # Call to skipped name becomes out-of-scope
    assert not graph.has_edge(caller.id, "global_dup_1")
    assert not graph.has_edge(caller.id, "global_dup_2")
    da_test_logger.info("Passed: test_build_graph_call_to_skipped_name_is_out_of_scope")

def test_build_graph_complex_overload_resolution(da_test_logger: lg.Logger):
    caller = MockPLSQLCodeObject(name="caller", package_name="app", type=CodeObjectType.PROCEDURE)
    
    # Target overloads for 'app.util.process_data'
    util_proc_v1 = MockPLSQLCodeObject(name="process_data", package_name="app.util", type=CodeObjectType.PROCEDURE, overloaded=True, parsed_parameters=[{'name':'p_text', 'type':'VARCHAR2'}], id="app.util.process_data_v1")
    util_proc_v2 = MockPLSQLCodeObject(name="process_data", package_name="app.util", type=CodeObjectType.PROCEDURE, overloaded=True, parsed_parameters=[{'name':'p_num', 'type':'NUMBER'}], id="app.util.process_data_v2")
    util_proc_v3 = MockPLSQLCodeObject(name="process_data", package_name="app.util", type=CodeObjectType.PROCEDURE, overloaded=True, parsed_parameters=[{'name':'p_date', 'type':'DATE', 'default':'SYSDATE'}], id="app.util.process_data_v3")

    # Calls
    caller.add_call("app.util.process_data", named_params={"p_text": "hello"})  # -> v1
    caller.add_call("app.util.process_data", named_params={"p_num": "123"}) # -> v2
    caller.add_call("app.util.process_data") # -> v3 (uses default)
    caller.add_call("app.util.process_data", pos_params=["true"]) # -> Ambiguous/failed (no boolean overload)

    constructor = GraphConstructor([caller, util_proc_v1, util_proc_v2, util_proc_v3], da_test_logger)
    graph, out_of_scope = constructor.build_graph()

    assert graph.has_edge(caller.id, util_proc_v1.id)
    assert graph.has_edge(caller.id, util_proc_v2.id)
    assert graph.has_edge(caller.id, util_proc_v3.id)
    
    failed_call_detail_str = "CallDetailsTuple(call_name='app.util.process_data', line_no=1, start_idx=0, end_idx=0, positional_params=['true'], named_params={})"
    expected_oos_entry = f"app.util.process_data (overloaded, resolution_failed: {failed_call_detail_str})"
    assert any(expected_oos_entry in item for item in out_of_scope), f"Expected failed overload not in out_of_scope. Got: {out_of_scope}"
    da_test_logger.info("Passed: test_build_graph_complex_overload_resolution")

# In test_graph_constructor.py
def test_global_suffix_match_resolution(da_test_logger: lg.Logger):
    """
    Test that a call using an abbreviated FQN suffix can be resolved globally.
    e.g., call 'sub_pkg.proc' resolves to 'main_pkg.sub_pkg.proc'.
    """
    target_obj = MockPLSQLCodeObject(
        name="proc", 
        package_name="main_pkg.sub_pkg", 
        type=CodeObjectType.PROCEDURE, 
        id="main_pkg.sub_pkg.proc"
    )
    caller_obj = MockPLSQLCodeObject(
        name="caller", 
        package_name="another_pkg", 
        type=CodeObjectType.PROCEDURE, 
        id="another_pkg.caller"
    )
    caller_obj.add_call("sub_pkg.proc") # Call using suffix

    constructor = GraphConstructor(code_objects=[target_obj, caller_obj], logger=da_test_logger)
    graph, out_of_scope = constructor.build_graph()

    assert not out_of_scope, f"Suffix match resolution failed, out_of_scope: {out_of_scope}"
    assert graph.has_edge(caller_obj.id, target_obj.id)
    da_test_logger.info("Passed: test_global_suffix_match_resolution")

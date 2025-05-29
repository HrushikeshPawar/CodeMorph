from __future__ import annotations
import pytest
import networkx as nx
from unittest.mock import Mock, patch
from typing import Optional

import loguru as lg

from dependency_analyzer.analysis.analyzer import analyze_cycles_enhanced, find_circular_dependencies

# Fixtures

@pytest.fixture
def mock_logger_fixture() -> Mock:
    return Mock(spec=lg.logger)

@pytest.fixture
def empty_graph() -> nx.DiGraph:
    return nx.DiGraph()

@pytest.fixture
def no_cycles_graph() -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_node("A", name="NodeA", type="PROCEDURE", package_name="PKG1")
    g.add_node("B", name="NodeB", type="FUNCTION", package_name="PKG1")
    g.add_node("C", name="NodeC", type="TABLE", package_name="PKG2")
    g.add_edges_from([("A", "B"), ("B", "C")])
    return g

@pytest.fixture
def simple_cycle_graph_fixture() -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_node("A", name="NodeA", type="PROCEDURE", package_name="PKG1", loc=10)
    g.add_node("B", name="NodeB", type="FUNCTION", package_name="PKG1", loc=20)
    g.add_node("C", name="NodeC", type="TABLE", package_name="PKG2", loc=0)
    g.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")]) # Cycle A->B->C->A
    return g

@pytest.fixture
def multiple_cycles_graph_fixture() -> nx.DiGraph:
    g = nx.DiGraph()
    # Cycle 1 (len 2): N1 <-> N2
    g.add_node("N1", name="NodeN1", type="P1", package_name="PKG_N")
    g.add_node("N2", name="NodeN2", type="P2", package_name="PKG_N")
    g.add_edges_from([("N1", "N2"), ("N2", "N1")])

    # Cycle 2 (len 3): N3 -> N4 -> N5 -> N3
    g.add_node("N3", name="NodeN3", type="P3", package_name="PKG_N")
    g.add_node("N4", name="NodeN4", type="P4", package_name="PKG_N")
    g.add_node("N5", name="NodeN5", type="P5", package_name="PKG_N")
    g.add_edges_from([("N3", "N4"), ("N4", "N5"), ("N5", "N3")])

    # Cycle 3 (len 4): N6 -> N7 -> N8 -> N9 -> N6
    g.add_node("N6", name="NodeN6", type="P6", package_name="PKG_N")
    g.add_node("N7", name="NodeN7", type="P7", package_name="PKG_N")
    g.add_node("N8", name="NodeN8", type="P8", package_name="PKG_N")
    g.add_node("N9", name="NodeN9", type="P9", package_name="PKG_N")
    g.add_edges_from([("N6", "N7"), ("N7", "N8"), ("N8", "N9"), ("N9", "N6")])
    
    # Some non-cycle nodes and edges
    g.add_node("X", name="NodeX", type="PX", package_name="PKG_X")
    g.add_edge("N1", "X")
    return g

@pytest.fixture
def overlapping_cycles_graph_fixture() -> nx.DiGraph:
    g = nx.DiGraph()
    # Cycle 1: A -> B -> C -> A
    # Cycle 2: B -> D -> E -> B
    g.add_node("A", name="NodeA", type="T1", package_name="P1")
    g.add_node("B", name="NodeB", type="T2", package_name="P1")
    g.add_node("C", name="NodeC", type="T3", package_name="P2")
    g.add_node("D", name="NodeD", type="T4", package_name="P2")
    g.add_node("E", name="NodeE", type="T5", package_name="P3")
    g.add_edges_from([("A", "B"), ("B", "C"), ("C", "A")])
    g.add_edges_from([("B", "D"), ("D", "E"), ("E", "B")])
    return g

# Test Cases

def test_analyze_cycles_empty_graph(empty_graph: nx.DiGraph, mock_logger_fixture: Mock):
    result = analyze_cycles_enhanced(empty_graph, mock_logger_fixture)
    assert result == []
    mock_logger_fixture.warning.assert_called_with("Graph is empty or None. Cannot analyze cycles.")

def test_analyze_cycles_no_cycles_graph(no_cycles_graph: nx.DiGraph, mock_logger_fixture: Mock):
    result = analyze_cycles_enhanced(no_cycles_graph, mock_logger_fixture)
    assert result == []
    # find_circular_dependencies (called internally) will log "No circular dependencies found."
    # analyze_cycles_enhanced will then log "No circular dependencies found."
    assert any("No circular dependencies found." in call.args[0] for call in mock_logger_fixture.info.call_args_list)


def test_analyze_cycles_simple_cycle_default_params(simple_cycle_graph_fixture: nx.DiGraph, mock_logger_fixture: Mock):
    result = analyze_cycles_enhanced(simple_cycle_graph_fixture, mock_logger_fixture)
    assert len(result) == 1
    cycle_info = result[0]
    assert cycle_info['cycle_id'] == 1
    assert sorted(cycle_info['nodes']) == sorted(["A", "B", "C"]) # Order may vary
    assert cycle_info['length'] == 3
    
    expected_complexity = sum(simple_cycle_graph_fixture.degree(node) for node in ["A", "B", "C"])
    assert cycle_info['complexity'] == expected_complexity
    
    # Path check needs to account for starting node variation
    assert cycle_info['cycle_path'].count("→") == 3
    for node in ["A", "B", "C"]:
        assert node in cycle_info['cycle_path']
    assert cycle_info['cycle_path'].endswith(f"→ {cycle_info['nodes'][0]}")

    assert 'node_details' not in cycle_info

def test_analyze_cycles_simple_cycle_include_node_details(simple_cycle_graph_fixture: nx.DiGraph, mock_logger_fixture: Mock):
    result = analyze_cycles_enhanced(simple_cycle_graph_fixture, mock_logger_fixture, include_node_details=True)
    assert len(result) == 1
    cycle_info = result[0]
    assert 'node_details' in cycle_info
    assert len(cycle_info['node_details']) == 3
    
    for detail in cycle_info['node_details']:
        assert detail['id'] in ["A", "B", "C"]
        node_data = simple_cycle_graph_fixture.nodes[detail['id']]
        assert detail['name'] == node_data['name']
        assert detail['type'] == node_data['type']
        assert detail['package'] == node_data['package_name']
        assert detail['in_degree'] == simple_cycle_graph_fixture.in_degree(detail['id'])
        assert detail['out_degree'] == simple_cycle_graph_fixture.out_degree(detail['id'])

@pytest.mark.parametrize("min_len, max_len, expected_lengths", [
    (3, None, {3, 4}),
    (None, 3, {2, 3}),
    (3, 3, {3}),
    (5, None, set()),
    (None, 1, set())
])
def test_analyze_cycles_length_filters(
    multiple_cycles_graph_fixture: nx.DiGraph, 
    mock_logger_fixture: Mock,
    min_len: Optional[int], 
    max_len: Optional[int], 
    expected_lengths: set
):
    result = analyze_cycles_enhanced(
        multiple_cycles_graph_fixture, 
        mock_logger_fixture, 
        min_cycle_length=min_len, 
        max_cycle_length=max_len
    )
    
    result_lengths = {cycle['length'] for cycle in result}
    assert result_lengths == expected_lengths
    if not expected_lengths:
         assert any("No circular dependencies found." in call.args[0] for call in mock_logger_fixture.info.call_args_list) or \
                any("Found 0 cycles after filtering" in call.args[0] for call in mock_logger_fixture.info.call_args_list)


def test_analyze_cycles_sort_by_length(multiple_cycles_graph_fixture: nx.DiGraph, mock_logger_fixture: Mock):
    result = analyze_cycles_enhanced(multiple_cycles_graph_fixture, mock_logger_fixture, sort_by="length")
    assert len(result) == 3 # Cycles of length 2, 3, 4
    assert [r['length'] for r in result] == [2, 3, 4]

def test_analyze_cycles_sort_by_nodes(multiple_cycles_graph_fixture: nx.DiGraph, mock_logger_fixture: Mock):
    # Ensure node IDs are sortable for predictability (N1, N2, N3...)
    result = analyze_cycles_enhanced(multiple_cycles_graph_fixture, mock_logger_fixture, sort_by="nodes")
    assert len(result) == 3
    first_nodes = [r['nodes'][0] for r in result]
    assert first_nodes == sorted(first_nodes) # Check if sorted by the first node ID

def test_analyze_cycles_sort_by_complexity(multiple_cycles_graph_fixture: nx.DiGraph, mock_logger_fixture: Mock):
    result = analyze_cycles_enhanced(multiple_cycles_graph_fixture, mock_logger_fixture, sort_by="complexity")
    assert len(result) == 3
    complexities = [r['complexity'] for r in result]
    assert complexities == sorted(complexities, reverse=True)

def test_analyze_cycles_overlapping_cycles_identified(overlapping_cycles_graph_fixture: nx.DiGraph, mock_logger_fixture: Mock):
    result = analyze_cycles_enhanced(overlapping_cycles_graph_fixture, mock_logger_fixture)
    # Expected cycles: (A,B,C) and (B,D,E)
    assert len(result) == 2 
    
    cycle_node_sets = [set(cycle['nodes']) for cycle in result]
    assert { 'A', 'B', 'C' } in cycle_node_sets
    assert { 'B', 'D', 'E' } in cycle_node_sets
    mock_logger_fixture.info.assert_any_call("Found 2 cycles after filtering (from 2 total)")


@patch('dependency_analyzer.analysis.analyzer.find_circular_dependencies')
def test_analyze_cycles_exception_handling(
    mock_find_cycles: Mock, 
    simple_cycle_graph_fixture: nx.DiGraph, 
    mock_logger_fixture: Mock
):
    mock_find_cycles.side_effect = Exception("Test find_cycles error")
    result = analyze_cycles_enhanced(simple_cycle_graph_fixture, mock_logger_fixture)
    assert result == []
    mock_logger_fixture.error.assert_called_once()
    assert "Error analyzing cycles: Test find_cycles error" in mock_logger_fixture.error.call_args[0][0]

def test_find_circular_dependencies_itself(simple_cycle_graph_fixture: nx.DiGraph, mock_logger_fixture: Mock):
    # This is more of an integration check that find_circular_dependencies works as expected by analyze_cycles_enhanced
    # Assuming find_circular_dependencies is well-tested elsewhere, but a quick check here.
    cycles = find_circular_dependencies(simple_cycle_graph_fixture, mock_logger_fixture)
    assert len(cycles) == 1
    assert sorted(cycles[0]) == sorted(['A', 'B', 'C'])
    mock_logger_fixture.info.assert_any_call("Found 1 circular dependencies.")

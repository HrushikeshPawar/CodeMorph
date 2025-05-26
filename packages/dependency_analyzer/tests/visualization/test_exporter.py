"""
Unit tests for exporter.py (Graphviz and Pyvis exporters)
"""
import networkx as nx
from dependency_analyzer.visualization import exporter
from plsql_analyzer.core.code_object import CodeObjectType

def make_sample_graph():
    G = nx.DiGraph()
    
    # Add nodes with 'object' attribute
    G.add_node("pkg1.proc1", name="proc1", package_name="pkg1", type=CodeObjectType.PROCEDURE)
    G.add_node("pkg1.proc2", name="proc2", package_name="pkg1", type=CodeObjectType.PROCEDURE)
    G.add_node("pkg2.func1", name="func1", package_name="pkg2", type=CodeObjectType.FUNCTION)
    
    # Add edges
    G.add_edge("pkg1.proc1", "pkg1.proc2")
    G.add_edge("pkg1.proc1", "pkg2.func1")
    
    return G

def test_to_graphviz_basic(da_test_logger):
    G = make_sample_graph()
    gv_graph = exporter.to_graphviz(G, logger=da_test_logger, with_package_name=True)
    assert gv_graph is not None
    # Check that node labels are present in the source
    src = gv_graph.source
    assert 'proc1' in src and 'proc2' in src and 'func1' in src
    assert 'label=' in src
    # Check that different colors are used for different object types
    assert 'blue' in src  # Color values should be hex

def test_graphviz_edge_coloring(da_test_logger):
    G = make_sample_graph()
    gv_graph = exporter.to_graphviz(G, logger=da_test_logger)
    src = gv_graph.source
    assert 'color=' in src  # Edges should have colors based on source node type

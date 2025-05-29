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

def test_to_graphviz_with_legend(da_test_logger):
    """Test that legend is included by default and contains expected elements."""
    G = make_sample_graph()
    gv_graph = exporter.to_graphviz(G, logger=da_test_logger, show_legend=True)
    src = gv_graph.source
    
    # Check that legend cluster is present
    assert 'cluster_legend' in src
    assert 'Legend - Node Types' in src
    
    # Check that legend contains the types present in our graph
    assert 'legend_procedure' in src
    assert 'legend_function' in src
    
    # Legend should not contain types not present in the graph
    assert 'legend_package' not in src
    assert 'legend_trigger' not in src

def test_to_graphviz_without_legend(da_test_logger):
    """Test that legend can be disabled."""
    G = make_sample_graph()
    gv_graph = exporter.to_graphviz(G, logger=da_test_logger, show_legend=False)
    src = gv_graph.source
    
    # Check that legend cluster is not present
    assert 'cluster_legend' not in src
    assert 'Legend - Node Types' not in src

def test_legend_with_all_node_types(da_test_logger):
    """Test legend with all possible node types."""
    G = nx.DiGraph()
    
    # Add nodes of all types
    G.add_node("pkg1", name="pkg1", package_name="SYS", type=CodeObjectType.PACKAGE)
    G.add_node("proc1", name="proc1", package_name="PKG1", type=CodeObjectType.PROCEDURE)
    G.add_node("func1", name="func1", package_name="PKG1", type=CodeObjectType.FUNCTION)
    G.add_node("trigger1", name="trigger1", package_name="PKG1", type=CodeObjectType.TRIGGER)
    G.add_node("type1", name="type1", package_name="PKG1", type=CodeObjectType.TYPE)
    G.add_node("unknown1", name="unknown1", package_name="PKG1", type=CodeObjectType.UNKNOWN)
    
    gv_graph = exporter.to_graphviz(G, logger=da_test_logger, show_legend=True)
    src = gv_graph.source
    
    # Check that all legend types are present
    assert 'legend_package' in src
    assert 'legend_procedure' in src
    assert 'legend_function' in src
    assert 'legend_trigger' in src
    assert 'legend_type' in src
    assert 'legend_unknown' in src

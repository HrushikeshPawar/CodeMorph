"""
Unit tests for exporter.py (Graphviz and Pyvis exporters)
"""
import networkx as nx
from dependency_analyzer.visualization import exporter
from plsql_analyzer.core.code_object import PLSQL_CodeObject, CodeObjectType

def make_sample_graph():
    class MockCodeObject(PLSQL_CodeObject):
        def __init__(self, name, package_name, object_type=CodeObjectType.PROCEDURE, source=True):
            super().__init__(name=name, package_name=package_name, type=object_type)
            self.source = source  # Added for backward compatibility with tests
            self.id = f"{package_name}.{name}"
    G = nx.DiGraph()
    # Add nodes with 'object' attribute
    G.add_node("pkg1.proc1", object=MockCodeObject("proc1", "pkg1", CodeObjectType.PROCEDURE, source=True))
    G.add_node("pkg1.proc2", object=MockCodeObject("proc2", "pkg1", CodeObjectType.PROCEDURE, source=False))
    G.add_node("pkg2.func1", object=MockCodeObject("func1", "pkg2", CodeObjectType.FUNCTION, source=True))
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
    assert '#' in src  # Color values should be hex

def test_to_pyvis_basic(da_test_logger):
    G = make_sample_graph()
    net = exporter.to_pyvis(G, logger=da_test_logger, with_package_name=True)
    assert net is not None
    # Pyvis stores nodes in net.nodes, which is a list of dicts
    node_labels = [n['label'] for n in net.nodes]
    assert any('proc1' in label for label in node_labels)
    assert any('proc2' in label for label in node_labels)
    assert any('func1' in label for label in node_labels)
    # Check that color dictionaries are used
    assert all(isinstance(n['color'], dict) for n in net.nodes)
    # Check shapes match our defined types
    node_shapes = [n['shape'] for n in net.nodes]
    assert 'ellipse' in node_shapes  # For PROCEDURE
    assert 'diamond' in node_shapes  # For FUNCTION

def test_graphviz_handles_missing_object(caplog, da_test_logger):
    G = make_sample_graph()
    G.add_node("orphan")  # No 'object' attribute
    gv_graph = exporter.to_graphviz(G, logger=da_test_logger)
    assert gv_graph is not None
    # Should not raise, and should log a warning
    # (caplog is a pytest fixture for capturing logs)
    assert any('missing' in rec.message for rec in caplog.records)

def test_pyvis_handles_missing_object(caplog, da_test_logger):
    G = make_sample_graph()
    G.add_node("orphan")  # No 'object' attribute
    net = exporter.to_pyvis(G, logger=da_test_logger)
    assert net is not None
    assert any('missing' in rec.message for rec in caplog.records)

def test_graphviz_edge_coloring(da_test_logger):
    G = make_sample_graph()
    gv_graph = exporter.to_graphviz(G, logger=da_test_logger)
    src = gv_graph.source
    assert 'color=' in src  # Edges should have colors based on source node type

def test_pyvis_kwargs_passthrough(da_test_logger):
    G = make_sample_graph()
    net = exporter.to_pyvis(G, logger=da_test_logger, pyvis_kwargs={"height": "400px", "width": "600px"})
    assert net.height == "400px"
    assert net.width == "600px"

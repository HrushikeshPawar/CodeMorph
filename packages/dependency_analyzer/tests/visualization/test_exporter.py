"""
Unit tests for exporter.py (Graphviz and Pyvis exporters)
"""
import networkx as nx
from dependency_analyzer.visualization import exporter

def make_sample_graph():
    class DummyCodeObject:
        def __init__(self, name, package_name, source=True, signature=None):
            self.name = name
            self.package_name = package_name
            self.source = source
            self.signature = signature
            self.id = f"{package_name}.{name}"
    G = nx.DiGraph()
    # Add nodes with 'object' attribute
    G.add_node("pkg1.proc1", object=DummyCodeObject("proc1", "pkg1", source=True, signature="sig1"))
    G.add_node("pkg1.proc2", object=DummyCodeObject("proc2", "pkg1", source=False, signature="sig2"))
    G.add_node("pkg2.func1", object=DummyCodeObject("func1", "pkg2", source=True, signature="sig3"))
    # Add edges
    G.add_edge("pkg1.proc1", "pkg1.proc2")
    G.add_edge("pkg1.proc1", "pkg2.func1")
    return G

def test_to_graphviz_basic(da_test_logger):
    G = make_sample_graph()
    gv_graph = exporter.to_graphviz(G, logger=da_test_logger, with_package_name=True, package_colors={"PKG1": "red", "PKG2": "blue"})
    assert gv_graph is not None
    # Check that node labels and colors are present in the source
    src = gv_graph.source
    assert 'proc1' in src and 'proc2' in src and 'func1' in src
    assert 'color=red' in src or 'color=blue' in src
    assert 'label=' in src

def test_to_pyvis_basic(da_test_logger):
    G = make_sample_graph()
    net = exporter.to_pyvis(G, logger=da_test_logger, with_package_name=True, package_colors={"PKG1": "red", "PKG2": "blue"})
    assert net is not None
    # Pyvis stores nodes in net.nodes, which is a list of dicts
    node_labels = [n['label'] for n in net.nodes]
    assert any('proc1' in label for label in node_labels)
    assert any('proc2' in label for label in node_labels)
    assert any('func1' in label for label in node_labels)
    # Check color assignment
    node_colors = [n['color'] for n in net.nodes]
    assert 'red' in node_colors or 'blue' in node_colors

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
    gv_graph = exporter.to_graphviz(G, logger=da_test_logger, package_colors={"PKG1": "#123456", "PKG2": "#654321"})
    src = gv_graph.source
    assert '#123456' in src or '#654321' in src

def test_pyvis_kwargs_passthrough(da_test_logger):
    G = make_sample_graph()
    net = exporter.to_pyvis(G, logger=da_test_logger, pyvis_kwargs={"height": "400px", "width": "600px"})
    assert net.height == "400px"
    assert net.width == "600px"

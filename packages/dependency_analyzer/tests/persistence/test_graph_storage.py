"""
Tests for the GraphStorage class in the persistence module.
"""
from __future__ import annotations
import pytest
import os
import tempfile
import networkx as nx
import loguru as lg
from typing import List, Optional
from enum import Enum

from dependency_analyzer.persistence.graph_storage import GraphStorage

# Mock classes for testing
class MockCodeObjectType(Enum):
    PROCEDURE = "PROCEDURE"
    FUNCTION = "FUNCTION"
    PACKAGE = "PACKAGE"
    UNKNOWN = "UNKNOWN"

class MockCodeObject:
    """Mock PLSQL_CodeObject for testing"""
    
    def __init__(self, id: str, name: str, package_name: Optional[str] = None, type_value: str = "PROCEDURE"):
        self.id = id
        self.name = name
        self.package_name = package_name
        self.type = MockCodeObjectType(type_value)
        self.parsed_parameters = []
        self.extracted_calls = []
        self.clean_code = "-- Mock code"
        self.overloaded = False

# Use the fixture from conftest.py for logger
# If your conftest.py has a da_test_logger fixture, use that

@pytest.fixture
def test_graph():
    """Creates a simple test graph for testing"""
    G = nx.DiGraph()
    # Add some test nodes and edges
    G.add_node("node1", attr1="value1")
    G.add_node("node2", attr2="value2")
    G.add_edge("node1", "node2", weight=1.0)
    return G

@pytest.fixture
def temp_dir():
    """Creates a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.fixture
def mock_database_loader(da_test_logger):
    """Creates a mock DatabaseLoader for testing"""
    class MockDatabaseLoader:
        def __init__(self, logger):
            self.logger = logger
            
        def load_all_objects(self) -> List[MockCodeObject]:
            """Return mock code objects"""
            return [
                MockCodeObject("proc1", "procedure1", "package1"),
                MockCodeObject("proc2", "procedure2", "package1"),
                MockCodeObject("func1", "function1", None, "FUNCTION")
            ]
    
    return MockDatabaseLoader(da_test_logger)

@pytest.fixture
def test_graph_with_objects():
    """Creates a test graph with mock code objects"""
    G = nx.DiGraph()
    
    # Create and add mock objects
    obj1 = MockCodeObject("proc1", "procedure1", "package1")
    obj2 = MockCodeObject("proc2", "procedure2", "package1") 
    obj3 = MockCodeObject("func1", "function1", None, "FUNCTION")
    
    # Add nodes with objects
    G.add_node("proc1", object=obj1)
    G.add_node("proc2", object=obj2) 
    G.add_node("func1", object=obj3)
    
    # Add edges
    G.add_edge("proc1", "proc2", weight=1.0)
    G.add_edge("proc2", "func1", weight=0.5)
    
    return G

def test_init(da_test_logger: lg.Logger):
    """Test that GraphStorage initializes correctly"""
    storage = GraphStorage(da_test_logger)
    assert storage is not None
    assert storage.logger is not None

def test_save_load_gpickle(da_test_logger: lg.Logger, test_graph, temp_dir):
    """Test saving and loading in gpickle format"""
    storage = GraphStorage(da_test_logger)
    file_path = os.path.join(temp_dir, "test_graph.gpickle")
    
    # Test saving
    result = storage.save_graph(test_graph, file_path)
    assert result is True
    assert os.path.exists(file_path)
    
    # Test loading
    loaded_graph = storage.load_graph(file_path)
    assert loaded_graph is not None
    assert loaded_graph.number_of_nodes() == test_graph.number_of_nodes()
    assert loaded_graph.number_of_edges() == test_graph.number_of_edges()
    assert "node1" in loaded_graph.nodes
    assert loaded_graph.nodes["node1"]["attr1"] == "value1"

def test_save_load_graphml(da_test_logger: lg.Logger, test_graph, temp_dir):
    """Test saving and loading in graphml format"""
    storage = GraphStorage(da_test_logger)
    file_path = os.path.join(temp_dir, "test_graph.graphml")
    
    # Test saving
    result = storage.save_graph(test_graph, file_path)
    assert result is True
    assert os.path.exists(file_path)
    
    # Test loading
    loaded_graph = storage.load_graph(file_path)
    assert loaded_graph is not None
    assert loaded_graph.number_of_nodes() == test_graph.number_of_nodes()
    assert loaded_graph.number_of_edges() == test_graph.number_of_edges()
    assert "node1" in loaded_graph.nodes

def test_save_load_gexf(da_test_logger: lg.Logger, test_graph, temp_dir):
    """Test saving and loading in gexf format"""
    storage = GraphStorage(da_test_logger)
    file_path = os.path.join(temp_dir, "test_graph.gexf")
    
    # Test saving
    result = storage.save_graph(test_graph, file_path)
    assert result is True
    assert os.path.exists(file_path)
    
    # Test loading
    loaded_graph = storage.load_graph(file_path)
    assert loaded_graph is not None
    assert loaded_graph.number_of_nodes() == test_graph.number_of_nodes()
    assert loaded_graph.number_of_edges() == test_graph.number_of_edges()
    assert "node1" in loaded_graph.nodes

def test_save_load_json(da_test_logger: lg.Logger, test_graph, temp_dir):
    """Test saving and loading in json format"""
    storage = GraphStorage(da_test_logger)
    file_path = os.path.join(temp_dir, "test_graph.json")
    
    # Test saving
    result = storage.save_graph(test_graph, file_path)
    assert result is True
    assert os.path.exists(file_path)
    
    # Test loading
    loaded_graph = storage.load_graph(file_path)
    assert loaded_graph is not None
    assert loaded_graph.number_of_nodes() == test_graph.number_of_nodes()
    assert loaded_graph.number_of_edges() == test_graph.number_of_edges()
    assert "node1" in loaded_graph.nodes

def test_format_autodetection(da_test_logger: lg.Logger, test_graph, temp_dir):
    """Test automatic format detection from file extension"""
    storage = GraphStorage(da_test_logger)
    
    # Test with different file extensions
    extensions = ["gpickle", "graphml", "gexf", "json"]
    
    for ext in extensions:
        file_path = os.path.join(temp_dir, f"test_graph.{ext}")
        
        # Test saving with auto-detection
        result = storage.save_graph(test_graph, file_path)
        assert result is True
        assert os.path.exists(file_path)
        
        # Test loading with auto-detection
        loaded_graph = storage.load_graph(file_path)
        assert loaded_graph is not None
        assert loaded_graph.number_of_nodes() == test_graph.number_of_nodes()

def test_invalid_format(da_test_logger: lg.Logger, test_graph, temp_dir):
    """Test behavior with invalid formats"""
    storage = GraphStorage(da_test_logger)
    file_path = os.path.join(temp_dir, "test_graph.invalid")
    
    # Test saving with invalid format
    result = storage.save_graph(test_graph, file_path, format="invalid")
    assert result is False
    
    # Create an empty file to test loading
    with open(file_path, 'w') as f:
        f.write("invalid content")
    
    # Test loading with invalid format
    loaded_graph = storage.load_graph(file_path, format="invalid")
    assert loaded_graph is None

def test_nonexistent_file(da_test_logger: lg.Logger):
    """Test loading a non-existent file"""
    storage = GraphStorage(da_test_logger)
    loaded_graph = storage.load_graph("/path/to/nonexistent/file.gpickle")
    assert loaded_graph is None

def test_parent_directory_creation(da_test_logger: lg.Logger, test_graph, temp_dir):
    """Test that parent directories are created when saving"""
    storage = GraphStorage(da_test_logger)
    nested_dir = os.path.join(temp_dir, "nested", "dir", "structure")
    file_path = os.path.join(nested_dir, "test_graph.gpickle")
    
    # Test saving - should create parent directories
    result = storage.save_graph(test_graph, file_path)
    assert result is True
    assert os.path.exists(file_path)

def test_save_structure_only(da_test_logger, test_graph_with_objects, temp_dir):
    """Test saving only the structure of a graph with code objects"""
    storage = GraphStorage(da_test_logger)
    file_path = os.path.join(temp_dir, "test_structure.json")
    
    # Save structure-only graph
    result = storage.save_graph(test_graph_with_objects, file_path)
    assert result is True
    assert os.path.exists(file_path)
    
    # Load the saved structure
    loaded_graph = storage.load_graph(file_path)
    assert loaded_graph is not None
    assert loaded_graph.number_of_nodes() == test_graph_with_objects.number_of_nodes()
    assert loaded_graph.number_of_edges() == test_graph_with_objects.number_of_edges()
    
    # Verify code objects are not present, but their basic attributes are
    for node_id in loaded_graph.nodes():
        assert 'object' not in loaded_graph.nodes[node_id]
        assert 'object_id' in loaded_graph.nodes[node_id]
        assert loaded_graph.nodes[node_id]['object_id'] == node_id

def test_load_and_populate(da_test_logger, test_graph_with_objects, mock_database_loader, temp_dir):
    """Test loading a structure-only graph and populating it with code objects"""
    storage = GraphStorage(da_test_logger)
    file_path = os.path.join(temp_dir, "test_structure.json")
    
    # First save structure-only graph
    storage.save_graph(test_graph_with_objects, file_path)
    
    # Load and populate with objects from mock database loader
    populated_graph = storage.load_and_populate(file_path, mock_database_loader)
    
    assert populated_graph is not None
    assert populated_graph.number_of_nodes() == test_graph_with_objects.number_of_nodes()
    assert populated_graph.number_of_edges() == test_graph_with_objects.number_of_edges()
    
    # Verify code objects are present now
    for node_id in populated_graph.nodes():
        assert 'object' in populated_graph.nodes[node_id]
        assert hasattr(populated_graph.nodes[node_id]['object'], 'id')
        assert populated_graph.nodes[node_id]['object'].id == node_id

"""
Integration tests for the dependency analyzer CLI commands.

These tests verify that the structured CLI command interface works as expected
by simulating command-line invocation.
"""
import sys
import tempfile
from pathlib import Path


from dependency_analyzer.cli_app import app
from dependency_analyzer.settings import DependencyAnalyzerSettings

def test_cli_command_groups_structure():
    """Test that the CLI has the expected command group structure."""
    # Check that the main commands exist
    assert "init" in app
    assert "build" in app
    assert "analyze" in app
    assert "visualize" in app
    assert "query" in app
    
    # Check that each command has the expected subcommands
    assert "full" in app["build"]
    assert "subgraph" in app["build"]
    
    assert "classify" in app["analyze"]
    assert "cycles" in app["analyze"]
    
    assert "graph" in app["visualize"]
    assert "subgraph" in app["visualize"]
    
    assert "reachability" in app["query"]
    assert "paths" in app["query"]
    assert "list" in app["query"]

def test_init_config_creates_file():
    """Test that the init config command creates a config file."""
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        config_path = temp_path / "test_config.toml"
        
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Execute the command
            app(["init", "--output-path", str(config_path)])
            
            # Check that the config file was created
            assert config_path.exists()
            
            # Check that the file contains expected sections
            with open(config_path, "r") as f:
                content = f.read()
                assert "[paths]" in content
                assert "[logging]" in content
                assert "[graph]" in content
                assert "[visualization]" in content
                assert "[features]" in content
                assert "[analysis]" in content
                
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

def test_build_full_with_config(mocker):
    """Test the build full command with a config file."""
    # Import here to avoid circular imports during patching
    import networkx as nx
    
    # Create test objects
    test_graph = nx.DiGraph()
    test_graph.add_node("test")
    
    # Create a mock PLSQL_CodeObject 
    class MockCodeObject:
        def __init__(self, id: str):
            self.id = id
    
    mock_objects = [MockCodeObject("obj1")]
    
    # Setup mocks
    mock_constructor = mocker.patch("dependency_analyzer.cli.service.GraphConstructor")
    mock_constructor_instance = mock_constructor.return_value
    mock_constructor_instance.build_graph.return_value = (test_graph, [])
    
    mock_loader = mocker.patch("dependency_analyzer.cli.service.DatabaseLoader")
    mock_loader_instance = mock_loader.return_value
    mock_loader_instance.load_all_objects.return_value = mock_objects
    
    mock_db_manager = mocker.patch("dependency_analyzer.cli.service.DatabaseManager")
    
    mock_graph_storage = mocker.patch("dependency_analyzer.cli.service.GraphStorage")
    mock_storage_instance = mock_graph_storage.return_value
    
    # Mock the analyzer function 
    mock_analyzer = mocker.patch("dependency_analyzer.cli.service.analyzer")
    mock_analyzer.calculate_node_complexity_metrics.return_value = test_graph
    
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        config_path = temp_path / "test_config.toml"
        db_path = temp_path / "test.db"
        output_fname = "output"
        
        # Create mock database file
        with open(db_path, "w") as f:
            f.write("mock db")
        
        
        # Create config file
        settings = DependencyAnalyzerSettings(output_base_dir = temp_path)
        settings.database_path = db_path

        settings.ensure_artifact_dirs()
        settings.write_default_config(config_path)
        
        # Mock Path.exists to return True for db_path
        mocker.patch.object(Path, "exists", return_value=True)
        

        with Path(settings.graphs_dir, f"{output_fname}.graphml").open('w') as graph_file:
            graph_file.write("mock graph data")
        
        # Execute the command with all required parameters including db-path
        app(["build", "full",
            "--db", str(db_path),
            "--config", str(config_path),
            "-o", str(output_fname),
            "--format", "graphml",
            "-v", "3",
        ])
        
        # Verify the mocks were called correctly
        mock_db_manager.assert_called_once()
        mock_loader.assert_called_once()
        mock_constructor.assert_called_once()
        mock_constructor_instance.build_graph.assert_called_once()
        mock_storage_instance.save_graph.assert_called_once()


def test_visualize_subgraph_command_structure():
    """Test that the visualize-subgraph command exists with expected parameters."""
    # Check that the command exists
    assert "subgraph" in app["visualize"]
    
    # The command should be a top-level command, not a subcommand


def test_cli_visualize_subgraph_integration(mocker):
    """Test the integrated visualize-subgraph command."""
    # Mock all the dependencies
    mock_db_manager = mocker.patch("dependency_analyzer.cli.service.DatabaseManager")
    mock_loader = mocker.patch("dependency_analyzer.cli.service.DatabaseLoader")
    mock_constructor = mocker.patch("dependency_analyzer.cli.service.GraphConstructor")
    mock_analyzer = mocker.patch("dependency_analyzer.cli.service.analyzer")
    mock_exporter = mocker.patch("dependency_analyzer.cli.service.exporter")
    mock_storage = mocker.patch("dependency_analyzer.cli.service.GraphStorage")
    
    # Setup mock objects
    mock_code_objects = [mocker.Mock(id="test_node")]
    mock_loader_instance = mock_loader.return_value
    mock_loader_instance.load_all_objects.return_value = mock_code_objects
    
    mock_full_graph = mocker.Mock()
    mock_full_graph.number_of_nodes.return_value = 10
    mock_full_graph.number_of_edges.return_value = 15
    mock_full_graph.__contains__ = mocker.Mock(return_value=True)
    
    mock_subgraph = mocker.Mock()
    mock_subgraph.number_of_nodes.return_value = 5
    mock_subgraph.number_of_edges.return_value = 7
    
    mock_constructor_instance = mock_constructor.return_value
    mock_constructor_instance.build_graph.return_value = (mock_full_graph, [])
    
    mock_analyzer.generate_subgraph_for_node.return_value = mock_subgraph
    
    mock_viz_graph = mocker.Mock()
    mock_exporter.to_graphviz.return_value = mock_viz_graph
    
    mock_storage_instance = mock_storage.return_value
    mock_storage_instance.save_graph.return_value = True
    
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        config_path = temp_path / "test_config.toml"
        db_path = temp_path / "test.db"
        
        # Create mock database file
        with open(db_path, "w") as f:
            f.write("mock db")
        
        # Create config file
        settings = DependencyAnalyzerSettings(output_base_dir=temp_path)
        settings.database_path = db_path
        settings.ensure_artifact_dirs()
        settings.write_default_config(config_path)
        
        # Mock Path.exists to return True for db_path
        mocker.patch.object(Path, "exists", return_value=True)
        
        # Execute the visualize-subgraph command
        app(["visualize", 
            "subgraph",
            "--config", str(config_path),
            "--db", str(db_path),
            "--node-id", "test_node",
            "--output-image", "test_output",
            "--upstream-depth", "2",
            "--downstream-depth", "3",
            "--title", "Test Subgraph",
            "-v", "3",
        ])
        
        # Verify the mocks were called correctly
        mock_db_manager.assert_called_once()
        mock_loader.assert_called_once()
        mock_constructor.assert_called_once()
        mock_constructor_instance.build_graph.assert_called_once()
        mock_analyzer.generate_subgraph_for_node.assert_called_once_with(
            mock_full_graph, "test_node", mocker.ANY, 2, 3
        )
        mock_exporter.to_graphviz.assert_called_once()
        mock_viz_graph.render.assert_called()
    
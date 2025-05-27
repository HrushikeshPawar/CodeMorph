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
    
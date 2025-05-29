import pytest
from unittest.mock import patch, Mock, ANY
from pathlib import Path
import sys

from cyclopts.exceptions import MissingArgumentError
from dependency_analyzer.cli.service import CLIService, CLIError
from dependency_analyzer.settings import DependencyAnalyzerSettings

# Fixtures

@pytest.fixture
def cli_runner_fixture(mocker):
    # For cyclopts, direct invocation or a custom runner might be needed.
    # Here, we'll mock the service layer and check calls.
    # A more integrated approach might use typer.testing.CliRunner if applicable
    # or directly invoke app.main() with sys.argv patching.
    def run_cli_command(command_list):
        # Patch sys.argv and call the app's entry point
        # This is a simplified way; a real CLI runner would be better.
        # For now, we'll focus on mocking the service call.
        with patch.object(sys, 'argv', ["dependency-analyzer"] + command_list):
            try:
                # Assuming your cyclopts app has a main or similar entry point
                # If not, you might need to directly call the command function
                # For this example, we'll assume a structure where service is called
                pass # Test will mock service directly
            except SystemExit as e:
                return e.code # Capture exit code
            except MissingArgumentError as e:
                 # Cyclopts raises this for missing args, often before SystemExit
                print(f"MissingArgumentError: {e}", file=sys.stderr)
                return 1 # Simulate error exit code
            except Exception as e:
                print(f"CLI run failed: {e}", file=sys.stderr)
                return 1
        return 0 # Default success
    return run_cli_command

@pytest.fixture
def mock_cli_service_class_fixture(mocker) -> Mock:
    mock_service_instance = Mock(spec=CLIService)
    mock_service_instance.analyze_cycles = Mock(return_value=[]) # Default successful call
    mock_service_instance.initialize_config = Mock()
    # Add other methods if your CLI commands use them

    mock_service_class = mocker.patch('dependency_analyzer.cli_app.CLIService', return_value=mock_service_instance)
    return mock_service_class # Return the class mock to get the instance via .return_value

@pytest.fixture
def valid_config_file_fixture(tmp_path: Path) -> Path:
    config_content = """ 
[settings]
# dummy content, structure might be more complex
database_path = "dummy.db"
    """
    config_file = tmp_path / "dep_analyzer_config.toml"
    config_file.write_text(config_content)
    return config_file

@pytest.fixture
def valid_graph_file_fixture(tmp_path: Path) -> Path:
    graph_file = tmp_path / "graph.gpickle"
    graph_file.touch() # Just needs to exist for path validation in CLI
    return graph_file

@pytest.fixture
def mock_settings_from_toml(mocker):
    mock_settings = Mock(spec=DependencyAnalyzerSettings)
    mock_settings.log_verbose_level = 1 # Default
    return mocker.patch('dependency_analyzer.cli_app.DependencyAnalyzerSettings.from_toml', return_value=mock_settings)

# Test Cases

# Note: Testing help output with cyclopts might require capturing stdout
# or using a specific testing utility if cyclopts provides one.
# For now, we focus on parameter passing and service calls.

@patch('dependency_analyzer.cli_app.sys.exit') # Mock sys.exit to prevent test runner from exiting
@patch('dependency_analyzer.cli_app.handle_cli_error')
def test_cli_cycles_basic_run_calls_service(
    mock_handle_error: Mock, mock_sys_exit: Mock, 
    cli_runner_fixture, 
    mock_cli_service_class_fixture: Mock, 
    valid_graph_file_fixture: Path, 
    valid_config_file_fixture: Path,
    mock_settings_from_toml: Mock
):
    mock_service_instance = mock_cli_service_class_fixture.return_value
    
    # Directly invoke the command function for more control with cyclopts
    from dependency_analyzer.cli_app import analyze_cycles # Import the command function
    
    analyze_cycles(
        graph_path=valid_graph_file_fixture,
        config_file=valid_config_file_fixture,
        # Defaults for other params
        verbose=1,
        min_cycle_length=None,
        max_cycle_length=None,
        output_format="table",
        include_node_details=False,
        sort_cycles="length",
        output_fname=None
    )

    mock_settings_from_toml.assert_called_with(valid_config_file_fixture)
    mock_cli_service_class_fixture.assert_called_with(mock_settings_from_toml.return_value)
    mock_service_instance.analyze_cycles.assert_called_once_with(
        graph_path=valid_graph_file_fixture,
        min_cycle_length=None,
        max_cycle_length=None,
        output_format="table",
        include_node_details=False,
        sort_cycles="length",
        output_fname=None
    )
    mock_sys_exit.assert_not_called() # Should not exit if successful
    mock_handle_error.assert_not_called()

@patch('dependency_analyzer.cli_app.sys.exit')
@patch('dependency_analyzer.cli_app.handle_cli_error')
def test_cli_cycles_all_options_forwarded(
    mock_handle_error: Mock, mock_sys_exit: Mock,
    mock_cli_service_class_fixture: Mock, 
    valid_graph_file_fixture: Path, 
    valid_config_file_fixture: Path,
    mock_settings_from_toml: Mock
):
    mock_service_instance = mock_cli_service_class_fixture.return_value
    mock_settings_instance = mock_settings_from_toml.return_value

    from dependency_analyzer.cli_app import analyze_cycles
    analyze_cycles(
        graph_path=valid_graph_file_fixture,
        config_file=valid_config_file_fixture,
        verbose=2,
        min_cycle_length=3,
        max_cycle_length=5,
        output_format="json",
        include_node_details=True,
        sort_cycles="complexity",
        output_fname="my_out"
    )

    mock_settings_from_toml.assert_called_with(valid_config_file_fixture)
    assert mock_settings_instance.log_verbose_level == 2 # Check if settings object was updated
    mock_cli_service_class_fixture.assert_called_with(mock_settings_instance)
    mock_service_instance.analyze_cycles.assert_called_once_with(
        graph_path=valid_graph_file_fixture,
        min_cycle_length=3,
        max_cycle_length=5,
        output_format="json",
        include_node_details=True,
        sort_cycles="complexity",
        output_fname="my_out"
    )

@patch('dependency_analyzer.cli_app.sys.exit')
@patch('dependency_analyzer.cli_app.handle_cli_error')
def test_cli_cycles_service_cli_error_handled(
    mock_handle_error: Mock, mock_sys_exit: Mock,
    mock_cli_service_class_fixture: Mock, 
    valid_graph_file_fixture: Path, 
    valid_config_file_fixture: Path,
    mock_settings_from_toml: Mock
):
    mock_service_instance = mock_cli_service_class_fixture.return_value
    test_error = CLIError("Test Service Error")
    mock_service_instance.analyze_cycles.side_effect = test_error

    from dependency_analyzer.cli_app import analyze_cycles
    analyze_cycles(
        graph_path=valid_graph_file_fixture,
        config_file=valid_config_file_fixture
    )
    
    mock_handle_error.assert_called_once_with(test_error, ANY) # ANY for logger instance
    mock_sys_exit.assert_called_once_with(1)

@patch('dependency_analyzer.cli_app.sys.exit')
@patch('dependency_analyzer.cli_app.handle_cli_error')
def test_cli_cycles_service_unexpected_error_handled(
    mock_handle_error: Mock, mock_sys_exit: Mock,
    mock_cli_service_class_fixture: Mock, 
    valid_graph_file_fixture: Path, 
    valid_config_file_fixture: Path,
    mock_settings_from_toml: Mock
):
    mock_service_instance = mock_cli_service_class_fixture.return_value
    unexpected_error = ValueError("Unexpected")
    mock_service_instance.analyze_cycles.side_effect = unexpected_error

    from dependency_analyzer.cli_app import analyze_cycles
    analyze_cycles(
        graph_path=valid_graph_file_fixture,
        config_file=valid_config_file_fixture
    )
    
    # Check that handle_cli_error was called with a CLIError wrapping the original
    assert mock_handle_error.call_count == 1
    args, kwargs = mock_handle_error.call_args
    assert isinstance(args[0], CLIError)
    assert "Unexpected error during cycle analysis: Unexpected" in str(args[0])
    mock_sys_exit.assert_called_once_with(1)

# To test missing arguments with cyclopts, you'd typically let cyclopts raise the error.
# This requires running the command through a mechanism that cyclopts controls.
# For unit tests focusing on the command function's logic after parsing, direct invocation is common.
# If you need to test cyclopts parsing itself, you might need a more integrated CLI runner.

# Example of how you might test help (requires capturing stdout):
@patch('builtins.print') # Or patch sys.stdout if cyclopts prints there
def test_cli_cycles_help(mock_print, cli_runner_fixture):
    # This is a conceptual test. Actual cyclopts help testing might differ.
    # cli_runner_fixture(["analyze", "cycles", "--help"]) # This would be for a full CLI runner
    # For now, we assume help is implicitly tested by cyclopts if parameters are defined.
    # If you have a way to invoke help directly and capture output, use that.
    pass

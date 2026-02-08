import pytest
from unittest.mock import Mock, patch, ANY, mock_open
from pathlib import Path
from typing import List, Dict, Callable
import json
import csv
import io

from rich.console import Console
from rich.table import Table

from dependency_analyzer.cli.service import CLIService
from dependency_analyzer.settings import DependencyAnalyzerSettings
from dependency_analyzer.cli.utils import CLIError
from dependency_analyzer.analysis import analyzer as analyzer_module # Alias to avoid conflict

# Fixtures

@pytest.fixture
def mock_settings_fixture() -> Mock:
    settings = Mock(spec=DependencyAnalyzerSettings)
    settings.log_verbose_level = 1
    settings.logs_dir = Path("mock_logs")
    settings.database_path = Path("mock_db.sqlite") # Add other necessary defaults
    return settings

@pytest.fixture
def mock_logger_fixture() -> Mock:
    return Mock()

@pytest.fixture
def mock_graph_storage_fixture(mocker) -> Mock:
    mock_storage = Mock()
    mock_storage.load_graph = Mock(return_value=mocker.MagicMock(name="MockGraph")) # Return a mock graph object
    return mock_storage

@pytest.fixture
def mock_analyzer_module_fixture(mocker) -> Mock:
    mock_analyzer = Mock(spec=analyzer_module)
    mock_analyzer.analyze_cycles_enhanced = Mock(return_value=[]) # Default to no cycles
    return mock_analyzer

@pytest.fixture
def sample_cycles_data_no_details() -> List[Dict]:
    return [
        {
            'cycle_id': 1,
            'nodes': ['A', 'B', 'C'],
            'length': 3,
            'complexity': 6,
            'cycle_path': 'A → B → C → A'
        },
        {
            'cycle_id': 2,
            'nodes': ['D', 'E'],
            'length': 2,
            'complexity': 4,
            'cycle_path': 'D → E → D'
        }
    ]

@pytest.fixture
def sample_cycles_data_with_details() -> List[Dict]:
    return [
        {
            'cycle_id': 1,
            'nodes': ['A', 'B', 'C'],
            'length': 3,
            'complexity': 6,
            'cycle_path': 'A → B → C → A',
            'node_details': [
                {'id': 'A', 'name': 'NodeA', 'type': 'PROC', 'package': 'PKG1', 'in_degree': 1, 'out_degree': 1},
                {'id': 'B', 'name': 'NodeB', 'type': 'FUNC', 'package': 'PKG1', 'in_degree': 1, 'out_degree': 1},
                {'id': 'C', 'name': 'NodeC', 'type': 'TABLE', 'package': 'PKG2', 'in_degree': 1, 'out_degree': 1},
            ]
        }
    ]

@pytest.fixture
def mock_console_fixture(mocker) -> Mock:
    mock_console = Mock(spec=Console)
    mocker.patch('dependency_analyzer.cli.service.Console', return_value=mock_console)
    return mock_console

@pytest.fixture
def mock_table_fixture(mocker) -> Mock:
    """Mock Table class and return the instance that receives method calls."""
    mock_table_instance = Mock(spec=Table)
    # Patch the Table class to return our mock instance
    mocker.patch('dependency_analyzer.cli.service.Table', return_value=mock_table_instance)
    return mock_table_instance

@pytest.fixture
def service_instance(mock_settings_fixture, mock_logger_fixture, mock_graph_storage_fixture, mock_analyzer_module_fixture, mocker):
    # Patch dependencies for CLIService instantiation and its methods
    mocker.patch('dependency_analyzer.cli.service.configure_logger', return_value=mock_logger_fixture)
    mocker.patch('dependency_analyzer.cli.service.GraphStorage', return_value=mock_graph_storage_fixture)
    mocker.patch('dependency_analyzer.cli.service.analyzer', mock_analyzer_module_fixture) # Patch the aliased module
    return CLIService(mock_settings_fixture)

# Test Cases for CLIService.analyze_cycles()
def test_service_analyze_cycles_graph_file_not_exist(service_instance: CLIService, mocker):
    graph_path = Path("non_existent_graph.gpickle")
    mocker.patch('dependency_analyzer.cli.service.validate_file_exists', side_effect=CLIError("File not found"))
    with pytest.raises(CLIError, match="File not found"):
        service_instance.analyze_cycles(graph_path)
    service_instance.logger.info.assert_not_called()  # Should not log if file does not exist

def test_service_analyze_cycles_graph_load_fails(mocker, service_instance: CLIService, mock_graph_storage_fixture):
    graph_path = Path("test_graph.gpickle")

    # Mock validate_file_exists to prevent file validation error
    mocker.patch('dependency_analyzer.cli.service.validate_file_exists')
    
    mock_graph_storage_fixture.load_graph.return_value = None
    with pytest.raises(CLIError, match="Failed to load graph from"):
        service_instance.analyze_cycles(graph_path)
    service_instance.graph_storage.load_graph.assert_called_with(graph_path)

def test_service_analyze_cycles_no_cycles_found(service_instance: CLIService, mock_analyzer_module_fixture, mocker):
    graph_path = Path("test_graph.gpickle")
    
    # Mock validate_file_exists to prevent file validation error
    mocker.patch('dependency_analyzer.cli.service.validate_file_exists')
    
    mock_analyzer_module_fixture.analyze_cycles_enhanced.return_value = []
    mocker.spy(service_instance, '_display_cycles_results')
    mocker.spy(service_instance, '_save_cycles_results')

    result = service_instance.analyze_cycles(graph_path)
    
    assert result == []
    service_instance.logger.info.assert_any_call(f"Analyzing cycles in graph '{graph_path}'")
    mock_analyzer_module_fixture.analyze_cycles_enhanced.assert_called_once()
    
    service_instance._display_cycles_results.assert_not_called() # Should not display if no cycles
    service_instance._save_cycles_results.assert_not_called() # Should not save if no cycles found

def test_service_analyze_cycles_success_display_only(
    service_instance: CLIService, 
    mock_analyzer_module_fixture, 
    sample_cycles_data_no_details, 
    mocker
):
    graph_path = Path("test_graph.gpickle")

    # Mock validate_file_exists to prevent file validation error
    mocker.patch('dependency_analyzer.cli.service.validate_file_exists')
    
    mock_analyzer_module_fixture.analyze_cycles_enhanced.return_value = sample_cycles_data_no_details
    mocker.spy(service_instance, '_display_cycles_results')
    mocker.spy(service_instance, '_save_cycles_results')

    result = service_instance.analyze_cycles(graph_path, output_fname=None)

    assert result == sample_cycles_data_no_details
    mock_analyzer_module_fixture.analyze_cycles_enhanced.assert_called_once_with(
        ANY, # graph object
        service_instance.logger,
        min_cycle_length=None,
        max_cycle_length=None,
        sort_by="length",
        include_node_details=False
    )
    service_instance._display_cycles_results.assert_called_once_with(sample_cycles_data_no_details, "table", False)
    service_instance._save_cycles_results.assert_not_called()

def test_service_analyze_cycles_success_display_and_save(
    mocker,
    service_instance: CLIService, 
    mock_analyzer_module_fixture, 
    sample_cycles_data_no_details,
):
    graph_path = Path("test_graph.gpickle")
    
    # Mock validate_file_exists to prevent file validation error
    mocker.patch('dependency_analyzer.cli.service.validate_file_exists')
    
    output_fname = "test_output"
    mock_analyzer_module_fixture.analyze_cycles_enhanced.return_value = sample_cycles_data_no_details
    mocker.spy(service_instance, '_display_cycles_results')
    mocker.spy(service_instance, '_save_cycles_results')

    service_instance.analyze_cycles(graph_path, output_fname=output_fname, output_format="json")

    service_instance._display_cycles_results.assert_called_once_with(sample_cycles_data_no_details, "json", False)
    service_instance._save_cycles_results.assert_called_once_with(sample_cycles_data_no_details, output_fname, "json")

def test_service_analyze_cycles_params_forwarded_correctly(
    mocker,
    service_instance: CLIService, mock_analyzer_module_fixture
):
    graph_path = Path("test_graph.gpickle")

    # Mock validate_file_exists to prevent file validation error
    mocker.patch('dependency_analyzer.cli.service.validate_file_exists')
    
    service_instance.analyze_cycles(
        graph_path,
        min_cycle_length=3,
        max_cycle_length=5,
        output_format="csv",
        include_node_details=True,
        sort_cycles="complexity",
        output_fname="out"
    )
    mock_analyzer_module_fixture.analyze_cycles_enhanced.assert_called_with(
        ANY, # graph object
        service_instance.logger,
        min_cycle_length=3,
        max_cycle_length=5,
        sort_by="complexity",
        include_node_details=True
    )

# Test Cases for CLIService._display_cycles_results()

def test_display_table_no_details(
    mocker,
    service_instance: CLIService, 
    sample_cycles_data_no_details: List[Dict], 
    mock_console_fixture: Mock, 
    mock_table_fixture: Mock
):
    # Add a spy to see all Table() calls
    # table_spy = mocker.spy(service_instance, '_display_cycles_results')
    
    service_instance._display_cycles_results(sample_cycles_data_no_details, "table", False)

    # Print all calls made to the mock for debugging
    print(f"Table mock calls: {mock_table_fixture.method_calls}")
    print(f"Console mock calls: {mock_console_fixture.method_calls}")
    
    mock_table_fixture.add_column.assert_any_call("Cycle ID", justify="center", style="cyan")
    mock_table_fixture.add_column.assert_any_call("Length", justify="center", style="yellow")
    mock_table_fixture.add_column.assert_any_call("Complexity", justify="center", style="red")
    mock_table_fixture.add_column.assert_any_call("Cycle Path", justify="left", style="green", overflow="fold")
    
    assert mock_table_fixture.add_row.call_count == len(sample_cycles_data_no_details)
    mock_console_fixture.print.assert_any_call(mock_table_fixture)

def test_display_table_with_details(
    service_instance: CLIService, 
    sample_cycles_data_with_details: List[Dict], 
    mock_console_fixture: Mock, 
    mock_table_fixture: Mock # This will be the main table, new tables are created inside
):
    # We need to mock Table class to capture creations of detail_tables
    with patch('dependency_analyzer.cli.service.Table') as PatchedTableCls:
        mock_main_table_instance = Mock(spec=Table)
        mock_detail_table_instance = Mock(spec=Table)
        # First call to Table() is main, subsequent are detail tables
        PatchedTableCls.side_effect = [mock_main_table_instance, mock_detail_table_instance]

        service_instance._display_cycles_results(sample_cycles_data_with_details, "table", True)

        # Main table assertions
        PatchedTableCls.assert_any_call(title="Circular Dependencies Analysis", show_lines=True)
        mock_main_table_instance.add_column.assert_any_call("Cycle ID", justify="center", style="cyan")
        mock_console_fixture.print.assert_any_call(mock_main_table_instance)

        # Detail table assertions (for the one cycle in fixture)
        PatchedTableCls.assert_any_call(title=f"Cycle {sample_cycles_data_with_details[0]['cycle_id']} - Node Details", show_lines=True)
        mock_detail_table_instance.add_column.assert_any_call("Node ID", style="cyan")
        mock_detail_table_instance.add_column.assert_any_call("Name", style="yellow")
        mock_detail_table_instance.add_column.assert_any_call("Type", style="red")
        mock_detail_table_instance.add_column.assert_any_call("Package", style="green")
        mock_detail_table_instance.add_column.assert_any_call("In Degree", justify="center")
        mock_detail_table_instance.add_column.assert_any_call("Out Degree", justify="center")
        assert mock_detail_table_instance.add_row.call_count == len(sample_cycles_data_with_details[0]['node_details'])
        mock_console_fixture.print.assert_any_call(mock_detail_table_instance)
        mock_console_fixture.print.assert_any_call() # For spacing

def test_display_json(service_instance: CLIService, sample_cycles_data_with_details: List[Dict], mock_console_fixture: Mock):
    service_instance._display_cycles_results(sample_cycles_data_with_details, "json", True)
    expected_json_output = json.dumps(sample_cycles_data_with_details, indent=2)
    mock_console_fixture.print_json.assert_called_once_with(expected_json_output)

def test_display_csv_no_details(service_instance: CLIService, sample_cycles_data_no_details: List[Dict], mock_console_fixture: Mock):
    service_instance._display_cycles_results(sample_cycles_data_no_details, "csv", False)
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['cycle_id', 'length', 'complexity', 'cycle_path'])
    writer.writeheader()
    for cycle in sample_cycles_data_no_details:
        writer.writerow({'cycle_id': cycle['cycle_id'], 'length': cycle['length'], 'complexity': cycle['complexity'], 'cycle_path': cycle['cycle_path']})
    
    mock_console_fixture.print.assert_called_once_with(output.getvalue())

def test_display_csv_with_details(service_instance: CLIService, sample_cycles_data_with_details: List[Dict], mock_console_fixture: Mock):
    service_instance._display_cycles_results(sample_cycles_data_with_details, "csv", True)
    
    output = io.StringIO()
    fieldnames = ['cycle_id', 'length', 'complexity', 'cycle_path', 'node_ids', 'node_names', 'node_types', 'node_packages']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for cycle in sample_cycles_data_with_details:
        row = {
            'cycle_id': cycle['cycle_id'], 'length': cycle['length'],
            'complexity': cycle['complexity'], 'cycle_path': cycle['cycle_path']
        }
        if 'node_details' in cycle:
            details = cycle['node_details']
            row['node_ids'] = ';'.join(str(nd['id']) for nd in details)
            row['node_names'] = ';'.join(str(nd['name']) for nd in details)
            row['node_types'] = ';'.join(str(nd['type']) for nd in details)
            row['node_packages'] = ';'.join(str(nd['package']) for nd in details)
        writer.writerow(row)
        
    mock_console_fixture.print.assert_called_once_with(output.getvalue())

def test_display_empty_data(service_instance: CLIService, mock_console_fixture: Mock, mock_table_fixture: Mock):
    # Table format
    service_instance._display_cycles_results([], "table", False)
    mock_table_fixture.add_row.assert_not_called() # No rows for empty data
    mock_console_fixture.print.assert_any_call(ANY)
    mock_console_fixture.reset_mock()

    # JSON format
    service_instance._display_cycles_results([], "json", False)
    mock_console_fixture.print_json.assert_called_once_with(json.dumps([], indent=2))
    mock_console_fixture.reset_mock()

    # CSV format
    service_instance._display_cycles_results([], "csv", False)
    output = io.StringIO()
    mock_console_fixture.print.assert_called_once_with(output.getvalue()) # Header only

# Test Cases for CLIService._save_cycles_results()

@patch("builtins.open", new_callable=mock_open)
def test_save_json(mock_open: Mock, service_instance: CLIService, sample_cycles_data_no_details: List[Dict], tmp_path: Path):
    output_fname = "out"
    file_path = tmp_path / f"{output_fname}.json"
    service_instance.settings.project_root = tmp_path # Needed for ensure_output_directory if it uses settings

    service_instance._save_cycles_results(sample_cycles_data_no_details, str(tmp_path / output_fname), "json")
    
    mock_open.assert_called_once_with(file_path, 'w')
    # handle = mock_open()
    # json.dump will call handle.write multiple times for formatted JSON
    # We can check if the first argument to json.dump was our data
    # For more precise check, capture all writes and reconstruct JSON, or use a spy on json.dump
    with patch('json.dump') as mock_json_dump:
        service_instance._save_cycles_results(sample_cycles_data_no_details, str(tmp_path / output_fname), "json")
        mock_json_dump.assert_called_once_with(sample_cycles_data_no_details, ANY, indent=2)

@patch("builtins.open", new_callable=mock_open)
def test_save_csv_no_details_in_file(mock_open: Mock, service_instance: CLIService, sample_cycles_data_with_details: List[Dict], tmp_path: Path):
    output_fname = "out"
    file_path = tmp_path / f"{output_fname}.csv"
    service_instance.settings.project_root = tmp_path

    service_instance._save_cycles_results(sample_cycles_data_with_details, str(tmp_path / output_fname), "csv")
    
    mock_open.assert_called_once_with(file_path, 'w', newline='')
    # handle = mock_open()
    
    # Construct expected CSV content
    expected_output = io.StringIO()
    fieldnames = ['cycle_id', 'length', 'complexity', 'cycle_path']
    writer = csv.DictWriter(expected_output, fieldnames=fieldnames)
    writer.writeheader()
    for cycle in sample_cycles_data_with_details: # Data has details, but function saves only these fields for CSV
        writer.writerow({
            'cycle_id': cycle['cycle_id'],
            'length': cycle['length'],
            'complexity': cycle['complexity'],
            'cycle_path': cycle['cycle_path']
        })
    
    # Check calls to write (header then rows)
    # This is tricky with mock_open. It might be easier to check the content if we could read it back.
    # For now, let's check that DictWriter was used correctly.
    with patch('csv.DictWriter') as mock_csv_writer_cls:
        mock_writer_instance = Mock()
        mock_csv_writer_cls.return_value = mock_writer_instance
        service_instance._save_cycles_results(sample_cycles_data_with_details, str(tmp_path / output_fname), "csv")
        mock_csv_writer_cls.assert_called_with(ANY, fieldnames=fieldnames)
        mock_writer_instance.writeheader.assert_called_once()
        assert mock_writer_instance.writerow.call_count == len(sample_cycles_data_with_details)


@patch("builtins.open", new_callable=mock_open)
def test_save_table_as_text(mock_open: Mock, mocker, service_instance: CLIService, sample_cycles_data_no_details: List[Dict], tmp_path: Path):
    output_fname = "out"
    file_path = tmp_path / f"{output_fname}.txt"
    service_instance.settings.project_root = tmp_path

    service_instance._save_cycles_results(sample_cycles_data_no_details, str(tmp_path / output_fname), "table")
    
    mock_open.assert_called_once_with(file_path, 'w')
    handle = mock_open()
    handle.write.assert_any_call("Circular Dependencies Analysis\n")
    handle.write.assert_any_call("=" * 50 + "\n\n")
    for cycle in sample_cycles_data_no_details:
        handle.write.assert_any_call(f"Cycle {cycle['cycle_id']}:\n")
        handle.write.assert_any_call(f"  Length: {cycle['length']}\n")
        handle.write.assert_any_call(f"  Complexity: {cycle['complexity']}\n")
        handle.write.assert_any_call(f"  Path: {cycle['cycle_path']}\n\n")

@patch("builtins.open", side_effect=IOError("Disk full"))
def test_save_file_write_error(mocker, service_instance: CLIService, sample_cycles_data_no_details: List[Dict], tmp_path: Path):
    output_fname = "out"
    file_path = tmp_path / f"{output_fname}.json"
    service_instance.settings.project_root = tmp_path

    # FIX: Patch print_success BEFORE calling the method
    mock_print_success = mocker.patch('dependency_analyzer.cli.utils.print_success')

    with pytest.raises(CLIError, match=f"Failed to save results to '{file_path}': Disk full"):
        service_instance._save_cycles_results(sample_cycles_data_no_details, str(tmp_path / output_fname), "json")
    
    mock_print_success.assert_not_called()

@patch("builtins.open", new_callable=mock_open)
def test_save_empty_data_to_file(mock_open: Mock, service_instance: CLIService, tmp_path: Path):
    output_fname = "empty_out"
    service_instance.settings.project_root = tmp_path

    # JSON
    json_path = tmp_path / f"{output_fname}.json"
    with patch('json.dump') as mock_json_dump:
        service_instance._save_cycles_results([], str(tmp_path / output_fname), "json")
        mock_open.assert_called_with(json_path, 'w')
        mock_json_dump.assert_called_with([], ANY, indent=2)
    mock_open.reset_mock()

    # CSV
    with patch('csv.DictWriter') as mock_csv_writer_cls:
        mock_writer_instance = Mock()
        mock_csv_writer_cls.return_value = mock_writer_instance
        service_instance._save_cycles_results([], str(tmp_path / output_fname), "csv")
        
        # For empty data, CSV writer is not created due to the `if cycles_info:` condition
        mock_csv_writer_cls.assert_not_called()
        mock_writer_instance.writeheader.assert_not_called() # Header should be written
        mock_writer_instance.writerow.assert_not_called() # No data rows
    mock_open.reset_mock()

    # Text
    txt_path = tmp_path / f"{output_fname}.txt"
    service_instance._save_cycles_results([], str(tmp_path / output_fname), "table")
    mock_open.assert_called_with(txt_path, 'w')
    handle = mock_open()
    handle.write.assert_any_call("Circular Dependencies Analysis\n") # Header still written

def test_save_creates_output_directory_if_not_exists(service_instance: CLIService, tmp_path: Path, mocker):
    output_fname = "newdir/out"
    target_dir = tmp_path / "newdir"
    target_file = target_dir / "out.json"
    service_instance.settings.project_root = tmp_path # ensure_output_directory might use this
    
    mock_ensure_dir:Callable = mocker.patch('dependency_analyzer.cli.service.ensure_output_directory')
    
    with patch("builtins.open", new_callable=mock_open) as mock_file_open:
        with patch('json.dump') :
            service_instance._save_cycles_results([{"data":1}], str(tmp_path / output_fname), "json")
            mock_ensure_dir.assert_called_once_with(target_dir, ANY)
            mock_file_open.assert_called_once_with(target_file, 'w')

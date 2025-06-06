import pytest
import tomllib
import tomlkit

from pathlib import Path
from plsql_analyzer.cli import app as cli_app
from plsql_analyzer.settings import CALL_EXTRACTOR_KEYWORDS_TO_DROP
from plsql_analyzer.settings import PLSQLAnalyzerSettings # Added for testing init
from unittest.mock import patch # Added for mocking input

@pytest.fixture
def default_app_config_values():
    # Provides default values from PLSQLAnalyzerSettings for comparison
    # Note: source_code_root_dir is required and has no Pydantic default.
    return {
        "output_base_dir": str(Path("generated/artifacts").resolve()),
        "log_verbose_level": 1,
        "database_filename": "PLSQL_CodeObjects.db",
        "file_extensions_to_include": ["sql"],
        "exclude_names_from_processed_path": [],
        "exclude_names_for_package_derivation": ["PROCEDURES", "PACKAGE_BODIES", "FUNCTIONS"],
        "enable_profiler": False,
        "force_reprocess": [],
        "clear_history_for_file": [],
        "call_extractor_keywords_to_drop": CALL_EXTRACTOR_KEYWORDS_TO_DROP,
    }

@pytest.fixture
def temp_config_file_all_fields(tmp_path: Path) -> Path:
    config_content = {
        "source_code_root_dir": str(tmp_path / "toml_sources"),
        "output_base_dir": str(tmp_path / "toml_output"),
        "log_verbose_level": 3,
        "database_filename": "toml_db.sqlite",
        "file_extensions_to_include": ["*.pkg", "*.pks"],
        "exclude_names_from_processed_path": ["temp", "archive"],
        "exclude_names_for_package_derivation": ["DEV_PACKAGES"],
        "enable_profiler": True,
        "force_reprocess": ["/path/to/force1.sql", "/path/to/force2.sql"],
        "clear_history_for_file": ["processed/path/clear1.sql"],
        "call_extractor_keywords_to_drop": CALL_EXTRACTOR_KEYWORDS_TO_DROP,
    }
    config_file = tmp_path / "detailed_config.toml"
    with open(config_file, "w") as f:
        tomlkit.dump(config_content, f) # Use imported toml for writing

    (tmp_path / "toml_sources").mkdir(exist_ok=True, parents=True)
    (tmp_path / "toml_output").mkdir(exist_ok=True, parents=True)
    return config_file

@pytest.fixture
def dummy_source_dir(tmp_path: Path) -> Path:
    dir_path = tmp_path / "dummy_sources_cli"
    dir_path.mkdir(exist_ok=True, parents=True)
    (dir_path / "file1.sql").touch()
    (dir_path / "file2.pkg").touch()
    return dir_path

@pytest.fixture
def dummy_output_dir(tmp_path: Path) -> Path:
    dir_path = tmp_path / "dummy_output_cli"
    dir_path.mkdir(exist_ok=True, parents=True)
    return dir_path

@pytest.fixture
def mock_run_plsql_analyzer(mocker):
    return mocker.patch("plsql_analyzer.cli.run_plsql_analyzer")

def test_cli_help_parse_command(capsys, mock_run_plsql_analyzer):
    
    cli_app(["parse", "--help"])
    std_out = capsys.readouterr().out
    # The usage line should start with 'Usage:' and include the 'parse' command
    first_line = std_out.splitlines()[0]
    assert first_line.startswith("Usage:") and ' parse' in first_line
    assert "Parse PL/SQL source code" in std_out
    assert "--source-dir" in std_out
    assert "--output-dir" in std_out
    assert "--config-file" in std_out
    assert "--verbose" in std_out
    assert "-v" in std_out
    assert "--profile" in std_out
    assert "--fext" in std_out
    assert "--exd" in std_out
    assert "--exn" in std_out
    assert "--db-filename" in std_out
    assert "--df" in std_out
    # log_file_prefix and log_trace_file_prefix are CLI args, not directly in PLSQLAnalyzerSettings help text
    # but their corresponding PLSQLAnalyzerSettings fields might be if they existed.

def test_cli_parse_missing_source_dir_fails(capsys):
    with pytest.raises(SystemExit) as e:
        cli_app(["parse"])

    std_out = capsys.readouterr().out
    assert e.value.code != 0
    assert "Command \"parse\" parameter \"--source-dir\" requires an argument." in std_out

def test_path_converter_and_validator(capsys, tmp_path: Path):
    # Test non-existent path
    non_existent = tmp_path / "does_not_exist"
    with pytest.raises(SystemExit) as e:
        cli_app(["parse", "--source-dir", str(non_existent)])
    
    std_out = capsys.readouterr().out
    assert "Path" in std_out
    assert "does not exist" in std_out
    assert e.value.code != 0

    # Test valid path
    valid_dir = tmp_path / "exists"
    valid_dir.mkdir()
    cli_app(["parse", "--source-dir", str(valid_dir)])
    std_out = capsys.readouterr().out
    assert "does not exist" not in std_out

def test_cli_argument_aliases(capsys, dummy_source_dir, mocker):
    # Mock the run_plsql_analyzer function to capture the config
    mock_run = mocker.patch('plsql_analyzer.cli.run_plsql_analyzer')
    
    # Test file extension pattern
    cli_app(["parse", "--source-dir", str(dummy_source_dir), "--fext", "sql"])
    config_fext = mock_run.call_args[0][0]  # First argument to run_plsql_analyzer
    assert ["sql"] == config_fext.file_extensions_to_include

    # Test with -e alias
    cli_app(["parse", "--source-dir", str(dummy_source_dir), "-e", "*.pkg"])
    config_e = mock_run.call_args[0][0]  # First argument to run_plsql_analyzer
    assert ["pkg"] == config_e.file_extensions_to_include

    # Test multiple file extensions
    cli_app(["parse", "--source-dir", str(dummy_source_dir), "--fext", "*.sql", ".pks"])
    config_multiple_fext = mock_run.call_args[0][0]  # First argument to run_plsql_analyzer
    assert sorted(["sql", "pks"]) == sorted(config_multiple_fext.file_extensions_to_include)

    cli_app(["parse", "--source-dir", str(dummy_source_dir), "--fext", "*.sql", ".pks", "-e", "pkb"])
    config_multiple_fext = mock_run.call_args[0][0]  # First argument to run_plsql_analyzer
    assert sorted(["sql", "pks", "pkb"]) == sorted(config_multiple_fext.file_extensions_to_include)


    # Test database filename aliases
    cli_app(["parse", "--source-dir", str(dummy_source_dir), "--df", "test1.db"])
    config_dbf = mock_run.call_args[0][0]  # First argument to run_plsql_analyzer
    assert "test1.db" == config_dbf.database_filename

    # Test with full name
    cli_app(["parse", "--source-dir", str(dummy_source_dir), "--db-filename", "test2.db"])
    config_db_filename = mock_run.call_args[0][0]
    assert "test2.db" == config_db_filename.database_filename

def test_cli_multiple_file_extensions(capsys, dummy_source_dir, mocker):
    mock_run = mocker.patch('plsql_analyzer.cli.run_plsql_analyzer')
    extensions = ["*.sql", ".pks", "pkb"]
    cmd = ["parse", "--source-dir", str(dummy_source_dir)]
    for ext in extensions:
        cmd.extend(["--fext", ext])
    
    cli_app(cmd)
    config = mock_run.call_args[0][0]
    assert sorted(config.file_extensions_to_include) == sorted(["sql", "pks", "pkb"])

def test_cli_exclude_dirs_and_names(capsys, dummy_source_dir, mocker):
    mock_run = mocker.patch('plsql_analyzer.cli.run_plsql_analyzer')

    # Test exclude_dirs (--exd)
    exclude_dirs = ["temp", "test", "logs"]
    cmd = ["parse", "--source-dir", str(dummy_source_dir)]
    for d in exclude_dirs:
        cmd.extend(["--exd", d])
    
    cli_app(cmd)
    config = mock_run.call_args[0][0]
    assert sorted(config.exclude_names_from_processed_path) == sorted(exclude_dirs + list(Path.cwd().resolve().parts))

    # Test exclude_names (--exn)
    exclude_names = ["PROCEDURES", "FUNCTIONS"]
    cmd = ["parse", "--source-dir", str(dummy_source_dir)]
    for n in exclude_names:
        cmd.extend(["--exn", n])
    
    cli_app(cmd)
    config = mock_run.call_args[0][0]
    assert sorted(config.exclude_names_for_package_derivation) == sorted(exclude_names + list(Path.cwd().resolve().parts))

def test_cli_verbosity_validation(capsys, dummy_source_dir, mocker):
    mock_run = mocker.patch('plsql_analyzer.cli.run_plsql_analyzer')

    # Test invalid verbosity level
    with pytest.raises(SystemExit) as e:
        cli_app(["parse", "--source-dir", str(dummy_source_dir), "--verbose", "4"])
    std_out = capsys.readouterr().out
    assert "Must be <= 3." in std_out
    assert e.value.code != 0

    with pytest.raises(SystemExit) as e:
        cli_app(["parse", "--source-dir", str(dummy_source_dir), "--verbose", "-1"])
    std_out = capsys.readouterr().out
    assert "Must be >= 0." in std_out
    assert e.value.code != 0

    # Test valid verbosity levels
    for level in range(4):
        cli_app(["parse", "--source-dir", str(dummy_source_dir), "--verbose", str(level)])
        config = mock_run.call_args[0][0]
        assert config.log_verbose_level == level

def test_cli_config_file_precedence(capsys, temp_config_file_all_fields, dummy_source_dir, mocker):
    mock_run = mocker.patch('plsql_analyzer.cli.run_plsql_analyzer')
    # Test that CLI args override config file values
    cli_verbose = 0  # Config file has 3
    cli_db = "cli.db"  # Config file has "toml_db.sqlite"
    cli_extensions = ["*.proc"]  # Config file has ["*.pkg", "*.pks"]
    
    cmd = [
        "parse",
        "--source-dir", str(dummy_source_dir),  # Override source_dir from config
        "--config-file", str(temp_config_file_all_fields),
        "--verbose", str(cli_verbose),
        "--db-filename", cli_db,
        "--fext", cli_extensions[0],
    ]
    
    cli_app(cmd)
    config = mock_run.call_args[0][0]
    
    # CLI values should take precedence
    assert config.log_verbose_level == cli_verbose
    assert config.database_filename == cli_db
    assert config.file_extensions_to_include == ["proc"]
    assert config.source_code_root_dir == dummy_source_dir.resolve()

    # Values from config file not overridden should remain
    assert config.enable_profiler is True  # From config file

def test_cli_empty_config_file(capsys, dummy_source_dir, tmp_path, mocker):
    mock_run = mocker.patch('plsql_analyzer.cli.run_plsql_analyzer')
    # Create an empty config file
    empty_config = tmp_path / "empty.toml"
    empty_config.touch()
    
    # Should work with defaults
    cli_app(["parse", "--source-dir", str(dummy_source_dir), "--config-file", str(empty_config)])
    config = mock_run.call_args[0][0]
    
    # Should use PLSQLAnalyzerSettings defaults
    assert config.log_verbose_level == 1
    assert config.database_filename == "PLSQL_CodeObjects.db"
    assert config.file_extensions_to_include == ["sql"]
    assert not config.enable_profiler

def test_cli_invalid_config_file(capsys, dummy_source_dir, tmp_path):
    # Create an invalid TOML file
    invalid_config = tmp_path / "invalid.toml"
    invalid_config.write_text("this is not valid TOML]")
    
    with pytest.raises(tomllib.TOMLDecodeError):
        cli_app(["parse", "--source-dir", str(dummy_source_dir), "--config-file", str(invalid_config)])

def test_cli_paths_absolute_relative(capsys, dummy_source_dir, tmp_path, mocker):
    mock_run = mocker.patch('plsql_analyzer.cli.run_plsql_analyzer')
    # Test with relative paths
    relative_source = Path("./src")
    relative_output = Path("./output")
    
    # Create the directories
    (tmp_path / "src").mkdir()
    (tmp_path / "output").mkdir()
    
    # Change to tmp_path directory
    import os
    old_cwd = os.getcwd()
    os.chdir(str(tmp_path))
    
    try:
        cli_app(["parse", "--source-dir", str(relative_source), "--output-dir", str(relative_output)])
        config = mock_run.call_args[0][0]
        
        # Paths should be resolved to absolute
        assert config.source_code_root_dir.is_absolute()
        assert config.output_base_dir.is_absolute()
        
        # Resolved paths should point to our temp directories
        assert config.source_code_root_dir.resolve() == (tmp_path / "src").resolve()
        assert config.output_base_dir.resolve() == (tmp_path / "output").resolve()
    
    finally:
        os.chdir(old_cwd)

def test_force_reprocess_option(mocker, dummy_source_dir):
    """Test that the --force-reprocess option is properly parsed and passed to the app config."""

    mock_run = mocker.patch('plsql_analyzer.cli.run_plsql_analyzer')
    cli_app([
        "parse",
        "--source-dir", str(dummy_source_dir),
        "--force-reprocess", "/path/to/file1.sql",
        "--force-reprocess", "/path/to/file2.sql"
    ])
    config = mock_run.call_args[0][0]  # First argument to run_plsql_analyzer
    # The PLSQLAnalyzerSettings should have the force_reprocess list with both files
    assert len(config.force_reprocess) == 2
    assert "/path/to/file1.sql" in config.force_reprocess
    assert "/path/to/file2.sql" in config.force_reprocess

def test_clear_history_for_file_option(mocker, dummy_source_dir):
    """Test that the --clear-history-for-file option is properly parsed and passed to the app config."""
    
    mock_run = mocker.patch('plsql_analyzer.cli.run_plsql_analyzer')
    cli_app([
        "parse",
        "--source-dir", str(dummy_source_dir),
        "--clear-history-for-file", "processed/path/file1.sql",
        "--clear-history-for-file", "processed/path/file2.sql"])
    
    config = mock_run.call_args[0][0]

    # The PLSQLAnalyzerSettings should have the clear_history_for_file list with both files
    assert len(config.clear_history_for_file) == 2
    assert "processed/path/file1.sql" in config.clear_history_for_file
    assert "processed/path/file2.sql" in config.clear_history_for_file

# --- Tests for strict_calls CLI option --- #

def test_cli_strict_calls_option(mocker, tmp_path: Path):
    """Test that the --strict-calls CLI option is properly processed."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    
    mock_run = mocker.patch('plsql_analyzer.cli.run_plsql_analyzer')
    
    # Test with --strict-calls (should set strict_lpar_only_calls=True)
    cli_app([
        "parse",
        "--source-dir", str(source_dir),
        "--strict-calls"
    ])
    
    mock_run.assert_called_once()
    config = mock_run.call_args[0][0]
    assert config.strict_lpar_only_calls

def test_cli_no_strict_calls_option(mocker, tmp_path: Path):
    """Test that the --no-strict-calls CLI option is properly processed."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    
    mock_run = mocker.patch('plsql_analyzer.cli.run_plsql_analyzer')
    
    # Test with --no-strict-calls (should set strict_lpar_only_calls=False)
    cli_app([
        "parse",
        "--source-dir", str(source_dir),
        "--no-strict-calls"
    ])
    
    mock_run.assert_called_once()
    config = mock_run.call_args[0][0]
    assert not config.strict_lpar_only_calls

def test_cli_strict_calls_default(mocker, tmp_path: Path):
    """Test that strict_lpar_only_calls defaults to False when no option is provided."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    
    mock_run = mocker.patch('plsql_analyzer.cli.run_plsql_analyzer')
    
    # Test without any strict-calls option
    cli_app([
        "parse",
        "--source-dir", str(source_dir)
    ])
    
    mock_run.assert_called_once()
    config = mock_run.call_args[0][0]
    assert not config.strict_lpar_only_calls

def test_cli_strict_calls_with_config_file(mocker, tmp_path: Path):
    """Test CLI strict_calls option overrides config file setting."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    
    # Create config file with strict_lpar_only_calls=False
    config_content = {
        "source_code_root_dir": str(source_dir),
        "strict_lpar_only_calls": False
    }
    config_file = tmp_path / "config.toml"
    with open(config_file, "w") as f:
        tomlkit.dump(config_content, f)
    
    mock_run = mocker.patch('plsql_analyzer.cli.run_plsql_analyzer')
    
    # CLI argument should override config file
    cli_app([
        "parse",
        "--source-dir", str(source_dir),
        "--config-file", str(config_file),
        "--strict-calls"
    ])
    
    mock_run.assert_called_once()
    config = mock_run.call_args[0][0]
    assert config.strict_lpar_only_calls  # CLI should override config file

@pytest.mark.parametrize("toml_value,expected_value", [
    (True, True),
    (False, False),
])
def test_config_file_strict_lpar_only_calls(mocker, tmp_path: Path, toml_value, expected_value):
    """Test that strict_lpar_only_calls can be set via TOML config file."""
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    
    config_content = {
        "source_code_root_dir": str(source_dir),
        "strict_lpar_only_calls": toml_value
    }
    config_file = tmp_path / "config.toml"
    with open(config_file, "w") as f:
        tomlkit.dump(config_content, f)
    
    mock_run = mocker.patch('plsql_analyzer.cli.run_plsql_analyzer')
    
    cli_app([
        "parse",
        "--source-dir", str(source_dir),
        "--config-file", str(config_file)
    ])
    
    mock_run.assert_called_once()
    config = mock_run.call_args[0][0]
    assert config.strict_lpar_only_calls == expected_value

# --- Tests for init command ---

def test_cli_init_creates_file(tmp_path: Path, capsys):
    """Test that 'init' command creates a config file."""
    config_file = tmp_path / "plsql_analyzer_config.toml"
    cli_app(["init", "--file-path", str(config_file)])
    
    assert config_file.exists()
    captured = capsys.readouterr()
    assert f"Successfully created configuration file: {config_file.resolve()}" in captured.out

def test_cli_init_creates_file_default_path(tmp_path: Path, capsys, mocker):
    """Test that 'init' command creates a config file in the current directory by default."""
    
    # Mock Path.cwd() to control the current working directory for the test
    mocker.patch("pathlib.Path.cwd", return_value=tmp_path)
    
    config_file = tmp_path / "plsql_analyzer_config.toml"
    
    cli_app(["init"]) # No --file-path, should use cwd
    
    assert config_file.exists()
    captured = capsys.readouterr()
    assert f"Successfully created configuration file: {config_file.resolve()}" in captured.out


def test_cli_init_file_content(tmp_path: Path):
    """Test the content of the generated config file."""
    config_file = tmp_path / "plsql_analyzer_config.toml"
    cli_app(["init", "--file-path", str(config_file)])

    content = config_file.read_text()
    assert "PL/SQL Analyzer Configuration File" in content
    assert "Generated by 'plsql-analyzer init'" in content

    # Verify some settings are present
    loaded_toml = tomllib.loads(content)
    
    # Check for a required field with a placeholder
    assert "source_code_root_dir" in loaded_toml
    assert loaded_toml["source_code_root_dir"] == "./plsql_source_code"

    # Check for a field with a default value
    assert "log_verbose_level" in loaded_toml
    assert loaded_toml["log_verbose_level"] == PLSQLAnalyzerSettings.model_fields["log_verbose_level"].get_default(call_default_factory=True)

    assert "database_filename" in loaded_toml
    assert loaded_toml["database_filename"] == PLSQLAnalyzerSettings.model_fields["database_filename"].get_default(call_default_factory=True)
    
    assert "file_extensions_to_include" in loaded_toml
    assert loaded_toml["file_extensions_to_include"] == PLSQLAnalyzerSettings.model_fields["file_extensions_to_include"].get_default(call_default_factory=True)

    # Check that computed fields are not in the generated config
    assert "artifacts_dir" not in loaded_toml
    assert "logs_dir" not in loaded_toml
    assert "database_path" not in loaded_toml


@patch("builtins.input", return_value="y")
def test_cli_init_overwrite_existing_file_yes(mock_input, tmp_path: Path, capsys):
    """Test overwriting an existing file when user confirms."""
    config_file = tmp_path / "plsql_analyzer_config.toml"
    config_file.write_text("initial content")

    cli_app(["init", "--file-path", str(config_file)])
    
    mock_input.assert_called_once()
    captured = capsys.readouterr()
    assert f"Successfully created configuration file: {config_file.resolve()}" in captured.out
    
    content = config_file.read_text()
    assert "initial content" not in content # Should be overwritten
    assert "PL/SQL Analyzer Configuration File" in content

@patch("builtins.input", return_value="N")
def test_cli_init_overwrite_existing_file_no(mock_input, tmp_path: Path, capsys):
    """Test not overwriting an existing file when user denies."""
    config_file = tmp_path / "plsql_analyzer_config.toml"
    initial_content = "initial content"
    config_file.write_text(initial_content)

    cli_app(["init", "--file-path", str(config_file)])
    
    mock_input.assert_called_once()
    captured = capsys.readouterr()
    assert "Aborted. Configuration file not created." in captured.out
    
    content = config_file.read_text()
    assert content == initial_content # Should not be overwritten

def test_cli_init_force_overwrite(tmp_path: Path, capsys):
    """Test --force option overwrites without prompting."""
    config_file = tmp_path / "plsql_analyzer_config.toml"
    config_file.write_text("initial content")

    with patch("builtins.input") as mock_input: # Ensure input is not called
        cli_app(["init", "--file-path", str(config_file), "--force"])
        mock_input.assert_not_called()

    captured = capsys.readouterr()
    assert f"Successfully created configuration file: {config_file.resolve()}" in captured.out
    
    content = config_file.read_text()
    assert "initial content" not in content
    assert "PL/SQL Analyzer Configuration File" in content

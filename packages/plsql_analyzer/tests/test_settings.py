import tempfile
from pathlib import Path
from plsql_analyzer.settings import PLSQLAnalyzerSettings

def test_default_instantiation():
    config = PLSQLAnalyzerSettings(source_code_root_dir="/tmp")
    assert config.source_code_root_dir == Path("/tmp").resolve()
    assert config.output_base_dir == Path("generated/artifacts").resolve()
    assert config.log_verbose_level == 1
    assert config.database_filename == "PLSQL_CodeObjects.db"
    assert config.file_extensions_to_include == ["sql"]
    assert sorted(config.exclude_names_from_processed_path) == sorted(list(Path.cwd().resolve().parts))
    assert sorted(config.exclude_names_for_package_derivation) == sorted(["PROCEDURES", "PACKAGE_BODIES", "FUNCTIONS"] + list(Path.cwd().resolve().parts))
    assert config.enable_profiler is False

def test_override_values():
    config = PLSQLAnalyzerSettings(
        source_code_root_dir="src",
        output_base_dir="out",
        log_verbose_level=2,
        database_filename="test.db",
        file_extensions_to_include=["*.foo"],
        exclude_names_from_processed_path=["bar"],
        enable_profiler=True
    )
    assert config.source_code_root_dir == Path("src").resolve()
    assert config.output_base_dir == Path("out").resolve()
    assert config.log_verbose_level == 2
    assert config.database_filename == "test.db"
    assert config.file_extensions_to_include == ["foo"]
    assert sorted(config.exclude_names_from_processed_path) == sorted(["bar"] + list(Path.cwd().resolve().parts))
    assert sorted(config.exclude_names_for_package_derivation) == sorted(["PROCEDURES", "PACKAGE_BODIES", "FUNCTIONS"] + ["bar"] + list(Path.cwd().resolve().parts))
    assert config.enable_profiler is True

def test_derived_properties():
    config = PLSQLAnalyzerSettings(source_code_root_dir="/tmp", output_base_dir="/tmp/out", database_filename="foo.db")
    assert config.artifacts_dir == Path("/tmp/out").resolve()
    assert config.logs_dir == Path("/tmp/out/logs/plsql_analyzer").resolve()
    assert config.database_path == Path("/tmp/out/foo.db").resolve()

def test_ensure_artifact_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = PLSQLAnalyzerSettings(source_code_root_dir=tmpdir, output_base_dir=tmpdir)
        logs_dir = config.logs_dir
        assert not logs_dir.exists()
        config.ensure_artifact_dirs()
        assert config.artifacts_dir.exists()
        assert config.logs_dir.exists()

def test_path_expansion(monkeypatch):
    monkeypatch.setenv("MY_TEST_DIR", "/tmp/mytest")
    config = PLSQLAnalyzerSettings(
        source_code_root_dir="~/../",  # Should expand user
        output_base_dir="$MY_TEST_DIR/subdir"  # Should expand env var
    )
    assert str(config.source_code_root_dir).startswith(str(Path.home().parent))
    assert config.output_base_dir == Path("/tmp/mytest/subdir").resolve()

def test_call_analysis_settings():
    """Test call analysis related settings including the new strict_lpar_only_calls."""
    # Test default values
    config = PLSQLAnalyzerSettings(source_code_root_dir="/tmp")
    assert not config.allow_parameterless_calls
    assert not config.strict_lpar_only_calls
    
    # Test explicit values
    config_custom = PLSQLAnalyzerSettings(
        source_code_root_dir="/tmp",
        allow_parameterless_calls=True,
        strict_lpar_only_calls=True
    )
    assert config_custom.allow_parameterless_calls
    assert config_custom.strict_lpar_only_calls

def test_strict_lpar_only_calls_boolean_validation():
    """Test that strict_lpar_only_calls accepts boolean values and type coercion."""
    # Valid boolean values
    config_true = PLSQLAnalyzerSettings(source_code_root_dir="/tmp", strict_lpar_only_calls=True)
    assert config_true.strict_lpar_only_calls
    
    config_false = PLSQLAnalyzerSettings(source_code_root_dir="/tmp", strict_lpar_only_calls=False)
    assert not config_false.strict_lpar_only_calls
    
    # Test that Pydantic performs type coercion for common boolean representations
    # These should be coerced to boolean values, not raise errors
    config_str_true = PLSQLAnalyzerSettings(source_code_root_dir="/tmp", strict_lpar_only_calls="true")
    assert config_str_true.strict_lpar_only_calls
    
    config_str_false = PLSQLAnalyzerSettings(source_code_root_dir="/tmp", strict_lpar_only_calls="false")
    assert not config_str_false.strict_lpar_only_calls
    
    config_int_true = PLSQLAnalyzerSettings(source_code_root_dir="/tmp", strict_lpar_only_calls=1)
    assert config_int_true.strict_lpar_only_calls
    
    config_int_false = PLSQLAnalyzerSettings(source_code_root_dir="/tmp", strict_lpar_only_calls=0)
    assert not config_int_false.strict_lpar_only_calls

def test_settings_field_descriptions():
    """Test that the new setting has proper field description."""
    from plsql_analyzer.settings import PLSQLAnalyzerSettings
    
    # Get field info from the Pydantic model
    fields = PLSQLAnalyzerSettings.model_fields
    
    # Check that strict_lpar_only_calls field exists and has description
    assert 'strict_lpar_only_calls' in fields
    field_info = fields['strict_lpar_only_calls']
    assert field_info.description is not None
    assert "only identifiers followed by '('" in field_info.description
    assert "ignoring ';' terminated identifiers" in field_info.description

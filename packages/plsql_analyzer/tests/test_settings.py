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

import tempfile
from pathlib import Path
from plsql_analyzer.settings import AppConfig

def test_default_instantiation():
    config = AppConfig(source_code_root_dir="/tmp")
    assert config.source_code_root_dir == Path("/tmp")
    assert config.output_base_dir == Path("generated/artifacts").resolve()
    assert config.log_verbose_level == 1
    assert config.log_file_prefix == "dependency_debug_"
    assert config.log_trace_file_prefix == "dependency_trace_"
    assert config.database_filename == "dependency_graph.db"
    assert config.include_patterns == ["*.sql", "*.pls"]
    assert config.exclude_dirs == ["__pycache__", ".git", "tests", "logs"]
    assert config.enable_profiler is False

def test_override_values():
    config = AppConfig(
        source_code_root_dir="src",
        output_base_dir="out",
        log_verbose_level=2,
        log_file_prefix="log_",
        log_trace_file_prefix="trace_",
        database_filename="test.db",
        include_patterns=["*.foo"],
        exclude_dirs=["bar"],
        enable_profiler=True
    )
    assert config.source_code_root_dir == Path("src").resolve()
    assert config.output_base_dir == Path("out").resolve()
    assert config.log_verbose_level == 2
    assert config.log_file_prefix == "log_"
    assert config.log_trace_file_prefix == "trace_"
    assert config.database_filename == "test.db"
    assert config.include_patterns == ["*.foo"]
    assert config.exclude_dirs == ["bar"]
    assert config.enable_profiler is True

def test_derived_properties():
    config = AppConfig(source_code_root_dir="/tmp", output_base_dir="/tmp/out", database_filename="foo.db")
    assert config.artifacts_dir == Path("/tmp/out").resolve()
    assert config.logs_dir == Path("/tmp/out/logs").resolve()
    assert config.database_path == Path("/tmp/out/foo.db").resolve()

def test_ensure_artifact_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = AppConfig(source_code_root_dir=tmpdir, output_base_dir=tmpdir)
        logs_dir = config.logs_dir
        assert not logs_dir.exists()
        config.ensure_artifact_dirs()
        assert config.artifacts_dir.exists()
        assert config.logs_dir.exists()

def test_path_expansion(monkeypatch):
    monkeypatch.setenv("MY_TEST_DIR", "/tmp/mytest")
    config = AppConfig(
        source_code_root_dir="~/../",  # Should expand user
        output_base_dir="$MY_TEST_DIR/subdir"  # Should expand env var
    )
    assert str(config.source_code_root_dir).startswith(str(Path.home().parent))
    assert config.output_base_dir == Path("/tmp/mytest/subdir").resolve()

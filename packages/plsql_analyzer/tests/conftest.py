# tests/conftest.py
from __future__ import annotations
import pytest
import loguru
import sys

from plsql_analyzer.settings import PLSQLAnalyzerSettings

@pytest.fixture(scope="session")
def test_logger() -> loguru.Logger:
    """A logger instance for tests, outputting to stderr at TRACE level for visibility."""
    logger = loguru.logger
    logger.remove() # Remove any default handlers
    logger.add(
        sys.stderr,
        level="TRACE", # Set to TRACE to see all logs during tests
        colorize=True,
        format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    return logger

@pytest.fixture
def caplog(caplog: pytest.LogCaptureFixture):
    logger = loguru.logger
    handler_id = logger.add(
        caplog.handler,
        format="{message}",
        level=0,
        filter=lambda record: record["level"].no >= caplog.handler.level,
        enqueue=False,  # Set to 'True' if your test is spawning child processes.
    )
    yield caplog
    logger.remove(handler_id)

@pytest.fixture
def temp_db_path(tmp_path):
    """Provides a temporary path for a test database."""
    return tmp_path / "test_plsql_analysis.db"

@pytest.fixture
def sample_app_config(tmp_path):
    """Provides an PLSQLAnalyzerSettings instance with test values."""
    test_source_dir = tmp_path / "source"
    test_output_dir = tmp_path / "output"
    
    # Create directories
    test_source_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a config instance with test values
    config = PLSQLAnalyzerSettings(
        source_code_root_dir=test_source_dir,
        output_base_dir=test_output_dir,
        log_verbose_level=3,  # TRACE for tests
        file_extensions_to_include=["sql"],
        exclude_names_from_processed_path=["/mnt/some_base"],
        exclude_names_for_package_derivation=["src", "sources", "db_objects"],
        call_extractor_keywords_to_drop=["IF", "LOOP", "BEGIN", "SELECT"]
    )
    
    # Create necessary directories
    config.ensure_artifact_dirs()
    
    return config

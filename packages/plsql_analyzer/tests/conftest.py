# tests/conftest.py
from __future__ import annotations
import pytest
import loguru
import sys
from pathlib import Path

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
def sample_config_dict():
    """Provides a sample configuration dictionary for tests."""
    # Mock parts of the config that might be used by components directly or indirectly
    # In a real scenario, you might load a test-specific config or mock config module access
    class MockConfig:
        LOG_VERBOSE_LEVEL = 3 # TRACE for tests
        LOGS_DIR = Path("temp_test_logs") # Temporary log dir
        DATABASE_PATH = Path("temp_test_db.db")
        EXCLUDE_FROM_PROCESSED_PATH = ["/mnt/some_base"]
        EXCLUDE_FROM_PATH_FOR_PACKAGE_DERIVATION = ["src", "sources", "db_objects"]
        FILE_EXTENSION = "sql"
        CALL_EXTRACTOR_KEYWORDS_TO_DROP = ["IF", "LOOP", "BEGIN"]
        SOURCE_CODE_ROOT_DIR = Path("/mock/source/root")

    # Ensure mock logs dir exists for tests that might try to write there via logger setup
    MockConfig.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return MockConfig()

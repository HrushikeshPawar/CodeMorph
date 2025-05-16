from __future__ import annotations
import pytest
import loguru
import sys

@pytest.fixture(scope="session")
def da_test_logger() -> loguru.Logger:
    """A logger instance for dependency_analyzer tests."""
    logger = loguru.logger
    logger.remove() 
    logger.add(
        sys.stderr,
        level="TRACE", 
        colorize=True,
        format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | DA_TESTS | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
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

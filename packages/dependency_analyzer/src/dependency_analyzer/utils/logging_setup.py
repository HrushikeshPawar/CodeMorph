# plsql_analyzer/utils/logging_setup.py
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime
import loguru as lg # Ensure loguru is installed: pip install loguru

# Renamed to avoid conflict with the loguru.logger object
global_logger = lg.logger 

def configure_logger(verbose_lvl: int, log_dir: Path) -> lg.Logger:
    """
    Configures the global logger for:
    - Console output based on verbose_lvl.
    - A dedicated DEBUG log file for every run.
    - A dedicated TRACE log file for every run.

    Args:
        verbose_lvl: Controls console verbosity (0=WARN, 1=INFO, 2=DEBUG, 3=TRACE).
        log_dir: The directory where log files will be stored.
    Returns:
        Configured loguru logger instance.
    """
    global_logger.remove()  # Remove previous handlers to avoid duplicates

    # --- Console Logging Level (Determined by verbose_lvl) ---
    console_level: str
    if verbose_lvl == 0:
        console_level = "WARNING"
    elif verbose_lvl == 1:
        console_level = "INFO"
    elif verbose_lvl == 2:
        console_level = "DEBUG"
    else:  # verbose_lvl >= 3
        console_level = "TRACE"

    # --- Add Console Sink ---
    global_logger.add(
        sys.stderr,
        level=console_level,
        colorize=True,
        format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    global_logger.info(f"Console logging configured to level: {console_level}")

    # --- Add Fixed TRACE File Sink --- #
    current_datetime = datetime.now().strftime("%Y%m%d_%Hh")
    try:
        # Directory creation already attempted above
        trace_log_filename = log_dir / f"dependency_trace_{current_datetime}.log"

        global_logger.add(
            trace_log_filename,
            level="TRACE",
            rotation="1 GB", # Trace logs can be larger
            backtrace=True,
            diagnose=True,
            catch=True,
            retention=10,
            compression=None,
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            enqueue=True,
        )
        global_logger.info(f"TRACE file logging configured (Level: TRACE) to '{trace_log_filename}'")

    except Exception as e:
        global_logger.error(f"Failed to configure TRACE file logging in '{log_dir}': {e}")
    
    # --- Add Fixed DEBUG File Sink --- #
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        debug_log_filename = log_dir / f"dependency_debug_{current_datetime}.log"

        global_logger.add(
            debug_log_filename,
            level="DEBUG",
            rotation="1 GB",
            retention=5,
            compression=None,
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            enqueue=True,
        )
        global_logger.info(f"DEBUG file logging configured (Level: DEBUG) to '{debug_log_filename}'")

    except Exception as e:
        global_logger.error(f"Failed to configure DEBUG file logging in '{log_dir}': {e}")

    return global_logger.opt(colors=True)
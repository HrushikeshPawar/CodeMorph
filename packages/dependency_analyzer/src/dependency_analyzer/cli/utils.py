"""
Utility functions for CLI operations.

This module provides common utilities used across CLI commands including
path resolution, format inference, validation, and error handling.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Union, Dict, Any

import loguru as lg

from dependency_analyzer.settings import DependencyAnalyzerSettings
from dependency_analyzer.cli.constants import (
    ERROR_MESSAGES, SUPPORTED_GRAPH_FORMATS, 
    GRAPH_EXTENSIONS, PERCENTILE_RANGE, DEPTH_RANGE, ERROR_SUGGESTIONS
)


class CLIError(Exception):
    """Custom exception for CLI errors with user-friendly messages."""
    
    def __init__(self, message: str, suggestion: Optional[str] = None, exit_code: int = 1):
        self.message = message
        self.suggestion = suggestion
        self.exit_code = exit_code
        super().__init__(message)


def handle_cli_error(error: Union[CLIError, Exception], logger: lg.Logger) -> None:
    """
    Handle CLI errors with consistent logging and user feedback.
    
    Args:
        error: The error to handle
        logger: Logger instance for structured logging
    """
    if isinstance(error, CLIError):
        logger.error(error.message)
        if error.suggestion:
            print(f"💡 Suggestion: {error.suggestion}")
        sys.exit(error.exit_code)
    else:
        logger.error(f"Unexpected error: {error}")
        print("💡 This appears to be an unexpected error. Please check the logs for details.")
        sys.exit(1)


def resolve_config_file(config_file: Optional[Path]) -> Optional[Path]:
    """
    Resolve configuration file with fallback to auto-discovery.
    
    Args:
        config_file: Explicitly provided config file path
        
    Returns:
        Resolved config file path or None if not found
        
    Raises:
        CLIError: If explicitly provided config file doesn't exist
    """
    if config_file:
        if not config_file.exists():
            raise CLIError(
                ERROR_MESSAGES['file_not_found'].format(path=config_file),
                "Check the path and ensure the file exists."
            )
        return config_file
    
    # Auto-discovery in current directory
    auto_config = Path.cwd() / DependencyAnalyzerSettings.DEFAULT_CONFIG_FILENAME
    if auto_config.exists():
        return auto_config
    
    return None


def infer_graph_format(file_path: Path, explicit_format: Optional[str] = None) -> str:
    """
    Infer graph format from file extension or use explicit format.
    
    Args:
        file_path: Path to the graph file
        explicit_format: Explicitly specified format
        
    Returns:
        Inferred or explicit format
        
    Raises:
        CLIError: If format cannot be determined or is unsupported
    """
    if explicit_format:
        if explicit_format.lower() not in SUPPORTED_GRAPH_FORMATS:
            raise CLIError(
                ERROR_MESSAGES['invalid_format'].format(
                    format=explicit_format,
                    supported_formats=', '.join(SUPPORTED_GRAPH_FORMATS)
                ),
                f"Use one of: {', '.join(SUPPORTED_GRAPH_FORMATS)}"
            )
        return explicit_format.lower()
    
    # Infer from file extension
    extension = file_path.suffix.lower()
    if extension in GRAPH_EXTENSIONS:
        return GRAPH_EXTENSIONS[extension]
    
    # Default fallback
    return "gpickle"


def validate_percentile(value: float, parameter_name: str) -> None:
    """
    Validate percentile value is within valid range.
    
    Args:
        value: Percentile value to validate
        parameter_name: Name of the parameter for error reporting
        
    Raises:
        CLIError: If percentile is outside valid range
    """
    if not (PERCENTILE_RANGE[0] <= value <= PERCENTILE_RANGE[1]):
        raise CLIError(
            ERROR_MESSAGES['invalid_percentile'].format(value=value),
            f"For {parameter_name}, use a value between {PERCENTILE_RANGE[0]} and {PERCENTILE_RANGE[1]}"
        )


def validate_depth(value: int, parameter_name: str) -> None:
    """
    Validate depth value is within reasonable range.
    
    Args:
        value: Depth value to validate
        parameter_name: Name of the parameter for error reporting
        
    Raises:
        CLIError: If depth is outside valid range
    """
    if not (DEPTH_RANGE[0] <= value <= DEPTH_RANGE[1]):
        raise CLIError(
            ERROR_MESSAGES['invalid_depth'].format(value=value),
            f"For {parameter_name}, use a value between {DEPTH_RANGE[0]} and {DEPTH_RANGE[1]}"
        )


def validate_file_exists(file_path: Path, file_type: str = "file") -> None:
    """
    Validate that a file exists and provide helpful error message.
    
    Args:
        file_path: Path to validate
        file_type: Type of file for error message
        
    Raises:
        CLIError: If file doesn't exist
    """
    if not file_path.exists():
        if file_type == "graph":
            raise CLIError(
                ERROR_MESSAGES['graph_not_found'].format(path=file_path),
                "Make sure you've built the graph first using the 'build' command."
            )
        elif file_type == "database":
            raise CLIError(
                ERROR_MESSAGES['database_not_found'].format(path=file_path),
                "Run the PL/SQL analyzer first to generate the database file."
            )
        else:
            raise CLIError(
                ERROR_MESSAGES['file_not_found'].format(path=file_path),
                f"Ensure the {file_type} exists and is readable."
            )


def ensure_output_directory(output_path: Path, logger: lg.Logger) -> None:
    """
    Ensure output directory exists, creating it if necessary.
    
    Args:
        output_path: Path where output will be written
        logger: Logger instance
        
    Raises:
        CLIError: If directory cannot be created
    """
    try:
        output_dir = output_path.parent if output_path.suffix else output_path
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured output directory exists: {output_dir}")
    except PermissionError:
        raise CLIError(
            ERROR_MESSAGES['permission_denied'].format(path=output_dir),
            ERROR_SUGGESTIONS['permission_fix']
        )
    except Exception as e:
        raise CLIError(
            f"Failed to create output directory {output_dir}: {e}",
            "Check the path and permissions."
        )


def load_settings_with_overrides(
    config_file: Optional[Path] = None, 
    logger: Optional[lg.Logger] = None,
    **overrides
) -> DependencyAnalyzerSettings:
    """
    Load settings with proper precedence and error handling.
    
    Args:
        config_file: Optional config file path
        logger: Optional logger for reporting
        **overrides: CLI parameter overrides
        
    Returns:
        Loaded settings with overrides applied
        
    Raises:
        CLIError: If configuration cannot be loaded
    """
    # Remove None values to avoid overriding config values
    clean_overrides = {k: v for k, v in overrides.items() if v is not None}
    
    try:
        config_path = resolve_config_file(config_file)
        
        if config_path:
            if logger:
                logger.info(f"Loading configuration from {config_path}")
            settings = DependencyAnalyzerSettings.from_toml(config_path)
        else:
            if logger:
                logger.info("Using default configuration (no config file found)")
            settings = DependencyAnalyzerSettings()
        
        # Apply CLI overrides
        for key, value in clean_overrides.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
                if logger:
                    logger.debug(f"Applied CLI override: {key} = {value}")
        
        return settings
        
    except Exception as e:
        raise CLIError(
            ERROR_MESSAGES['config_load_error'].format(
                path=config_file or "auto-discovery", 
                error=str(e)
            ),
            "Check the configuration file syntax and permissions."
        )


def generate_output_path(
    base_dir: Path,
    filename: str,
    extension: str,
    add_timestamp: bool = False,
    settings: Optional[DependencyAnalyzerSettings] = None
) -> Path:
    """
    Generate a full output path with optional timestamp.
    
    Args:
        base_dir: Base directory for output
        filename: Base filename without extension
        extension: File extension (with or without dot)
        add_timestamp: Whether to add timestamp to filename
        settings: Settings object for timestamp access
        
    Returns:
        Complete output path
    """
    # Ensure extension starts with dot
    if not extension.startswith('.'):
        extension = f'.{extension}'
    
    if add_timestamp and settings:
        filename = f"{filename}_{settings.timestamp}"
    
    return base_dir / f"{filename}{extension}"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def print_success(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Print a success message with optional details.
    
    Args:
        message: Success message to display
        details: Optional details to include
    """
    print(f"✅ {message}")
    if details:
        for key, value in details.items():
            print(f"   {key}: {value}")


def print_warning(message: str, suggestion: Optional[str] = None) -> None:
    """
    Print a warning message with optional suggestion.
    
    Args:
        message: Warning message to display
        suggestion: Optional suggestion
    """
    print(f"⚠️  {message}")
    if suggestion:
        print(f"   💡 {suggestion}")


def print_info(message: str) -> None:
    """
    Print an informational message.
    
    Args:
        message: Info message to display
    """
    print(f"ℹ️  {message}")

"""Utility functions for date parsing, file operations, and logging."""
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


def parse_date(date_str: Optional[str], default: datetime) -> datetime:
    """Parses a date string in YYYY-MM-DD format.

    Args:
        date_str: The date string to parse.
        default: The default datetime to return if parsing fails.

    Returns:
        The parsed datetime object or the default value.
    """
    if date_str is None:
        return default
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return default


def ensure_dir(path: Path) -> Path:
    """Ensures that a directory exists, creating it if necessary.

    Args:
        path: The directory path to check and create.

    Returns:
        The same Path object that was passed in.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def setup_logging(level=logging.INFO) -> None:
    """Configures basic logging for the application.

    Sets up a basic configuration for the root logger to output messages
    to the console.

    Args:
        level: The minimum logging level to display (e.g., logging.INFO).
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def clean_dir(path: Path) -> None:
    """Recursively deletes a directory and its contents, or a single file.

    Ignores errors if the path does not exist.

    Args:
        path: The file or directory path to delete.
    """
    if not path.exists():
        return
    if path.is_file():
        try:
            path.unlink()
        except OSError as e:
            logging.warning(f"Error removing file {path}: {e}")
        return

    try:
        shutil.rmtree(path)
    except OSError as e:
        logging.warning(f"Error removing directory {path}: {e}")

"""Utility functions for date parsing and file operations."""
from datetime import datetime
from pathlib import Path
from typing import Optional


def parse_date(date_str: Optional[str], default: datetime) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    if date_str is None:
        return default
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return default


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists and return Path object."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_temp_media(temp_dir: Path) -> None:
    """Clean temporary media directory."""
    if temp_dir.exists():
        for file in temp_dir.iterdir():
            if file.is_file():
                file.unlink()

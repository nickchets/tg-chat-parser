"""Tests for utility functions in src/utils.py."""

import logging
from datetime import datetime
from pathlib import Path

import pytest

from src.utils import clean_dir, ensure_dir, parse_date, setup_logging


def test_parse_date_valid():
    """Test that parse_date handles valid YYYY-MM-DD strings."""
    expected = datetime(2023, 10, 26)
    result = parse_date("2023-10-26", datetime.now())
    assert result == expected


def test_parse_date_invalid_returns_default():
    """Test that parse_date returns the default value for invalid strings."""
    default_date = datetime(2000, 1, 1)
    result = parse_date("invalid-date", default_date)
    assert result == default_date


def test_parse_date_none_returns_default():
    """Test that parse_date returns the default value for None input."""
    default_date = datetime(2000, 1, 1)
    result = parse_date(None, default_date)
    assert result == default_date


def test_ensure_dir(tmp_path: Path):
    """Test that ensure_dir creates a directory if it doesn't exist."""
    dir_path = tmp_path / "new_dir"
    assert not dir_path.exists()

    returned_path = ensure_dir(dir_path)

    assert dir_path.exists()
    assert dir_path.is_dir()
    assert returned_path == dir_path


def test_clean_dir_deletes_file(tmp_path: Path):
    """Test that clean_dir deletes a single file."""
    file_path = tmp_path / "test_file.txt"
    file_path.touch()
    assert file_path.exists()

    clean_dir(file_path)

    assert not file_path.exists()


def test_clean_dir_deletes_directory(tmp_path: Path):
    """Test that clean_dir recursively deletes a directory."""
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    (dir_path / "file1.txt").touch()
    (dir_path / "subdir").mkdir()
    (dir_path / "subdir" / "file2.txt").touch()

    assert dir_path.exists()

    clean_dir(dir_path)

    assert not dir_path.exists()


def test_clean_dir_non_existent_path(tmp_path: Path):
    """Test that clean_dir does not raise an error for a non-existent path."""
    dir_path = tmp_path / "non_existent_dir"
    try:
        clean_dir(dir_path)
    except Exception as e:
        pytest.fail(f"clean_dir raised an unexpected exception: {e}")


def test_setup_logging(caplog):
    """Test that setup_logging configures the root logger."""
    setup_logging(level=logging.DEBUG)
    test_message = "This is a debug message."

    with caplog.at_level(logging.DEBUG):
        logging.debug(test_message)

    assert test_message in caplog.text

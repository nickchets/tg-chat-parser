"""Tests for configuration data classes in src/config.py."""

from datetime import datetime
from pathlib import Path

from src.config import APIConfig, ExportConfig


def test_api_config():
    """Test that APIConfig correctly stores API credentials."""
    api_id = 12345
    api_hash = "abcdef123456"

    config = APIConfig(api_id=api_id, api_hash=api_hash)

    assert config.api_id == api_id
    assert config.api_hash == api_hash


def test_export_config():
    """Test that ExportConfig correctly stores all export settings."""
    now = datetime.now()
    output_path = Path("/fake/path/output.docx")

    config = ExportConfig(
        channel_url="t.me/test_channel",
        start_date=now,
        end_date=now,
        image_position="after",
        hyperlink_handling="active",
        include_date_heading=True,
        output_file=output_path,
    )

    assert config.channel_url == "t.me/test_channel"
    assert config.start_date == now
    assert config.end_date == now
    assert config.image_position == "after"
    assert config.hyperlink_handling == "active"
    assert config.include_date_heading is True
    assert config.output_file == output_path

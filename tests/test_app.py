"""Tests for the ExporterApp class in src/app.py."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.app import ExporterApp
from src.config import APIConfig, ExportConfig
from src.tg_client import ContentBlock


@pytest.fixture
def api_config():
    """Provides a sample APIConfig."""
    return APIConfig(api_id=123, api_hash="abc")


@pytest.fixture
def export_config(tmp_path: Path):
    """Provides a sample ExportConfig."""
    return ExportConfig(
        channel_url="test_channel",
        start_date=datetime.now(),
        end_date=datetime.now(),
        image_position="after",
        hyperlink_handling="active",
        include_date_heading=True,
        output_file=tmp_path / "output.docx",
    )


@pytest.fixture
def app_mocks():
    """Fixture to mock all external dependencies for ExporterApp."""
    with (
        patch("src.app.TelegramFetcher") as mock_tg_fetcher_class,
        patch("src.app.DocxExporter") as mock_docx_exporter_class,
        patch("src.app.clean_dir") as mock_clean_dir,
    ):
        yield {
            "tg_fetcher_class": mock_tg_fetcher_class,
            "docx_exporter_class": mock_docx_exporter_class,
            "clean_dir": mock_clean_dir,
            "tg_fetcher_instance": mock_tg_fetcher_class.return_value,
            "docx_exporter_instance": mock_docx_exporter_class.return_value,
        }


@pytest.mark.asyncio
async def test_run_export_success(api_config, export_config, app_mocks):
    """Test the successful export workflow."""
    # Arrange
    app = ExporterApp(api_config, export_config)
    mock_progress = MagicMock()
    # Mock fetch_messages to return some blocks
    app_mocks["tg_fetcher_instance"].fetch_messages = AsyncMock(
        return_value=[
            ContentBlock(date=datetime.now(), text="a", entities=[], media_paths=[], _messages=[]),
            ContentBlock(date=datetime.now(), text="b", entities=[], media_paths=[], _messages=[]),
        ]
    )

    # Act
    await app.run_export(mock_progress)

    # Assert
    app_mocks["tg_fetcher_class"].assert_called_once()
    app_mocks["docx_exporter_class"].assert_called_once()
    app_mocks["tg_fetcher_instance"].fetch_messages.assert_awaited_once()
    # Check that add_post was called for each block
    assert app_mocks["docx_exporter_instance"].add_post.call_count == 2
    app_mocks["docx_exporter_instance"].save.assert_called_once_with(str(export_config.output_file))
    app_mocks["clean_dir"].assert_called_once()


@pytest.mark.asyncio
async def test_run_export_no_messages(api_config, export_config, app_mocks):
    """Test the workflow when no messages are found."""
    # Arrange
    app = ExporterApp(api_config, export_config)
    mock_progress = MagicMock()
    # Mock fetch_messages to return an empty list
    app_mocks["tg_fetcher_instance"].fetch_messages = AsyncMock(return_value=[])

    # Act
    await app.run_export(mock_progress)

    # Assert
    app_mocks["tg_fetcher_instance"].fetch_messages.assert_awaited_once()
    # Ensure processing and saving were not called
    app_mocks["docx_exporter_instance"].add_post.assert_not_called()
    app_mocks["docx_exporter_instance"].save.assert_not_called()
    app_mocks["clean_dir"].assert_called_once()  # Cleanup should still run

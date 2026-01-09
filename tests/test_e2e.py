"""E2E-style tests covering the main export flow without real network/docx IO."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.app import ExporterApp
from src.config import APIConfig, ExportConfig
from src.tg_client import ContentBlock


def _make_configs(tmp_path: Path) -> tuple[APIConfig, ExportConfig]:
    api_config = APIConfig(api_id=123, api_hash="hash")
    export_config = ExportConfig(
        channel_url="test_channel",
        start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2024, 2, 1, tzinfo=timezone.utc),
        image_position="after",
        hyperlink_handling="active",
        include_date_heading=True,
        output_file=tmp_path / "out.docx",
    )
    return api_config, export_config


def _make_progress() -> MagicMock:
    progress = MagicMock()
    progress.add_task.side_effect = ["fetch", "media", "posts"]
    return progress


@pytest.mark.asyncio
@patch("src.app.clean_dir")
@patch("src.app.ensure_dir")
@patch("src.app.DocxExporter")
@patch("src.app.TelegramFetcher")
async def test_e2e_run_export_happy_path(mock_fetcher_cls, mock_docx_cls, mock_ensure_dir, mock_clean_dir, tmp_path):
    api_config, export_config = _make_configs(tmp_path)
    temp_media_dir = tmp_path / "temp_media"
    mock_ensure_dir.return_value = temp_media_dir

    blocks = [
        ContentBlock(
            date=datetime(2024, 1, 10, tzinfo=timezone.utc),
            text="hello",
            entities=[],
            media_paths=[str(tmp_path / "img.png")],
        )
    ]

    fetcher = mock_fetcher_cls.return_value
    fetcher.fetch_messages = AsyncMock(return_value=blocks)

    docx = mock_docx_cls.return_value

    progress = _make_progress()

    app = ExporterApp(api_config, export_config)
    await app.run_export(progress)

    mock_fetcher_cls.assert_called_once_with(
        api_config.api_id,
        api_config.api_hash,
        export_config.channel_url,
        temp_media_dir,
    )
    mock_docx_cls.assert_called_once_with(
        export_config.image_position,
        export_config.hyperlink_handling,
        export_config.include_date_heading,
    )

    fetcher.fetch_messages.assert_awaited_once()
    _, kwargs = fetcher.fetch_messages.call_args
    assert kwargs["media_progress_callback"] is not None

    docx.add_post.assert_called_once_with(
        date=blocks[0].date,
        text=blocks[0].text,
        images=blocks[0].media_paths,
        entities=blocks[0].entities,
    )
    docx.save.assert_called_once_with(str(export_config.output_file))

    mock_clean_dir.assert_called_once_with(temp_media_dir)


@pytest.mark.asyncio
@patch("src.app.clean_dir")
@patch("src.app.ensure_dir")
@patch("src.app.DocxExporter")
@patch("src.app.TelegramFetcher")
async def test_e2e_run_export_no_blocks_still_cleans_up(
    mock_fetcher_cls, mock_docx_cls, mock_ensure_dir, mock_clean_dir, tmp_path
):
    api_config, export_config = _make_configs(tmp_path)
    temp_media_dir = tmp_path / "temp_media"
    mock_ensure_dir.return_value = temp_media_dir

    fetcher = mock_fetcher_cls.return_value
    fetcher.fetch_messages = AsyncMock(return_value=[])

    docx = mock_docx_cls.return_value
    progress = _make_progress()

    app = ExporterApp(api_config, export_config)
    await app.run_export(progress)

    docx.add_post.assert_not_called()
    docx.save.assert_not_called()
    mock_clean_dir.assert_called_once_with(temp_media_dir)


@pytest.mark.asyncio
@patch("src.app.clean_dir")
@patch("src.app.ensure_dir")
@patch("src.app.DocxExporter")
@patch("src.app.TelegramFetcher")
async def test_e2e_media_progress_total_zero_is_handled(
    mock_fetcher_cls, mock_docx_cls, mock_ensure_dir, mock_clean_dir, tmp_path
):
    api_config, export_config = _make_configs(tmp_path)
    temp_media_dir = tmp_path / "temp_media"
    mock_ensure_dir.return_value = temp_media_dir

    async def fetch_messages_side_effect(start_date, end_date, media_progress_callback=None):
        assert media_progress_callback is not None
        media_progress_callback(0, 0)
        return []

    fetcher = mock_fetcher_cls.return_value
    fetcher.fetch_messages = AsyncMock(side_effect=fetch_messages_side_effect)

    progress = _make_progress()
    app = ExporterApp(api_config, export_config)
    await app.run_export(progress)

    assert any(
        (call.args[0] == "media" and call.kwargs.get("total") == 1 and call.kwargs.get("completed") == 0)
        for call in progress.update.call_args_list
    )

    mock_docx_cls.return_value.save.assert_not_called()
    mock_clean_dir.assert_called_once_with(temp_media_dir)

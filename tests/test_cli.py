"""Tests for the CLI functions in src/cli.py."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.cli import generate_filename, get_channel_name, interactive_setup, main_cli, parse_date_input


# Tests for helper functions
def test_get_channel_name():
    """Test that get_channel_name correctly sanitizes URLs and usernames."""
    assert get_channel_name("https://t.me/test_channel") == "test_channel"
    assert get_channel_name("t.me/test_channel") == "test_channel"
    assert get_channel_name("@test_channel") == "test_channel"
    assert get_channel_name("test_channel") == "test_channel"
    assert get_channel_name("https://t.me/test-channel_123") == "test-channel_123"


def test_generate_filename():
    """Test that filenames are generated correctly based on date ranges."""
    start = datetime(2023, 1, 15)
    end = datetime(2023, 3, 20)
    assert generate_filename("channel", start, end) == "channel_Jan23_Mar23.docx"


def test_generate_filename_same_month():
    """Test filename generation when start and end dates are in the same month."""
    start = datetime(2023, 1, 15)
    end = datetime(2023, 1, 25)
    assert generate_filename("channel", start, end) == "channel_Jan23.docx"


def test_parse_date_input_valid():
    """Test that valid dd.mm.yyyy strings are parsed correctly."""
    expected = datetime(2023, 5, 10, tzinfo=timezone.utc)
    assert parse_date_input("10.05.2023") == expected


def test_parse_date_input_empty():
    """Test that an empty string defaults to four months ago."""
    result = parse_date_input("")
    assert result.tzinfo == timezone.utc
    assert result.day == 1


def test_parse_date_input_empty_wraps_year():
    """Test that empty date calculation wraps year correctly when month - 4 <= 0."""

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2024, 1, 15, tzinfo=tz)

    with patch("src.cli.datetime", FixedDatetime):
        result = parse_date_input("")

    assert result == datetime(2023, 9, 1, tzinfo=timezone.utc)


def test_parse_date_input_invalid_raises():
    """Test that invalid date strings raise ValueError."""
    with pytest.raises(ValueError):
        parse_date_input("31-12-2024")


@pytest.mark.asyncio
@patch("src.cli.load_dotenv")
@patch("src.cli.os.getenv")
@patch("src.cli.Prompt.ask")
@patch("src.cli.IntPrompt.ask")
@patch("src.cli.Confirm.ask")
async def test_interactive_setup_happy_path(
    mock_confirm_ask,
    mock_int_ask,
    mock_prompt_ask,
    mock_getenv,
    mock_load_dotenv,
    tmp_path,
):
    """Test interactive_setup returns configs matching user choices and uses deterministic end_date."""

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2024, 2, 15, tzinfo=tz)

    mock_getenv.side_effect = lambda key, default=None: {"API_ID": "123", "API_HASH": "hash"}.get(key, default)
    mock_prompt_ask.side_effect = ["@chan", "10.01.2024"]
    mock_int_ask.side_effect = [1, 1]
    mock_confirm_ask.return_value = False

    console = MagicMock()

    with patch("src.cli.datetime", FixedDatetime):
        api_config, export_config = await interactive_setup(console)

    assert api_config.api_id == 123
    assert api_config.api_hash == "hash"
    assert export_config.channel_url == "@chan"
    assert export_config.start_date == datetime(2024, 1, 10, tzinfo=timezone.utc)
    assert export_config.end_date == datetime(2024, 2, 15, tzinfo=timezone.utc)
    assert export_config.image_position == "before"
    assert export_config.hyperlink_handling == "ignore"
    assert export_config.include_date_heading is False
    assert export_config.output_file.suffix == ".docx"

    mock_load_dotenv.assert_called_once()


@pytest.mark.asyncio
@patch("src.cli.load_dotenv")
@patch("src.cli.os.getenv")
async def test_interactive_setup_missing_credentials_raises(mock_getenv, mock_load_dotenv):
    """Test that missing API credentials fail fast with ValueError."""
    mock_getenv.side_effect = lambda key, default=None: {"API_ID": "0", "API_HASH": ""}.get(key, default)

    with pytest.raises(ValueError):
        await interactive_setup(MagicMock())


@pytest.mark.asyncio
@patch("src.cli.load_dotenv")
@patch("src.cli.os.getenv")
@patch("src.cli.Prompt.ask")
async def test_interactive_setup_missing_channel_raises(mock_prompt_ask, mock_getenv, mock_load_dotenv):
    """Test that an empty channel URL raises ValueError."""
    mock_getenv.side_effect = lambda key, default=None: {"API_ID": "123", "API_HASH": "hash"}.get(key, default)
    mock_prompt_ask.return_value = ""

    with pytest.raises(ValueError):
        await interactive_setup(MagicMock())


@pytest.mark.asyncio
@patch("src.cli.interactive_setup", new_callable=AsyncMock)
@patch("src.cli.Confirm.ask", side_effect=[True, False])
@patch("src.cli.ExporterApp", autospec=True)
async def test_main_cli_runs_export_on_confirm(mock_app_class, mock_confirm, mock_setup):
    """Test that main_cli creates and runs ExporterApp when the user confirms."""
    # Arrange: Mock the setup to return dummy configs
    mock_api_config = MagicMock()
    mock_export_config = MagicMock()
    mock_setup.return_value = (mock_api_config, mock_export_config)

    # Mock the app instance and its run method
    mock_app_instance = mock_app_class.return_value
    mock_app_instance.run_export = AsyncMock()

    # Act
    await main_cli()

    # Assert
    mock_setup.assert_awaited_once()
    assert mock_confirm.call_count == 2
    assert mock_confirm.call_args_list[0].args[0] == "\nProceed with export?"
    assert mock_confirm.call_args_list[1].args[0] == "\nRun another export?"
    mock_app_class.assert_called_once_with(mock_api_config, mock_export_config)
    mock_app_instance.run_export.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.cli.interactive_setup", new_callable=AsyncMock)
@patch("src.cli.Confirm.ask", side_effect=[False, False])
@patch("src.cli.ExporterApp", autospec=True)
async def test_main_cli_cancels_export(mock_app_class, mock_confirm, mock_setup):
    """Test that main_cli does not run ExporterApp when the user cancels."""
    mock_setup.return_value = (MagicMock(), MagicMock())

    await main_cli()

    mock_setup.assert_awaited_once()
    assert mock_confirm.call_count == 2
    assert mock_confirm.call_args_list[0].args[0] == "\nProceed with export?"
    assert mock_confirm.call_args_list[1].args[0] == "\nRun another export?"
    mock_app_class.assert_not_called() # App should not be instantiated

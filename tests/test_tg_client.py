"""Tests for the TelegramFetcher class in src/tg_client.py."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telethon.tl.types import MessageMediaPhoto

from src.tg_client import TelegramFetcher


@pytest.fixture
def mock_telethon_client():
    """Fixture to create a mock Telethon client."""
    with patch("src.tg_client.TelegramClient", autospec=True) as mock_client_class:
        client_instance = mock_client_class.return_value
        client_instance.connect = AsyncMock()
        client_instance.disconnect = AsyncMock()
        client_instance.is_user_authorized = AsyncMock()
        client_instance.get_me = AsyncMock()
        client_instance.send_code_request = AsyncMock()
        client_instance.sign_in = AsyncMock()
        client_instance.get_entity = AsyncMock()
        client_instance.iter_messages = MagicMock()
        client_instance.download_media = AsyncMock()
        yield client_instance


@pytest.fixture
def fetcher(mock_telethon_client, tmp_path):
    """Fixture to create a TelegramFetcher instance."""
    return TelegramFetcher(
        api_id=123,
        api_hash="abc",
        channel_url="test_channel",
        temp_media_dir=tmp_path,
    )


class MockMessage:
    """A mock class for Telethon's Message object."""

    def __init__(self, id, text, date, grouped_id=None, media=None, action=None, entities=None):
        self.id = id
        self.message = text
        self.date = date
        self.grouped_id = grouped_id
        self.media = media
        self.action = action
        self.entities = entities or []


@pytest.mark.asyncio
async def test_auth_already_authorized(fetcher, mock_telethon_client):
    """Test interactive_auth when user is already authorized."""
    mock_telethon_client.is_user_authorized.return_value = True
    mock_telethon_client.get_me.return_value = MagicMock(first_name="Test", last_name="User", username="testuser")

    result = await fetcher.interactive_auth()

    assert result is True
    mock_telethon_client.connect.assert_awaited_once()
    mock_telethon_client.get_me.assert_awaited_once()


@pytest.mark.asyncio
@patch("builtins.input", side_effect=["+1234567890", "12345"])
async def test_auth_new_login_success(mock_input, fetcher, mock_telethon_client):
    """Test successful new user login."""
    mock_telethon_client.is_user_authorized.return_value = False
    mock_telethon_client.get_me.return_value = MagicMock(first_name="Test")

    result = await fetcher.interactive_auth()

    assert result is True
    mock_telethon_client.send_code_request.assert_awaited_with("+1234567890")
    mock_telethon_client.sign_in.assert_awaited_with("+1234567890", "12345")


@pytest.mark.asyncio
async def test_fetch_messages_groups_albums(fetcher, mock_telethon_client):
    """Test that messages with the same grouped_id are grouped into one block."""
    fetcher.interactive_auth = AsyncMock(return_value=True)
    start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2023, 1, 31, tzinfo=timezone.utc)

    # iter_messages should be an async generator
    async def mock_iterator():
        yield MockMessage(id=1, text="Album text", date=end_date, grouped_id=100)
        yield MockMessage(id=2, text="", date=end_date, grouped_id=100, media=MessageMediaPhoto(photo=None))
        yield MockMessage(id=3, text="Standalone post", date=end_date)
        yield MockMessage(id=4, text="", date=start_date - timedelta(days=1))  # Should be filtered out

    mock_telethon_client.iter_messages.return_value = mock_iterator()

    blocks = await fetcher.fetch_messages(start_date, end_date)

    assert len(blocks) == 2
    texts = {b.text for b in blocks}
    assert texts == {"Album text", "Standalone post"}
    album_block = next(b for b in blocks if b.text == "Album text")
    assert len(album_block._messages) == 0  # сообщения очищаются после скачивания медиа


@pytest.mark.asyncio
async def test_download_media_for_block(fetcher, mock_telethon_client):
    """Test that media is downloaded for a block."""
    mock_message_with_media = MockMessage(
        id=1,
        text="",
        date=datetime.now(tz=timezone.utc),
        media=MessageMediaPhoto(photo=None),
    )
    block = MagicMock()
    block._messages = [mock_message_with_media]
    block.media_paths = []

    mock_telethon_client.download_media.return_value = "/fake/path/image.jpg"

    await fetcher._download_media_for_block(block, 0, 1)

    mock_telethon_client.download_media.assert_awaited_once_with(
        mock_message_with_media,
        file=str(fetcher.temp_media_dir),
    )
    assert block.media_paths == ["/fake/path/image.jpg"]

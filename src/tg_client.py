"""Telegram client for fetching channel messages with media grouping."""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from telethon import TelegramClient
from telethon.tl.types import (
    Message,
    MessageMediaDocument,
    MessageMediaPhoto,
)


@dataclass
class ContentBlock:
    """Represents a single logical post, which may consist of multiple messages (e.g., an album).

    Attributes:
        date: The timestamp of the post.
        text: The main text content of the post.
        entities: A list of Telegram MessageEntity objects for text formatting.
        media_paths: A list of local file paths for downloaded media.
        _messages: Internal list of raw Message objects used for media downloading.
    """
    date: datetime
    text: str
    entities: List = field(default_factory=list)  # Telegram MessageEntity objects
    media_paths: List[str] = field(default_factory=list)
    _messages: List[Message] = field(default_factory=list, repr=False)  # Internal: messages for media download


class AlbumGrouper:
    """DEPRECATED: grouping of album messages is now in `TelegramFetcher`."""

    def __init__(self):
        self.pending_groups: Dict[int, List[Message]] = {}

    def add_message(self, message: Message) -> Optional[ContentBlock]:
        """Add a message and return a ContentBlock if group is complete."""
        grouped_id = getattr(message, 'grouped_id', None)

        if grouped_id is None:
            # Not part of a group, process immediately
            return self._create_block_from_message(message)

        # Part of a group
        if grouped_id not in self.pending_groups:
            self.pending_groups[grouped_id] = []

        self.pending_groups[grouped_id].append(message)

        # Check if this is the last message in the group
        # We'll assume the group is complete when we encounter a message
        # that doesn't have the same grouped_id in subsequent iterations
        # For now, we'll process groups when we see a different grouped_id or end
        return None

    def flush_pending(self) -> List[ContentBlock]:
        """Flush all pending groups and return ContentBlocks."""
        blocks = []
        for grouped_id, messages in self.pending_groups.items():
            block = self._merge_grouped_messages(messages)
            if block:
                blocks.append(block)
        self.pending_groups.clear()
        return blocks

    def _merge_grouped_messages(self, messages: List[Message]) -> Optional[ContentBlock]:
        """Merge multiple messages with the same grouped_id into one ContentBlock."""
        if not messages:
            return None

        # Sort by message ID to maintain order
        messages.sort(key=lambda m: m.id)

        # Find the message with text (usually the first one)
        text_message = None
        for msg in messages:
            if msg.message and msg.message.strip():
                text_message = msg
                break

        if not text_message:
            text_message = messages[0]

        # Collect all media from all messages
        media_paths = []
        entities = list(text_message.entities or [])

        # Use the date from the first message
        date = text_message.date

        block = ContentBlock(
            date=date,
            text=text_message.message or "",
            entities=entities,
            media_paths=media_paths,  # Will be populated during download
            _messages=messages  # Store messages for media download
        )
        return block

    def _create_block_from_message(self, message: Message) -> Optional[ContentBlock]:
        """Create a ContentBlock from a single message."""
        if not message.message and not self._has_media(message):
            return None  # Skip empty messages without media

        return ContentBlock(
            date=message.date,
            text=message.message or "",
            entities=list(message.entities or []),
            media_paths=[],  # Will be populated during download
            _messages=[message]  # Store message for media download
        )

    @staticmethod
    def _has_media(message: Message) -> bool:
        """Check if message has media."""
        return isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument))


class TelegramFetcher:
    """Handles all communication with the Telegram API.

    This class is responsible for connecting to Telegram, authenticating the user,
    fetching messages from a specified channel within a date range, and downloading
    associated media.

    Attributes:
        client: The Telethon `TelegramClient` instance.
        channel_url: The URL of the target channel.
        temp_media_dir: The directory to store downloaded media files.
    """

    def __init__(self, api_id: int, api_hash: str, channel_url: str, temp_media_dir: Path):
        self.client = TelegramClient('session', api_id, api_hash)
        self.channel_url = channel_url
        self.temp_media_dir = temp_media_dir
        self.temp_media_dir.mkdir(parents=True, exist_ok=True)

    async def interactive_auth(self) -> bool:
        """Performs interactive authentication with the user if necessary.

        Connects the client and checks for an existing session. If not authorized,
        it prompts the user for their phone number, confirmation code, and 2FA password.

        Returns:
            True if authentication is successful or already established, False otherwise.
        """
        try:
            # Try to connect without interaction first
            await self.client.connect()

            # Check if already authorized
            if await self.client.is_user_authorized():
                me = await self.client.get_me()
                logging.info(f"Authorized as {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
                return True

            # Need to authorize
            logging.info("No valid session found. Starting authorization...")
            phone = input("Enter phone number (e.g., +7...): ")

            await self.client.send_code_request(phone)
            code = input("Enter confirmation code: ")

            try:
                await self.client.sign_in(phone, code)
            except Exception as e:
                if "2FA password" in str(e):
                    password = input("Enter 2FA password: ")
                    await self.client.sign_in(password=password)
                else:
                    raise e

            me = await self.client.get_me()
            logging.info("Authorization successful!")
            logging.info(f"  Logged in as: {me.first_name} {me.last_name or ''} (@{me.username or 'no username'})")
            logging.info("  Session saved to: session.session")
            return True

        except Exception as e:
            logging.error(f"Authorization failed: {e}")
            return False

    async def fetch_messages(  # noqa: C901
        self,
        start_date: datetime,
        end_date: datetime,
        media_progress_callback=None,
    ) -> list[ContentBlock]:
        """Fetches and groups messages from the channel within a specified date range.

        It handles authentication, iterates through messages, groups them into
        logical content blocks (handling albums), and downloads all associated media.

        Args:
            start_date: The earliest date from which to fetch messages.
            end_date: The latest date for fetching messages.
            media_progress_callback: An optional callback function to report media
                download progress, accepting `(downloaded, total)` arguments.

        Returns:
            A list of `ContentBlock` objects, sorted by date.

        Raises:
            Exception: If authentication fails.
        """
        # Perform interactive authentication
        if not await self.interactive_auth():
            raise Exception("Authentication failed")

        try:
            # Get the channel entity
            entity = await self.client.get_entity(self.channel_url)

            # Fetch messages - collect all first, then group
            grouper = AlbumGrouper()
            all_messages = []

            async for message in self.client.iter_messages(
                entity,
                offset_date=end_date,
                reverse=False,
            ):
                # Filter by date range
                if message.date < start_date:
                    break
                if message.date > end_date:
                    continue

                    # Skip service messages
                if message.action is not None:
                    continue

                all_messages.append(message)

            total_media_items = 0
            for message in all_messages:
                if isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
                    total_media_items += 1

            # Process messages through grouper
            # Group messages by grouped_id first
            grouped_messages: Dict[Optional[int], List[Message]] = {}
            standalone_messages = []

            for message in all_messages:
                grouped_id = getattr(message, 'grouped_id', None)
                if grouped_id is not None:
                    if grouped_id not in grouped_messages:
                        grouped_messages[grouped_id] = []
                    grouped_messages[grouped_id].append(message)
                else:
                    standalone_messages.append(message)

            all_blocks = []

            # Process grouped messages
            for grouped_id, messages in grouped_messages.items():
                block = grouper._merge_grouped_messages(messages)
                if block:
                    all_blocks.append(block)

            # Process standalone messages
            for message in standalone_messages:
                block = grouper._create_block_from_message(message)
                if block:
                    all_blocks.append(block)

            # Download media for all blocks
            downloaded_media_items = 0
            for block in all_blocks:
                downloaded_media_items = await self._download_media_for_block(
                    block,
                    downloaded_media_items,
                    total_media_items,
                    media_progress_callback,
                )
                # Clear message references after download
                block._messages = []

            # Sort by date
            all_blocks.sort(key=lambda b: b.date)

            return all_blocks

        finally:
            await self.client.disconnect()

    async def _download_media_for_block(
        self,
        block: ContentBlock,
        downloaded_media_items: int,
        total_media_items: int,
        media_progress_callback=None,
    ) -> int:
        """Downloads all media files associated with a single ContentBlock.

        Args:
            block: The `ContentBlock` to download media for.
            downloaded_media_items: The current count of downloaded items.
            total_media_items: The total number of media items to download.
            media_progress_callback: The callback for reporting progress.

        Returns:
            The updated count of downloaded media items.
        """
        for message in block._messages:
            if not isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
                continue

            try:
                file_path = await self.client.download_media(
                    message,
                    file=str(self.temp_media_dir),
                )
                if file_path:
                    block.media_paths.append(str(file_path))
                downloaded_media_items += 1
                if media_progress_callback is not None:
                    media_progress_callback(downloaded_media_items, total_media_items)
            except Exception as e:
                logging.error(f"Error downloading media from message {message.id}: {e}")

        return downloaded_media_items

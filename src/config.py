"""Configuration data classes for the application.

This module defines the data structures used to hold configuration settings
for the Telegram exporter application.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class APIConfig:
    """Holds Telegram API credentials.

    Attributes:
        api_id: The unique identifier for the Telegram application.
        api_hash: The secret hash for the Telegram application.
    """

    api_id: int
    api_hash: str


@dataclass
class ExportConfig:
    """Holds all settings for a single export operation.

    Attributes:
        channel_url: The URL or username of the target Telegram channel.
        start_date: The starting date for fetching messages (inclusive).
        end_date: The ending date for fetching messages (inclusive).
        image_position: Where to place images relative to post text ('before' or 'after').
        hyperlink_handling: How to handle links ('active' or 'ignore').
        include_date_heading: Whether to add a heading for each post's date.
        output_file: The full path for the generated .docx file.
    """

    channel_url: str
    start_date: datetime
    end_date: datetime
    image_position: str
    hyperlink_handling: str
    include_date_heading: bool
    output_file: Path

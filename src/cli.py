"""Command-line interface for the Telegram exporter."""

import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.prompt import Confirm, IntPrompt, Prompt

from src.app import ExporterApp
from src.config import APIConfig, ExportConfig
from src.utils import setup_logging


def parse_date_input(date_str: str) -> datetime:
    """Parses a date string and returns a timezone-aware datetime object.

    Supports 'dd.mm.yyyy' format. If the string is empty, it defaults to
    four months before the current date.

    Args:
        date_str: The date string to parse.

    Returns:
        A datetime object in UTC.

    Raises:
        ValueError: If the date format is invalid.
    """
    if not date_str.strip():
        now = datetime.now(timezone.utc)
        month = now.month - 4
        year = now.year
        while month <= 0:
            month += 12
            year -= 1
        return datetime(year, month, 1, tzinfo=timezone.utc)

    try:
        day, month, year = map(int, date_str.split("."))
        return datetime(year, month, day, tzinfo=timezone.utc)
    except ValueError:
        logging.error("Invalid date format. Please use dd.mm.yyyy format.")
        raise


def get_channel_name(channel_url: str) -> str:
    """Extracts a clean channel name from a URL for use in filenames.

    Removes protocol, domain, and special characters.

    Args:
        channel_url: The URL or username of the channel.

    Returns:
        A sanitized string suitable for a filename.
    """
    name = channel_url.lstrip("@")
    for prefix in ["https://t.me/", "t.me/"]:
        if name.startswith(prefix):
            name = name[len(prefix) :]
    name = re.sub(r"[^\w\s-]", "", name).strip()
    return name


def generate_filename(channel_name: str, start_date: datetime, end_date: datetime) -> str:
    """Generates a .docx filename from the channel name and date range.

    Example:
        `MyChannel_Jan24_Mar24.docx`

    Args:
        channel_name: The sanitized name of the channel.
        start_date: The start date of the export range.
        end_date: The end date of the export range.

    Returns:
        A formatted filename string.
    """
    start_str = start_date.strftime("%b%y")
    end_str = end_date.strftime("%b%y")
    date_part = start_str if start_str == end_str else f"{start_str}_{end_str}"
    return f"{channel_name}_{date_part}.docx"


async def interactive_setup(console: Console) -> tuple[APIConfig, ExportConfig]:
    """Guides the user through an interactive setup process.

    Collects all necessary information for the export, including API credentials,
    channel URL, date range, and formatting options.

    Args:
        console: A rich Console object for interactive I/O.

    Returns:
        A tuple containing APIConfig and ExportConfig objects.

    Raises:
        ValueError: If required inputs like API credentials or channel URL are missing.
    """
    console.print(
        Panel.fit(
            "[bold blue]Telegram to Word Exporter[/bold blue]\n"
            "Export Telegram channel messages to formatted Word documents",
            title="Welcome",
        )
    )

    load_dotenv()
    api_id = int(os.getenv("API_ID", "0"))
    api_hash = os.getenv("API_HASH", "")

    if not api_id or not api_hash:
        logging.error("Error: API_ID and API_HASH must be set in .env file")
        raise ValueError("Missing API credentials")

    api_config = APIConfig(api_id=api_id, api_hash=api_hash)

    channel_url = Prompt.ask("Enter channel URL or username", default="")
    if not channel_url:
        logging.error("Channel URL is required")
        raise ValueError("Channel URL required")

    start_date_str = Prompt.ask("Enter start date (dd.mm.yyyy). Leave empty for 4 months ago", default="")
    start_date = parse_date_input(start_date_str)
    end_date = datetime.now(timezone.utc)

    console.print("\n[bold]Image Positioning:[/bold]")
    console.print("1. Images Before Text")
    console.print("2. Images After Text (Default)")
    image_choice = IntPrompt.ask("Choose image positioning", choices=["1", "2"], default=2)
    image_position = "before" if image_choice == 1 else "after"

    console.print("\n[bold]Hyperlink Handling:[/bold]")
    console.print("1. Ignore Links (Plain text)")
    console.print("2. Active Hyperlinks (Blue/Underlined and Clickable)")
    link_choice = IntPrompt.ask("Choose hyperlink handling", choices=["1", "2"], default=2)
    hyperlink_handling = "ignore" if link_choice == 1 else "active"

    include_date_heading = Confirm.ask("\nAdd post date as a heading?", default=True)

    results_dir = Path("./results").resolve()
    results_dir.mkdir(exist_ok=True)
    channel_name = get_channel_name(channel_url)
    filename = generate_filename(channel_name, start_date, end_date)
    output_file = results_dir / filename

    export_config = ExportConfig(
        channel_url=channel_url,
        start_date=start_date,
        end_date=end_date,
        image_position=image_position,
        hyperlink_handling=hyperlink_handling,
        include_date_heading=include_date_heading,
        output_file=output_file,
    )

    return api_config, export_config


async def main_cli():
    """The main entry point and loop for the CLI application.

    This function orchestrates the entire user interaction flow, including setup,
    confirmation, execution, and the option to run another export.
    """
    setup_logging()
    console = Console()

    while True:
        try:
            api_config, export_config = await interactive_setup(console)

            console.print("\n[bold green]Configuration:[/bold green]")
            console.print(f"Channel: {export_config.channel_url}")
            console.print(
                (
                "Date range: "
                f"{export_config.start_date.strftime('%B %d, %Y')} to "
                f"{export_config.end_date.strftime('%B %d, %Y')}"
            )
            )
            console.print(f"Output file: {export_config.output_file}")

            if not Confirm.ask("\nProceed with export?"):
                logging.warning("Export cancelled.")
            else:
                app = ExporterApp(api_config, export_config)
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    console=console,
                ) as progress:
                    await app.run_export(progress)
                logging.info(f"Export complete! Document saved to {export_config.output_file}")

        except (ValueError, KeyboardInterrupt) as e:
            logging.error(f"Operation cancelled: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}", exc_info=True)

        if not Confirm.ask("\nRun another export?", default=False):
            break


if __name__ == "__main__":
    asyncio.run(main_cli())

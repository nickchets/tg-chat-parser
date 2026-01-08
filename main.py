"""Interactive Telegram to Word document exporter with rich CLI interface."""
import asyncio
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint

from src.tg_client import TelegramFetcher, ContentBlock
from src.docx_client import DocxExporter
from src.utils import parse_date, ensure_dir


def parse_date_input(date_str: str) -> datetime:
    """Parse date string in dd.mm.yyyy format and return UTC datetime."""
    if not date_str.strip():
        # Default to 4 months ago
        now = datetime.now(timezone.utc)
        default_date = datetime(now.year - (now.month <= 4), (now.month - 4) % 12 or 12, 1, tzinfo=timezone.utc)
        return default_date
    
    try:
        # Parse dd.mm.yyyy format
        day, month, year = map(int, date_str.split('.'))
        return datetime(year, month, day, tzinfo=timezone.utc)
    except ValueError:
        rprint("[red]Invalid date format. Please use dd.mm.yyyy format.[/red]")
        raise


def get_channel_name(channel_url: str) -> str:
    """Extract channel name from URL for file naming."""
    # Remove @ if present and clean up the name
    name = channel_url.lstrip('@')
    # Remove common prefixes
    for prefix in ['https://t.me/', 't.me/']:
        if name.startswith(prefix):
            name = name[len(prefix):]
    # Clean up for filename
    name = re.sub(r'[^\w\s-]', '', name).strip()
    return name


def generate_filename(channel_name: str, start_date: datetime, end_date: datetime) -> str:
    """Generate filename based on channel name and date range."""
    start_str = start_date.strftime("%b%y")
    end_str = end_date.strftime("%b%y")
    
    if start_str == end_str:
        date_part = start_str
    else:
        date_part = f"{start_str}_{end_str}"
    
    return f"{channel_name}_{date_part}.docx"


def clean_dir(path: Path) -> None:
    if not path.exists():
        return
    if path.is_file():
        try:
            path.unlink()
        except Exception:
            pass
        return
    shutil.rmtree(path, ignore_errors=True)


async def interactive_setup() -> Tuple[str, datetime, datetime, str, str, bool]:
    """Interactive setup for getting user inputs."""
    console = Console()
    
    console.print(Panel.fit(
        "[bold blue]Telegram to Word Exporter[/bold blue]\n"
        "Export Telegram channel messages to formatted Word documents",
        title="Welcome"
    ))
    
    # Load environment variables
    load_dotenv()
    api_id = int(os.getenv('API_ID', '0'))
    api_hash = os.getenv('API_HASH', '')
    
    if not api_id or not api_hash:
        console.print("[red]Error: API_ID and API_HASH must be set in .env file[/red]")
        raise ValueError("Missing API credentials")
    
    # Get channel URL
    channel_url = Prompt.ask("Enter channel URL or username", default="")
    if not channel_url:
        console.print("[red]Channel URL is required[/red]")
        raise ValueError("Channel URL required")
    
    # Get start date
    start_date_str = Prompt.ask("Enter start date (dd.mm.yyyy). Leave empty for 4 months ago", default="")
    start_date = parse_date_input(start_date_str)
    
    # End date is always now
    end_date = datetime.now(timezone.utc)
    
    # Image positioning
    console.print("\n[bold]Image Positioning:[/bold]")
    console.print("1. Images Before Text")
    console.print("2. Images After Text (Default)")
    
    image_choice = IntPrompt.ask(
        "Choose image positioning",
        choices=["1", "2"],
        default=2
    )
    image_position = "before" if image_choice == 1 else "after"
    
    # Hyperlink handling
    console.print("\n[bold]Hyperlink Handling:[/bold]")
    console.print("1. Ignore Links (Plain text)")
    console.print("2. Active Hyperlinks (Blue/Underlined and Clickable)")
    
    link_choice = IntPrompt.ask(
        "Choose hyperlink handling",
        choices=["1", "2"],
        default=2
    )
    hyperlink_handling = "ignore" if link_choice == 1 else "active"

    include_date_heading = Confirm.ask("\nAdd post date as a heading?", default=True)
    
    return channel_url, start_date, end_date, image_position, hyperlink_handling, include_date_heading


async def process_content_blocks(
    blocks: List[ContentBlock],
    docx_exporter: DocxExporter,
    console: Console,
    autosave_path: Optional[Path] = None,
    autosave_every: int = 50
) -> Tuple[int, int, int]:
    """Process ContentBlocks and write them to Word document with progress tracking."""
    total_posts = len(blocks)
    total_images = 0
    total_links = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("Processing posts...", total=total_posts)
        
        for i, block in enumerate(blocks):
            # Count images and links
            total_images += len(block.media_paths)
            
            # Count links in entities
            if block.entities:
                for entity in block.entities:
                    entity_type = type(entity).__name__
                    if entity_type in ('MessageEntityTextUrl', 'MessageEntityUrl'):
                        total_links += 1
            
            # Add post to document
            docx_exporter.add_post(
                date=block.date,
                text=block.text,
                images=block.media_paths,
                entities=block.entities
            )

            if autosave_path is not None and (i + 1) % autosave_every == 0:
                docx_exporter.save(str(autosave_path))
            
            progress.update(task, advance=1)
    
    return total_posts, total_images, total_links


async def main():
    """Main entry point with interactive CLI."""
    console = Console()

    while True:
        temp_media_dir: Optional[Path] = None
        output_file: Optional[Path] = None
        docx_exporter: Optional[DocxExporter] = None

        try:
            # Interactive setup
            channel_url, start_date, end_date, image_position, hyperlink_handling, include_date_heading = await interactive_setup()

            # Setup directories
            temp_media_dir = ensure_dir(Path('./temp_media'))
            results_dir = ensure_dir(Path('./results'))

            channel_name = get_channel_name(channel_url)
            filename = generate_filename(channel_name, start_date, end_date)
            output_file = results_dir / filename
            autosave_file = results_dir / f".{filename}.partial.docx"

            # Display configuration
            console.print("\n[bold green]Configuration:[/bold green]")
            console.print(f"Channel: {channel_url}")
            console.print(f"Date range: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
            console.print(f"Image positioning: {'Before text' if image_position == 'before' else 'After text'}")
            console.print(f"Hyperlinks: {'Active' if hyperlink_handling == 'active' else 'Ignored'}")
            console.print(f"Date heading: {'On' if include_date_heading else 'Off'}")
            console.print(f"Output file: {output_file}")

            if not Confirm.ask("\nProceed with export?"):
                console.print("[yellow]Export cancelled.[/yellow]")
                if not Confirm.ask("Run another export?", default=False):
                    return
                continue

            # Initialize clients
            console.print("\n[bold]Initializing clients...[/bold]")
            tg_fetcher = TelegramFetcher(
                int(os.getenv('API_ID')),
                os.getenv('API_HASH'),
                channel_url,
                temp_media_dir
            )
            docx_exporter = DocxExporter(image_position, hyperlink_handling, include_date_heading)

            # Fetch messages from Telegram (with media download progress)
            console.print("\n[bold]Fetching messages from Telegram...[/bold]")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                fetch_task = progress.add_task("Connecting and fetching...", total=None)
                media_task = progress.add_task("Downloading media...", total=1)
                progress.update(media_task, completed=0)

                def on_media_progress(downloaded: int, total: int) -> None:
                    if total <= 0:
                        progress.update(media_task, total=1, completed=0)
                        return
                    progress.update(media_task, total=total, completed=downloaded)

                blocks = await tg_fetcher.fetch_messages(start_date, end_date, media_progress_callback=on_media_progress)
                progress.update(fetch_task, completed=True)

            console.print(f"[green]✓ Fetched {len(blocks)} content blocks[/green]")

            if not blocks:
                console.print("[yellow]No messages found in the specified date range.[/yellow]")
                if not Confirm.ask("Run another export?", default=False):
                    return
                continue

            # Process and write to Word document
            console.print("\n[bold]Processing content and generating document...[/bold]")
            total_posts, total_images, total_links = await process_content_blocks(
                blocks,
                docx_exporter,
                console,
                autosave_path=autosave_file,
                autosave_every=50
            )

            docx_exporter.save(str(output_file))
            clean_dir(autosave_file)

            # Display summary
            console.print("\n[bold green]✓ Export complete![/bold green]")
            console.print(f"Document saved: [cyan]{output_file.absolute()}[/cyan]")

            table = Table(title="Export Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="green")
            table.add_row("Total Posts", str(total_posts))
            table.add_row("Images Downloaded", str(total_images))
            table.add_row("Links Found", str(total_links))
            console.print(table)

        except KeyboardInterrupt:
            console.print("\n[yellow]Export interrupted by user.[/yellow]")
            if docx_exporter is not None and output_file is not None:
                try:
                    partial_path = output_file.with_suffix(".partial.docx")
                    docx_exporter.save(str(partial_path))
                    console.print(f"[yellow]Partial document saved: {partial_path.absolute()}[/yellow]")
                except Exception:
                    pass
        except Exception as e:
            console.print(f"\n[red]Error during export: {e}[/red]")
            raise
        finally:
            if temp_media_dir is not None:
                clean_dir(temp_media_dir)

        if not Confirm.ask("Run another export?", default=False):
            return


if __name__ == '__main__':
    asyncio.run(main())
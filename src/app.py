"""Core application logic for the Telegram exporter."""

import logging
from pathlib import Path

from rich.progress import Progress

from src.config import APIConfig, ExportConfig
from src.docx_client import DocxExporter
from src.tg_client import ContentBlock, TelegramFetcher
from src.utils import clean_dir, ensure_dir


class ExporterApp:
    """Orchestrates the full export process from fetching to saving.

    This class encapsulates the core business logic of the application.
    It coordinates the fetching of messages from Telegram and the generation
    of the .docx file.

    Attributes:
        api_config: Configuration for the Telegram API.
        export_config: Configuration for the current export job.
        temp_media_dir: A Path object pointing to the temporary directory for media.
    """

    def __init__(self, api_config: APIConfig, export_config: ExportConfig):
        """Initializes the ExporterApp.

        Args:
            api_config: An APIConfig object with Telegram API credentials.
            export_config: An ExportConfig object with settings for the export.
        """
        self.api_config = api_config
        self.export_config = export_config
        self.temp_media_dir = ensure_dir(Path("./temp_media"))

    async def run_export(self, progress: Progress) -> None:
        """Runs the entire export process.

        This method handles the main workflow: initializing clients, fetching messages,
        processing content, and saving the final document. It also ensures that
        temporary files are cleaned up.

        Args:
            progress: A rich Progress object to update the UI with task status.
        """
        try:
            # Initialize clients
            logging.info("Initializing clients...")
            tg_fetcher = TelegramFetcher(
                self.api_config.api_id, self.api_config.api_hash, self.export_config.channel_url, self.temp_media_dir
            )
            docx_exporter = DocxExporter(
                self.export_config.image_position,
                self.export_config.hyperlink_handling,
                self.export_config.include_date_heading,
            )

            # Fetch messages
            logging.info("Fetching messages from Telegram...")
            fetch_task = progress.add_task("Connecting and fetching...", total=None)
            media_task = progress.add_task("Downloading media...", total=1)
            progress.update(media_task, completed=0)

            def on_media_progress(downloaded: int, total: int) -> None:
                if total <= 0:
                    progress.update(media_task, total=1, completed=0)
                    return
                progress.update(media_task, total=total, completed=downloaded)

            blocks = await tg_fetcher.fetch_messages(
                self.export_config.start_date, self.export_config.end_date, media_progress_callback=on_media_progress
            )
            progress.update(fetch_task, completed=True)
            logging.info(f"Fetched {len(blocks)} content blocks")

            if not blocks:
                logging.warning("No messages found in the specified date range.")
                return

            # Process and write to Word document
            logging.info("Processing content and generating document...")
            await self._process_content_blocks(blocks, docx_exporter, progress)

            # Save final document
            docx_exporter.save(str(self.export_config.output_file))

        finally:
            # Clean up temporary media files
            logging.info("Cleaning up temporary media files...")
            clean_dir(self.temp_media_dir)

    async def _process_content_blocks(
        self, blocks: list[ContentBlock], docx_exporter: DocxExporter, progress: Progress
    ) -> None:
        """Processes a list of ContentBlocks and adds them to the document.

        Args:
            blocks: A list of ContentBlock objects to be processed.
            docx_exporter: An instance of DocxExporter to add posts to.
            progress: A rich Progress object to update the post processing task.
        """
        task = progress.add_task("Processing posts...", total=len(blocks))

        for block in blocks:
            docx_exporter.add_post(
                date=block.date,
                text=block.text,
                images=block.media_paths,
                entities=block.entities,
            )
            progress.update(task, advance=1)

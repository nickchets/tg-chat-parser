"""Main entry point for the Telegram Chat Exporter application."""

import asyncio

from src.cli import main_cli

if __name__ == "__main__":
    asyncio.run(main_cli())

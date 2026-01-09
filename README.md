# Telegram Chat Exporter

An interactive command-line tool to export chat history from Telegram channels into beautifully formatted `.docx` Word documents.

## Features

-   **Interactive CLI**: A user-friendly interface guides you through the entire export process. No more editing config files!
-   **`.docx` Export**: Generates high-quality Word documents that are easy to read, edit, and share.
-   **Flexible Options**: Customize your export with toggles for:
    -   **Image Positioning**: Place images before or after the post text.
    -   **Hyperlink Handling**: Keep links active and clickable or convert them to plain text.
    -   **Date Headings**: Add the date of each post as a distinct heading.
-   **Smart Media Handling**:
    -   Automatically groups media albums into a single post.
    -   Downloads all media to a temporary folder.
    -   Gracefully handles non-image files (videos, PDFs) by inserting a placeholder instead of crashing.
-   **Automatic File Naming**: Output files are automatically named based on the channel and date range (e.g., `MyChannel_Sep25_Jan26.docx`).
-   **Progress Visualization**: Real-time progress bars show the status of message fetching, media downloading, and document processing.
-   **Session Management**: Remembers your Telegram session, so you only need to log in with your phone and code once.

## Prerequisites

1.  **Python 3.12+**
2.  **Telegram API Credentials**:
    -   Go to [my.telegram.org/apps](https://my.telegram.org/apps).
    -   Log in and create a new application to get your `API_ID` and `API_HASH`.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/nickchets/tg-chat-parser.git
    cd tg-chat-parser
    ```

2.  **Set up a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your API credentials:**
    -   Create a file named `.env` in the project root.
    -   Add your Telegram API credentials to it:
        ```
        API_ID=12345678
        API_HASH=your_api_hash_here
        ```

5.  **Run tests (optional but recommended):**
    ```bash
    pytest
    ```

6.  **Run linting (optional but recommended):**
    ```bash
    ruff check src/ tests/
    ```

## Usage

Simply run the main script from your activated virtual environment:

```bash
source venv/bin/activate
python main.py
```

The script will guide you through the following steps:
1.  **Authentication**: On the first run, it will ask for your phone number, login code, and 2FA password (if enabled).
2.  **Configuration**: You'll be prompted to enter the channel URL, date range, and formatting options.
3.  **Export**: The tool will fetch messages, download media, and generate the `.docx` file in the `results/` directory.

### Testing

Run the test suite to verify everything is working correctly:
```bash
pytest
```

For coverage report:
```bash
pytest --cov=src --cov-report=html
```

### Linting

Check code quality with ruff:
```bash
ruff check src/ tests/
```

Auto-fix linting issues:
```bash
ruff check --fix src/ tests/
```

## Project Structure

```
/
├── .env                # Your private API credentials
├── main.py             # The main interactive script
├── requirements.txt    # Project dependencies
├── pyproject.toml      # Project configuration and dependencies (uv)
├── results/            # Output .docx files are saved here
├── temp_media/         # Temporary cache for downloaded media (auto-cleaned)
├── session.session     # Telegram session file (created after first login)
└── src/
    ├── app.py          # Main application orchestrator
    ├── cli.py          # Interactive CLI interface
    ├── config.py       # Configuration classes
    ├── docx_client.py  # Handles .docx creation and formatting
    ├── tg_client.py    # Handles Telegram communication and message fetching
    └── utils.py        # Helper functions
└── tests/
    ├── test_app.py     # Tests for main application
    ├── test_cli.py     # Tests for CLI interface
    ├── test_docx_client.py  # Tests for DOCX functionality
    ├── test_tg_client.py    # Tests for Telegram client
    └── test_e2e.py     # End-to-end tests
```

## Dependencies

- **Python 3.12+**
- **Telethon** - Telegram client library
- **python-docx** - Word document creation
- **Pillow** - Image processing
- **rich** - Beautiful terminal output
- **python-dotenv** - Environment variable management
- **pytest** - Testing framework
- **pytest-asyncio** - Async testing support
- **pytest-mock** - Mocking support
- **pytest-cov** - Coverage reporting
- **ruff** - Fast Python linter and formatter

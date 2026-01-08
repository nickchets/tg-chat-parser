# Telegram Channel to Google Docs Exporter

Automated pipeline to extract content (text + media) from a Telegram Channel and compile it into a structured Google Document with preserved formatting.

## Features

- ✅ Fetches messages from Telegram channels within a specified date range
- ✅ Groups media albums (multi-photo posts) into single entries
- ✅ Preserves text formatting (bold, italic, code, links)
- ✅ Downloads and inserts images into Google Docs
- ✅ Maintains chronological order
- ✅ Handles service messages gracefully

## Prerequisites

1. **Python 3.12+**
2. **Telegram API Credentials**
   - Go to https://my.telegram.org/apps
   - Create an application to get `API_ID` and `API_HASH`
3. **Google Cloud Service Account**
   - Create a project in Google Cloud Console
   - Enable Google Docs API and Google Drive API
   - Create a Service Account and download the JSON credentials file
   - Save it as `service_account.json` in the project root

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:
```
API_ID=your_api_id_here
API_HASH=your_api_hash_here
CHANNEL_URL=your_channel_username_or_url
CREDENTIALS_PATH=service_account.json
START_DATE=2025-09-01
END_DATE=2025-12-31
```

4. Place your Google Cloud service account credentials file as `service_account.json` in the project root

## Usage

Run the main script:
```bash
python main.py
```

The script will:
1. Connect to Telegram (you'll need to authenticate on first run)
2. Fetch messages from the specified channel within the date range
3. Download media files to `./temp_media/`
4. Create a new Google Document
5. Write all content with formatting preserved
6. Insert images inline with text

The script will output the Google Document URL when complete.

## Project Structure

```
/
├── .env                   # Environment variables (create from .env.example)
├── main.py                # Entry point (Orchestrator)
├── requirements.txt       # Python dependencies
├── service_account.json   # Google Cloud Credentials (you provide)
├── temp_media/            # Temporary media cache (auto-created)
└── src/
    ├── tg_client.py       # Telethon logic + Media Grouping
    ├── gdocs_client.py    # Google API Wrapper + Formatting Logic
    └── utils.py           # Date parsers, file helpers
```

## Configuration

### Date Range
Set `START_DATE` and `END_DATE` in `.env` (format: YYYY-MM-DD). Defaults to September 1, 2025 - December 31, 2025.

### Channel URL
Use the channel username (e.g., `@channelname`) or full URL.

### Image Sizing
Images are automatically resized to fit page width (max 500pt) while maintaining aspect ratio.

## Notes

- First Telegram authentication will require phone number verification
- Service messages (pinned notifications, etc.) are automatically skipped
- Media albums are automatically grouped into single posts
- The `temp_media/` directory stores downloaded images temporarily
- Images uploaded to Drive for Google Docs insertion may remain in Drive (they can be cleaned up manually)

## Troubleshooting

**"API_ID and API_HASH must be set"**
- Make sure your `.env` file exists and contains valid credentials

**"Credentials file not found"**
- Ensure `service_account.json` is in the project root
- Check that `CREDENTIALS_PATH` in `.env` points to the correct file

**"FloodWait" errors**
- Telegram rate limiting - the script will automatically wait and retry

**Image insertion fails**
- Ensure Google Drive API is enabled in your Google Cloud project
- Check that the service account has proper permissions

## License

This project is provided as-is for educational and personal use.

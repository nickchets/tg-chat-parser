# Troubleshooting Guide

This guide covers common issues you might encounter while using the Telegram Chat Exporter.

## Authentication & Session Issues

#### Error: `telethon.errors.rpcerrorlist.PhoneNumberInvalidError`
-   **Cause**: The phone number was entered in an incorrect format.
-   **Solution**: Make sure to enter your phone number in the full international format, including the `+` sign (e.g., `+1...`, `+7...`).

#### Error: `telethon.errors.rpcerrorlist.SessionPasswordNeededError`
-   **Cause**: Your Telegram account is protected by a Two-Factor Authentication (2FA) password.
-   **Solution**: The script will automatically prompt you to enter your 2FA password after you enter the login code. Enter it to proceed.

#### The script asks for my phone number every time I run it.
-   **Cause**: The `session.session` file is not being created or is not writable.
-   **Solution**:
    1.  Check file permissions in the project directory. Make sure you can write files.
    2.  If the issue persists, try deleting the `session.session` file and authenticating again.

## Dependency & Environment Issues

#### Error: `ModuleNotFoundError: No module named 'dotenv'` (or `rich`, `telethon`)
-   **Cause**: The required Python libraries are not installed correctly.
-   **Solution**:
    1.  Make sure your virtual environment is activated: `source venv/bin/activate`.
    2.  Run the installation command again: `pip install -r requirements.txt`.

#### The CLI looks broken or displays strange characters.
-   **Cause**: Your terminal may not fully support the rich text formatting used by the `rich` library.
-   **Solution**: Try using a modern terminal application like Windows Terminal, iTerm2 (macOS), or the default terminal in most Linux distributions.

## Exporting Issues

#### Error: `API_ID and API_HASH must be set in .env file`
-   **Cause**: The `.env` file is missing, empty, or doesn't contain the required keys.
-   **Solution**:
    1.  Ensure a file named `.env` exists in the project root.
    2.  Verify that it contains your `API_ID` and `API_HASH` in the correct format:
        ```
        API_ID=12345678
        API_HASH=your_api_hash_here
        ```

#### The script can't find the channel or says `telethon.errors.rpcerrorlist.UsernameNotOccupiedError`.
-   **Cause**: The channel URL or username is incorrect, or it's a private channel you don't have access to.
-   **Solution**:
    1.  Double-check the spelling of the channel URL or username.
    2.  For private channels, ensure you are a member of that channel with the account you authenticated with.

#### The script finishes but the `.docx` file is empty or incomplete.
-   **Cause**: No messages were found in the specified date range, or an error occurred during processing.
-   **Solution**:
    1.  Check the date range you entered. Make sure the format is `dd.mm.yyyy`.
    2.  Look for any error messages in the console output that might indicate why processing failed.
    3.  If the process was interrupted, look for a `.partial.docx` file in the `results/` directory, which may contain a partially saved document.

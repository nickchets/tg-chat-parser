# Setup Guide

This guide provides a complete walkthrough for setting up and running the Telegram Chat Exporter.

## Step 1: Get Telegram API Credentials

First, you need to get API credentials from Telegram to allow the script to access your account.

1.  **Go to the Telegram Apps portal**: [my.telegram.org/apps](https://my.telegram.org/apps)
2.  **Log in** with your phone number. You will receive a confirmation code in your Telegram app.
3.  **Create a new application**:
    *   **App title**: Choose any name (e.g., `Chat Exporter`).
    *   **Short name**: A short identifier (e.g., `chatexporter`).
    *   **Platform**: Select `Desktop`.
4.  Click **"Create application"**.
5.  You will now see your **`api_id`** and **`api_hash`**. Keep this page open.

## Step 2: Clone the Project

Get the project code onto your local machine.

```bash
git clone https://github.com/nickchets/tg-chat-parser.git
cd tg-chat-parser
```

## Step 3: Set Up the Environment

It's best practice to use a Python virtual environment to manage dependencies.

1.  **Create and activate the virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install the required libraries**:
    ```bash
    pip install -r requirements.txt
    ```

## Step 4: Configure Your API Credentials

1.  **Create a `.env` file** in the root of the project directory.
2.  **Add your API ID and Hash** from Step 1 to this file:
    ```
    API_ID=12345678
    API_HASH=your_api_hash_from_telegram
    ```

## Step 5: Run the Exporter

You are now ready to run the script!

1.  **Make sure your virtual environment is active**.
2.  **Run the main script**:
    ```bash
    python main.py
    ```

### First-Time Authentication

The first time you run the script, it will prompt you for:
1.  Your **phone number** (in international format, e.g., `+1...`).
2.  The **login code** sent to your Telegram app.
3.  Your **Two-Factor Authentication (2FA) password**, if you have one enabled.

After a successful login, a `session.session` file will be created. This file keeps you logged in, so you won't have to repeat this process on subsequent runs.

### Interactive Export

After authentication, the script will guide you through the export options:
-   Channel URL
-   Start date
-   Image positioning
-   Hyperlink handling
-   And more...

Your exported `.docx` files will be saved in the `results/` directory.

# Setup Guide: Getting Your Credentials

This guide will walk you through obtaining all the credentials needed to run the Telegram to Google Docs exporter.

## 📋 What You Need to Provide

You'll need to send me:
1. **API_ID** (a number)
2. **API_HASH** (a long string)
3. **CHANNEL_URL** (channel username or URL)
4. **service_account.json** file (or its contents)

---

## 🔵 Step 1: Get Telegram API Credentials

### Option A: If you already have a Telegram account

1. Go to **https://my.telegram.org/apps**
2. Log in with your phone number (you'll receive a code via Telegram)
3. Once logged in, you'll see:
   - **api_id**: A number (e.g., `12345678`)
   - **api_hash**: A long string (e.g., `abcdef1234567890abcdef1234567890`)

### Option B: Create a new application

1. If you don't have an app yet, click **"Create new application"**
2. Fill in:
   - **App title**: Any name (e.g., "Docs Exporter")
   - **Short name**: Any short identifier
   - **Platform**: Choose "Desktop"
   - **Description**: Optional
3. Click **"Create application"**
4. Copy the **api_id** and **api_hash**

### 📝 Send me:
```
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
```

---

## 📢 Step 2: Get Your Channel URL

### For Public Channels:
- If your channel is public, use the username (e.g., `@my_channel`)
- Or use the full URL: `https://t.me/my_channel`

### For Private Channels:
- You need to be a member/admin of the channel
- Use the channel username or invite link
- The script will access it using your Telegram account

### 📝 Send me:
```
CHANNEL_URL=@my_channel
```
or
```
CHANNEL_URL=https://t.me/my_channel
```

---

## 🔴 Step 3: Get Google Cloud Service Account Credentials

### Step 3.1: Create a Google Cloud Project

1. Go to **https://console.cloud.google.com/**
2. Sign in with your Google account
3. Click the project dropdown at the top
4. Click **"New Project"**
5. Enter a project name (e.g., "Telegram Docs Exporter")
6. Click **"Create"**
7. Wait for the project to be created, then select it

### Step 3.2: Enable Required APIs

1. Go to **"APIs & Services" > "Library"** (or search "API Library")
2. Search for **"Google Docs API"** and click it
3. Click **"Enable"**
4. Go back to the Library
5. Search for **"Google Drive API"** and click it
6. Click **"Enable"**

### Step 3.3: Create a Service Account

1. Go to **"APIs & Services" > "Credentials"**
2. Click **"Create Credentials"** at the top
3. Select **"Service account"**
4. Fill in:
   - **Service account name**: Any name (e.g., "docs-exporter")
   - **Service account ID**: Auto-generated (you can change it)
   - **Description**: Optional
5. Click **"Create and Continue"**
6. Skip the "Grant access" step (click **"Continue"**)
7. Click **"Done"**

### Step 3.4: Create and Download Key

1. In the **"Credentials"** page, find your service account in the list
2. Click on the service account email
3. Go to the **"Keys"** tab
4. Click **"Add Key" > "Create new key"**
5. Select **"JSON"** format
6. Click **"Create"**
7. A JSON file will download automatically - this is your `service_account.json`

### Step 3.5: Share the File

**Option A: Send me the file**
- Upload the `service_account.json` file and send it to me
- I'll place it in the project directory

**Option B: Send me the contents**
- Open the JSON file in a text editor
- Copy the entire contents
- Send it to me, and I'll create the file

The file looks like this:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "...@....iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  ...
}
```

---

## ✅ Quick Checklist

Before running the script, make sure you have:

- [ ] **API_ID** - Number from my.telegram.org/apps
- [ ] **API_HASH** - String from my.telegram.org/apps
- [ ] **CHANNEL_URL** - Your channel username (e.g., @channel)
- [ ] **service_account.json** - Google Cloud credentials file
- [ ] Date range (optional, defaults to Sept-Dec 2025)

---

## 🚀 After You Send Me the Info

Once you provide:
1. API_ID and API_HASH
2. CHANNEL_URL
3. service_account.json file or contents

I'll:
- ✅ Update the `.env` file with your credentials
- ✅ Place the `service_account.json` file in the project
- ✅ Verify everything is set up correctly

Then you can run:
```bash
pip install -r requirements.txt
python main.py
```

---

## 🔒 Security Note

- Never commit `.env` or `service_account.json` to version control (they're in `.gitignore`)
- Keep these credentials private
- The service account has access to create Google Docs - you can delete it later if needed

---

## ❓ Troubleshooting

**"I can't find my.telegram.org/apps"**
- Make sure you're logged into Telegram on your phone
- Try a different browser
- Clear cookies and try again

**"Google Cloud is confusing"**
- Follow the steps one by one
- Take screenshots if you get stuck
- The key is: Enable APIs → Create Service Account → Download JSON key

**"I don't have access to the channel"**
- Make sure you're a member of the channel
- For private channels, you need to be added first
- Public channels should work automatically

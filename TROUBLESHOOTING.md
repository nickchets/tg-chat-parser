# Troubleshooting Google Docs API 403 Error

## Current Issue
The service account is getting a 403 "permission denied" error when trying to create documents.

## Verification Steps

### 1. Verify API is Enabled
1. Go to: https://console.cloud.google.com/apis/library/docs.googleapis.com?project=gen-lang-client-0950802038
2. Look for "Google Docs API" 
3. It should show **"API enabled"** with a green checkmark
4. If it shows **"Enable"** button, click it and wait 1-2 minutes

### 2. Check Billing Account
Some Google Cloud features require a billing account:
1. Go to: https://console.cloud.google.com/billing?project=gen-lang-client-0950802038
2. Make sure a billing account is linked to the project

### 3. Verify Service Account Permissions
The service account might need IAM roles:
1. Go to: https://console.cloud.google.com/iam-admin/iam?project=gen-lang-client-0950802038
2. Find: `lapio-28@gen-lang-client-0950802038.iam.gserviceaccount.com`
3. Check if it has roles like:
   - "Editor" or
   - "Service Account User" or
   - Custom role with Docs API permissions

### 4. Alternative: Grant Service Account Access
If the above doesn't work, try granting the service account the "Editor" role:
1. Go to IAM: https://console.cloud.google.com/iam-admin/iam?project=gen-lang-client-0950802038
2. Click "Grant Access"
3. Add: `lapio-28@gen-lang-client-0950802038.iam.gserviceaccount.com`
4. Role: "Editor"
5. Save

### 5. Wait for Propagation
After enabling/changing anything, wait 1-2 minutes for changes to propagate.

## Quick Test
Run this to test:
```bash
source venv/bin/activate
python test_google_auth.py
```

## Still Not Working?
If after all these steps it still doesn't work, the issue might be:
- Organization policies blocking service account access
- Quota limits
- API not actually enabled (double-check the API library page)

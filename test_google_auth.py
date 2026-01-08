"""Test script to diagnose Google API authentication issues."""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

credentials_path = 'service_account.json'

print("Testing Google API authentication...")
print(f"Using credentials: {credentials_path}")

try:
    scopes = [
        'https://www.googleapis.com/auth/documents',
        'https://www.googleapis.com/auth/drive'
    ]
    
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=scopes
    )
    
    print(f"✓ Credentials loaded successfully")
    print(f"  Service account email: {credentials.service_account_email}")
    print(f"  Project ID: {credentials.project_id}")
    
    # Test Drive API
    print("\nTesting Drive API...")
    drive_service = build('drive', 'v3', credentials=credentials)
    about = drive_service.about().get(fields='user').execute()
    print(f"✓ Drive API accessible")
    
    # Test Docs API
    print("\nTesting Docs API...")
    docs_service = build('docs', 'v1', credentials=credentials)
    
    # Try to create a test document
    print("Attempting to create a test document...")
    document = {'title': 'Test Document'}
    doc = docs_service.documents().create(body=document).execute()
    print(f"✓ Document created successfully!")
    print(f"  Document ID: {doc.get('documentId')}")
    print(f"  Document URL: https://docs.google.com/document/d/{doc.get('documentId')}")
    
except FileNotFoundError:
    print(f"✗ Error: Credentials file not found: {credentials_path}")
except HttpError as e:
    print(f"✗ HTTP Error: {e}")
    print(f"  Status: {e.resp.status}")
    print(f"  Reason: {e.error_details if hasattr(e, 'error_details') else 'Unknown'}")
    
    if e.resp.status == 403:
        print("\n⚠️  Permission denied. This usually means:")
        print("  1. Google Docs API is not enabled in your Google Cloud project")
        print("  2. Google Drive API is not enabled in your Google Cloud project")
        print("\nTo fix this:")
        print("  1. Go to https://console.cloud.google.com/apis/library")
        print("  2. Search for 'Google Docs API' and click 'Enable'")
        print("  3. Search for 'Google Drive API' and click 'Enable'")
        print("  4. Make sure you're in the correct project: gen-lang-client-0950802038")
except Exception as e:
    print(f"✗ Unexpected error: {type(e).__name__}: {e}")

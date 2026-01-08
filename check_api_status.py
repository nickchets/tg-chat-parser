"""Check if Google Docs API is enabled in the project."""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

credentials_path = 'service_account.json'

print("Checking Google Cloud API status...")
print(f"Project: gen-lang-client-0950802038")
print(f"Service Account: lapio-28@gen-lang-client-0950802038.iam.gserviceaccount.com\n")

try:
    scopes = [
        'https://www.googleapis.com/auth/cloud-platform.read-only'
    ]
    
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=scopes
    )
    
    # Try to list enabled APIs (requires Service Usage API)
    service_usage = build('serviceusage', 'v1', credentials=credentials)
    
    parent = f'projects/gen-lang-client-0950802038'
    
    print("Checking enabled APIs...")
    request = service_usage.services().list(parent=parent, filter='state:ENABLED')
    
    enabled_apis = []
    while request is not None:
        response = request.execute()
        for service in response.get('services', []):
            name = service.get('name', '').split('/')[-1]
            enabled_apis.append(name)
        request = service_usage.services().list_next(previous_request=request, previous_response=response)
    
    print(f"\nFound {len(enabled_apis)} enabled APIs")
    
    docs_enabled = any('docs' in api.lower() for api in enabled_apis)
    drive_enabled = any('drive' in api.lower() for api in enabled_apis)
    
    print(f"\nGoogle Docs API: {'✓ ENABLED' if docs_enabled else '✗ NOT ENABLED'}")
    print(f"Google Drive API: {'✓ ENABLED' if drive_enabled else '✗ NOT ENABLED'}")
    
    if not docs_enabled:
        print("\n⚠️  Google Docs API is not enabled!")
        print("   Go to: https://console.cloud.google.com/apis/library/docs.googleapis.com?project=gen-lang-client-0950802038")
        print("   Click 'Enable' and wait 1-2 minutes for it to activate.")
    
except HttpError as e:
    if e.resp.status == 403:
        print("⚠️  Cannot check API status (permission denied)")
        print("   This might mean Service Usage API is not enabled.")
        print("\n   Please manually verify:")
        print("   1. Go to: https://console.cloud.google.com/apis/library?project=gen-lang-client-0950802038")
        print("   2. Search for 'Google Docs API'")
        print("   3. Make sure it shows 'Enabled' (not 'Enable')")
        print("   4. If you just enabled it, wait 1-2 minutes and try again")
    else:
        print(f"Error: {e}")
except Exception as e:
    print(f"Error checking API status: {e}")
    print("\nPlease manually verify the API is enabled:")
    print("https://console.cloud.google.com/apis/library/docs.googleapis.com?project=gen-lang-client-0950802038")

"""
Diagnostic script for Google Drive API access issues
"""

import sys
import codecs
import json
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def diagnose_drive_access():
    """Run comprehensive diagnostics on Drive API access"""

    print("="*70)
    print("  GOOGLE DRIVE API DIAGNOSTICS")
    print("="*70 + "\n")

    # Step 1: Check credentials file
    print("1. Checking credentials file...")
    creds_file = Path('google_credentials.json')

    if not creds_file.exists():
        print("   ❌ google_credentials.json not found")
        return False

    print("   ✓ File exists")

    try:
        with open(creds_file, 'r', encoding='utf-8') as f:
            creds_data = json.load(f)

        print(f"   ✓ Valid JSON")
        print(f"   Project ID: {creds_data.get('project_id')}")
        print(f"   Client Email: {creds_data.get('client_email')}")
        print(f"   Type: {creds_data.get('type')}\n")

    except Exception as e:
        print(f"   ❌ Error reading credentials: {e}")
        return False

    # Step 2: Check API scopes
    print("2. Checking API scopes...")
    scopes_to_test = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.readonly'
    ]

    for scope in scopes_to_test:
        print(f"   Testing: {scope}")
    print()

    # Step 3: Authenticate with different scopes
    print("3. Testing authentication with full Drive scope...")

    try:
        # Try with full drive scope
        credentials = service_account.Credentials.from_service_account_file(
            str(creds_file),
            scopes=['https://www.googleapis.com/auth/drive']
        )

        service = build('drive', 'v3', credentials=credentials)
        print("   ✓ Authentication successful\n")

    except Exception as e:
        print(f"   ❌ Authentication failed: {e}\n")
        return False

    # Step 4: Test API access with about endpoint
    print("4. Testing Drive API access...")

    try:
        about = service.about().get(fields="user, storageQuota").execute()
        print("   ✓ API is accessible")
        print(f"   Service account: {about.get('user', {}).get('emailAddress', 'N/A')}\n")

    except HttpError as e:
        print(f"   ❌ API Error: {e}")
        print(f"   Status: {e.resp.status}")
        print(f"   Reason: {e.error_details}\n")

        if e.resp.status == 403:
            print("   🔍 This is a permissions error. Possible causes:")
            print("      - Google Drive API not enabled in Cloud Console")
            print("      - Service account doesn't have proper IAM roles")
            print()
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}\n")
        return False

    # Step 5: List all files/folders service account can see
    print("5. Listing all accessible files/folders...")

    try:
        # List everything the service account can access
        results = service.files().list(
            pageSize=100,
            fields='files(id, name, mimeType, owners, shared, permissions)',
            q="trashed=false"
        ).execute()

        files = results.get('files', [])

        if not files:
            print("   ⚠ Service account cannot see ANY files or folders")
            print("   This means:")
            print("      - No files have been shared with the service account")
            print("      - OR the sharing hasn't propagated yet (can take a few minutes)")
            print()

        else:
            print(f"   ✓ Found {len(files)} accessible item(s):\n")

            for item in files:
                mime_type = item.get('mimeType', 'unknown')
                item_type = "📁" if 'folder' in mime_type else "📄"
                print(f"   {item_type} {item['name']}")
                print(f"      ID: {item['id']}")
                print(f"      Type: {mime_type}")

                # Check permissions
                perms = item.get('permissions', [])
                if perms:
                    print(f"      Permissions: {len(perms)} permission(s)")

                print()

    except Exception as e:
        print(f"   ❌ Error listing files: {e}\n")
        return False

    # Step 6: Search specifically for MicroCapAgent folder
    print("6. Searching for 'MicroCapAgent' folder...")

    try:
        query = "name='MicroCapAgent' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query,
            fields='files(id, name, owners, shared, permissions)',
            pageSize=10
        ).execute()

        folders = results.get('files', [])

        if folders:
            print(f"   ✓ Found {len(folders)} folder(s) named 'MicroCapAgent':\n")
            for folder in folders:
                print(f"   📁 {folder['name']}")
                print(f"      ID: {folder['id']}")
                print(f"      Shared: {folder.get('shared', False)}")

                perms = folder.get('permissions', [])
                print(f"      Permissions: {len(perms)}")

                if perms:
                    for perm in perms:
                        print(f"         - {perm.get('type')}: {perm.get('emailAddress', perm.get('id'))}")
                print()
        else:
            print("   ❌ No folder named 'MicroCapAgent' found")
            print()

    except Exception as e:
        print(f"   ❌ Error searching: {e}\n")

    # Step 7: Check if Drive API is enabled
    print("7. Recommendations:")
    print()

    if not files:
        print("   🔧 TROUBLESHOOTING STEPS:")
        print()
        print("   A. Verify Drive API is enabled:")
        print("      1. Go to: https://console.cloud.google.com/apis/library")
        print(f"      2. Make sure project '{creds_data.get('project_id')}' is selected")
        print("      3. Search for 'Google Drive API'")
        print("      4. Click on it and ensure it shows 'API enabled'")
        print()
        print("   B. Re-share the folder (sharing can take a few minutes to propagate):")
        print("      1. Go to https://drive.google.com")
        print("      2. Find the 'MicroCapAgent' folder")
        print("      3. Right-click → 'Share'")
        print(f"      4. Verify {creds_data.get('client_email')} is listed")
        print("      5. Make sure role is 'Editor' not 'Viewer'")
        print("      6. If not listed, add it again")
        print()
        print("   C. Wait a few minutes and run this diagnostic again")
        print()
    else:
        print("   ✓ Service account has access to some files")
        print("   If MicroCapAgent folder not found, check folder name spelling")
        print()

    print("="*70)
    return True


if __name__ == "__main__":
    try:
        success = diagnose_drive_access()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nDiagnostic cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

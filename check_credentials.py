"""
Check for Google Drive credentials and validate them
"""

import json
from pathlib import Path
import sys
import codecs

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def check_google_credentials():
    """
    Check if Google Drive credentials exist and are valid

    Returns:
        Tuple of (success: bool, error_message: str or None)
    """
    creds_file = Path('google_credentials.json')

    # Check if file exists
    if not creds_file.exists():
        error_msg = """
⚠️  Google Drive credentials not found.

To set up:
1. Go to https://console.cloud.google.com
2. Create project: 'MicroCapAgent'
3. Enable Google Drive API:
   - In APIs & Services > Library
   - Search "Google Drive API"
   - Click Enable

4. Create Service Account:
   - Go to APIs & Services > Credentials
   - Create Credentials > Service Account
   - Name it: 'microcap-agent'
   - Grant role: Editor

5. Create JSON key:
   - Click on the service account
   - Go to Keys tab
   - Add Key > Create new key > JSON
   - Save file as 'google_credentials.json'

6. Move file to project:
   - Place in: ~/microcap_agent/google_credentials.json

7. Set up Drive folder:
   - Create folder in Google Drive: 'MicroCapAgent'
   - Right-click > Share
   - Add service account email (from JSON file)
   - Grant Editor access

Run this check again after setup is complete.
"""
        return False, error_msg

    # Try to parse JSON
    try:
        with open(creds_file, 'r', encoding='utf-8') as f:
            creds_data = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"""
❌ Error: google_credentials.json is not valid JSON

Parse error: {e}

Please download a fresh credentials file from Google Cloud Console.
"""
        return False, error_msg
    except Exception as e:
        error_msg = f"""
❌ Error reading google_credentials.json: {e}

Please check file permissions and try again.
"""
        return False, error_msg

    # Validate required fields
    required_fields = [
        'type',
        'project_id',
        'private_key_id',
        'private_key',
        'client_email',
        'client_id'
    ]

    missing_fields = [field for field in required_fields if field not in creds_data]

    if missing_fields:
        error_msg = f"""
❌ Error: google_credentials.json is missing required fields

Missing: {', '.join(missing_fields)}

This doesn't look like a valid service account JSON file.
Please download the correct file from Google Cloud Console.
"""
        return False, error_msg

    # Validate it's a service account
    if creds_data.get('type') != 'service_account':
        error_msg = f"""
❌ Error: Invalid credential type

Expected: service_account
Found: {creds_data.get('type')}

Please create a Service Account key, not an OAuth client ID.
"""
        return False, error_msg

    # All good!
    success_msg = f"""
✓ Google Drive credentials found and validated!

Project: {creds_data.get('project_id')}
Service Account: {creds_data.get('client_email')}

Next steps:
1. Make sure you've enabled Google Drive API in the project
2. Create a folder in Google Drive called 'MicroCapAgent'
3. Share that folder with: {creds_data.get('client_email')}
4. Grant Editor permissions

You're ready to use Google Drive integration!
"""
    return True, success_msg


def main():
    """Run credentials check"""
    print("\n" + "="*70)
    print("  GOOGLE DRIVE CREDENTIALS CHECK")
    print("="*70)

    success, message = check_google_credentials()

    print(message)

    if success:
        print("="*70)
        return 0
    else:
        print("="*70)
        return 1


if __name__ == "__main__":
    sys.exit(main())

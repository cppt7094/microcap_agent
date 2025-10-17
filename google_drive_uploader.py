"""
Google Drive Upload Module
Handles uploading files to Google Drive using service account credentials
"""

import sys
import codecs
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


# Google Drive API scopes
# Using full 'drive' scope to access shared folders
# The more restrictive 'drive.file' scope only works with files the app creates itself
SCOPES = ['https://www.googleapis.com/auth/drive']

# Folder name in Google Drive
DRIVE_FOLDER_NAME = 'MicroCapAgent'

# Hardcoded folder ID (faster, skips search)
DRIVE_FOLDER_ID = '1uJq5oCvIw7ryqjgEbWWnJQB7U2IFC-Pw'


class GoogleDriveUploader:
    """Handles Google Drive uploads"""

    def __init__(self, credentials_path: str = 'google_credentials.json'):
        """
        Initialize Drive uploader

        Args:
            credentials_path: Path to service account JSON credentials
        """
        self.credentials_path = Path(credentials_path)
        self.service = None
        self.folder_id = None

    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive API

        Returns:
            Boolean success status
        """
        try:
            if not self.credentials_path.exists():
                logging.error(f"Credentials file not found: {self.credentials_path}")
                return False

            credentials = service_account.Credentials.from_service_account_file(
                str(self.credentials_path),
                scopes=SCOPES
            )

            self.service = build('drive', 'v3', credentials=credentials)
            logging.info("Successfully authenticated with Google Drive")
            return True

        except Exception as e:
            logging.error(f"Failed to authenticate with Google Drive: {e}")
            return False

    def list_all_folders(self) -> list:
        """
        List all folders the service account can access (for debugging)

        Returns:
            List of folder names and IDs
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return []

            query = "mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=100
            ).execute()

            folders = results.get('files', [])
            return folders

        except Exception as e:
            logging.error(f"Error listing folders: {e}")
            return []

    def find_folder(self, folder_name: str = DRIVE_FOLDER_NAME) -> Optional[str]:
        """
        Find folder by name in Google Drive

        Args:
            folder_name: Name of folder to find

        Returns:
            Folder ID if found, None otherwise
        """
        try:
            if not self.service:
                if not self.authenticate():
                    return None

            # Search for folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            folders = results.get('files', [])

            if not folders:
                logging.warning(f"Folder '{folder_name}' not found in Google Drive")

                # List all accessible folders for debugging
                all_folders = self.list_all_folders()
                if all_folders:
                    logging.info(f"Service account can access {len(all_folders)} folder(s)")
                    for folder in all_folders:
                        logging.info(f"  - {folder['name']} (ID: {folder['id']})")
                else:
                    logging.warning("Service account cannot access any folders")

                return None

            folder_id = folders[0]['id']
            logging.info(f"Found folder '{folder_name}' with ID: {folder_id}")
            self.folder_id = folder_id
            return folder_id

        except HttpError as e:
            logging.error(f"HTTP error finding folder: {e}")
            return None
        except Exception as e:
            logging.error(f"Error finding folder: {e}")
            return None

    def upload_file(self, file_path: str, folder_id: Optional[str] = None,
                   mime_type: str = 'application/json') -> Optional[Dict]:
        """
        Upload file to Google Drive

        Args:
            file_path: Path to file to upload
            folder_id: Optional folder ID (uses DRIVE_FOLDER_ID constant if None)
            mime_type: MIME type of file

        Returns:
            File metadata dict if successful, None otherwise
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                logging.error(f"File not found: {file_path}")
                return None

            if not self.service:
                if not self.authenticate():
                    return None

            # Use hardcoded folder ID if not provided (skip search for speed)
            if not folder_id:
                folder_id = DRIVE_FOLDER_ID
                logging.info(f"Using hardcoded folder ID: {folder_id}")

            # Check if file already exists in folder
            existing_file_id = self._find_file_in_folder(file_path.name, folder_id)

            # Prepare file metadata
            file_metadata = {
                'name': file_path.name,
            }

            if not existing_file_id:
                # New upload
                file_metadata['parents'] = [folder_id]

            # Create media upload
            media = MediaFileUpload(
                str(file_path),
                mimetype=mime_type,
                resumable=True
            )

            if existing_file_id:
                # Update existing file
                logging.info(f"Updating existing file: {file_path.name}")
                file = self.service.files().update(
                    fileId=existing_file_id,
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, webViewLink, modifiedTime',
                    supportsAllDrives=False  # Use personal Drive storage
                ).execute()
            else:
                # Create new file
                # Note: File will be stored in the owner's Drive (not service account)
                # The service account only needs Editor permission on the folder
                logging.info(f"Uploading new file: {file_path.name}")
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, webViewLink, modifiedTime',
                    supportsAllDrives=False  # Use personal Drive storage
                ).execute()

            logging.info(f"Successfully uploaded: {file.get('name')}")
            return file

        except HttpError as e:
            logging.error(f"HTTP error uploading file: {e}")
            return None
        except Exception as e:
            logging.error(f"Error uploading file: {e}", exc_info=True)
            return None

    def _find_file_in_folder(self, filename: str, folder_id: str) -> Optional[str]:
        """
        Check if file exists in folder

        Args:
            filename: Name of file to find
            folder_id: Folder to search in

        Returns:
            File ID if found, None otherwise
        """
        try:
            query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            files = results.get('files', [])
            if files:
                return files[0]['id']
            return None

        except Exception as e:
            logging.error(f"Error checking for existing file: {e}")
            return None

    def upload_market_close_summary(self, summary_file: str) -> bool:
        """
        Upload market close summary JSON to Drive

        Args:
            summary_file: Path to summary JSON file

        Returns:
            Boolean success status
        """
        try:
            result = self.upload_file(
                file_path=summary_file,
                mime_type='application/json'
            )

            if result:
                logging.info(f"Market close summary uploaded: {result.get('webViewLink')}")
                return True
            return False

        except Exception as e:
            logging.error(f"Error uploading market close summary: {e}")
            return False

    def upload_log_file(self, log_file: str) -> bool:
        """
        Upload log file to Drive

        Args:
            log_file: Path to log file

        Returns:
            Boolean success status
        """
        try:
            result = self.upload_file(
                file_path=log_file,
                mime_type='text/plain'
            )

            if result:
                logging.info(f"Log file uploaded: {result.get('webViewLink')}")
                return True
            return False

        except Exception as e:
            logging.error(f"Error uploading log file: {e}")
            return False


def test_upload():
    """Test Google Drive upload functionality"""
    print("\n" + "="*70)
    print("  GOOGLE DRIVE UPLOAD TEST")
    print("="*70 + "\n")

    uploader = GoogleDriveUploader()

    # Authenticate
    print("Authenticating...")
    if not uploader.authenticate():
        print("❌ Authentication failed")
        return False

    print("✓ Authenticated successfully\n")

    # Find folder
    print(f"Looking for folder: {DRIVE_FOLDER_NAME}")
    folder_id = uploader.find_folder()

    if not folder_id:
        print(f"❌ Folder '{DRIVE_FOLDER_NAME}' not found")

        # Show accessible folders
        all_folders = uploader.list_all_folders()
        if all_folders:
            print(f"\nService account CAN access {len(all_folders)} folder(s):")
            for folder in all_folders:
                print(f"  • {folder['name']}")
            print(f"\n⚠ The folder exists but may be named differently.")
            print(f"   Or you need to share '{DRIVE_FOLDER_NAME}' with the service account.")
        else:
            print(f"\n⚠ Service account cannot access ANY folders.")
            print(f"   This means no folders have been shared with it yet.")

        print(f"\nTo fix:")
        print(f"1. Go to https://drive.google.com")
        print(f"2. Create or find folder: '{DRIVE_FOLDER_NAME}'")
        print(f"3. Right-click → Share")
        print(f"4. Add: monitoring-agent@microcapagent.iam.gserviceaccount.com")
        print(f"5. Grant 'Editor' permission")
        print(f"6. Click 'Send'")
        return False

    print(f"✓ Found folder: {folder_id}\n")

    # Create test file
    from pathlib import Path
    import json

    test_file = Path('test_upload.json')
    test_data = {
        'test': True,
        'timestamp': datetime.now().isoformat(),
        'message': 'Test upload from monitoring agent'
    }

    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2)

    print(f"Uploading test file: {test_file}")
    result = uploader.upload_file(str(test_file))

    # Clean up test file
    test_file.unlink()

    if result:
        print(f"✓ Upload successful!")
        print(f"  File ID: {result.get('id')}")
        print(f"  View at: {result.get('webViewLink')}")
        print("\n" + "="*70)
        return True
    else:
        print("❌ Upload failed")
        print("="*70)
        return False


if __name__ == "__main__":
    import sys
    success = test_upload()
    sys.exit(0 if success else 1)

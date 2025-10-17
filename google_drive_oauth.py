"""
Google Drive Upload Module using OAuth 2.0
This works with personal Gmail accounts without storage quota issues
"""

import sys
import codecs
import logging
import json
import pickle
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
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
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Folder name in Google Drive
DRIVE_FOLDER_NAME = 'MicroCapAgent'


class GoogleDriveOAuthUploader:
    """Handles Google Drive uploads using OAuth 2.0"""

    def __init__(self, credentials_path: str = 'google_oauth_credentials.json',
                 token_path: str = 'token.pickle'):
        """
        Initialize Drive uploader with OAuth

        Args:
            credentials_path: Path to OAuth 2.0 client credentials JSON
            token_path: Path to store user token
        """
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.service = None
        self.folder_id = None

    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive API using OAuth 2.0

        Returns:
            Boolean success status
        """
        try:
            creds = None

            # Load existing token if available
            if self.token_path.exists():
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)

            # If no valid credentials, let user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logging.info("Refreshing expired token")
                    creds.refresh(Request())
                else:
                    if not self.credentials_path.exists():
                        logging.error(f"OAuth credentials file not found: {self.credentials_path}")
                        return False

                    logging.info("Starting OAuth flow")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), SCOPES)
                    creds = flow.run_local_server(port=0)

                # Save the credentials for next run
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)

            self.service = build('drive', 'v3', credentials=creds)
            logging.info("Successfully authenticated with Google Drive")
            return True

        except Exception as e:
            logging.error(f"Failed to authenticate with Google Drive: {e}")
            return False

    def find_or_create_folder(self, folder_name: str = DRIVE_FOLDER_NAME) -> Optional[str]:
        """
        Find folder by name, create if it doesn't exist

        Args:
            folder_name: Name of folder to find or create

        Returns:
            Folder ID if found/created, None otherwise
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

            if folders:
                folder_id = folders[0]['id']
                logging.info(f"Found folder '{folder_name}' with ID: {folder_id}")
                self.folder_id = folder_id
                return folder_id

            # Folder doesn't exist, create it
            logging.info(f"Creating folder '{folder_name}'")
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name'
            ).execute()

            folder_id = folder.get('id')
            logging.info(f"Created folder '{folder_name}' with ID: {folder_id}")
            self.folder_id = folder_id
            return folder_id

        except HttpError as e:
            logging.error(f"HTTP error finding/creating folder: {e}")
            return None
        except Exception as e:
            logging.error(f"Error finding/creating folder: {e}")
            return None

    def upload_file(self, file_path: str, folder_id: Optional[str] = None,
                   mime_type: str = 'application/json') -> Optional[Dict]:
        """
        Upload file to Google Drive

        Args:
            file_path: Path to file to upload
            folder_id: Optional folder ID (uses DRIVE_FOLDER_NAME if None)
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

            # Find/create folder if not provided
            if not folder_id:
                folder_id = self.find_or_create_folder()
                if not folder_id:
                    logging.error(f"Cannot upload without folder ID")
                    return None

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
                    fields='id, name, webViewLink, modifiedTime'
                ).execute()
            else:
                # Create new file
                logging.info(f"Uploading new file: {file_path.name}")
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, webViewLink, modifiedTime'
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
    """Test Google Drive OAuth upload functionality"""
    print("\n" + "="*70)
    print("  GOOGLE DRIVE OAUTH UPLOAD TEST")
    print("="*70 + "\n")

    uploader = GoogleDriveOAuthUploader()

    # Authenticate
    print("Authenticating with OAuth 2.0...")
    print("(A browser window will open for authorization)\n")

    if not uploader.authenticate():
        print("❌ Authentication failed")
        return False

    print("✓ Authenticated successfully\n")

    # Find/create folder
    print(f"Finding or creating folder: {DRIVE_FOLDER_NAME}")
    folder_id = uploader.find_or_create_folder()

    if not folder_id:
        print(f"❌ Could not find/create folder")
        return False

    print(f"✓ Folder ready: {folder_id}\n")

    # Create test file
    test_file = Path('test_upload.json')
    test_data = {
        'test': True,
        'timestamp': datetime.now().isoformat(),
        'message': 'Test OAuth upload from monitoring agent',
        'method': 'OAuth 2.0 (user authentication)'
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

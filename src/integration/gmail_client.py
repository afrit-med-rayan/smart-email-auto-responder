import os.path
import base64
import logging
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailClient:
    """Wrapper for Gmail API."""
    
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        self.creds = None
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticates with Gmail API."""
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if os.path.exists(self.credentials_path):
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                    # Note: This requires browser interaction which might not work in headless server env without port forwarding
                    # For now, we assume this is run locally or token.json is provided.
                    self.creds = flow.run_local_server(port=0)
                else:
                    logger.warning(f"Credentials file not found at {self.credentials_path}. Gmail Client disabled.")
                    return

            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())
                
        if self.creds:
            self.service = build('gmail', 'v1', credentials=self.creds)
            logger.info("Gmail API Service created successfully.")

    def list_unread_emails(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """List unread emails from Inbox."""
        if not self.service:
            logger.error("Gmail service not initialized.")
            return []

        try:
            results = self.service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD'], maxResults=max_results).execute()
            messages = results.get('messages', [])
            
            emails = []
            for msg in messages:
                full_msg = self.service.users().messages().get(userId='me', id=msg['id']).execute()
                emails.append(full_msg)
            return emails
        except Exception as e:
            logger.error(f"Error listing emails: {e}")
            return []

    def create_draft(self, to: str, subject: str, body: str) -> Optional[Dict[str, Any]]:
        """Create a draft email."""
        if not self.service:
            return None

        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            body = {'message': {'raw': raw}}
            
            draft = self.service.users().drafts().create(userId='me', body=body).execute()
            logger.info(f"Draft created with ID: {draft['id']}")
            return draft
        except Exception as e:
            logger.error(f"Error creating draft: {e}")
            return None

if __name__ == "__main__":
    # Test client
    client = GmailClient()
    if client.service:
        print("Gmail Client Ready.")
        unread = client.list_unread_emails(max_results=1)
        print(f"Found {len(unread)} unread emails.")

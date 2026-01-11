"""
Email Parser Module

Parses raw email data from Gmail API into structured format.
Handles MIME parsing, thread detection, and attachment metadata.
"""

import base64
import email
import re
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional, Any
from src.config_loader import config

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

class EmailParser:
    """Parses raw email data from Gmail API."""
    
    def __init__(self):
        pass
        
    def parse_gmail_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a Gmail API message object.
        
        Args:
            message: Gmail API message dictionary
            
        Returns:
            Structured email dictionary
        """
        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        
        # Extract headers
        header_dict = {h['name'].lower(): h['value'] for h in headers}
        
        # specific headers
        sender = header_dict.get('from', '')
        recipient = header_dict.get('to', '')
        subject = header_dict.get('subject', '')
        date_str = header_dict.get('date', '')
        message_id = header_dict.get('message-id', '')
        
        # Parse date
        try:
            timestamp = parsedate_to_datetime(date_str)
        except:
            timestamp = None
            
        # Extract body
        body_text, body_html = self._get_email_body(payload)
        
        # If no plain text, try to strip HTML
        if not body_text and body_html:
            if HAS_BS4:
                soup = BeautifulSoup(body_html, 'html.parser')
                body_text = soup.get_text(separator='\n')
            else:
                # Fallback simple regex strip
                body_text = re.sub(r'<[^>]+>', '', body_html)
            
        # Identify attachments
        attachments = self._get_attachments(payload)
        
        return {
            "id": message.get('id'),
            "thread_id": message.get('threadId'),
            "message_id": message_id,
            "sender": sender,
            "recipient": recipient,
            "subject": subject,
            "date": date_str,
            "timestamp": timestamp,
            "body": body_text,
            "body_html": body_html,
            "snippet": message.get('snippet', ''),
            "label_ids": message.get('labelIds', []),
            "attachments": attachments
        }
    
    def _get_email_body(self, payload: Dict[str, Any]) -> tuple[str, str]:
        """
        Recursively extract plain text and HTML body.
        
        Returns:
            (plain_text, html_content)
        """
        body_text = ""
        body_html = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType', '')
                
                if mime_type == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        body_text += self._decode_base64(data)
                
                elif mime_type == 'text/html':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        body_html += self._decode_base64(data)
                        
                elif mime_type.startswith('multipart/'):
                    sub_text, sub_html = self._get_email_body(part)
                    body_text += sub_text
                    body_html += sub_html
        else:
            # Single part message
            mime_type = payload.get('mimeType', '')
            data = payload.get('body', {}).get('data', '')
            
            if data:
                content = self._decode_base64(data)
                if mime_type == 'text/plain':
                    body_text = content
                elif mime_type == 'text/html':
                    body_html = content
                    
        return body_text, body_html

    def _get_attachments(self, payload: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract attachment metadata."""
        attachments = []
        
        if 'parts' in payload:
            for part in payload['parts']:
                filename = part.get('filename', '')
                if filename:
                    attachments.append({
                        "filename": filename,
                        "mime_type": part.get('mimeType', ''),
                        "attachment_id": part.get('body', {}).get('attachmentId', ''),
                        "size": part.get('body', {}).get('size', 0)
                    })
                
                # Check nested parts
                if 'parts' in part:
                    attachments.extend(self._get_attachments(part))
                    
        return attachments

    def _decode_base64(self, data: str) -> str:
        """Decode URL-safe base64 string."""
        try:
            # Add padding if needed
            pad = len(data) % 4
            if pad:
                data += "=" * (4 - pad)
            return base64.urlsafe_b64decode(data).decode('utf-8')
        except Exception:
            return ""

# Example usage
if __name__ == "__main__":
    parser = EmailParser()
    print("Email Parser initialized.")

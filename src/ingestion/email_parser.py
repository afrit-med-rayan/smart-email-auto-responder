"""
Email Parser Module

Extracts structured data from raw email messages.
Handles MIME parsing, header extraction, and body processing.
"""

import re
from typing import Dict, List, Optional, Any
from email import message_from_string
from email.header import decode_header
from bs4 import BeautifulSoup
from datetime import datetime


class EmailParser:
    """Parse raw email messages into structured format."""
    
    def __init__(self):
        self.signature_patterns = [
            r'--\s*\n',  # Standard signature delimiter
            r'Sent from my \w+',  # Mobile signatures
            r'Best regards,?\n',
            r'Sincerely,?\n',
            r'Thanks,?\n',
        ]
    
    def parse(self, raw_email: str, email_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse raw email into structured format.
        
        Args:
            raw_email: Raw email string (MIME format)
            email_id: Optional email ID
            
        Returns:
            Structured email dictionary
        """
        msg = message_from_string(raw_email)
        
        return {
            "id": email_id or self._generate_id(),
            "sender": self._parse_address(msg.get("From", "")),
            "recipient": self._parse_address(msg.get("To", "")),
            "subject": self._decode_header(msg.get("Subject", "")),
            "body": self._extract_body(msg),
            "timestamp": self._parse_timestamp(msg.get("Date", "")),
            "thread_id": msg.get("Thread-ID", ""),
            "message_id": msg.get("Message-ID", ""),
            "in_reply_to": msg.get("In-Reply-To", ""),
            "labels": [],  # Will be populated by Gmail API
            "attachments": self._extract_attachments(msg),
            "raw_headers": dict(msg.items()),
        }
    
    def parse_gmail_message(self, gmail_msg: Dict) -> Dict[str, Any]:
        """
        Parse Gmail API message format.
        
        Args:
            gmail_msg: Message from Gmail API
            
        Returns:
            Structured email dictionary
        """
        headers = {h["name"]: h["value"] for h in gmail_msg.get("payload", {}).get("headers", [])}
        
        return {
            "id": gmail_msg.get("id"),
            "sender": self._parse_address(headers.get("From", "")),
            "recipient": self._parse_address(headers.get("To", "")),
            "subject": headers.get("Subject", ""),
            "body": self._extract_gmail_body(gmail_msg.get("payload", {})),
            "timestamp": self._parse_gmail_timestamp(gmail_msg.get("internalDate")),
            "thread_id": gmail_msg.get("threadId", ""),
            "message_id": headers.get("Message-ID", ""),
            "in_reply_to": headers.get("In-Reply-To", ""),
            "labels": gmail_msg.get("labelIds", []),
            "attachments": self._extract_gmail_attachments(gmail_msg.get("payload", {})),
            "raw_headers": headers,
        }
    
    def _parse_address(self, address: str) -> str:
        """Extract email address from 'Name <email@domain.com>' format."""
        match = re.search(r'<(.+?)>', address)
        if match:
            return match.group(1).strip()
        return address.strip()
    
    def _decode_header(self, header: str) -> str:
        """Decode email header (handles encoding)."""
        if not header:
            return ""
        
        decoded_parts = decode_header(header)
        result = []
        
        for content, encoding in decoded_parts:
            if isinstance(content, bytes):
                result.append(content.decode(encoding or 'utf-8', errors='ignore'))
            else:
                result.append(content)
        
        return ' '.join(result)
    
    def _extract_body(self, msg) -> str:
        """Extract email body (prefer plain text, fallback to HTML)."""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        continue
                elif content_type == "text/html" and not body:
                    try:
                        html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        body = self._html_to_text(html)
                    except:
                        continue
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                if msg.get_content_type() == "text/html":
                    body = self._html_to_text(body)
            except:
                body = str(msg.get_payload())
        
        return body.strip()
    
    def _extract_gmail_body(self, payload: Dict) -> str:
        """Extract body from Gmail API payload."""
        import base64
        
        body = ""
        
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                elif part.get("mimeType") == "text/html" and not body:
                    data = part.get("body", {}).get("data", "")
                    if data:
                        html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        body = self._html_to_text(html)
        else:
            data = payload.get("body", {}).get("data", "")
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                if payload.get("mimeType") == "text/html":
                    body = self._html_to_text(body)
        
        return body.strip()
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _parse_timestamp(self, date_str: str) -> str:
        """Parse email date header to ISO format."""
        if not date_str:
            return datetime.now().isoformat()
        
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            return dt.isoformat()
        except:
            return datetime.now().isoformat()
    
    def _parse_gmail_timestamp(self, internal_date: str) -> str:
        """Parse Gmail internal date (milliseconds since epoch)."""
        if not internal_date:
            return datetime.now().isoformat()
        
        try:
            timestamp_ms = int(internal_date)
            dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
            return dt.isoformat()
        except:
            return datetime.now().isoformat()
    
    def _extract_attachments(self, msg) -> List[Dict[str, str]]:
        """Extract attachment metadata."""
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            "filename": self._decode_header(filename),
                            "content_type": part.get_content_type(),
                            "size": len(part.get_payload(decode=True) or b""),
                        })
        
        return attachments
    
    def _extract_gmail_attachments(self, payload: Dict) -> List[Dict[str, str]]:
        """Extract attachment metadata from Gmail payload."""
        attachments = []
        
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("filename"):
                    attachments.append({
                        "filename": part["filename"],
                        "content_type": part.get("mimeType", ""),
                        "size": part.get("body", {}).get("size", 0),
                    })
        
        return attachments
    
    def _generate_id(self) -> str:
        """Generate unique email ID."""
        import uuid
        return str(uuid.uuid4())


# Example usage
if __name__ == "__main__":
    parser = EmailParser()
    
    # Test with sample email
    sample_email = """From: professor@university.edu
To: student@email.com
Subject: Assignment Deadline Extension
Date: Fri, 10 Jan 2026 10:30:00 +0100

Hi Student,

I wanted to let you know that the deadline for the final project has been extended to next Friday.

Best regards,
Professor Smith
"""
    
    parsed = parser.parse(sample_email)
    print("Parsed Email:")
    print(f"Sender: {parsed['sender']}")
    print(f"Subject: {parsed['subject']}")
    print(f"Body: {parsed['body'][:100]}...")

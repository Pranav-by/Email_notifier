import base64
import email
import json
import logging
import os
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import CREDENTIALS_FILE, TOKEN_FILE, GMAIL_SCOPES

logger = logging.getLogger(__name__)

class GmailFetcher:
    def __init__(self):
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail using OAuth 2.0 (file or env var)."""
        creds = None
        
        # 1. Check if token file exists or is provided via environment variable
        token_env = os.getenv("GMAIL_TOKEN_JSON")
        if TOKEN_FILE.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), GMAIL_SCOPES)
            except Exception as e:
                logger.warning(f"Failed to load token file: {e}")
        elif token_env:
            try:
                token_info = json.loads(token_env)
                creds = Credentials.from_authorized_user_info(token_info, GMAIL_SCOPES)
            except Exception as e:
                logger.warning(f"Failed to load token from environment variable: {e}")

        # 2. Refresh or re-authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Token refresh failed: {e}.")
                    creds = None
            
            if not creds:
                creds_env = os.getenv("GMAIL_CREDENTIALS_JSON")
                if CREDENTIALS_FILE.exists():
                    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), GMAIL_SCOPES)
                    creds = flow.run_local_server(port=0)
                elif creds_env:
                    client_config = json.loads(creds_env)
                    flow = InstalledAppFlow.from_client_config(client_config, GMAIL_SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    raise FileNotFoundError(
                        f"Missing OAuth credentials. Ensure token.json or credential.json exists."
                    )

            # Save the credentials for subsequent runs
            try:
                with open(TOKEN_FILE, "w") as token:
                    token.write(creds.to_json())
            except Exception:
                pass

        self.service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail API service successfully initialized.")

    def _clean_html(self, html_content: str) -> str:
        """Convert HTML body into clean readable text."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            # Remove script and style elements
            for script in soup(["script", "style", "head", "title", "meta"]):
                script.extract()
            text = soup.get_text(separator="\n")
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            return "\n".join(chunk for chunk in chunks if chunk)
        except Exception:
            return html_content

    def _get_body_from_payload(self, payload: dict) -> tuple[str, list[str]]:
        """Recursively extract plain text or HTML body and attachment filenames."""
        body = ""
        attachments = []

        def parse_part(part):
            nonlocal body, attachments
            mime_type = part.get("mimeType", "")
            filename = part.get("filename", "")
            
            if filename:
                attachments.append(filename)

            if mime_type == "text/plain" and "data" in part.get("body", {}):
                data = part["body"]["data"]
                decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                if not body:
                    body = decoded
            elif mime_type == "text/html" and "data" in part.get("body", {}):
                data = part["body"]["data"]
                decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                # Clean html if no plain text yet
                if not body:
                    body = self._clean_html(decoded)
            
            # Recurse through parts if multipart
            if "parts" in part:
                for subpart in part["parts"]:
                    parse_part(subpart)

        if "parts" in payload:
            for part in payload["parts"]:
                parse_part(part)
        elif "body" in payload and "data" in payload["body"]:
            data = payload["body"]["data"]
            decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            if payload.get("mimeType") == "text/html":
                body = self._clean_html(decoded)
            else:
                body = decoded

        return body.strip(), attachments

    def fetch_recent_emails(self, max_results: int = 10, query: str = "is:unread") -> list[dict]:
        """Fetch emails matching the given query."""
        if not self.service:
            self._authenticate()

        try:
            results = self.service.users().messages().list(
                userId="me",
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get("messages", [])
            email_list = []

            for msg_summary in messages:
                msg_id = msg_summary["id"]
                msg = self.service.users().messages().get(
                    userId="me",
                    id=msg_id,
                    format="full"
                ).execute()

                payload = msg.get("payload", {})
                headers = payload.get("headers", [])
                
                header_dict = {h["name"].lower(): h["value"] for h in headers}
                
                subject = header_dict.get("subject", "(No Subject)")
                sender = header_dict.get("from", "Unknown Sender")
                date = header_dict.get("date", "")
                snippet = msg.get("snippet", "")

                body, attachments = self._get_body_from_payload(payload)
                if not body:
                    body = snippet

                email_list.append({
                    "id": msg_id,
                    "thread_id": msg.get("threadId"),
                    "subject": subject,
                    "sender": sender,
                    "date": date,
                    "snippet": snippet,
                    "body": body,
                    "attachments": attachments
                })

            return email_list

        except Exception as e:
            logger.error(f"Error fetching emails from Gmail: {e}")
            return []

    def get_unread_message_ids(self) -> set[str]:
        """Fetch all currently unread message IDs quickly (IDs only)."""
        if not self.service:
            self._authenticate()
        try:
            results = self.service.users().messages().list(
                userId="me",
                q="is:unread",
                maxResults=100
            ).execute()
            messages = results.get("messages", [])
            return {m["id"] for m in messages}
        except Exception as e:
            logger.error(f"Error fetching unread message IDs: {e}")
            return set()

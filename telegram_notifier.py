import html
import logging
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, token: str = TELEGRAM_BOT_TOKEN, chat_id: str = TELEGRAM_CHAT_ID):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def test_connection(self) -> bool:
        """Verify bot credentials and get bot details."""
        try:
            res = requests.get(f"{self.base_url}/getMe", timeout=10)
            data = res.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                logger.info(f"Connected to Telegram Bot: @{bot_info.get('username')}")
                return True
            else:
                logger.error(f"Telegram getMe failed: {data}")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            return False

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a formatted message to the configured chat_id."""
        if not self.token or not self.chat_id:
            logger.error("Telegram token or chat_id is missing.")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        try:
            res = requests.post(url, json=payload, timeout=15)
            data = res.json()
            if data.get("ok"):
                return True
            else:
                logger.warning(f"Failed to send HTML formatted message, retrying plain text. Error: {data}")
                payload["parse_mode"] = ""
                res2 = requests.post(url, json=payload, timeout=15)
                return res2.json().get("ok", False)
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
            return False

    def send_email_with_summary(self, email_data: dict, analysis: dict) -> bool:
        """
        Send the full email message first, followed by the AI summary at the last.
        """
        priority_emoji = {
            "URGENT": "🚨",
            "HIGH": "🔥",
            "MEDIUM": "📌",
            "LOW": "📩"
        }.get(analysis.get("priority", "MEDIUM").upper(), "📬")

        priority = analysis.get("priority", "NORMAL").upper()
        category = html.escape(analysis.get("category", "General"))
        subject = html.escape(email_data.get("subject", "(No Subject)"))
        sender = html.escape(email_data.get("sender", "Unknown"))
        date = html.escape(email_data.get("date", ""))
        body_text = email_data.get("body", "").strip()

        # Format AI summary & action items
        raw_summary = analysis.get("summary", [])
        if isinstance(raw_summary, list):
            summary_text = "\n".join([f"• {html.escape(s)}" for s in raw_summary if s])
        else:
            summary_text = html.escape(str(raw_summary))

        action_items = analysis.get("action_items", [])
        action_text = ""
        if action_items:
            items_str = "\n".join([f"• {html.escape(item)}" for item in action_items if item])
            if items_str.strip():
                action_text = f"\n⚡ <b>Action Items / Deadlines:</b>\n{items_str}"

        att_text = ""
        if email_data.get("attachments"):
            att_names = ", ".join([html.escape(a) for a in email_data["attachments"]])
            att_text = f"\n📎 <b>Attachments:</b> {att_names}"

        # 1. Prepare AI summary section for the last
        ai_summary_block = (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🤖 <b>AI Executive Summary:</b>\n"
            f"{summary_text if summary_text else '• (No summary generated)'}"
            f"{action_text}"
        )

        # 2. Check body length
        # Telegram character limit is 4096.
        # Header + AI summary takes ~800-1000 chars.
        max_single_msg_body_len = 2500

        if len(body_text) <= max_single_msg_body_len:
            # Send everything together: Header -> Full Email Body -> AI Summary at the last
            clean_body = html.escape(body_text) if body_text else "<i>(Empty message body)</i>"
            
            message_text = (
                f"{priority_emoji} <b>[{priority}] New Email Received</b>\n"
                f"🏷️ <b>Category:</b> {category}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>From:</b> {sender}\n"
                f"📌 <b>Subject:</b> {subject}\n"
                f"🕒 <b>Date:</b> {date}"
                f"{att_text}\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"📄 <b>Email Content:</b>\n"
                f"{clean_body}\n\n"
                f"{ai_summary_block}"
            )
            return self.send_message(message_text)

        else:
            # If email is very long:
            # Message 1: Full Email Message Content
            clean_body = html.escape(body_text[:3500]) + "\n\n<i>[... Full message truncated to fit Telegram limit ...]</i>"
            msg1 = (
                f"{priority_emoji} <b>[{priority}] New Email Received</b>\n"
                f"🏷️ <b>Category:</b> {category}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>From:</b> {sender}\n"
                f"📌 <b>Subject:</b> {subject}\n"
                f"🕒 <b>Date:</b> {date}"
                f"{att_text}\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"📄 <b>Email Content:</b>\n"
                f"{clean_body}"
            )
            self.send_message(msg1)

            # Message 2: AI Summary at the last
            msg2 = (
                f"📌 <b>Re: {subject}</b>\n"
                f"{ai_summary_block}"
            )
            return self.send_message(msg2)

import argparse
import json
import logging
import sys
import time
from datetime import datetime

from config import CHECK_INTERVAL_SECONDS, MAX_AGE_MINUTES, NOTIFY_ALL_EMAILS, PROCESSED_DB_FILE
from email_fetcher import GmailFetcher
from ai_analyzer import AIAnalyzer
from telegram_notifier import TelegramNotifier

# Force UTF-8 on Windows stdout if possible
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("EmailAIAgent")

def load_processed_ids() -> set[str]:
    """Load previously processed message IDs to prevent duplicate alerts."""
    if PROCESSED_DB_FILE.exists():
        try:
            with open(PROCESSED_DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("processed_ids", []))
        except Exception as e:
            logger.warning(f"Could not load processed IDs file: {e}")
    return set()

def save_processed_ids(ids: set[str]):
    """Save processed message IDs to file."""
    try:
        with open(PROCESSED_DB_FILE, "w", encoding="utf-8") as f:
            json.dump({"processed_ids": list(ids), "last_updated": datetime.now().isoformat()}, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving processed IDs: {e}")

class EmailAIAgent:
    def __init__(self):
        self.telegram = TelegramNotifier()
        self.ai = AIAnalyzer()
        self.fetcher = None
        self.processed_ids = load_processed_ids()

    def init_gmail(self):
        """Initialize Gmail client."""
        if not self.fetcher:
            logger.info("Connecting to Gmail...")
            self.fetcher = GmailFetcher()

    def ignore_existing_emails(self):
        """Mark all existing unread messages as processed so only new future messages are sent."""
        self.init_gmail()
        current_unread_ids = self.fetcher.get_unread_message_ids()
        if current_unread_ids:
            new_ids = current_unread_ids - self.processed_ids
            if new_ids:
                logger.info(f"Marking {len(new_ids)} existing unread emails as seen (ignoring past emails).")
                self.processed_ids.update(new_ids)
                save_processed_ids(self.processed_ids)
            else:
                logger.info("All current unread emails are already recorded.")
        else:
            logger.info("No unread emails currently in inbox.")

    def process_cycle(self, query: str = None, max_results: int = 10):
        """Run one check cycle over inbox, analyze with AI, and forward to Telegram."""
        if query is None:
            query = f"is:unread newer_than:{MAX_AGE_MINUTES}m"

        self.init_gmail()
        emails = self.fetcher.fetch_recent_emails(max_results=max_results, query=query)

        if not emails:
            return

        new_processed = False
        for email_item in reversed(emails):
            msg_id = email_item["id"]
            if msg_id in self.processed_ids:
                continue

            clean_subject = email_item['subject'].encode('ascii', 'replace').decode('ascii')
            clean_sender = email_item['sender'].encode('ascii', 'replace').decode('ascii')
            logger.info(f"Processing fresh email: '{clean_subject}' from {clean_sender}")
            
            # Generate AI summary & analysis
            analysis = self.ai.analyze_email(
                sender=email_item["sender"],
                subject=email_item["subject"],
                body=email_item["body"]
            )
            
            # Send to Telegram
            sent = self.telegram.send_email_with_summary(email_item, analysis)
            if sent:
                logger.info(f"[SUCCESS] Delivered with AI summary: '{clean_subject}'")
                self.fetcher.mark_as_read(msg_id)
            else:
                logger.error(f"[FAILED] Could not deliver: '{clean_subject}'")

            self.processed_ids.add(msg_id)
            new_processed = True
            time.sleep(1)

        if new_processed:
            save_processed_ids(self.processed_ids)

    def test_telegram(self):
        """Send a test message with AI summary card to Telegram."""
        logger.info("Testing Telegram Bot connection...")
        if not self.telegram.test_connection():
            logger.error("Failed to verify Telegram Bot token.")
            return False

        sample_email = {
            "subject": "AI Email Summarizer - Setup Verified",
            "sender": "Antigravity Assistant <bot@local>",
            "date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S"),
            "body": "Your AI Email Assistant is fully active. Every incoming email will now be read, summarized by AI, and delivered straight to this Telegram chat.",
            "attachments": ["summary_report.pdf"]
        }

        test_analysis = {
            "priority": "HIGH",
            "category": "System Alert",
            "summary": [
                "AI Email Summarizer pipeline is fully configured.",
                "Every new email arriving in your inbox will be summarized automatically.",
                "Action items and deadlines will be extracted and highlighted."
            ],
            "action_items": [
                "Your setup is complete and ready for 24/7 cloud operation."
            ]
        }

        sent = self.telegram.send_email_with_summary(sample_email, test_analysis)
        if sent:
            logger.info("Test message sent to Telegram successfully!")
            return True
        else:
            logger.error("Failed to send test message to Telegram.")
            return False

    def run_polling(self, interval_seconds: int = CHECK_INTERVAL_SECONDS, ignore_past: bool = True):
        """Continuous background monitor loop."""
        self.init_gmail()
        if ignore_past:
            self.ignore_existing_emails()

        logger.info(f"AI Email Summarizer Agent ACTIVE (Checking every {interval_seconds}s for NEW emails in last {MAX_AGE_MINUTES}m)...")
        self.telegram.send_message("🤖 <b>AI Email Summarizer is now ACTIVE</b>\nI will summarize all new incoming emails and send them here.")

        default_query = f"is:unread newer_than:{MAX_AGE_MINUTES}m"
        try:
            while True:
                try:
                    self.process_cycle(query=default_query, max_results=10)
                except Exception as e:
                    logger.error(f"Error during check cycle: {e}")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("Agent stopped by user.")
            self.telegram.send_message("⏸️ <b>AI Email Summarizer STOPPED</b>")

def main():
    parser = argparse.ArgumentParser(description="AI Email Summarizer & Telegram Forwarder")
    parser.add_argument("--test-telegram", action="store_true", help="Send a test AI summary to Telegram")
    parser.add_argument("--once", action="store_true", help="Run one check cycle and exit")
    parser.add_argument("--include-past", action="store_true", help="Process existing past unread emails on startup")
    parser.add_argument("--interval", type=int, default=CHECK_INTERVAL_SECONDS, help="Polling interval in seconds")

    args = parser.parse_args()
    agent = EmailAIAgent()

    if args.test_telegram:
        agent.test_telegram()
    elif args.once:
        query = "is:unread" if args.include_past else f"is:unread newer_than:{MAX_AGE_MINUTES}m"
        agent.process_cycle(query=query)
    else:
        agent.run_polling(interval_seconds=args.interval, ignore_past=(not args.include_past))

if __name__ == "__main__":
    main()

import json
import logging
import time
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self, api_key: str = GROQ_API_KEY, model: str = GROQ_MODEL):
        self.api_key = api_key
        self.model = model
        self.client = None
        if self.api_key:
            self.client = Groq(api_key=self.api_key)

    def analyze_email(self, sender: str, subject: str, body: str) -> dict:
        """
        Analyze an incoming email using Groq LLM to generate an executive summary,
        priority level, category, and action items.
        """
        if not self.client:
            logger.warning("Groq API Key is not configured. Using fallback summary.")
            return {
                "priority": "NORMAL",
                "category": "General",
                "summary": [body[:250].strip() + ("..." if len(body) > 250 else "")],
                "action_items": []
            }

        # Truncate body if excessively long to prevent token overflow
        truncated_body = body[:6000]

        system_prompt = """You are an AI email assistant. Summarize the incoming email and extract key insights.
Respond strictly in valid JSON format matching this schema:
{
  "priority": "URGENT" | "HIGH" | "MEDIUM" | "LOW",
  "category": "Work & Business" | "Finance & Bills" | "Security/OTP" | "Education/Career" | "Social/Notifications" | "Marketing/Offers" | "Personal",
  "summary": [
    "Key takeaway point 1",
    "Key takeaway point 2",
    "Key takeaway point 3 (optional)"
  ],
  "action_items": [
    "Any required action, deadline, or next step (if none, leave empty list)"
  ]
}
"""

        user_content = f"""FROM: {sender}
SUBJECT: {subject}

EMAIL BODY:
{truncated_body}
"""

        for attempt in range(2):
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    model=self.model,
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )

                response_text = chat_completion.choices[0].message.content
                result = json.loads(response_text)
                return result
            except Exception as e:
                logger.warning(f"AI analysis attempt {attempt + 1} failed: {e}")
                if "429" in str(e):
                    time.sleep(2)
                else:
                    break

        # Fallback if API fails
        return {
            "priority": "NORMAL",
            "category": "General",
            "summary": [body[:250].strip() + ("..." if len(body) > 250 else "")],
            "action_items": []
        }

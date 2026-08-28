# 🤖 AI Email Summarizer & Telegram Forwarder

An intelligent agent that monitors your Gmail inbox in real-time, reads every new incoming email, generates an **AI Executive Summary** using Groq (`qwen/qwen3.8-27b`), extracts priority, category, and action items, and delivers rich alert cards to your Telegram bot.

---

## ⚡ Features

- 🧠 **AI Executive Summary**: Generates concise takeaway bullet points for every new email.
- ⚡ **Action Items & Deadlines**: Automatically detects required next steps, dates, and deadlines.
- 📩 **Only New Emails**: Automatically ignores past/old emails and processes only new incoming emails.
- 💬 **Rich Telegram Cards**: Formatted with emoji priority badges (`🚨 URGENT`, `🔥 HIGH`, `📌 MEDIUM`, `📩 NORMAL`), category tags, and clean preview.
- 🔄 **Deduplication**: Remembers processed email IDs in `processed_emails.json` to prevent duplicates.
- ⏱️ **Real-time Polling**: Checks your inbox every 15 seconds.

---

## 📁 Project Structure

- [`.env`](file:///d:/Users/prana/Documents/agent/.env) - Environment configuration (Tokens, Keys, Polling interval).
- [`config.py`](file:///d:/Users/prana/Documents/agent/config.py) - Configuration loader and settings.
- [`ai_analyzer.py`](file:///d:/Users/prana/Documents/agent/ai_analyzer.py) - Groq AI summarizer & action item extractor.
- [`email_fetcher.py`](file:///d:/Users/prana/Documents/agent/email_fetcher.py) - Gmail API connector and HTML parser.
- [`telegram_notifier.py`](file:///d:/Users/prana/Documents/agent/telegram_notifier.py) - Telegram Bot notification sender.
- [`main.py`](file:///d:/Users/prana/Documents/agent/main.py) - Main service & polling engine.
- [`requirements.txt`](file:///d:/Users/prana/Documents/agent/requirements.txt) - Python dependencies for cloud deployment.
- [`Dockerfile`](file:///d:/Users/prana/Documents/agent/Dockerfile) & [`Procfile`](file:///d:/Users/prana/Documents/agent/Procfile) - Cloud runner configs for Koyeb.
- [`DEPLOY_TO_KOYEB.md`](file:///d:/Users/prana/Documents/agent/DEPLOY_TO_KOYEB.md) - 24/7 Free cloud deployment instructions.

---

## 🚀 How to Run Locally

Double-click [`start_agent.bat`](file:///d:/Users/prana/Documents/agent/start_agent.bat) or run:

```powershell
python main.py
```

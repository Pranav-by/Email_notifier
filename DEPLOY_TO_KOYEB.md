# 🚀 How to Deploy 24/7 on Koyeb (100% Free)

Follow these simple steps to run your AI Email Summarizer 24/7 in the cloud:

---

### Step 1: Push Code to GitHub
Your repository should contain only the source code (credentials and tokens are excluded by `.gitignore` for your safety):
- `main.py`
- `email_fetcher.py`
- `ai_analyzer.py`
- `telegram_notifier.py`
- `config.py`
- `requirements.txt`
- `Dockerfile`
- `Procfile`

---

### Step 2: Create a Free Account & Connect Service on Koyeb
1. Go to **[app.koyeb.com](https://app.koyeb.com/)** and sign in with GitHub (100% Free).
2. Click **Create Service** → Choose **GitHub**.
3. Select your repository (`Email_notifier`).
4. Under **Type of service**, select **Worker** (or Docker).

---

### Step 3: Add Environment Variables in Koyeb
Under the **Environment Variables** section on Koyeb, add:

1. `TELEGRAM_BOT_TOKEN` = `your_telegram_bot_token`
2. `TELEGRAM_CHAT_ID` = `your_telegram_chat_id`
3. `GROQ_API_KEY` = `your_groq_api_key`
4. `GMAIL_TOKEN_JSON` = `(Paste the single-line JSON string from your local token.json file)`
5. `CHECK_INTERVAL_SECONDS` = `15`

Click **Deploy**! Koyeb will start your bot in the cloud and keep it running 24/7.

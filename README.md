# Daily Standup AI Assistant

Production-ready assistant that reads daily standup CSV data and gives a
Project Lead: blockers, pending work, action-oriented follow-ups, AI
recommendations, a dashboard UI, and email alerts.

## Files

| File | Purpose |
|------|---------|
| `standup_core.py` | Core logic: CSV parsing, blocker detection, follow-up + recommendation generation, rule-based & LLM summaries. Shared by CLI and dashboard. |
| `standup_assistant_v3.py` | Command-line version. |
| `streamlit_app.py` | Web dashboard (Streamlit). |
| `email_notifier.py` | Sends the summary report via email. |
| `standup.csv` | Sample data for testing. |

## Setup

```bash
pip install -r requirements.txt
```

## 1. Run CLI version

```bash
python standup_assistant_v3.py standup.csv
```

Options:
- `--llm` → use OpenAI for the summary instead of rule-based text
- `--email` → send the report by email after printing it

## 2. Run Streamlit Dashboard

```bash
streamlit run streamlit_app.py
```

Opens a browser UI where you can upload a CSV, toggle AI summary, view
blockers/pending/follow-ups/recommendations in tabs, and send an email
straight from the sidebar.

## 3. Enable LLM (OpenAI) Summary

Get an API key from https://platform.openai.com/api-keys, then either:

```bash
export OPENAI_API_KEY="sk-..."
```

or paste it directly into the Streamlit sidebar field (session-only, not stored).

If no key is set, the assistant automatically falls back to a rule-based
summary — it never breaks.

## 4. Enable Email Notifications

Using Gmail:
1. Turn on 2-Step Verification on the Google account.
2. Go to Google Account → Security → App Passwords → generate one for "Mail".
3. Set environment variables:

```bash
export STANDUP_EMAIL_SENDER="youraddress@gmail.com"
export STANDUP_EMAIL_PASSWORD="16_char_app_password"
export STANDUP_EMAIL_RECEIVER="projectlead@example.com"
```

Or enter them directly in the Streamlit sidebar.

## CSV Format Expected

```
Name,Yesterday,Today,Blocker,Status
Ravi,UI design done,API integration,None,In Progress
Priya,DB schema,Testing queries,Need server access approval,Blocked
```

Blocker column accepts: `None`, `NA`, `N/A`, `-`, `--`, `Nil`, or empty —
all correctly treated as "no blocker".

# Gmail Watcher Setup Guide

## Step 1 — Google Cloud Console
1. https://console.cloud.google.com/ kholo
2. New Project banao → naam do (e.g. "AI Employee")
3. Left menu → "APIs & Services" → "Enable APIs"
4. "Gmail API" search karo → Enable karo

## Step 2 — Credentials banao
1. "APIs & Services" → "Credentials"
2. "Create Credentials" → "OAuth 2.0 Client ID"
3. Application type → "Desktop App"
4. Download karo → naam badlo → credentials.json
5. Is file ko project root mein rakho:
   /mnt/d/hackathon 0/credentials.json

## Step 3 — Libraries install karo
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## Step 4 — Pehli baar run karo
```bash
cd "/mnt/d/hackathon 0"
python watchers/gmail_watcher.py
```
- Browser khulega → Gmail account se login karo
- Permission do → token.json ban jaega
- Ab automatic chalega

## Step 5 — Test karo
- Apne Gmail pe koi email bhejo (unread chhoddo)
- 60 seconds mein Needs_Action/ mein EMAIL_xxxx.md file ban jaegi

## Flow
Gmail Inbox (Unread)
      ↓
gmail_watcher.py (har 60 sec)
      ↓
Needs_Action/EMAIL_xxxx.md
      ↓
Claude reads & processes

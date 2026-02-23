# Skill: send-email

Manually trigger email sending for an approved file (bypasses watcher, direct send).

## Instructions

Given a filename in Approved/ (or specify directly):

1. Read the file from AI_Employee_Vault/Approved/{filename}
2. Parse fields:
   - **To:** field → recipient email
   - **Subject:** field → email subject
   - ## Body section → email body text
3. Verify credentials.json exists at project root
4. If credentials.json found:
   - Use Gmail API to send the email
   - Authenticate with token_send.json (create if not exists via OAuth flow)
   - Send via gmail.users.messages.send()
   - Log: "EMAIL SENT: {filename} → {recipient} at {timestamp}"
   - Move file to AI_Employee_Vault/Done/{filename}
   - Print: "✅ Email sent to {recipient}"
5. If no credentials:
   - Print: "[DRY RUN] Would send to: {recipient} | Subject: {subject}"
   - Print email body
   - Move to Done/ with [DRY_RUN] prefix

## Usage
/send-email {filename}
/send-email (sends all files in Approved/)

# Skill: draft-reply

Draft a professional email reply for a task in Needs_Action or Plans.

## Instructions

Given a filename (or run on all files in Needs_Action/):

1. Read the source email from AI_Employee_Vault/Needs_Action/{filename}
2. Understand the context:
   - Who sent it (From field)
   - What they need (Subject + Body)
   - Priority level
3. Write a professional, concise reply that:
   - Acknowledges their message
   - Addresses their specific request
   - Gives a clear next step or answer
   - Is polite and business-appropriate
4. Save the draft to AI_Employee_Vault/Pending_Approval/ with this format:

```markdown
**To:** {original sender email}
**Subject:** Re: {original subject}
**Priority:** {HIGH/MEDIUM/LOW}
**Client:** {sender email}

## Body

Dear {first name or Sir/Madam},

{professional reply body}

Best regards,
AutoOps AI Assistant
```

5. Print: "Draft saved to Pending_Approval/{filename} — awaiting human approval"

## Usage
/draft-reply {filename}
/draft-reply (runs on all Needs_Action files)

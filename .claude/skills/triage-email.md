# Skill: triage-email

Triage and prioritize all emails currently in AI_Employee_Vault/Needs_Action/.

## Instructions

1. Read every .md file in AI_Employee_Vault/Needs_Action/
2. For each file, detect:
   - **Priority**: Check for keywords
     - HIGH: urgent, asap, immediately, critical, invoice, overdue, payment
     - MEDIUM: meeting, schedule, follow-up, proposal, contract
     - LOW: newsletter, fyi, update, general
   - **Client**: Extract "From:" field email address
   - **Action needed**: Summarize in 1 line what needs to be done
3. Create a triage report at AI_Employee_Vault/Plans/triage_report.md with this format:

```
# Email Triage Report
Date: {today}

## High Priority
- [filename] | Client: [email] | Action: [what to do]

## Medium Priority
- [filename] | Client: [email] | Action: [what to do]

## Low Priority
- [filename] | Client: [email] | Action: [what to do]
```

4. Update AI_Employee_Vault/Dashboard.md with triage summary

## Usage
/triage-email

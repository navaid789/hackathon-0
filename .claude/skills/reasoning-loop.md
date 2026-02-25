# Skill: reasoning-loop

Run the Claude AI reasoning loop — reads emails from Needs_Action, creates Plan.md files, and moves drafts to Pending_Approval.

## Instructions

1. Run: `python orchestration/reasoning_loop.py`

2. For each unprocessed file in AI_Employee_Vault/Needs_Action/:
   - Detect priority (HIGH/MEDIUM/LOW) from content keywords
   - Extract client email from **From:** field
   - If ANTHROPIC_API_KEY is set: call Claude API to analyze and generate action plan
   - If no API key: generate rule-based plan based on email type
   - Save Plan.md to AI_Employee_Vault/Plans/plan_{filename}.md
   - Save draft reply to AI_Employee_Vault/Pending_Approval/{filename}

3. Report: how many files processed, plans created, drafts ready

4. Already-processed files are tracked in Logs/reasoning_processed.txt (no duplicates)

## With Claude API (live mode)
Set ANTHROPIC_API_KEY environment variable to enable Claude reasoning:
```
export ANTHROPIC_API_KEY=your_key_here
python orchestration/reasoning_loop.py
```

## Watch mode (continuous)
```
python orchestration/reasoning_loop.py --watch --interval 60
```

## Usage
/reasoning-loop

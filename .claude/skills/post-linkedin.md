# Skill: post-linkedin

Auto-generate and post a professional LinkedIn business update to generate sales leads.

## Instructions

1. Run: `python watchers/linkedin_watcher.py`

2. Selects post type based on day of week (rotates 4 templates):
   - productivity_tip — AI email automation tips
   - case_study — SMB success story
   - industry_insight — 3 AI trends
   - value_prop — cost of slow responses

3. Generates post content:
   - If ANTHROPIC_API_KEY set: Claude generates fresh, unique content
   - If no API key: uses professional fallback templates

4. Posts to LinkedIn:
   - If LINKEDIN_ACCESS_TOKEN set: posts live via LinkedIn API
   - If no token: DRY-RUN (shows post, saves to Logs/linkedin_posts.md)

5. All posts logged to AI_Employee_Vault/Logs/linkedin_posts.md

## Setup for live posting
```
# LinkedIn Developer Portal → Create App → Get token
export LINKEDIN_ACCESS_TOKEN=your_token
export ANTHROPIC_API_KEY=your_claude_key   # optional, for AI-generated content
python watchers/linkedin_watcher.py
```

## Watch mode (daily at 10:00 AM)
```
python watchers/linkedin_watcher.py --watch
```

## Usage
/post-linkedin

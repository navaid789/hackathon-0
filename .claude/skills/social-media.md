# Skill: social-media

Auto-post to Facebook, Instagram, and Twitter/X and get engagement summary.

## Instructions

### Post to all platforms:
```
python watchers/social_media_watcher.py
```

### Post to one platform:
```
python watchers/social_media_watcher.py --platform facebook
python watchers/social_media_watcher.py --platform instagram
python watchers/social_media_watcher.py --platform twitter
```

### Get engagement summary:
```
python watchers/social_media_watcher.py --summary
```

### Watch mode (daily at 11:00 AM):
```
python watchers/social_media_watcher.py --watch
```

## Content Generation
- If ANTHROPIC_API_KEY set: Claude generates fresh unique content per platform
- If no API key: uses professional business templates (4 rotating templates)

## Setup for live posting

**Facebook + Instagram:**
```bash
export FB_PAGE_ACCESS_TOKEN=your_token
export FB_PAGE_ID=your_page_id
export IG_USER_ID=your_instagram_business_id
```

**Twitter/X:**
```bash
export TWITTER_BEARER_TOKEN=your_bearer
export TWITTER_API_KEY=your_key
export TWITTER_API_SECRET=your_secret
export TWITTER_ACCESS_TOKEN=your_access_token
export TWITTER_ACCESS_SECRET=your_access_secret
```

All posts logged to: AI_Employee_Vault/Logs/social_media_posts.md

## Usage
/social-media
/social-media --platform twitter
/social-media --summary

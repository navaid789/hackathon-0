# Skill: weekly-audit

Generate the weekly business & accounting audit with CEO briefing.

## Instructions

Run the weekly audit:
```
python orchestration/weekly_audit.py
```

This generates a comprehensive report including:
1. Email operations summary (processed, approved, rejected, sent)
2. Priority breakdown (HIGH/MEDIUM/LOW across all folders)
3. Accounting summary (live from Odoo if connected, or vault activity estimate)
4. Social media activity (LinkedIn, Facebook, Instagram, Twitter posts)
5. AI system health check (all services, MCP servers, tests)
6. CEO briefing narrative (Claude AI generated or template)
7. Action items for next week

Report saved to: AI_Employee_Vault/Logs/weekly_audit_{date}.md

## Watch mode (auto-run every Monday 08:00):
```
python orchestration/weekly_audit.py --watch
```

## Setup for enhanced reports

**Odoo accounting (live data):**
```bash
export ODOO_URL=http://localhost:8069
export ODOO_DB=odoo
export ODOO_USER=admin
export ODOO_PASSWORD=admin
```

**Claude AI CEO briefing (instead of template):**
```bash
export ANTHROPIC_API_KEY=your_key
```

## Usage
/weekly-audit

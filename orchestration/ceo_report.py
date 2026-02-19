from pathlib import Path
from datetime import datetime

VAULT   = Path("AI_Employee_Vault")
DONE    = VAULT / "Done"
NEEDS   = VAULT / "Needs_Action"
PENDING = VAULT / "Pending_Approval"
LOGS    = VAULT / "Logs"

done    = list(DONE.glob("*.md"))
needs   = list(NEEDS.glob("*.md"))
pending = list(PENDING.glob("*.md"))
today   = datetime.now().strftime("%Y-%m-%d")

report = f"""
=============================
   AI EMPLOYEE — DAILY REPORT
   {today}
=============================

Emails / Tasks Aaye   : {len(needs) + len(done)}
Pending Approval      : {len(pending)}
Completed (Done)      : {len(done)}

Done Tasks:
{chr(10).join(f'  ✓ {f.name}' for f in done) or '  (kuch nahi)'}

Pending Tasks:
{chr(10).join(f'  ⏳ {f.name}' for f in pending) or '  (kuch nahi)'}

=============================
"""

print(report)

# Logs mein save karo
report_file = LOGS / f"ceo_report_{today}.md"
report_file.write_text(report, encoding="utf-8")
print(f"Report saved: {report_file.name}")

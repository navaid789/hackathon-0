from pathlib import Path

VAULT = Path("AI_Employee_Vault")

folders = {
    "Pending": VAULT / "Pending_Approval",
    "Approved": VAULT / "Approved",
    "Done": VAULT / "Done"
}

dashboard = VAULT / "Dashboard.md"

content = "# AI Employee Dashboard\n\n"

for name, folder in folders.items():
    count = len(list(folder.glob("*.md")))
    content += f"## {name}: {count}\n\n"

dashboard.write_text(content)

print("Dashboard updated.")

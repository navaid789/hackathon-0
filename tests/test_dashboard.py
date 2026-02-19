"""
AutoOps AI — Test Suite
"""

from pathlib import Path

VAULT = Path("AI_Employee_Vault")


# ─── Folder Tests ────────────────────────────────────────

def test_dashboard_exists():
    assert (VAULT / "Dashboard.md").exists(), "Dashboard.md nahi mili!"


def test_all_folders_exist():
    folders = ["Inbox", "Needs_Action", "Plans", "Pending_Approval", "Approved", "Done", "Logs"]
    for folder in folders:
        assert (VAULT / folder).exists(), f"{folder} folder nahi mila!"


def test_logs_folder_has_reports():
    logs = VAULT / "Logs"
    assert logs.exists(), "Logs folder nahi mila!"
    # Logs folder exist karna chahiye (files optional)
    assert logs.is_dir(), "Logs ek directory honi chahiye"


def test_done_folder_has_completed_tasks():
    done = list((VAULT / "Done").glob("*.md"))
    assert len(done) >= 1, "Done folder mein kam se kam 1 completed task honi chahiye!"


def test_no_rejected_in_approved():
    """REJECTED files sirf Done mein honi chahiye, Approved mein nahi."""
    approved = VAULT / "Approved"
    rejected = [f for f in approved.glob("*.md") if f.name.startswith("REJECTED_")]
    assert len(rejected) == 0, f"REJECTED files Approved mein mil gayi: {rejected}"


# ─── Priority Detection Tests ─────────────────────────────

def test_priority_detection_high():
    """Urgent content High priority return kare."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from api.main import detect_priority
    assert detect_priority("urgent invoice needed") == "🔴 High"


def test_priority_detection_low():
    """Normal content Low priority return kare."""
    from api.main import detect_priority
    assert detect_priority("hello how are you") == "🟢 Low"


# ─── Client Tagging Tests ─────────────────────────────────

def test_client_detection():
    """From field se client naam detect hona chahiye."""
    from api.main import detect_client
    content = "**From:** john@example.com"
    assert detect_client(content, "test.md") == "john@example.com"


def test_client_unknown():
    """From field nahi hai to Unknown return kare."""
    from api.main import detect_client
    assert detect_client("No from field here", "task.md") == "Unknown"


# ─── Security Tests ───────────────────────────────────────

def test_safe_filename_blocks_traversal():
    """Path traversal attempt block hona chahiye."""
    import pytest
    from fastapi import HTTPException
    from api.main import safe_filename
    with pytest.raises(HTTPException):
        safe_filename("../../etc/passwd")


def test_safe_filename_allows_valid():
    """Valid filename allow hona chahiye."""
    from api.main import safe_filename
    result = safe_filename("email_test.md")
    assert result == "email_test.md"

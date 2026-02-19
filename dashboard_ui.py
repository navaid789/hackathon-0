"""
AI Employee Dashboard UI
------------------------
Browser mein live status dikhata hai.

Run karo:
    cd "/mnt/d/hackathon 0"
    python dashboard_ui.py

Phir browser mein kholo:
    http://localhost:5000
"""

from flask import Flask, jsonify
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

VAULT   = Path("AI_Employee_Vault")
FOLDERS = ["Inbox", "Needs_Action", "Plans", "Pending_Approval", "Approved", "Done", "Logs"]


def get_folder_data():
    data = {}
    for folder in FOLDERS:
        path = VAULT / folder
        files = list(path.glob("*")) if path.exists() else []
        data[folder] = {
            "count": len(files),
            "files": [f.name for f in files]
        }
    return data


@app.route("/")
def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Employee Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', sans-serif;
            background: #0f0f1a;
            color: #e0e0e0;
            min-height: 100vh;
            padding: 30px;
        }

        h1 {
            text-align: center;
            font-size: 2rem;
            color: #00d4ff;
            margin-bottom: 8px;
            letter-spacing: 2px;
        }

        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 30px;
            font-size: 0.9rem;
        }

        .status-bar {
            text-align: center;
            margin-bottom: 30px;
        }

        .status-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #00ff88;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50%       { opacity: 0.3; }
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }

        .card {
            background: #1a1a2e;
            border: 1px solid #2a2a4a;
            border-radius: 12px;
            padding: 20px;
            transition: border-color 0.3s;
        }

        .card:hover { border-color: #00d4ff; }

        .card-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #888;
            margin-bottom: 10px;
        }

        .card-count {
            font-size: 2.5rem;
            font-weight: bold;
            color: #00d4ff;
            margin-bottom: 10px;
        }

        .card-count.has-items { color: #ff6b6b; }
        .card-count.done      { color: #00ff88; }

        .file-list {
            list-style: none;
            font-size: 0.8rem;
            color: #aaa;
        }

        .file-list li {
            padding: 4px 0;
            border-bottom: 1px solid #2a2a4a;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .file-list li:last-child { border-bottom: none; }

        .empty { color: #555; font-style: italic; font-size: 0.8rem; }

        .last-update {
            text-align: center;
            color: #555;
            font-size: 0.8rem;
            margin-top: 30px;
        }

        .flow {
            text-align: center;
            color: #555;
            font-size: 0.85rem;
            margin-bottom: 30px;
            letter-spacing: 1px;
        }

        .flow span { color: #00d4ff; margin: 0 6px; }
    </style>
</head>
<body>
    <h1>AI Employee Dashboard</h1>
    <p class="subtitle">Real-time Vault Status</p>

    <div class="status-bar">
        <span class="status-dot"></span>
        <span style="color:#00ff88">Online</span>
    </div>

    <div class="flow">
        Inbox <span>→</span> Needs_Action <span>→</span> Plans
        <span>→</span> Pending_Approval <span>→</span> Approved <span>→</span> Done
    </div>

    <div class="grid" id="grid">Loading...</div>
    <p class="last-update" id="last-update"></p>

    <script>
        const colors = {
            "Inbox":            "has-items",
            "Needs_Action":     "has-items",
            "Plans":            "has-items",
            "Pending_Approval": "has-items",
            "Approved":         "has-items",
            "Done":             "done",
            "Logs":             "done"
        };

        async function refresh() {
            const res  = await fetch("/api/status");
            const data = await res.json();
            const grid = document.getElementById("grid");

            grid.innerHTML = Object.entries(data).map(([folder, info]) => {
                const cls   = info.count > 0 ? colors[folder] : "";
                const files = info.files.length
                    ? `<ul class="file-list">${info.files.map(f => `<li>📄 ${f}</li>`).join("")}</ul>`
                    : `<p class="empty">Khali hai</p>`;

                return `
                <div class="card">
                    <div class="card-title">${folder.replace("_", " ")}</div>
                    <div class="card-count ${cls}">${info.count}</div>
                    ${files}
                </div>`;
            }).join("");

            document.getElementById("last-update").textContent =
                "Last updated: " + new Date().toLocaleTimeString();
        }

        refresh();
        setInterval(refresh, 5000);  // har 5 second mein refresh
    </script>
</body>
</html>"""


@app.route("/api/status")
def api_status():
    return jsonify(get_folder_data())


if __name__ == "__main__":
    print("Dashboard UI chal raha hai...")
    print("Browser mein kholo: http://localhost:5000")
    app.run(debug=False, port=5000)

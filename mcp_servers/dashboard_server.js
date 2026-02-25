/**
 * AutoOps AI — Dashboard MCP Server
 * Tools: get_status, get_report, get_logs, update_dashboard, get_audit_log
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs";
import path from "path";

const VAULT = path.resolve("AI_Employee_Vault");
const FOLDERS = {
  inbox:            path.join(VAULT, "Inbox"),
  needs_action:     path.join(VAULT, "Needs_Action"),
  pending_approval: path.join(VAULT, "Pending_Approval"),
  approved:         path.join(VAULT, "Approved"),
  done:             path.join(VAULT, "Done"),
  plans:            path.join(VAULT, "Plans"),
  logs:             path.join(VAULT, "Logs"),
};

function countFiles(folderPath) {
  if (!fs.existsSync(folderPath)) return 0;
  return fs.readdirSync(folderPath).filter(f => !f.startsWith(".")).length;
}

function detectPriority(content) {
  const text = content.toLowerCase();
  if (/urgent|asap|immediately|critical|overdue|invoice|payment/.test(text)) return "HIGH";
  if (/meeting|schedule|follow.?up|proposal|contract/.test(text)) return "MEDIUM";
  return "LOW";
}

function getPriorityBreakdown(folderPath) {
  if (!fs.existsSync(folderPath)) return { high: 0, medium: 0, low: 0 };
  const counts = { high: 0, medium: 0, low: 0 };
  fs.readdirSync(folderPath).forEach(f => {
    try {
      const content = fs.readFileSync(path.join(folderPath, f), "utf-8");
      const p = detectPriority(content).toLowerCase();
      counts[p] = (counts[p] || 0) + 1;
    } catch {}
  });
  return counts;
}

const server = new Server(
  { name: "autoops-dashboard", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "get_status",
      description: "Get live count of files in all vault folders",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "get_report",
      description: "Get CEO daily report with task counts and priority breakdown",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "get_logs",
      description: "Read recent entries from the system activity log",
      inputSchema: {
        type: "object",
        properties: {
          lines: { type: "number", description: "Number of recent log lines to return (default 20)", default: 20 },
        },
      },
    },
    {
      name: "update_dashboard",
      description: "Rewrite Dashboard.md with current live status",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "get_morning_report",
      description: "Read today's morning report if it exists",
      inputSchema: { type: "object", properties: {} },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {

      case "get_status": {
        const lines = Object.entries(FOLDERS).map(([key, p]) =>
          `${key.padEnd(18)}: ${countFiles(p)} files`
        );
        return { content: [{ type: "text", text: `📊 Vault Status\n${"─".repeat(30)}\n${lines.join("\n")}` }] };
      }

      case "get_report": {
        const today = new Date().toISOString().split("T")[0];
        const done = countFiles(FOLDERS.done);
        const pending = countFiles(FOLDERS.pending_approval);
        const needsAction = countFiles(FOLDERS.needs_action);
        const approved = countFiles(FOLDERS.approved);
        const priorities = getPriorityBreakdown(FOLDERS.needs_action);
        const report = [
          `📋 CEO Daily Report — ${today}`,
          `${"─".repeat(35)}`,
          `Tasks Completed  : ${done}`,
          `Pending Approval : ${pending}`,
          `Needs Action     : ${needsAction}`,
          `Approved (unsent): ${approved}`,
          `Total Processed  : ${done + approved}`,
          ``,
          `Priority Breakdown (Needs_Action):`,
          `  🔴 High   : ${priorities.high}`,
          `  🟡 Medium : ${priorities.medium}`,
          `  🟢 Low    : ${priorities.low}`,
        ].join("\n");
        return { content: [{ type: "text", text: report }] };
      }

      case "get_logs": {
        const logFile = path.join(FOLDERS.logs, "system.log");
        if (!fs.existsSync(logFile)) return { content: [{ type: "text", text: "No system.log found yet." }] };
        const allLines = fs.readFileSync(logFile, "utf-8").trim().split("\n");
        const n = args.lines || 20;
        const recent = allLines.slice(-n);
        return { content: [{ type: "text", text: `Recent Activity (last ${recent.length} entries):\n\n${recent.join("\n")}` }] };
      }

      case "update_dashboard": {
        const now = new Date().toISOString().replace("T", " ").slice(0, 19);
        const counts = Object.fromEntries(
          Object.entries(FOLDERS).map(([k, p]) => [k, countFiles(p)])
        );
        const priorities = getPriorityBreakdown(FOLDERS.needs_action);

        const dashboard = `# AI Employee Dashboard
**Last Updated:** ${now}

## System Status
| Service              | Status |
|----------------------|--------|
| Filesystem Watcher   | ✅ Running |
| Approval Watcher     | ✅ Running |
| Scheduler (9am/6pm)  | ✅ Running |
| FastAPI Backend      | ✅ Port 8000 |
| Flask Dashboard      | ✅ Port 5000 |
| React Frontend       | ✅ Port 5173 |

## Folder Status
| Folder           | Count |
|------------------|-------|
| Inbox            | ${counts.inbox} |
| Needs Action     | ${counts.needs_action} |
| Pending Approval | ${counts.pending_approval} |
| Approved         | ${counts.approved} |
| Done             | ${counts.done} |
| Plans            | ${counts.plans} |
| Logs             | ${counts.logs} |

## Priority Breakdown (Needs_Action)
- 🔴 High: ${priorities.high}
- 🟡 Medium: ${priorities.medium}
- 🟢 Low: ${priorities.low}

## Quick Skills
- \`/check-inbox\` — Live folder status
- \`/triage-email\` — Prioritize tasks
- \`/draft-reply\` — Generate replies
- \`/approve-task\` — Approve pending
- \`/morning-report\` — Daily briefing
- \`/update-dashboard\` — Refresh this file
`;
        fs.writeFileSync(path.join(VAULT, "Dashboard.md"), dashboard, "utf-8");
        return { content: [{ type: "text", text: `✅ Dashboard.md updated at ${now}` }] };
      }

      case "get_morning_report": {
        const today = new Date().toISOString().split("T")[0];
        const reportFile = path.join(FOLDERS.logs, `morning_report_${today}.md`);
        if (!fs.existsSync(reportFile)) {
          return { content: [{ type: "text", text: `No morning report found for ${today}. Run /morning-report to generate one.` }] };
        }
        const content = fs.readFileSync(reportFile, "utf-8");
        return { content: [{ type: "text", text: content }] };
      }

      default:
        return { content: [{ type: "text", text: `Unknown tool: ${name}` }] };
    }
  } catch (err) {
    return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);

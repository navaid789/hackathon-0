/**
 * AutoOps AI — Vault MCP Server
 * Exposes AI_Employee_Vault folder operations as Claude tools
 * Tools: list_inbox, list_needs_action, list_pending, approve_task, reject_task, read_task, write_plan
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs";
import path from "path";

// Vault root — relative to project root
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

// Safe filename — block path traversal
function safeFilename(filename) {
  if (!filename || filename.includes("..") || filename.includes("/") || filename.includes("\\")) {
    throw new Error("Invalid filename");
  }
  return path.basename(filename);
}

// List files in a folder
function listFolder(folderPath) {
  if (!fs.existsSync(folderPath)) return [];
  return fs.readdirSync(folderPath).filter(f => !f.startsWith("."));
}

// Detect priority from file content
function detectPriority(content) {
  const text = content.toLowerCase();
  if (/urgent|asap|immediately|critical|overdue|invoice|payment/.test(text)) return "HIGH";
  if (/meeting|schedule|follow.?up|proposal|contract/.test(text)) return "MEDIUM";
  return "LOW";
}

// Extract client from From field
function extractClient(content) {
  const match = content.match(/\*\*From:\*\*\s*(.+)/i);
  return match ? match[1].trim() : "Unknown";
}

const server = new Server(
  { name: "autoops-vault", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// ─── Tool Definitions ─────────────────────────────────────────────────────────
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "list_inbox",
      description: "List all files in the Inbox folder (new unprocessed items)",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "list_needs_action",
      description: "List all tasks in Needs_Action with priority and client info",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "list_pending",
      description: "List all items in Pending_Approval awaiting human review",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "read_task",
      description: "Read the content of a task file from any vault folder",
      inputSchema: {
        type: "object",
        properties: {
          filename: { type: "string", description: "Name of the file to read" },
          folder: {
            type: "string",
            description: "Folder name: inbox, needs_action, pending_approval, approved, done, plans, logs",
            default: "needs_action",
          },
        },
        required: ["filename"],
      },
    },
    {
      name: "approve_task",
      description: "Move a file from Pending_Approval to Approved folder",
      inputSchema: {
        type: "object",
        properties: {
          filename: { type: "string", description: "Filename to approve" },
          approved_by: { type: "string", description: "Who is approving", default: "claude" },
        },
        required: ["filename"],
      },
    },
    {
      name: "reject_task",
      description: "Move a file from Pending_Approval to Done with REJECTED_ prefix",
      inputSchema: {
        type: "object",
        properties: {
          filename: { type: "string", description: "Filename to reject" },
          reason: { type: "string", description: "Reason for rejection", default: "Not needed" },
        },
        required: ["filename"],
      },
    },
    {
      name: "write_plan",
      description: "Save a plan or draft to the Plans folder",
      inputSchema: {
        type: "object",
        properties: {
          filename: { type: "string", description: "Plan filename (e.g. triage_plan.md)" },
          content: { type: "string", description: "Plan content in markdown" },
        },
        required: ["filename", "content"],
      },
    },
    {
      name: "get_vault_status",
      description: "Get count of files in all vault folders — full status overview",
      inputSchema: { type: "object", properties: {} },
    },
  ],
}));

// ─── Tool Handlers ────────────────────────────────────────────────────────────
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {

      case "list_inbox": {
        const files = listFolder(FOLDERS.inbox);
        return {
          content: [{
            type: "text",
            text: files.length === 0
              ? "Inbox is empty — no new items."
              : `Inbox (${files.length} items):\n${files.map(f => `• ${f}`).join("\n")}`,
          }],
        };
      }

      case "list_needs_action": {
        const files = listFolder(FOLDERS.needs_action);
        if (files.length === 0) return { content: [{ type: "text", text: "Needs_Action is empty." }] };
        const details = files.map(f => {
          try {
            const content = fs.readFileSync(path.join(FOLDERS.needs_action, f), "utf-8");
            return `• ${f} | Priority: ${detectPriority(content)} | Client: ${extractClient(content)}`;
          } catch {
            return `• ${f} | (unreadable)`;
          }
        });
        return { content: [{ type: "text", text: `Needs_Action (${files.length} items):\n${details.join("\n")}` }] };
      }

      case "list_pending": {
        const files = listFolder(FOLDERS.pending_approval);
        if (files.length === 0) return { content: [{ type: "text", text: "No items pending approval." }] };
        const details = files.map(f => {
          try {
            const content = fs.readFileSync(path.join(FOLDERS.pending_approval, f), "utf-8");
            return `• ${f} | Priority: ${detectPriority(content)} | Client: ${extractClient(content)}`;
          } catch {
            return `• ${f}`;
          }
        });
        return { content: [{ type: "text", text: `Pending Approval (${files.length} items):\n${details.join("\n")}` }] };
      }

      case "read_task": {
        const fname = safeFilename(args.filename);
        const folderKey = (args.folder || "needs_action").toLowerCase().replace(" ", "_");
        const folder = FOLDERS[folderKey] || FOLDERS.needs_action;
        const filePath = path.join(folder, fname);
        if (!fs.existsSync(filePath)) return { content: [{ type: "text", text: `File not found: ${fname}` }] };
        const content = fs.readFileSync(filePath, "utf-8");
        return { content: [{ type: "text", text: `=== ${fname} ===\n\n${content}` }] };
      }

      case "approve_task": {
        const fname = safeFilename(args.filename);
        const src = path.join(FOLDERS.pending_approval, fname);
        const dst = path.join(FOLDERS.approved, fname);
        if (!fs.existsSync(src)) return { content: [{ type: "text", text: `File not found in Pending_Approval: ${fname}` }] };
        fs.renameSync(src, dst);
        const timestamp = new Date().toISOString();
        const logLine = `${timestamp} - APPROVED: ${fname} by ${args.approved_by || "claude"}\n`;
        fs.appendFileSync(path.join(FOLDERS.logs, "system.log"), logLine);
        return { content: [{ type: "text", text: `✅ Approved: ${fname}\nMoved to Approved/\nTimestamp: ${timestamp}` }] };
      }

      case "reject_task": {
        const fname = safeFilename(args.filename);
        const src = path.join(FOLDERS.pending_approval, fname);
        const dst = path.join(FOLDERS.done, `REJECTED_${fname}`);
        if (!fs.existsSync(src)) return { content: [{ type: "text", text: `File not found in Pending_Approval: ${fname}` }] };
        fs.renameSync(src, dst);
        const timestamp = new Date().toISOString();
        const logLine = `${timestamp} - REJECTED: ${fname} | Reason: ${args.reason || "Not needed"}\n`;
        fs.appendFileSync(path.join(FOLDERS.logs, "system.log"), logLine);
        return { content: [{ type: "text", text: `❌ Rejected: ${fname}\nArchived as Done/REJECTED_${fname}\nReason: ${args.reason || "Not needed"}` }] };
      }

      case "write_plan": {
        const fname = safeFilename(args.filename);
        const filePath = path.join(FOLDERS.plans, fname);
        fs.writeFileSync(filePath, args.content, "utf-8");
        return { content: [{ type: "text", text: `✅ Plan saved: Plans/${fname}` }] };
      }

      case "get_vault_status": {
        const status = Object.entries(FOLDERS).map(([key, folderPath]) => {
          const count = listFolder(folderPath).length;
          return `${key.padEnd(18)}: ${count} files`;
        });
        return { content: [{ type: "text", text: `Vault Status:\n${status.join("\n")}` }] };
      }

      default:
        return { content: [{ type: "text", text: `Unknown tool: ${name}` }] };
    }
  } catch (err) {
    return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);

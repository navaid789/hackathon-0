/**
 * AutoOps AI — Gmail MCP Server
 * Tools: check_unread_emails, send_email, get_email_content
 * Falls back to dry-run mode if credentials.json not found
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs";
import path from "path";
import { execSync } from "child_process";

const VAULT       = path.resolve("AI_Employee_Vault");
const NEEDS_ACTION = path.join(VAULT, "Needs_Action");
const LOGS        = path.join(VAULT, "Logs");
const CREDS_FILE  = path.resolve("credentials.json");
const TOKEN_FILE  = path.resolve("token_gmail_mcp.json");
const DRY_RUN     = !fs.existsSync(CREDS_FILE);

function log(msg) {
  const line = `${new Date().toISOString()} - [Gmail MCP] ${msg}\n`;
  try { fs.appendFileSync(path.join(LOGS, "system.log"), line); } catch {}
}

function callPythonGmail(action, args = {}) {
  // Delegate to Python helper for Gmail API calls
  const scriptPath = path.resolve("mcp_servers/gmail_helper.py");
  const argsJson = JSON.stringify({ action, ...args });
  try {
    const result = execSync(`python3 "${scriptPath}" '${argsJson}'`, {
      encoding: "utf-8",
      timeout: 30000,
    });
    return JSON.parse(result.trim());
  } catch (err) {
    return { error: err.message };
  }
}

const server = new Server(
  { name: "autoops-gmail", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "check_unread_emails",
      description: "Check Gmail for unread emails and save them to Needs_Action folder",
      inputSchema: {
        type: "object",
        properties: {
          max_results: { type: "number", description: "Max emails to fetch (default 10)", default: 10 },
        },
      },
    },
    {
      name: "send_email",
      description: "Send an email via Gmail API",
      inputSchema: {
        type: "object",
        properties: {
          to:      { type: "string", description: "Recipient email address" },
          subject: { type: "string", description: "Email subject" },
          body:    { type: "string", description: "Email body text" },
        },
        required: ["to", "subject", "body"],
      },
    },
    {
      name: "get_gmail_status",
      description: "Check if Gmail API credentials are configured and working",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "send_from_approved",
      description: "Send all emails from Approved/ folder via Gmail",
      inputSchema: { type: "object", properties: {} },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {

      case "get_gmail_status": {
        const hasCredentials = fs.existsSync(CREDS_FILE);
        const hasToken       = fs.existsSync(TOKEN_FILE);
        const mode           = hasCredentials ? "LIVE" : "DRY-RUN";
        return {
          content: [{
            type: "text",
            text: [
              `Gmail MCP Status`,
              `─────────────────────────────`,
              `credentials.json : ${hasCredentials ? "✅ Found" : "❌ Missing"}`,
              `token file       : ${hasToken ? "✅ Found" : "⚠️  Not yet (will create on first use)"}`,
              `Mode             : ${mode}`,
              ``,
              hasCredentials
                ? "Gmail API is ready. Use check_unread_emails to fetch emails."
                : "Add credentials.json to project root to enable live Gmail.\nAll operations will simulate in DRY-RUN mode.",
            ].join("\n"),
          }],
        };
      }

      case "check_unread_emails": {
        if (DRY_RUN) {
          // Simulate: create a sample email file
          const simFile = path.join(NEEDS_ACTION, `SIM_EMAIL_${Date.now()}.md`);
          const content = [
            `**From:** demo@client.com`,
            `**Subject:** [SIMULATED] Meeting request for project review`,
            `**Date:** ${new Date().toISOString()}`,
            `**Priority:** MEDIUM`,
            ``,
            `Hi team, can we schedule a project review meeting this week?`,
            `Please let me know your availability.`,
            ``,
            `Best regards,`,
            `Demo Client`,
          ].join("\n");
          fs.writeFileSync(simFile, content, "utf-8");
          log(`DRY-RUN: Simulated email saved to Needs_Action`);
          return {
            content: [{
              type: "text",
              text: `[DRY-RUN MODE] Simulated 1 email → saved to Needs_Action/\n\nTo enable real Gmail:\n1. Download credentials.json from Google Cloud Console\n2. Place in project root: /mnt/d/hackathon 0/credentials.json\n3. Restart this MCP server`,
            }],
          };
        }

        // Live mode — call Python helper
        const result = callPythonGmail("check_unread", { max_results: args.max_results || 10 });
        if (result.error) return { content: [{ type: "text", text: `Gmail error: ${result.error}` }], isError: true };
        log(`Fetched ${result.count} emails from Gmail`);
        return {
          content: [{
            type: "text",
            text: `✅ Fetched ${result.count} emails → saved to Needs_Action/\n\n${(result.files || []).map(f => `• ${f}`).join("\n")}`,
          }],
        };
      }

      case "send_email": {
        const { to, subject, body } = args;
        if (!to || !subject || !body) {
          return { content: [{ type: "text", text: "Missing required fields: to, subject, body" }], isError: true };
        }

        if (DRY_RUN) {
          log(`DRY-RUN: Would send email to ${to} | Subject: ${subject}`);
          return {
            content: [{
              type: "text",
              text: [
                `[DRY-RUN] Email NOT sent (no credentials.json)`,
                ``,
                `Would send:`,
                `  To:      ${to}`,
                `  Subject: ${subject}`,
                `  Body:    ${body.slice(0, 100)}...`,
              ].join("\n"),
            }],
          };
        }

        const result = callPythonGmail("send", { to, subject, body });
        if (result.error) return { content: [{ type: "text", text: `Send failed: ${result.error}` }], isError: true };
        log(`Email sent to ${to} | Subject: ${subject}`);
        return { content: [{ type: "text", text: `✅ Email sent to ${to}\nSubject: ${subject}\nMessage ID: ${result.message_id || "N/A"}` }] };
      }

      case "send_from_approved": {
        const approvedDir = path.join(VAULT, "Approved");
        if (!fs.existsSync(approvedDir)) return { content: [{ type: "text", text: "Approved/ folder not found." }] };
        const files = fs.readdirSync(approvedDir).filter(f => f.endsWith(".md"));
        if (files.length === 0) return { content: [{ type: "text", text: "No approved emails to send." }] };

        const results = [];
        for (const file of files) {
          const content = fs.readFileSync(path.join(approvedDir, file), "utf-8");
          const toMatch = content.match(/\*\*To:\*\*\s*(.+)/i);
          const subjectMatch = content.match(/\*\*Subject:\*\*\s*(.+)/i);
          const bodyMatch = content.match(/## Body\n([\s\S]+)/i);

          const to = toMatch ? toMatch[1].trim() : null;
          const subject = subjectMatch ? subjectMatch[1].trim() : "AutoOps Reply";
          const body = bodyMatch ? bodyMatch[1].trim() : content;

          if (!to) {
            results.push(`⚠️  ${file}: No To field found — skipped`);
            continue;
          }

          if (DRY_RUN) {
            results.push(`[DRY-RUN] ${file} → would send to ${to}`);
            // Move to Done anyway
            fs.renameSync(path.join(approvedDir, file), path.join(VAULT, "Done", file));
          } else {
            const result = callPythonGmail("send", { to, subject, body });
            if (result.error) {
              results.push(`❌ ${file}: ${result.error}`);
            } else {
              results.push(`✅ ${file} → sent to ${to}`);
              fs.renameSync(path.join(approvedDir, file), path.join(VAULT, "Done", file));
              log(`Email sent: ${file} → ${to}`);
            }
          }
        }

        return { content: [{ type: "text", text: `Processed ${files.length} approved emails:\n\n${results.join("\n")}` }] };
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

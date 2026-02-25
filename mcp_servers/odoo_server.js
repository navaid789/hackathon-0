/**
 * AutoOps AI — Odoo MCP Server
 * Integrates with Odoo 19+ Community via JSON-RPC API
 * Tools: create_invoice, list_invoices, get_customer, create_customer,
 *        get_accounting_summary, list_sales_orders, weekly_audit
 *
 * Setup:
 *   ODOO_URL=http://localhost:8069
 *   ODOO_DB=odoo_db
 *   ODOO_USER=admin
 *   ODOO_PASSWORD=admin
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import fetch from "node-fetch";
import fs from "fs";
import path from "path";

const ODOO_URL  = process.env.ODOO_URL      || "http://localhost:8069";
const ODOO_DB   = process.env.ODOO_DB        || "odoo";
const ODOO_USER = process.env.ODOO_USER      || "admin";
const ODOO_PASS = process.env.ODOO_PASSWORD  || "admin";
const DRY_RUN   = process.env.ODOO_URL ? false : true;

const VAULT = path.resolve("AI_Employee_Vault");
const LOGS  = path.join(VAULT, "Logs");

let uid = null; // Odoo session UID

// ─── Odoo JSON-RPC Helper ────────────────────────────────────────────────────
async function odooCall(endpoint, params) {
  const url = `${ODOO_URL}${endpoint}`;
  const payload = {
    jsonrpc: "2.0",
    method: "call",
    id: Date.now(),
    params,
  };
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(10000),
    });
    const data = await res.json();
    if (data.error) throw new Error(JSON.stringify(data.error));
    return data.result;
  } catch (err) {
    throw new Error(`Odoo API error: ${err.message}`);
  }
}

async function authenticate() {
  if (uid) return uid;
  uid = await odooCall("/web/dataset/call_kw", {
    model: "res.users",
    method: "authenticate",
    args: [ODOO_DB, ODOO_USER, ODOO_PASS, {}],
    kwargs: {},
  });
  return uid;
}

async function odooModel(model, method, args = [], kwargs = {}) {
  const sessionUid = await authenticate();
  return odooCall("/web/dataset/call_kw", {
    model,
    method,
    args,
    kwargs: { context: { uid: sessionUid }, ...kwargs },
  });
}

// ─── Dry-Run Simulation ──────────────────────────────────────────────────────
function dryRunResponse(tool, data) {
  return {
    content: [{
      type: "text",
      text: [
        `[DRY-RUN] Odoo not connected — simulating ${tool}`,
        ``,
        `To connect: set environment variables:`,
        `  ODOO_URL=http://localhost:8069`,
        `  ODOO_DB=your_db_name`,
        `  ODOO_USER=admin`,
        `  ODOO_PASSWORD=admin`,
        ``,
        `Simulated result:`,
        JSON.stringify(data, null, 2),
      ].join("\n"),
    }],
  };
}

// ─── Server Setup ────────────────────────────────────────────────────────────
const server = new Server(
  { name: "autoops-odoo", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "get_odoo_status",
      description: "Check Odoo connection status and company info",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "create_invoice",
      description: "Create a customer invoice in Odoo accounting",
      inputSchema: {
        type: "object",
        properties: {
          customer_name: { type: "string", description: "Customer name" },
          amount:        { type: "number", description: "Invoice amount (USD)" },
          description:   { type: "string", description: "Product/service description" },
          due_date:      { type: "string", description: "Due date (YYYY-MM-DD)" },
        },
        required: ["customer_name", "amount", "description"],
      },
    },
    {
      name: "list_invoices",
      description: "List recent invoices from Odoo (paid, unpaid, overdue)",
      inputSchema: {
        type: "object",
        properties: {
          state:  { type: "string", description: "Filter: draft, posted, paid, cancel", default: "posted" },
          limit:  { type: "number", description: "Max results (default 10)", default: 10 },
        },
      },
    },
    {
      name: "get_accounting_summary",
      description: "Get business accounting summary: revenue, expenses, outstanding invoices",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "create_customer",
      description: "Create a new customer record in Odoo CRM",
      inputSchema: {
        type: "object",
        properties: {
          name:  { type: "string", description: "Customer full name or company name" },
          email: { type: "string", description: "Customer email address" },
          phone: { type: "string", description: "Customer phone number" },
        },
        required: ["name", "email"],
      },
    },
    {
      name: "weekly_accounting_audit",
      description: "Generate weekly accounting audit report: invoices, payments, overdue, revenue",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "list_customers",
      description: "List customers from Odoo CRM",
      inputSchema: {
        type: "object",
        properties: {
          limit: { type: "number", description: "Max results", default: 10 },
        },
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {

      case "get_odoo_status": {
        if (DRY_RUN) return dryRunResponse("get_odoo_status", {
          connected: false, url: ODOO_URL, message: "Set ODOO_URL env var to connect",
        });
        const company = await odooModel("res.company", "search_read", [[]], {
          fields: ["name", "email", "phone", "currency_id"], limit: 1,
        });
        return { content: [{ type: "text", text: `✅ Odoo Connected\n\nCompany: ${JSON.stringify(company[0], null, 2)}` }] };
      }

      case "create_invoice": {
        if (DRY_RUN) return dryRunResponse("create_invoice", {
          id: 999, name: "INV/2026/0001",
          customer: args.customer_name, amount: args.amount,
          state: "draft", message: "Would create invoice in Odoo",
        });

        // Find or create partner
        let partners = await odooModel("res.partner", "search_read",
          [[["name", "ilike", args.customer_name]]],
          { fields: ["id", "name"], limit: 1 }
        );
        const partnerId = partners.length ? partners[0].id :
          await odooModel("res.partner", "create", [{ name: args.customer_name }]);

        // Create invoice
        const invoiceId = await odooModel("account.move", "create", [{
          move_type: "out_invoice",
          partner_id: partnerId,
          invoice_date_due: args.due_date || new Date(Date.now() + 30*86400000).toISOString().split("T")[0],
          invoice_line_ids: [[0, 0, {
            name: args.description,
            quantity: 1,
            price_unit: args.amount,
          }]],
        }]);

        return { content: [{ type: "text", text: `✅ Invoice created in Odoo\nID: ${invoiceId}\nCustomer: ${args.customer_name}\nAmount: $${args.amount}` }] };
      }

      case "list_invoices": {
        if (DRY_RUN) return dryRunResponse("list_invoices", {
          invoices: [
            { id: 1, name: "INV/2026/0001", partner: "ACME Corp", amount: 5000, state: "posted", date: "2026-02-20" },
            { id: 2, name: "INV/2026/0002", partner: "Test Client", amount: 2500, state: "paid",   date: "2026-02-15" },
          ],
        });
        const state = args.state || "posted";
        const invoices = await odooModel("account.move", "search_read",
          [[["move_type", "=", "out_invoice"], ["state", "=", state]]],
          { fields: ["name", "partner_id", "amount_total", "state", "invoice_date_due"], limit: args.limit || 10 }
        );
        const lines = invoices.map(i =>
          `• ${i.name} | ${i.partner_id[1]} | $${i.amount_total} | ${i.state} | Due: ${i.invoice_date_due}`
        );
        return { content: [{ type: "text", text: `Invoices (${state}):\n${lines.join("\n") || "None found"}` }] };
      }

      case "get_accounting_summary": {
        if (DRY_RUN) return dryRunResponse("get_accounting_summary", {
          total_revenue: 47500, outstanding: 12000, overdue: 3500,
          paid_this_month: 8000, invoice_count: 15,
        });

        const [posted, paid, overdue] = await Promise.all([
          odooModel("account.move", "search_read",
            [[["move_type","=","out_invoice"],["state","=","posted"]]],
            { fields: ["amount_total"], limit: 100 }),
          odooModel("account.move", "search_read",
            [[["move_type","=","out_invoice"],["state","=","paid"]]],
            { fields: ["amount_total"], limit: 100 }),
          odooModel("account.move", "search_read",
            [[["move_type","=","out_invoice"],["payment_state","=","not_paid"],
              ["invoice_date_due","<", new Date().toISOString().split("T")[0]]]],
            { fields: ["amount_total"], limit: 100 }),
        ]);

        const outstanding = posted.reduce((s, i) => s + i.amount_total, 0);
        const revenue     = paid.reduce((s, i) => s + i.amount_total, 0);
        const overdueAmt  = overdue.reduce((s, i) => s + i.amount_total, 0);

        return { content: [{ type: "text", text: [
          `📊 Accounting Summary`,
          `─────────────────────────────`,
          `Total Revenue (paid)  : $${revenue.toFixed(2)}`,
          `Outstanding           : $${outstanding.toFixed(2)}`,
          `Overdue               : $${overdueAmt.toFixed(2)}`,
          `Open invoices         : ${posted.length}`,
          `Paid invoices         : ${paid.length}`,
        ].join("\n") }] };
      }

      case "create_customer": {
        if (DRY_RUN) return dryRunResponse("create_customer", {
          id: 42, name: args.name, email: args.email, message: "Would create customer in Odoo CRM",
        });
        const id = await odooModel("res.partner", "create", [{
          name: args.name, email: args.email, phone: args.phone || "",
          customer_rank: 1,
        }]);
        return { content: [{ type: "text", text: `✅ Customer created in Odoo CRM\nID: ${id}\nName: ${args.name}\nEmail: ${args.email}` }] };
      }

      case "weekly_accounting_audit": {
        const now  = new Date();
        const week = now.toISOString().split("T")[0];

        if (DRY_RUN) {
          const report = [
            `# Weekly Accounting Audit — ${week}`,
            `Generated: ${now.toISOString()}`,
            `Mode: DRY-RUN (Odoo not connected)`,
            ``,
            `## Revenue Summary`,
            `- Total Invoiced:    $47,500 (simulated)`,
            `- Total Collected:   $35,000 (simulated)`,
            `- Outstanding:       $12,500 (simulated)`,
            `- Overdue (>30d):    $3,500  (simulated)`,
            ``,
            `## Invoice Status`,
            `- Paid:    8 invoices`,
            `- Open:    4 invoices`,
            `- Overdue: 2 invoices — REQUIRES FOLLOW-UP`,
            ``,
            `## Action Items`,
            `1. Follow up on 2 overdue invoices`,
            `2. Send payment reminders for open invoices`,
            `3. Reconcile payments from last week`,
            ``,
            `## CEO Recommendation`,
            `Collection rate is 74% — target is 90%.`,
            `Priority: contact overdue clients this week.`,
            ``,
            `*To enable live data: set ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD*`,
          ].join("\n");

          const reportPath = path.join(LOGS, `weekly_audit_${week}.md`);
          fs.writeFileSync(reportPath, report, "utf-8");
          return { content: [{ type: "text", text: `✅ Weekly audit saved to Logs/weekly_audit_${week}.md\n\n${report}` }] };
        }

        // Live Odoo data
        const summary = await odooModel("account.move", "search_read",
          [[["move_type","=","out_invoice"]]],
          { fields: ["name","partner_id","amount_total","state","payment_state","invoice_date_due"], limit: 200 }
        );
        const paid     = summary.filter(i => i.state === "paid");
        const open     = summary.filter(i => i.state === "posted" && i.payment_state === "not_paid");
        const overdueI = open.filter(i => i.invoice_date_due < week);

        const revenue     = paid.reduce((s,i) => s + i.amount_total, 0);
        const outstanding = open.reduce((s,i) => s + i.amount_total, 0);
        const overdueAmt  = overdueI.reduce((s,i) => s + i.amount_total, 0);

        const report = [
          `# Weekly Accounting Audit — ${week}`,
          ``,
          `## Revenue`,
          `- Collected: $${revenue.toFixed(2)}`,
          `- Outstanding: $${outstanding.toFixed(2)}`,
          `- Overdue: $${overdueAmt.toFixed(2)}`,
          ``,
          `## Overdue Invoices (action needed)`,
          ...overdueI.map(i => `- ${i.name} | ${i.partner_id[1]} | $${i.amount_total} | Due: ${i.invoice_date_due}`),
          ``,
          `## Stats`,
          `- Total invoices: ${summary.length}`,
          `- Paid: ${paid.length} | Open: ${open.length} | Overdue: ${overdueI.length}`,
        ].join("\n");

        const reportPath = path.join(LOGS, `weekly_audit_${week}.md`);
        fs.writeFileSync(reportPath, report, "utf-8");
        return { content: [{ type: "text", text: `✅ Weekly audit saved\n\n${report}` }] };
      }

      case "list_customers": {
        if (DRY_RUN) return dryRunResponse("list_customers", {
          customers: [
            { id: 1, name: "ACME Corp", email: "contact@acme.com" },
            { id: 2, name: "Test Client", email: "test@client.com" },
          ],
        });
        const customers = await odooModel("res.partner", "search_read",
          [[["customer_rank", ">", 0]]],
          { fields: ["name", "email", "phone"], limit: args.limit || 10 }
        );
        const lines = customers.map(c => `• ${c.name} | ${c.email || "no email"} | ${c.phone || "no phone"}`);
        return { content: [{ type: "text", text: `Customers (${customers.length}):\n${lines.join("\n")}` }] };
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

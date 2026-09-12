// mac-mcp.js — zero-dependency MCP server exposing a shell on this Mac.
// Run:  node mac-mcp.js
// Then expose with:  npx -y cloudflared tunnel --url http://localhost:8787
// Connector URL for Claude:  https://<tunnel-host>/mcp/<TOKEN>
const http = require("http");
const { exec } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const PORT = Number(process.env.PORT || 8787);
const TOKEN = process.env.TOKEN || "cb6mac-7f3a91c2e8d54b06";
const MAX_OUT = 60000;
let cwd = os.homedir();

const TOOLS = [
  {
    name: "run_command",
    description: "Run a shell command on the Mac (zsh). Returns stdout, stderr and exit code. Working directory persists between calls.",
    inputSchema: {
      type: "object",
      properties: {
        command: { type: "string", description: "Shell command to run" },
        timeout_seconds: { type: "number", description: "Kill after this many seconds (default 300)" }
      },
      required: ["command"]
    }
  },
  {
    name: "set_cwd",
    description: "Set the working directory used by run_command.",
    inputSchema: { type: "object", properties: { path: { type: "string" } }, required: ["path"] }
  },
  {
    name: "read_file",
    description: "Read a text file on the Mac.",
    inputSchema: { type: "object", properties: { path: { type: "string" } }, required: ["path"] }
  },
  {
    name: "write_file",
    description: "Write a text file on the Mac (creates parent folders).",
    inputSchema: {
      type: "object",
      properties: { path: { type: "string" }, content: { type: "string" } },
      required: ["path", "content"]
    }
  },
  {
    name: "list_dir",
    description: "List a directory on the Mac.",
    inputSchema: { type: "object", properties: { path: { type: "string" } }, required: ["path"] }
  }
];

function expand(p) {
  if (!p) return cwd;
  if (p.startsWith("~")) p = path.join(os.homedir(), p.slice(1));
  return path.resolve(cwd, p);
}

function clip(s) {
  if (s.length <= MAX_OUT) return s;
  return s.slice(0, MAX_OUT) + `\n...[truncated ${s.length - MAX_OUT} chars]`;
}

function runCommand(command, timeoutSeconds) {
  return new Promise((resolve) => {
    const t = Math.max(1, Number(timeoutSeconds) || 300) * 1000;
    exec(command, { cwd, shell: fs.existsSync("/bin/zsh") ? "/bin/zsh" : "/bin/bash", timeout: t, maxBuffer: 50 * 1024 * 1024,
      env: { ...process.env, PATH: process.env.PATH + ":/usr/local/bin:/opt/homebrew/bin" } },
      (err, stdout, stderr) => {
        const code = err ? (err.code === undefined ? 1 : err.code) : 0;
        const killed = err && err.killed ? "\n[killed: timeout]" : "";
        resolve(`exit ${code}${killed}\n--- stdout ---\n${clip(stdout || "")}\n--- stderr ---\n${clip(stderr || "")}`);
      });
  });
}

async function callTool(name, args) {
  args = args || {};
  switch (name) {
    case "run_command":
      return runCommand(args.command, args.timeout_seconds);
    case "set_cwd": {
      const p = expand(args.path);
      if (!fs.existsSync(p) || !fs.statSync(p).isDirectory()) return `not a directory: ${p}`;
      cwd = p;
      return `cwd = ${cwd}`;
    }
    case "read_file":
      return clip(fs.readFileSync(expand(args.path), "utf8"));
    case "write_file": {
      const p = expand(args.path);
      fs.mkdirSync(path.dirname(p), { recursive: true });
      fs.writeFileSync(p, args.content, "utf8");
      return `wrote ${Buffer.byteLength(args.content)} bytes to ${p}`;
    }
    case "list_dir": {
      const p = expand(args.path);
      return fs.readdirSync(p, { withFileTypes: true })
        .map((d) => (d.isDirectory() ? d.name + "/" : d.name)).join("\n") || "(empty)";
    }
    default:
      throw new Error(`unknown tool ${name}`);
  }
}

async function handleRpc(msg) {
  const { id, method, params } = msg;
  const reply = (result) => ({ jsonrpc: "2.0", id, result });
  const error = (code, message) => ({ jsonrpc: "2.0", id, error: { code, message } });
  switch (method) {
    case "initialize":
      return reply({
        protocolVersion: params && params.protocolVersion ? params.protocolVersion : "2025-03-26",
        capabilities: { tools: {} },
        serverInfo: { name: "macincloud-shell", version: "1.0.0" }
      });
    case "ping":
      return reply({});
    case "tools/list":
      return reply({ tools: TOOLS });
    case "tools/call":
      try {
        const text = await callTool(params.name, params.arguments);
        return reply({ content: [{ type: "text", text }], isError: false });
      } catch (e) {
        return reply({ content: [{ type: "text", text: String(e && e.message || e) }], isError: true });
      }
    default:
      if (method && method.startsWith("notifications/")) return null;
      return error(-32601, `method not found: ${method}`);
  }
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://x");
  const okPath = url.pathname === `/mcp/${TOKEN}`;
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Headers", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS");
  if (req.method === "OPTIONS") { res.writeHead(204); return res.end(); }
  if (url.pathname === "/health") { res.writeHead(200); return res.end("ok"); }
  if (!okPath) { res.writeHead(404); return res.end("not found"); }
  if (req.method === "GET") { res.writeHead(405); return res.end(); }
  if (req.method === "DELETE") { res.writeHead(200); return res.end(); }
  if (req.method !== "POST") { res.writeHead(405); return res.end(); }

  let body = "";
  req.on("data", (c) => (body += c));
  req.on("end", async () => {
    let parsed;
    try { parsed = JSON.parse(body); } catch { res.writeHead(400); return res.end("bad json"); }
    const msgs = Array.isArray(parsed) ? parsed : [parsed];
    const out = [];
    for (const m of msgs) { const r = await handleRpc(m); if (r) out.push(r); }
    if (out.length === 0) { res.writeHead(202); return res.end(); }
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(Array.isArray(parsed) ? out : out[0]));
  });
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`MCP shell server listening on http://localhost:${PORT}`);
  console.log(`Path: /mcp/${TOKEN}`);
  console.log(`Next: npx -y cloudflared tunnel --url http://localhost:${PORT}`);
});

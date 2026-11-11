// Local preview that serves ui/ and runs api/market the same way the host does.
// Run from stock-option-opp-finder: node ui/core/dev-server.mjs  (then open http://127.0.0.1:8000/)

import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, normalize, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { GET } from "../api/market.mjs";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const types = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css", ".json": "application/json" };
const port = Number(process.env.PORT || 8000);

createServer(async (req, res) => {
  const url = new URL(req.url, `http://127.0.0.1:${port}`);
  if (url.pathname === "/api/market") {
    const response = await GET(new Request(url));
    res.writeHead(response.status, Object.fromEntries(response.headers));
    res.end(Buffer.from(await response.arrayBuffer()));
    return;
  }
  const path = resolve(root, "." + normalize(url.pathname === "/" ? "/index.html" : url.pathname));
  if (path !== root && !path.startsWith(root + sep)) {
    res.writeHead(403).end();
    return;
  }
  try {
    const body = await readFile(path);
    res.writeHead(200, { "content-type": types[extname(path)] || "application/octet-stream" });
    res.end(body);
  } catch {
    res.writeHead(404).end("not found");
  }
}).listen(port, "127.0.0.1", () => console.log(`http://127.0.0.1:${port}/`));

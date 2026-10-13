// A read-only static server for this folder (headless Chrome reads video and
// image pixels only from one origin; file:// taints the canvas).
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json", ".png": "image/png", ".webm": "video/webm", ".css": "text/css" };
export async function serve(root) {
  const server = http.createServer((req, res) => {
    const url = decodeURIComponent(new URL(req.url, "http://x").pathname);
    const file = path.normalize(path.join(root, url));
    if (!file.startsWith(root + path.sep) && file !== root) { res.writeHead(403); return res.end(); }
    fs.stat(file, (e, st) => {
      if (e || !st.isFile()) { res.writeHead(404); return res.end(); }
      const type = TYPES[path.extname(file)] || "application/octet-stream";
      const range = req.headers.range;
      if (range) {
        const m = /bytes=(\d*)-(\d*)/.exec(range);
        const start = m[1] ? Number(m[1]) : 0, end = m[2] ? Number(m[2]) : st.size - 1;
        res.writeHead(206, { "content-type": type, "content-range": `bytes ${start}-${end}/${st.size}`, "content-length": end - start + 1, "accept-ranges": "bytes", "cache-control": "no-store" });
        return fs.createReadStream(file, { start, end }).pipe(res);
      }
      res.writeHead(200, { "content-type": type, "content-length": st.size, "accept-ranges": "bytes", "cache-control": "no-store" });
      fs.createReadStream(file).pipe(res);
    });
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  return { url: "http://127.0.0.1:" + server.address().port, close: () => new Promise((r) => server.close(r)) };
}

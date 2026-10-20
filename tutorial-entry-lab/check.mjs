// Run: node tutorial-entry-lab/check.mjs   (from Design/WoCG-3)
// Draws tutorial-entry-lab.html in Playwright's Chromium at 1400 wide and writes one picture per section
// into tutorial-entry-lab/check/, plus any page errors.
import { createRequire } from "node:module";
import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const DIR = path.dirname(new URL(import.meta.url).pathname);
const npx = execSync("ls -d ~/.npm/_npx/*/node_modules/playwright 2>/dev/null | head -1", { shell: "/bin/zsh" }).toString().trim();
const { chromium } = createRequire(import.meta.url)(npx);
fs.mkdirSync(path.join(DIR, "check"), { recursive: true });
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1400, height: 1000 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("requestfailed", (r) => errors.push("failed " + r.url()));
  await page.goto("file://" + path.join(DIR, "..", "tutorial-entry-lab.html"));
  await page.waitForTimeout(1500);
  const boxes = await page.evaluate(() => Array.from(document.querySelectorAll("main > h2")).map((h) => {
    const next = h.nextElementSibling, r1 = h.getBoundingClientRect();
    let end = next; while (end.nextElementSibling && end.nextElementSibling.tagName !== "H2") end = end.nextElementSibling;
    const r2 = end.getBoundingClientRect();
    return { name: h.textContent.slice(0, 2).replace(/\W/g, "") || "x", y: r1.top + scrollY, h: r2.bottom - r1.top };
  }));
  let i = 0;
  for (const b of boxes) {
    await page.screenshot({ path: path.join(DIR, "check", `${++i}.png`), clip: { x: 0, y: b.y - 10, width: 1400, height: Math.min(b.h + 20, 4000) }, fullPage: true });
  }
  console.log(JSON.stringify({ sections: boxes.length, errors }));
} finally {
  await browser.close();
}

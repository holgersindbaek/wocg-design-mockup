// Run: node app-play-menu-lab/check.mjs   (from Design/WoCG-3)
// Draws app-play-menu-lab.html in Playwright's Chromium at 1400 wide, writes one full-page picture to
// app-play-menu-lab/check.png and prints the page errors, each variant's panel size (in phone points) and any words
// that run out of their row or panel.
import { createRequire } from "node:module";
import { execSync } from "node:child_process";
import path from "node:path";

const DIR = path.dirname(new URL(import.meta.url).pathname);
const npx = execSync("ls -d ~/.npm/_npx/*/node_modules/playwright 2>/dev/null | head -1", { shell: "/bin/zsh" }).toString().trim();
const { chromium } = createRequire(import.meta.url)(npx);
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1400, height: 1000 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.on("requestfailed", (r) => errors.push("failed " + r.url()));
  page.on("response", (r) => { if (r.status() >= 400) errors.push(r.status() + " " + r.url()); });
  await page.goto("file://" + path.join(DIR, "..", "app-play-menu-lab.html"));
  await page.waitForTimeout(1200);
  const report = await page.evaluate(() => {
    const panels = Array.from(document.querySelectorAll("article")).map((a) => ({
      id: a.id,
      panels: Array.from(a.querySelectorAll(".dd, .psheet")).map((d) => [d.offsetWidth, d.offsetHeight])
    }));
    const overflow = Array.from(document.querySelectorAll(".dd *, .psheet *")).filter((e) => e.scrollWidth > e.clientWidth + 1 && e.clientWidth > 0)
      .map((e) => (e.closest("article") || {}).id + ": " + e.className + " '" + e.textContent.trim().slice(0, 40) + "' " + e.scrollWidth + ">" + e.clientWidth);
    Array.from(document.querySelectorAll(".dd, .psheet")).forEach((d) => {
      if (d.scrollHeight > d.clientHeight + 1) overflow.push((d.closest("article") || {}).id + ": panel cut at the foot " + d.scrollHeight + ">" + d.clientHeight);
    });
    const imgs = Array.from(document.images).filter((i) => !i.naturalWidth).map((i) => i.src);
    return { panels, overflow, brokenImages: imgs, height: document.documentElement.scrollHeight };
  });
  await page.screenshot({ path: path.join(DIR, "check.png"), fullPage: true });
  console.log(JSON.stringify({ errors, ...report }, null, 1));
} finally {
  await browser.close();
}

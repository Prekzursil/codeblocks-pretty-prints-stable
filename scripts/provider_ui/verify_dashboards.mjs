import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { chromium } from "@playwright/test";

function loadTargets() {
  if (process.env.DASHBOARD_TARGETS_JSON) {
    return JSON.parse(process.env.DASHBOARD_TARGETS_JSON);
  }
  const file = process.env.DASHBOARD_TARGETS_FILE;
  if (!file) {
    throw new Error("Set DASHBOARD_TARGETS_JSON or DASHBOARD_TARGETS_FILE before running dashboard verification.");
  }
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function normalizeTargets(raw) {
  if (!Array.isArray(raw) || raw.length === 0) {
    throw new Error("Dashboard target list must be a non-empty array.");
  }
  return raw.map((item) => {
    if (!item || typeof item !== "object") throw new Error("Each dashboard target must be an object.");
    const { name, url, expectedText } = item;
    if (!name || !url) throw new Error("Each dashboard target must contain name and url.");
    return { name, url, expectedText: expectedText ?? null };
  });
}

const outDir = path.resolve(process.cwd(), "build", "provider-ui");
fs.mkdirSync(outDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
const page = await context.newPage();
const targets = normalizeTargets(loadTargets());
const results = [];

for (const target of targets) {
  await page.goto(target.url, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.screenshot({ path: path.join(outDir, `${target.name.replace(/[^a-z0-9_-]+/gi, "-").toLowerCase()}.png`), fullPage: true });
  const text = await page.locator("body").innerText();
  if (target.expectedText && !text.includes(target.expectedText)) {
    throw new Error(`Dashboard ${target.name} did not contain expected text: ${target.expectedText}`);
  }
  results.push({ name: target.name, url: target.url, expectedText: target.expectedText });
}

fs.writeFileSync(path.join(outDir, "dashboard-results.json"), JSON.stringify({ targets: results }, null, 2) + "\n");
await browser.close();


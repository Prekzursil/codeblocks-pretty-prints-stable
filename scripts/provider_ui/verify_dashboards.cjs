const fs = require("node:fs");
const path = require("node:path");
const process = require("node:process");
const { chromium } = require("@playwright/test");

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

  const normalized = [];

  for (const item of raw) {
    if (!item || typeof item !== "object") {
      throw new Error("Each dashboard target must be an object.");
    }
    if (!item.name || !item.url) {
      throw new Error("Each dashboard target must contain name and url.");
    }
    normalized.push({
      name: item.name,
      url: item.url,
      expectedText: item.expectedText || null
    });
  }

  return normalized;
}

function buildScreenshotName(targetName) {
  return targetName.replaceAll(/[^a-z0-9_-]+/gi, "-").toLowerCase() + ".png";
}

async function verifyTargets(page, outDir, targets) {
  const results = [];

  for (const target of targets) {
    await page.goto(target.url, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.screenshot({
      path: path.join(outDir, buildScreenshotName(target.name)),
      fullPage: true
    });
    const text = await page.locator("body").innerText();
    if (target.expectedText && !text.includes(target.expectedText)) {
      throw new Error("Dashboard " + target.name + " did not contain expected text: " + target.expectedText);
    }
    results.push({
      name: target.name,
      url: target.url,
      expectedText: target.expectedText
    });
  }

  return results;
}

async function main() {
  const outDir = path.resolve(process.cwd(), "build", "provider-ui");
  const targets = normalizeTargets(loadTargets());

  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });

  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    const results = await verifyTargets(page, outDir, targets);
    fs.writeFileSync(
      path.join(outDir, "dashboard-results.json"),
      JSON.stringify({ targets: results }, null, 2) + "\n"
    );
  } finally {
    await browser.close();
  }
}

main().catch(function handleFailure(error) {
  console.error(error);
  process.exitCode = 1;
});

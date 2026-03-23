var fs = require("fs");
var path = require("path");
var process = require("process");
var playwright = require("@playwright/test");

function loadTargets() {
  if (process.env.DASHBOARD_TARGETS_JSON) {
    return JSON.parse(process.env.DASHBOARD_TARGETS_JSON);
  }
  var file = process.env.DASHBOARD_TARGETS_FILE;
  if (!file) {
    throw new Error("Set DASHBOARD_TARGETS_JSON or DASHBOARD_TARGETS_FILE before running dashboard verification.");
  }
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function normalizeTargets(raw) {
  var index;
  var item;
  var normalized = [];

  if (!Array.isArray(raw) || raw.length === 0) {
    throw new Error("Dashboard target list must be a non-empty array.");
  }

  for (index = 0; index < raw.length; index += 1) {
    item = raw[index];
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
  return targetName.replace(/[^a-z0-9_-]+/gi, "-").toLowerCase() + ".png";
}

async function verifyTargets(page, outDir, targets) {
  var index;
  var target;
  var text;
  var results = [];

  for (index = 0; index < targets.length; index += 1) {
    target = targets[index];
    await page.goto(target.url, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.screenshot({
      path: path.join(outDir, buildScreenshotName(target.name)),
      fullPage: true
    });
    text = await page.locator("body").innerText();
    if (target.expectedText && text.indexOf(target.expectedText) === -1) {
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
  var outDir = path.resolve(process.cwd(), "build", "provider-ui");
  var browser;
  var context;
  var page;
  var targets = normalizeTargets(loadTargets());
  var results;

  fs.mkdirSync(outDir, { recursive: true });
  browser = await playwright.chromium.launch({ headless: true });

  try {
    context = await browser.newContext();
    page = await context.newPage();
    results = await verifyTargets(page, outDir, targets);
  } finally {
    await browser.close();
  }

  fs.writeFileSync(
    path.join(outDir, "dashboard-results.json"),
    JSON.stringify({ targets: results }, null, 2) + "\n"
  );
}

main().catch(function handleFailure(error) {
  console.error(error);
  process.exitCode = 1;
});

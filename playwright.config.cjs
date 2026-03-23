var playwright = require("@playwright/test");

module.exports = playwright.defineConfig({
  timeout: 60000,
  use: {
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure"
  }
});

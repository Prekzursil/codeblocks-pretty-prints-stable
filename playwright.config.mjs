import { defineConfig } from "@playwright/test";

export default defineConfig({
  timeout: 60_000,
  use: {
    headless: true,
    screenshot: "only-on-failure",
    trace: "retain-on-failure"
  }
});


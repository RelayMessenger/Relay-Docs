#!/usr/bin/env node
// Frame pages hydrate local MDX components. Read the canonical rendered DOM;
// never submit a form, send analytics, or substitute a cache-busted page here.
import { createHash } from "node:crypto";
import puppeteer from "puppeteer";

const url = new URL(process.argv[2]);
if (!["https:", "http:"].includes(url.protocol) || url.search || url.hash) {
  throw new Error("Render an unmodified canonical HTTP(S) page URL");
}
const browser = await puppeteer.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
});
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 1000 });
  const blocked = [];
  const errors = [];
  await page.setRequestInterception(true);
  page.on("request", (request) => {
    if (!["GET", "HEAD"].includes(request.method())) {
      blocked.push({ method: request.method(), url: request.url() });
      void request.abort();
    } else {
      void request.continue();
    }
  });
  page.on("pageerror", (error) => errors.push(String(error)));
  const response = await page.goto(url.href, { waitUntil: "networkidle0", timeout: 60000 });
  await page.evaluate(() => document.fonts.ready);
  if (response?.status() !== 200 || page.url() !== url.href || errors.length) {
    throw new Error(JSON.stringify({
      status: response?.status(), final_url: page.url(), page_errors: errors,
    }));
  }
  const html = await page.content();
  process.stdout.write(JSON.stringify({
    requested_url: url.href, final_url: page.url(), status: response.status(),
    headers: response.headers(), bytes: Buffer.byteLength(html),
    sha256: createHash("sha256").update(html).digest("hex"),
    blocked_non_read_requests: blocked, page_errors: errors, html,
  }));
} finally {
  await browser.close();
}

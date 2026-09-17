// Daytona only. Start the candidate's pinned `mintlify dev --no-open` first:
// node scripts/test-mintlify-posthog-preview.mjs http://127.0.0.1:3000 /path/to/proof.json
//
// The browser sees the candidate's canonical origin so the production host
// guard stays intact. Documents/assets come from the actual Mintlify preview;
// only configured project tokens are substituted with nonfunctional fixtures.
// Every browser response is guarded against other keys before execution.
// This test never injects posthog.js or calls init/capture. Runner-level
// outbound deny is required: interception alone does not prevent egress.
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { gunzipSync } from "node:zlib";
import puppeteer from "puppeteer";
import { createProofFixture, loadOfflineProofSdk } from "./posthog-proof-safety.mjs";

const root = resolve(new URL("..", import.meta.url).pathname);
const preview = new URL(process.argv[2] || "http://127.0.0.1:3000");
assert.ok(["localhost", "127.0.0.1"].includes(preview.hostname), "Use a local Daytona preview, never a deployed site");
const proofPath = process.argv[3];
const source = readFileSync(resolve(root, "posthog.js"), "utf8");
const sha256 = value => createHash("sha256").update(value).digest("hex");
const target = readFileSync(resolve(root, ".docs-target"), "utf8").trim();
const projects = JSON.parse(readFileSync(resolve(root, "scripts/posthog-projects.json")));
const project = projects[target];
const fixture = createProofFixture({ source, projects, target });
const canonical = target === "production" ? "https://docs.relayapp.im" : "https://docs.staging.relayapp.im";
const pagePath = "/start/quickstart";
const sourceTitle = readFileSync(resolve(root, "start/quickstart.mdx"), "utf8").match(/^title: "(.+)"$/m)[1];
const sdkUrl = "https://t.relayapp.im/static/array.js";
const sdk = loadOfflineProofSdk();
// Inspect the first actual preview document before even launching Chromium.
// Served JS and every subsequent HTML/flight response are guarded below too.
const preflight = await fetch(new URL(pagePath, preview));
assert.ok(preflight.ok, `Preview preflight failed: ${preflight.status}`);
fixture.forBrowser(Buffer.from(await preflight.arrayBuffer()), "preview preflight HTML");

const proxyResponses = [];
const interceptedAnalytics = [];
const blockedExternal = new Set();
const pageErrors = [];
const handlerErrors = [];
const postBodies = [];
let sdkRequests = 0;
let proof = { target, configuredProjectId: project.projectId,
  candidateSha256: sha256(source), executableFixtureSha256: sha256(fixture.source),
  tokenSubstitutionOnly: true, nonfunctionalFixtureToken: fixture.token,
  outboundDenyOperatorConfirmed: true, preview: preview.origin };
const browser = await puppeteer.launch({
  headless: true, pipe: true, timeout: 60_000,
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--renderer-process-limit=2"],
});
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 1000 });
  await page.setBypassServiceWorker(true);
  await page.setUserAgent((await browser.userAgent()).replace("HeadlessChrome", "Chrome"));
  // Simulate the human-browser path; retain all application bot/privacy options.
  await page.evaluateOnNewDocument(() => {
    Object.defineProperty(navigator, "webdriver", { get: () => false });
    Object.defineProperty(navigator, "userAgentData", { get: () => undefined });
  });
  page.on("pageerror", error => pageErrors.push(error.message));
  const cdp = await page.createCDPSession();
  await cdp.send("Network.enable", { maxPostDataSize: 4 * 1024 * 1024 });
  cdp.on("Network.requestWillBeSent", ({ request }) => {
    if (request.method === "POST" && new URL(request.url).origin === "https://t.relayapp.im") {
      const entries = request.postDataEntries?.filter(entry => entry.bytes).map(entry => Buffer.from(entry.bytes, "base64"));
      postBodies.push({
        url: request.url,
        body: entries?.length ? Buffer.concat(entries) : Buffer.from(request.postData || ""),
      });
    }
  });
  await page.setRequestInterception(true);
  page.on("request", async request => {
    try {
      const url = new URL(request.url());
      if (url.href === sdkUrl) {
        sdkRequests++;
        // Exact SDK asset bytes, without test observers or configuration edits.
        await fixture.respond(request, {
          status: 200, contentType: "text/javascript",
          headers: { "access-control-allow-origin": "*" }, body: sdk,
        });
      } else if (url.origin === "https://t.relayapp.im") {
        interceptedAnalytics.push({ method: request.method(), path: url.pathname });
        await fixture.respond(request, {
          status: 200, contentType: "application/json",
          headers: { "access-control-allow-origin": "*" }, body: '{"status":1}',
        });
      } else if ([canonical, preview.origin, "http://localhost:3000"].includes(url.origin)
          && ["GET", "HEAD"].includes(request.method())) {
        // Only explicit token substitution; preserve every other source byte.
        const response = await fetch(new URL(url.pathname + url.search, preview), {
          headers: { Accept: request.headers().accept || "*/*" }, redirect: "manual",
        });
        const body = Buffer.from(await response.arrayBuffer());
        const headers = Object.fromEntries(response.headers);
        for (const key of ["content-encoding", "content-length", "transfer-encoding", "connection"]) delete headers[key];
        if (headers.location?.startsWith(preview.origin)) {
          headers.location = headers.location.replace(preview.origin, canonical);
        }
        proxyResponses.push({
          path: url.pathname, status: response.status, bytes: body.length,
          originalSha256: sha256(body),
          executableSha256: sha256(fixture.forBrowser(body, "preview response")),
          isCandidateScript: body.toString("utf8").trim() === source.trim(),
        });
        await fixture.respond(request, { status: response.status, headers, body });
      } else {
        // Includes Mintlify/vendor analytics and unexpected same-origin POSTs.
        blockedExternal.add(url.origin + url.pathname);
        await request.abort();
      }
    } catch (error) {
      handlerErrors.push(error.message);
      if (!request.isInterceptResolutionHandled()) await request.abort();
    }
  });

  // No page.addScriptTag, SDK init, capture, or fixture HTML anywhere in this test.
  await page.goto(`${canonical}${pagePath}?token=preview-secret#preview-content`, {
    waitUntil: "domcontentloaded", timeout: 120_000,
  });
  await page.waitForFunction(() => Boolean(window.posthog?.relayDocs?.__loaded), { timeout: 60_000 });
  await page.waitForSelector("h1", { timeout: 30_000 });
  const heading = await page.$eval("h1", node => node.textContent.trim());
  assert.ok(heading.includes(sourceTitle), `Actual candidate page title missing: ${heading}`);
  for (let attempt = 0; attempt < 60 && !postBodies.length; attempt++) await delay(250);
  assert.ok(postBodies.length, "Auto-loaded client did not send a batch to the intercepted transport");
  await delay(1500); // Catch duplicate initialization/pageviews.

  const events = postBodies.flatMap(({ url, body }) => {
    let bytes = body;
    if (new URL(url).searchParams.get("compression") === "gzip-js" || (bytes[0] === 31 && bytes[1] === 139)) {
      bytes = gunzipSync(bytes);
    }
    const text = bytes.toString("utf8");
    const decoded = text.startsWith("data=")
      ? JSON.parse(Buffer.from(new URLSearchParams(text).get("data"), "base64").toString("utf8"))
      : JSON.parse(text);
    return Array.isArray(decoded) ? decoded : decoded.batch || [decoded];
  });
  assert.equal(events.length, 1, "Exactly one initial pageview must be emitted");
  const event = events[0];
  assert.equal(event.event, "$pageview");
  assert.equal(event.properties.token, fixture.token);
  assert.equal(event.properties.environment, target);
  assert.equal(event.properties.$current_url, canonical + pagePath);
  assert.equal(event.properties.$pathname, pagePath);
  assert.equal(event.properties.analytics_source, "relay_docs");
  assert.equal(event.properties.docs_analytics_schema_version, 1);
  assert.ok(!JSON.stringify(event).includes("preview-secret"));
  assert.ok(!JSON.stringify(event).includes("preview-content"));
  assert.equal(sdkRequests, 1, "The root integration must load the SDK only once");
  const inlineScripts = await page.$$eval("script:not([src])", scripts => scripts.map(script => ({
    id: script.id, text: script.textContent,
  })));
  const matchingInline = inlineScripts.filter(script => script.text.trim() === fixture.source.trim());
  const matchingFetches = proxyResponses.filter(response => response.isCandidateScript);
  assert.equal(matchingInline.length + matchingFetches.length, 1,
    "Mintlify must deliver the candidate once with only explicit fixture-token substitution");
  assert.deepEqual(handlerErrors, []);
  assert.deepEqual(pageErrors, []);
  proof = {
    ...proof, passed: true, heading,
    sourceDelivery: matchingFetches.length ? "automatic asset fetch" : "Mintlify inline script",
    scriptIds: matchingInline.map(script => script.id),
    scriptFetches: matchingFetches,
    previewResponses: proxyResponses,
    sdkSha256: sha256(sdk), sdkVersion: event.properties.$lib_version,
    sdkRequests, eventCount: events.length,
    event,
    interceptedAnalytics, blockedExternal: [...blockedExternal],
    noApplicationScriptInjection: true, requestInterceptionConfigured: true,
  };
  if (proofPath) {
    await page.screenshot({ path: proofPath.replace(/\.json$/, "-desktop.png"), fullPage: false });
    await page.setViewport({ width: 390, height: 844 });
    await page.screenshot({ path: proofPath.replace(/\.json$/, "-mobile.png"), fullPage: false });
  }
  console.log(JSON.stringify({
    passed: true, target, configuredProjectId: project.projectId, candidateSha256: proof.candidateSha256,
    executableFixtureSha256: proof.executableFixtureSha256, tokenSubstitutionOnly: true,
    nonfunctionalFixtureToken: fixture.token,
    sourceDelivery: proof.sourceDelivery, scriptIds: proof.scriptIds,
    scriptFetches: proof.scriptFetches, eventCount: events.length,
    requestInterceptionConfigured: true, outboundDenyOperatorConfirmed: true,
  }, null, 2));
} catch (error) {
  proof = { ...proof, passed: false, error: error.message, proxyResponses, pageErrors, handlerErrors,
    sdkRequests, postBodyCount: postBodies.length, interceptedAnalytics, blockedExternal: [...blockedExternal] };
  throw error;
} finally {
  if (proofPath) writeFileSync(proofPath, JSON.stringify(proof, null, 2) + "\n");
  await browser.close();
}

// Run in Daytona: npm run check:posthog-browser
// Uses the real proxied SDK, but intercepts every browser request. No synthetic
// events, flags, recordings, or playground data reach any analytics project.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import puppeteer from "puppeteer";

const root = resolve(process.argv[2] || new URL("..", import.meta.url).pathname);
const source = readFileSync(resolve(root, "posthog.js"), "utf8");
const target = readFileSync(resolve(root, ".docs-target"), "utf8").trim();
const token = JSON.parse(readFileSync(resolve(root, "scripts/posthog-projects.json")))[target].token;
const origin = target === "production" ? "https://docs.relayapp.im" : "https://docs.staging.relayapp.im";
const response = await fetch("https://t.relayapp.im/static/array.js", { headers: { Origin: origin } });
assert.ok(response.ok, `SDK download failed: ${response.status}`);
assert.ok(["*", origin].includes(response.headers.get("access-control-allow-origin")),
  "proxied SDK must permit the docs origin");
const sdk = await response.text();
// Attach an observer before the SDK emits its initial pageview. This does not
// change collection options or the before_send filter.
const observer = `
(() => {
  const init = window.posthog.init;
  window.posthog.init = function(token, options, name) {
    const loaded = options.loaded;
    return init.call(this, token, {
      ...options,
      loaded(instance) {
        window.__events = [];
        instance.on("eventCaptured", event => window.__events.push(event));
        if (loaded) loaded(instance);
      }
    }, name);
  };
})();`;

const browser = await puppeteer.launch({ headless: true, args: ["--no-sandbox"] });
let diagnosticPage;
const requests = [];
const errors = [];
try {
  const page = await browser.newPage();
  diagnosticPage = page;
  // Exercise the human-browser path without disabling production bot filters.
  // PostHog checks UA, UA client hints, and webdriver:
  // packages/browser-common/src/utils/blocked-uas.ts in PostHog/posthog-js.
  await page.setUserAgent((await browser.userAgent()).replace("HeadlessChrome", "Chrome"));
  await page.evaluateOnNewDocument(() => {
    Object.defineProperty(navigator, "webdriver", { get: () => false });
    Object.defineProperty(navigator, "userAgentData", { get: () => undefined });
  });
  page.on("pageerror", error => errors.push(error.message));
  await page.setRequestInterception(true);
  page.on("request", async request => {
    const url = new URL(request.url());
    if (request.isNavigationRequest()) {
      await request.respond({
        status: 200, contentType: "text/html",
        body: '<!doctype html><title>Private page title</title><input id="token"><textarea id="message"></textarea><button>Send private content</button>',
      });
    } else if (url.href === "https://t.relayapp.im/static/array.js") {
      requests.push({ url: url.href, method: request.method() });
      await request.respond({
        status: 200, contentType: "text/javascript",
        headers: { "access-control-allow-origin": response.headers.get("access-control-allow-origin") },
        body: sdk + observer,
      });
    } else if (url.origin === "https://t.relayapp.im") {
      requests.push({ url: url.href, method: request.method() });
      await request.respond({
        status: 200, contentType: "application/json",
        headers: { "access-control-allow-origin": "*" },
        body: JSON.stringify({ status: 1, featureFlags: {}, sessionRecording: false }),
      });
    } else {
      await request.abort();
    }
  });
  await page.goto(`${origin}/messages/send?token=credential-sentinel#message-sentinel`);
  await page.addScriptTag({ content: source });
  await page.waitForFunction(() => window.__events?.length === 1);
  const sharedIdentity = await page.evaluate(() => {
    const client = window.posthog.relayDocs;
    return {
      version: window.__events[0].properties.$lib_version,
      persistence: client.config.persistence,
      cross_subdomain_cookie: client.config.cross_subdomain_cookie,
      cookieWinsOnConflict: client.config.cookieWinsOnConflict,
      persistence_name: client.config.persistence_name,
    };
  });
  const [major, minor] = sharedIdentity.version.split(".").map(Number);
  assert.ok(major > 1 || (major === 1 && minor >= 418),
    `SDK ${sharedIdentity.version} does not support the shared-cookie contract`);
  assert.deepEqual({ ...sharedIdentity, version: undefined }, {
    version: undefined, persistence: "localStorage+cookie", cross_subdomain_cookie: true,
    cookieWinsOnConflict: true, persistence_name: "",
  });
  await page.addScriptTag({ content: source });
  await page.type("#token", "credential-sentinel");
  await page.type("#message", "message-sentinel");
  await page.click("button");
  await page.evaluate(() => {
    window.posthog.relayDocs.capture("api_request", {
      authorization: "credential-sentinel", message: "message-sentinel",
    });
    history.pushState({}, "", "/start/quickstart?api_key=credential-sentinel#message-sentinel");
  });
  await page.waitForFunction(() => window.__events?.length === 2);
  await page.evaluate(() => history.replaceState({}, "", "/start/quickstart?other=credential-sentinel"));
  await delay(300);
  assert.equal(await page.evaluate(() => window.__events.length), 2, "query-only navigation is not a pageview");
  await page.evaluate(() => history.back());
  await page.waitForFunction(() => window.__events?.length === 3);
  await page.evaluate(() => history.pushState({}, "", "/credential-sentinel"));
  await delay(300);
  const events = await page.evaluate(() => window.__events);
  assert.equal(events.length, 3, "unknown paths are dropped");
  assert.deepEqual(events.map(event => event.properties.$pathname), [
    "/messages/send", "/start/quickstart", "/messages/send",
  ]);
  for (const event of events) {
    assert.equal(event.event, "$pageview");
    assert.equal(event.properties.token, token);
    assert.equal(event.properties.app, "relay-docs");
    assert.equal(event.properties.analytics_source, "relay_docs");
    assert.equal(event.properties.environment, target);
    assert.ok(event.properties.distinct_id);
    assert.ok(event.properties.$session_id);
    assert.equal(event.properties.$process_person_profile, false);
    assert.equal(event.properties.$current_url, origin + event.properties.$pathname);
    for (const sentinel of ["credential-sentinel", "message-sentinel", "Private page title"]) {
      assert.ok(!JSON.stringify(event).includes(sentinel), sentinel);
    }
  }
  await delay(3500); // Allow the real SDK's batch timer to reach the intercepted transport.
  assert.ok(requests.some(request => request.method === "POST"), "SDK delivered a batch to the mocked proxy");
  assert.equal(requests.filter(request => request.url.endsWith("/static/array.js")).length, 1);
  assert.ok(!requests.some(request => /recorder|surveys|web-vitals|\/flags\/|\/s\//.test(request.url)));
  await page.evaluate(() => {
    window.posthog.relayDocs.opt_out_capturing();
    history.pushState({}, "", "/messages/send");
  });
  await delay(300);
  assert.equal(await page.evaluate(() => window.__events.length), 3, "opt-out suppresses pageviews");
  assert.deepEqual(errors, []);
  console.log(`${target}: SDK ${events[0].properties.$lib_version} emitted 3 filtered pageviews (initial, SPA, back); one init; opt-out honored; no content, replay or extra events; all browser network intercepted`);
} catch (error) {
  console.error({
    errors,
    requests: requests.map(request => ({ ...request, url: request.url.replace(token, "[public-token]") })),
    state: await diagnosticPage?.evaluate(() => ({
      initialized: window.__relayDocsPostHog,
      sdk: typeof window.posthog,
      client: typeof window.posthog?.relayDocs,
      events: window.__events?.length,
      version: window.posthog?.relayDocs?.version,
      optedOut: window.posthog?.relayDocs?.has_opted_out_capturing(),
    })),
  });
  throw error;
} finally {
  await browser.close();
}

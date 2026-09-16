import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import { test } from "node:test";

const source = readFileSync(new URL("../posthog.js", import.meta.url), "utf8");
const projects = JSON.parse(readFileSync(new URL("./posthog-projects.json", import.meta.url)));
const target = readFileSync(new URL("../.docs-target", import.meta.url), "utf8").trim();
const origin = target === "production" ? "https://docs.relayapp.im" : "https://docs.staging.relayapp.im";

function client({ url = origin, dnt, existing = false, load = true } = {}) {
  const calls = [];
  const scripts = [];
  const sdk = { init: (...args) => calls.push(args) };
  const window = { location: new URL(url), ...(existing ? { posthog: sdk } : {}) };
  const context = {
    window, URL, navigator: { doNotTrack: dnt },
    document: {
      createElement: () => ({}),
      head: { appendChild: (script) => scripts.push(script) },
    },
  };
  const run = () => runInNewContext(source, context);
  run();
  if (scripts.length && load) {
    window.posthog = sdk;
    scripts[0].onload();
  }
  return { calls, scripts, window, run };
}

test("loads one proxied SDK and initializes a named, environment-specific client", () => {
  const { calls, scripts, run } = client();
  run();
  assert.equal(scripts.length, 1);
  assert.equal(scripts[0].src, "https://t.relayapp.im/static/array.js");
  assert.equal(scripts[0].referrerPolicy, "no-referrer");
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], projects[target].token);
  assert.equal(calls[0][2], "relayDocs");
});

test("reuses a loaded SDK without replacing its primary client", () => {
  const { calls, scripts } = client({ existing: true });
  assert.equal(scripts.length, 0);
  assert.equal(calls.length, 1);
  assert.equal(calls[0][2], "relayDocs");
});

test("an SDK load failure allows a later retry without initializing", () => {
  const { calls, scripts, run, window } = client({ load: false });
  scripts[0].onerror();
  assert.equal(window.__relayDocsPostHog, false);
  run();
  assert.equal(scripts.length, 2);
  assert.equal(calls.length, 0);
});

test("disabled on localhost, preview, wrong environment, and lookalike hosts", () => {
  for (const url of [
    "http://localhost:3000", "https://relay-staging.mintlify.app",
    "https://relay.mintlify.app", `${origin}.example.com`,
    target === "production" ? "https://docs.staging.relayapp.im" : "https://docs.relayapp.im",
  ]) {
    const result = client({ url });
    assert.equal(result.scripts.length, 0, url);
    assert.equal(result.calls.length, 0, url);
  }
});

test("DNT avoids loading the SDK", () => {
  const result = client({ dnt: "1" });
  assert.equal(result.scripts.length, 0);
  assert.equal(result.calls.length, 0);
});

test("privacy options cannot enable replay, autocapture, flags, surveys, or profiles", () => {
  const config = client().calls[0][1];
  assert.equal(config.api_host, "https://t.relayapp.im");
  assert.equal(config.ui_host, "https://us.posthog.com");
  assert.equal(config.capture_pageview, "history_change");
  assert.equal(config.person_profiles, "never");
  for (const key of [
    "autocapture", "capture_pageleave", "capture_dead_clicks", "rageclick",
    "capture_heatmaps", "capture_performance", "capture_exceptions", "cross_subdomain_cookie",
  ]) assert.equal(config[key], false, key);
  for (const key of [
    "disable_session_recording", "disable_surveys", "advanced_disable_flags", "respect_dnt",
  ]) assert.equal(config[key], true, key);
});

test("only pageview events are allowed", () => {
  const filter = client().calls[0][1].before_send;
  for (const event of [
    "$autocapture", "$snapshot", "$identify", "$set", "$pageleave",
    "$exception", "api_request", "message_sent", "search",
  ]) assert.equal(filter({ event, properties: {} }), null, event);
  assert.equal(filter(null), null);
});

test("pageviews strip sensitive data including URL parameters and nested properties", () => {
  const filter = client().calls[0][1].before_send;
  const event = filter({
    event: "$pageview",
    timestamp: "2026-09-16T00:00:00Z",
    uuid: "event-id",
    credentials: "top-level-secret",
    properties: {
      token: "untrusted-token",
      distinct_id: "anonymous-id",
      $device_id: "device-id",
      $session_id: "session-id",
      $window_id: "window-id",
      $current_url: `${origin}/messages/send/?token=secret#message-content`,
      $referrer: "https://example.com/private?token=secret",
      $initial_current_url: `${origin}/?secret`,
      $set: { $initial_current_url: `${origin}/?secret`, email: "private@example.com" },
      $set_once: { $initial_referrer: "https://example.com/private" },
      $browser: "Chrome", $browser_version: 130, $process_person_profile: false,
      $pathname: "/private", $host: "attacker.invalid", $title: "message-content",
      utm_campaign: "private", message: "message-content", attachment: { url: "private" },
      authorization: "Bearer secret", $elements: ["private"], environment: "wrong",
    },
  });
  assert.equal(event.event, "$pageview");
  assert.equal(event.properties.$current_url, `${origin}/messages/send`);
  assert.equal(event.properties.$pathname, "/messages/send");
  assert.equal(event.properties.environment, target);
  assert.equal(event.properties.app, "relay-docs");
  assert.equal(event.properties.token, projects[target].token);
  assert.equal(event.properties.distinct_id, "anonymous-id");
  assert.equal(event.properties.$session_id, "session-id");
  assert.equal(event.properties.$browser, "Chrome");
  assert.equal(event.properties.$process_person_profile, false);
  const serialized = JSON.stringify(event);
  for (const value of ["secret", "message-content", "private", "attacker.invalid", "untrusted-token"]) {
    assert.ok(!serialized.includes(value), value);
  }
});

test("unknown paths, external origins, invalid and missing URLs are dropped", () => {
  const filter = client().calls[0][1].before_send;
  for (const url of [
    `${origin}/some-secret-token`, "https://example.com/messages/send", "invalid", undefined,
  ]) assert.equal(filter({ event: "$pageview", properties: { $current_url: url } }), null);
  assert.equal(filter({ event: "$pageview" }), null);
  assert.equal(filter({ event: "$pageview", properties: null }), null);
});

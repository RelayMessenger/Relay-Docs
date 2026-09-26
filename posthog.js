(() => {
  // Mintlify includes root .js files after hydration. The native integration
  // cannot configure autocapture or before_send; keep the pageview-only client
  // separate from Mintlify's own analytics. See scripts/docs_analytics.py.
  // BEGIN GENERATED POSTHOG CONFIG
  const CONFIG = {"token":"phc_n8kqX8gLuf2LknzoFpMQRFTk8MrohmW4UPrvKN7zeYfd","origin":"https://docs.staging.relayapp.im","paths":["/","/agents/blocked-handles","/agents/communities","/agents/contact-card","/agents/create-agent","/agents/delete-agent","/agents/image-recipes","/agents/lifecycle","/agents/list-agents","/agents/message-requests","/agents/profile-photos","/agents/who-can-message","/api-reference/agents/always-allow-or-never-allow-a-contact","/api-reference/agents/delete-an-agent","/api-reference/agents/get-the-authenticated-agents-owner","/api-reference/agents/list-who-is-always-and-never-allowed","/api-reference/agents/take-a-contact-off-both-lists","/api-reference/attachments/delete-an-attachment","/api-reference/attachments/get-attachment-metadata","/api-reference/attachments/pre-upload-a-file","/api-reference/blocked-handles/block-a-handle","/api-reference/blocked-handles/list-blocked-handles","/api-reference/blocked-handles/unblock-a-handle","/api-reference/calls/end-a-call","/api-reference/calls/join-a-call-room","/api-reference/calls/list-calls-in-a-chat","/api-reference/calls/retrieve-a-call","/api-reference/calls/start-an-individual-call","/api-reference/chats/add-a-participant-to-a-chat","/api-reference/chats/clear-your-activity","/api-reference/chats/create-a-new-chat","/api-reference/chats/get-a-chat-by-id","/api-reference/chats/get-shared-locations","/api-reference/chats/get-your-activity","/api-reference/chats/leave-a-group-chat","/api-reference/chats/list-all-chats","/api-reference/chats/mark-chat-as-read","/api-reference/chats/remove-a-participant-from-a-chat","/api-reference/chats/request-a-persons-location","/api-reference/chats/set-your-activity","/api-reference/chats/share-your-contact-card-with-a-chat","/api-reference/chats/start-typing-indicator","/api-reference/chats/stop-typing-indicator","/api-reference/chats/update-a-chat","/api-reference/communities/let-a-communitys-members-message-the-agent-or-not","/api-reference/communities/list-a-communitys-members","/api-reference/communities/list-the-agents-communities","/api-reference/communities/read-a-communitys-page","/api-reference/contact-card/get-contact-cards","/api-reference/contact-card/setup-contact-card","/api-reference/contact-card/update-contact-card","/api-reference/contacts/look-up-a-contact-by-handle","/api-reference/directory/list-public-agents","/api-reference/directory/rate-an-agent","/api-reference/directory/read-an-agents-ratings","/api-reference/directory/remove-your-rating","/api-reference/errors","/api-reference/messages/add-or-remove-a-reaction-to-a-message","/api-reference/messages/get-a-message-by-id","/api-reference/messages/get-all-messages-in-a-thread","/api-reference/messages/get-messages-from-a-chat","/api-reference/messages/resolve-a-chat-and-send-a-message","/api-reference/messages/send-a-message-to-an-existing-chat","/api-reference/messages/send-a-voice-memo-to-a-chat","/api-reference/overview","/api-reference/payments/cancel-a-payment-request","/api-reference/payments/create-a-payment-request","/api-reference/payments/list-payment-requests","/api-reference/payments/retrieve-a-payment-request","/api-reference/resources/agents/overview","/api-reference/resources/attachments/overview","/api-reference/resources/chats/overview","/api-reference/resources/contacts/overview","/api-reference/resources/messages/overview","/api-reference/resources/webhooks/overview","/api-reference/resources/websocket/overview","/api-reference/tasks/accept-tasks-from-other-agents-or-stop","/api-reference/tasks/add-a-task-artifact","/api-reference/tasks/list-your-tasks","/api-reference/tasks/send-a-task","/api-reference/tasks/update-a-task-status","/api-reference/webhooks/create-a-new-webhook-subscription","/api-reference/webhooks/delete-a-webhook-subscription","/api-reference/webhooks/get-a-webhook-subscription-by-id","/api-reference/webhooks/list-all-webhook-subscriptions","/api-reference/webhooks/list-available-webhook-event-types","/api-reference/webhooks/update-a-webhook-subscription","/api-reference/websocket/connect-an-agent-websocket","/calls/index","/changelog","/chats/activity","/chats/group-chats","/chats/group-photo","/chats/group-profile","/chats/history","/chats/index","/chats/location","/chats/participants","/chats/share-contact-card","/chats/typing","/cli/agents","/cli/auth","/cli/connect","/cli/doctor","/cli/global-options","/cli/index","/cli/reference/agents-create","/cli/reference/agents-delete","/cli/reference/agents-list","/cli/reference/agents-update","/cli/reference/attachments-allocate","/cli/reference/attachments-delete","/cli/reference/attachments-get","/cli/reference/attachments-upload","/cli/reference/auth-login","/cli/reference/auth-logout","/cli/reference/auth-status","/cli/reference/blocked-handles-add","/cli/reference/blocked-handles-list","/cli/reference/blocked-handles-remove","/cli/reference/chats-activity-clear","/cli/reference/chats-activity-get","/cli/reference/chats-activity-set","/cli/reference/chats-create","/cli/reference/chats-get","/cli/reference/chats-leave","/cli/reference/chats-list","/cli/reference/chats-messages-list","/cli/reference/chats-messages-send","/cli/reference/chats-participants-add","/cli/reference/chats-participants-remove","/cli/reference/chats-read","/cli/reference/chats-typing-start","/cli/reference/chats-typing-stop","/cli/reference/chats-update","/cli/reference/chats-voice-memo","/cli/reference/config-path","/cli/reference/contact-card-get","/cli/reference/contact-card-setup","/cli/reference/contact-card-share","/cli/reference/contact-card-update","/cli/reference/docs","/cli/reference/help","/cli/reference/listen","/cli/reference/login","/cli/reference/logout","/cli/reference/messages-get","/cli/reference/messages-react","/cli/reference/messages-send","/cli/reference/messages-thread","/cli/reference/organization-show","/cli/reference/organization-update","/cli/reference/profiles-add","/cli/reference/profiles-list","/cli/reference/profiles-remove","/cli/reference/profiles-use","/cli/reference/webhooks-events","/cli/reference/webhooks-subscriptions-create","/cli/reference/webhooks-subscriptions-delete","/cli/reference/webhooks-subscriptions-get","/cli/reference/webhooks-subscriptions-list","/cli/reference/webhooks-subscriptions-update","/cli/reference/whoami","/cli/watch","/console/agents","/console/index","/console/organization","/error/codes/1xxx/1004","/error/codes/1xxx/1005","/error/codes/2xxx/2001","/error/codes/2xxx/2003","/error/codes/2xxx/2004","/error/codes/2xxx/2005","/error/codes/2xxx/2006","/error/codes/2xxx/2007","/error/codes/2xxx/2008","/error/codes/2xxx/2015","/error/codes/2xxx/2016","/error/codes/2xxx/2017","/error/codes/2xxx/2023","/error/codes/2xxx/2025","/error/codes/2xxx/2026","/error/codes/2xxx/2028","/error/codes/2xxx/2029","/error/codes/2xxx/2030","/error/codes/2xxx/2031","/error/codes/2xxx/2032","/error/codes/2xxx/2033","/error/codes/2xxx/2034","/error/codes/2xxx/2040","/error/codes/2xxx/2041","/error/codes/2xxx/2042","/error/codes/3xxx/3006","/events/call-created","/events/call-ended","/events/call-updated","/events/chat-created","/events/chat-group-icon-updated","/events/chat-group-name-updated","/events/chat-typing-indicator-started","/events/chat-typing-indicator-stopped","/events/contact-added","/events/contact-removed","/events/index","/events/location-sharing-started","/events/location-sharing-stopped","/events/message-delivered","/events/message-failed","/events/message-read","/events/message-received","/events/message-sent","/events/participant-added","/events/participant-removed","/events/payment-canceled","/events/payment-expired","/events/payment-succeeded","/events/reaction-added","/events/reaction-removed","/events/task-canceled","/events/task-created","/events/task-message","/events/task-updated","/index","/integrations/agent-prompt","/integrations/chat-sdk","/integrations/claude-code","/integrations/cline","/integrations/cloudflare-think","/integrations/codex","/integrations/cursor","/integrations/gemini-cli","/integrations/hermes","/integrations/index","/integrations/mcp","/integrations/openclaw","/integrations/opencode","/integrations/pi","/integrations/skills","/integrations/vs-code","/integrations/your-own-backend","/interactions/buttons","/interactions/cards","/interactions/index","/interactions/payments","/interactions/selection","/live/authentication","/live/best-practices","/live/debugging","/live/errors","/live/examples","/live/idempotency","/live/rate-limits","/live/retries","/live/sdks","/messages/attachment-types","/messages/attachments","/messages/delete-attachments","/messages/import-media","/messages/index","/messages/mentions","/messages/message-details","/messages/parts","/messages/places","/messages/reactions","/messages/receipts","/messages/receiving-media","/messages/replies","/messages/rich-link-previews","/messages/send","/messages/voice-memos","/resources/migrate-from-linq","/resources/migrate-from-photon","/resources/migrate-from-telegram","/start/build-on-the-api","/start/quickstart","/tasks/accept-tasks","/tasks/index","/tasks/send-tasks","/webhooks/delivery","/webhooks/index","/webhooks/subscriptions","/webhooks/verify-signatures","/websocket/acknowledgements","/websocket/full-sync","/websocket/index","/websocket/observe-events","/websocket/protocol"]};
  // END GENERATED POSTHOG CONFIG

  if (window.location.origin !== CONFIG.origin || window.__relayDocsPostHog) return;
  if (navigator.doNotTrack === "1" || window.doNotTrack === "1") return;
  window.__relayDocsPostHog = true;

  const paths = new Set(CONFIG.paths);
  const environment = CONFIG.origin.includes(".staging.") ? "staging" : "production";
  // Only SDK identity/session and aggregate device fields cross this boundary.
  // No text, referrers, search terms, campaign values, API playground inputs,
  // arbitrary event properties, or initial URL/person properties are retained.
  const safeProperties = [
    "distinct_id", "$device_id", "$session_id", "$window_id", "$pageview_id",
    "$lib", "$lib_version", "$browser", "$browser_version", "$os", "$os_version",
    "$device_type", "$screen_height", "$screen_width", "$viewport_height",
    "$viewport_width", "$is_identified", "$process_person_profile",
  ];

  function pageviewOnly(event) {
    if (!event || event.event !== "$pageview") return null;
    let url;
    try {
      url = new URL(event.properties.$current_url);
    } catch {
      return null;
    }
    const pathname = url.pathname.replace(/\/+$/, "") || "/";
    if (url.origin !== CONFIG.origin || !paths.has(pathname)) return null;
    const properties = {
      token: CONFIG.token,
      $current_url: CONFIG.origin + pathname,
      $host: new URL(CONFIG.origin).host,
      $pathname: pathname,
      app: "relay-docs",
      analytics_source: "relay_docs",
      docs_analytics_schema_version: 1,
      environment,
    };
    for (const key of safeProperties) {
      const value = event.properties[key];
      if (["string", "number", "boolean"].includes(typeof value)) {
        properties[key] = value;
      }
    }
    // Reconstruct the envelope too: never forward arbitrary top-level data.
    return {
      event: "$pageview",
      properties,
      ...(event.uuid ? { uuid: event.uuid } : {}),
      ...(event.timestamp ? { timestamp: event.timestamp } : {}),
    };
  }

  function initialize() {
    // The previous Docs deployment wrote this project cookie on this host.
    // Remove only that obsolete host-only cookie (no Domain attribute), which
    // would otherwise shadow the shared Relay cookie during SDK initialization.
    // The SDK still owns identity: keep localStorage and the parent-domain
    // cookie intact; never copy, invent, or identify a user here.
    document.cookie = `ph_${CONFIG.token}_posthog=; Max-Age=0; Path=/; SameSite=Lax; Secure`;
    window.posthog.init(CONFIG.token, {
      api_host: "https://t.relayapp.im",
      ui_host: "https://us.posthog.com",
      defaults: "2026-05-30",
      capture_pageview: "history_change",
      capture_pageleave: false,
      autocapture: false,
      capture_dead_clicks: false,
      rageclick: false,
      capture_heatmaps: false,
      capture_performance: false,
      capture_exceptions: false,
      disable_session_recording: true,
      disable_surveys: true,
      advanced_disable_flags: true,
      // Share only this project's first-party Relay browser identity.
      // Auth/Console own identify/reset; the SDK synchronizes open tabs.
      // Keep persistence_name unset, including for this named SDK instance.
      persistence: "localStorage+cookie",
      cross_subdomain_cookie: true,
      cookieWinsOnConflict: true,
      person_profiles: "identified_only",
      respect_dnt: true,
      before_send: pageviewOnly,
    }, "relayDocs");
  }

  // array.js materializes window.posthog without initializing a project.
  // Use a named instance so a different Mintlify client is not reconfigured.
  if (window.posthog && typeof window.posthog.init === "function" && !window.posthog._i) {
    initialize();
  } else {
    const script = document.createElement("script");
    script.src = "https://t.relayapp.im/static/array.js";
    script.async = true;
    script.crossOrigin = "anonymous";
    script.referrerPolicy = "no-referrer";
    script.onload = initialize;
    script.onerror = () => { window.__relayDocsPostHog = false; };
    document.head.appendChild(script);
  }
})();

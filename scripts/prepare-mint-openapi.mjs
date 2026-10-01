#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { readFile, writeFile } from "node:fs/promises";

const path = new URL("../api-reference/openapi.mint.yaml", import.meta.url);
const input = await readFile(path, "utf8");
const pagePaths = JSON.parse(await readFile(new URL("./api-page-paths.json", import.meta.url), "utf8"));
let output = input;
const webhooks = output.search(/^webhooks:\s*$/m);
const components = output.search(/^components:\s*$/m);

if (webhooks >= 0) {
  if (components < 0 || components <= webhooks) {
    throw new Error("Expected top-level webhooks before components in the Mintlify bundle.");
  }
  output = `${output.slice(0, webhooks)}${output.slice(components)}`;
}

const sidebarTitles = {
  getMe: "Get owner",
  listAgentAccess: "List access",
  setAgentAccess: "Set access",
  removeAgentAccess: "Remove access",
  getOAuth2Client: "Get OAuth2 client",
  createOAuth2Client: "Create OAuth2 client",
  updateOAuth2Client: "Update OAuth2 client",
  resetOAuth2ClientSecret: "Reset client secret",
  deleteAgent: "Delete",
  createChat: "Create",
  listChats: "List",
  getChat: "Retrieve",
  updateChat: "Update",
  addParticipant: "Add",
  removeParticipant: "Remove",
  leaveChat: "Leave",
  getActivity: "Get activity",
  setActivity: "Set activity",
  clearActivity: "Clear activity",
  requestLocation: "Request location",
  getLocation: "Get location",
  startTyping: "Start",
  stopTyping: "Stop",
  markChatAsRead: "Mark read",
  shareContactWithChat: "Share contact card",
  sendMessage: "Send",
  sendMessageToChat: "Send",
  getMessages: "List",
  getMessageThread: "List",
  sendVoiceMemoToChat: "Send voice memo",
  getMessage: "Retrieve",
  sendReaction: "Update",
  requestUpload: "Create",
  getAttachment: "Retrieve",
  deleteAttachment: "Delete",
  listBlockedHandles: "List",
  blockHandle: "Block",
  unblockHandle: "Unblock",
  listWebhookEvents: "List",
  createWebhookSubscription: "Create",
  listWebhookSubscriptions: "List",
  getWebhookSubscription: "Retrieve",
  updateWebhookSubscription: "Update",
  deleteWebhookSubscription: "Delete",
  getContactCard: "Retrieve",
  lookupContact: "Look up",
  listDirectory: "List public agents",
  rateAgent: "Rate",
  deleteAgentRating: "Remove rating",
  listAgentRatings: "List ratings",
  countAgentsInAddressBook: "Count agents your contacts use",
  listSuggestedAgents: "List suggested agents",
  requestAgent: "Ask for an agent",
  setupContactCard: "Create",
  updateContactCard: "Update",
  connectAgentWebSocket: "Connect",
  createCall: "Start",
  listCalls: "List",
  getCall: "Retrieve",
  connectCallRoom: "Join room",
  endCall: "End",
  createPaymentRequest: "Create",
  listPaymentRequests: "List",
  getPaymentRequest: "Retrieve",
  cancelPaymentRequest: "Cancel",
};

// Person-only routes leave the bundle whole, so Mintlify builds no page for
// them. scripts/api_navigation.py owns the list and the cut.
const scripts = new URL(".", import.meta.url).pathname;
const python = (code, input) =>
  execFileSync("python3", ["-c", `import sys; sys.path.insert(0, sys.argv[1]); ${code}`, scripts], { input, maxBuffer: 1 << 27 }).toString();
const hiddenOperations = new Set(JSON.parse(python("import json; from api_navigation import HIDDEN_OPERATIONS; print(json.dumps(sorted(HIDDEN_OPERATIONS)))", "")));
output = python("from api_navigation import strip_hidden_paths; sys.stdout.write(strip_hidden_paths(sys.stdin.read()))", output);

for (const [operationId, sidebarTitle] of Object.entries(sidebarTitles)) {
  if (hiddenOperations.has(operationId)) continue;
  const marker = `      operationId: ${operationId}`;
  const markerPattern = new RegExp(`^${marker}$`, "gm");
  const matches = output.match(markerPattern)?.length ?? 0;
  if (matches !== 1) {
    throw new Error(`Expected one ${operationId} operation, found ${matches}.`);
  }
  if (!pagePaths[operationId]?.href) {
    throw new Error(`Missing stable page URL for ${operationId}.`);
  }
  output = output.replace(
    markerPattern,
    `${marker}
      x-mint:
        metadata:
          sidebarTitle: ${sidebarTitle}
        href: ${pagePaths[operationId].href}`,
  );
}

await writeFile(path, output);
console.log("Mintlify bundle keeps HTTP endpoints with concise sidebar titles");

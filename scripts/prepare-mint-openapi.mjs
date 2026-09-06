#!/usr/bin/env node

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
  createChat: "Create",
  listChats: "List",
  getChat: "Retrieve",
  updateChat: "Update",
  addParticipant: "Add",
  removeParticipant: "Remove",
  leaveChat: "Leave",
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
  editMessage: "Edit",
  unsendMessage: "Unsend",
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
  setupContactCard: "Create",
  updateContactCard: "Update",
  connectAgentWebSocket: "Connect",
  createContactRequest: "Request",
};

for (const [operationId, sidebarTitle] of Object.entries(sidebarTitles)) {
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

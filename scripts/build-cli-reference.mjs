#!/usr/bin/env node
// Read help only. Never run a resource command without --help.
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import { createRequire } from 'node:module';

const root = fileURLToPath(new URL('../', import.meta.url));
const check = process.argv.includes('--check');
const require = createRequire(import.meta.url);
const cli = process.env.CLI_REFERENCE_BIN || require.resolve('relaymessenger/dist/cli.js');
const programModule = await import(pathToFileURL(require.resolve('relaymessenger/dist/program.js')).href);
const directory = path.join(root, 'cli/reference');
const tick = '`';
const fence = tick.repeat(3);

function help(args) {
  const result = spawnSync(process.execPath, [cli, '--agent', 'no', ...args], {
    cwd: root, encoding: 'utf8', env: { ...process.env, NO_COLOR: '1', FORCE_COLOR: '0' },
    timeout: 30000, maxBuffer: 1024 * 1024,
  });
  if (result.error || result.status !== 0) throw new Error(`Help failed for ${args.join(' ')}: ${result.error || result.stderr}`);
  return result.stdout.replace(/\r\n/g, '\n').trimEnd();
}

const rootHelp = help(['--help']);
if (!/^VERSION\n/m.test(rootHelp) || !/^USAGE\n/m.test(rootHelp) || !/^TOPICS\n/m.test(rootHelp) || !/^COMMANDS\n/m.test(rootHelp)) {
  throw new Error('Root help must contain VERSION, USAGE, TOPICS, and COMMANDS sections');
}
if (/^Options:\n/m.test(rootHelp)) throw new Error('Root help must not contain an Options section');
const exitCodes = help(['help', 'exit-codes']);

const program = programModule.createProgram({ configContext: { env: {} } });
const helper = program.createHelp();
const globalOptions = program.options
  .map((option) => helper.formatItem(
    helper.optionTerm(option),
    helper.padWidth(program, helper),
    helper.optionDescription(option),
    helper,
  ))
  .join('\n');

function commandAt(pathParts) {
  let command = program;
  for (const part of pathParts) {
    command = command.commands.find((candidate) => candidate.name() === part);
    if (!command) throw new Error(`Source command not found: ${pathParts.join(' ')}`);
  }
  return command;
}

function supportedChildren(command) {
  return command.commands.filter((child) =>
    child.name() !== 'exit-codes'
    && !(command === program && child.name() === 'events')
  );
}

const TITLES = {
  "agents-create": "Create an agent",
  "agents-list": "List agents",
  "agents-delete": "Delete an agent",
  "auth-login": "Save a token",
  "auth-status": "Check the token",
  "auth-logout": "Remove the token",
  "login": "Log in with a token",
  "logout": "Log out",
  "whoami": "Show the identity",
  "profiles-add": "Add a profile",
  "profiles-use": "Choose the default profile",
  "profiles-remove": "Remove a profile",
  "profiles-list": "List profiles",
  "chats-list": "List chats",
  "chats-get": "Show a chat",
  "chats-create": "Create a chat",
  "chats-update": "Rename a group",
  "chats-leave": "Leave a chat",
  "chats-read": "Mark a chat as read",
  "chats-voice-memo": "Send a voice memo",
  "chats-messages-list": "List messages",
  "chats-messages-send": "Send to a chat",
  "chats-participants-add": "Add a participant",
  "chats-participants-remove": "Remove a participant",
  "chats-typing-start": "Start typing",
  "chats-typing-stop": "Stop typing",
  "messages-send": "Send to handles",
  "messages-get": "Show a message",
  "messages-thread": "List replies",
  "messages-react": "React to a message",
  "attachments-allocate": "Reserve an upload",
  "attachments-upload": "Upload a file",
  "attachments-get": "Show an attachment",
  "attachments-delete": "Delete an attachment",
  "blocked-handles-list": "List blocked handles",
  "blocked-handles-add": "Block a handle",
  "blocked-handles-remove": "Unblock a handle",
  "webhooks-events": "List event types",
  "listen": "Forward events locally",
  "webhooks-subscriptions-list": "List subscriptions",
  "webhooks-subscriptions-get": "Show a subscription",
  "webhooks-subscriptions-create": "Create a subscription",
  "webhooks-subscriptions-update": "Update a subscription",
  "webhooks-subscriptions-delete": "Delete a subscription",
  "contact-card-get": "Show the contact card",
  "contact-card-setup": "Set up the contact card",
  "contact-card-update": "Update the contact card",
  "contact-card-share": "Share the contact card",
  "docs": "Print the docs",
  "config-path": "Print the config path",
  "help": "Help"
};

const CLI_GROUPS = [
  {
    "group": "Getting started",
    "pages": [
      "cli/index",
      "cli/connect",
      "cli/watch",
      "cli/global-options"
    ]
  },
  {
    "group": "Agents",
    "pages": [
      "cli/agents",
      "cli/reference/agents-create",
      "cli/reference/agents-list",
      "cli/reference/agents-delete"
    ]
  },
  {
    "group": "Tokens",
    "pages": [
      "cli/auth",
      "cli/reference/auth-login",
      "cli/reference/auth-status",
      "cli/reference/auth-logout",
      "cli/reference/login",
      "cli/reference/logout",
      "cli/reference/whoami",
      {
        "group": "Profiles",
        "pages": [
          "cli/reference/profiles-add",
          "cli/reference/profiles-use",
          "cli/reference/profiles-remove",
          "cli/reference/profiles-list"
        ]
      }
    ]
  },
  {
    "group": "Chats",
    "pages": [
      "cli/reference/chats-list",
      "cli/reference/chats-get",
      "cli/reference/chats-create",
      "cli/reference/chats-update",
      "cli/reference/chats-leave",
      "cli/reference/chats-read",
      "cli/reference/chats-voice-memo",
      {
        "group": "Messages in a chat",
        "pages": [
          "cli/reference/chats-messages-list",
          "cli/reference/chats-messages-send"
        ]
      },
      {
        "group": "Participants",
        "pages": [
          "cli/reference/chats-participants-add",
          "cli/reference/chats-participants-remove"
        ]
      },
      {
        "group": "Typing",
        "pages": [
          "cli/reference/chats-typing-start",
          "cli/reference/chats-typing-stop"
        ]
      }
    ]
  },
  {
    "group": "Messages",
    "pages": [
      "cli/reference/messages-send",
      "cli/reference/messages-get",
      "cli/reference/messages-thread",
      "cli/reference/messages-react"
    ]
  },
  {
    "group": "Attachments",
    "pages": [
      "cli/reference/attachments-allocate",
      "cli/reference/attachments-upload",
      "cli/reference/attachments-get",
      "cli/reference/attachments-delete"
    ]
  },
  {
    "group": "Blocked handles",
    "pages": [
      "cli/reference/blocked-handles-list",
      "cli/reference/blocked-handles-add",
      "cli/reference/blocked-handles-remove"
    ]
  },
  {
    "group": "Webhooks",
    "pages": [
      "cli/reference/webhooks-events",
      "cli/reference/listen",
      {
        "group": "Subscriptions",
        "pages": [
          "cli/reference/webhooks-subscriptions-list",
          "cli/reference/webhooks-subscriptions-get",
          "cli/reference/webhooks-subscriptions-create",
          "cli/reference/webhooks-subscriptions-update",
          "cli/reference/webhooks-subscriptions-delete"
        ]
      }
    ]
  },
  {
    "group": "Contact card",
    "pages": [
      "cli/reference/contact-card-get",
      "cli/reference/contact-card-setup",
      "cli/reference/contact-card-update",
      "cli/reference/contact-card-share"
    ]
  },
  {
    "group": "Tools",
    "pages": [
      "cli/doctor",
      "cli/reference/docs",
      "cli/reference/config-path",
      "cli/reference/help"
    ]
  }
];

const pages = new Map();
function collect(commandPath) {
  const command = commandPath[0] === 'help' ? program._helpCommand : commandAt(commandPath);
  if (commandPath[0] !== 'help' && command.commands.length) {
    for (const child of supportedChildren(command)) collect([...commandPath, child.name()]);
    return;
  }
  if (!commandPath.length || ['connect', 'watch', 'doctor'].includes(commandPath[0])) return;
  const text = commandPath.length ? help([...commandPath, '--help']) : rootHelp;
  if (commandPath.length && commandPath[0] !== 'help' && !text.startsWith('Usage: relaymessenger')) {
    throw new Error(`Unexpected help for ${commandPath.join(' ')}`);
  }
  const slug = commandPath.length ? commandPath.join('-') : 'index';
  if (pages.has(slug)) throw new Error(`Duplicate command slug ${slug}`);
  const title = TITLES[slug];
  if (!title) throw new Error(`Missing CLI title for ${slug}`);
  const invocation = ['relaymessenger', ...commandPath].join(' ');
  const rawDescription = command.description();
  const description = rawDescription.charAt(0).toUpperCase() + rawDescription.slice(1).replace(/[.]+$/, '') + '.';
  const options = text.split('\nOptions:\n')[1]?.split('\n\n')[0];
  const optionsSection = commandPath.length && commandPath[0] !== 'help'
    ? `## Options\n\n${options ? `${fence}text captured-output\n${options}\n${fence}` : 'This command lists its subcommands in Usage.'}\n\n### Global options\n\n${fence}text captured-output\n${globalOptions}\n${fence}\n\n`
    : '';
  const content = `---\ntitle: ${JSON.stringify(title)}\ndescription: ${JSON.stringify(description)}\nkeywords: ${JSON.stringify(['CLI', ...commandPath, 'command reference'])}\n---\n\n${description}\n\n${fence}bash\nnpx ${invocation}\n${fence}\n\n{/* Generated by scripts/build-cli-reference.mjs. Do not edit by hand. */}\n\n## Usage\n\n${fence}text captured-output\n${text}\n${fence}\n\n${optionsSection}## Exit codes\n\n${fence}text captured-output\n${exitCodes}\n${fence}\n\n## Next steps\n\n- [CLI](/cli/index)\n- [Global options](/cli/global-options)\n`;
  pages.set(slug, content);
}
collect([]);
collect(['help']);

function commandTree() {
  const topicNames = [];
  const commandNames = [];
  let current;
  for (const line of rootHelp.split('\n')) {
    if (/^TOPICS$/.test(line)) current = 'topics';
    else if (/^COMMANDS$/.test(line)) current = 'commands';
    else if (/^(?:Docs:|$)/.test(line)) continue;
    else if (current && /^  ([a-z][a-z-]*)\s{2,}/.test(line)) {
      const name = line.match(/^  ([a-z][a-z-]*)\s{2,}/)[1];
      (current === 'topics' ? topicNames : commandNames).push(name);
    }
  }
  const sourceNames = program.commands
    .filter((command) => command.helpGroup() !== '' && command.name() !== 'exit-codes')
    .map((command) => command.name());
  const names = [...new Set([...topicNames, ...commandNames, ...sourceNames])]
    .filter((name) => name !== 'help');
  names.push('help');
  const lines = ['relaymessenger'];
  const add = (command, prefix, isLast, commandPath) => {
    const term = commandPath.length ? helper.subcommandTerm(command) : command.name();
    const description = command.description();
    lines.push(`${prefix}${isLast ? '└── ' : '├── '}${term.padEnd(Math.max(34, term.length + 2))}${description}`);
    const children = supportedChildren(command);
    children.forEach((child, index) => add(child, `${prefix}${isLast ? '    ' : '│   '}`, index === children.length - 1, [...commandPath, child.name()]));
  };
  names.forEach((name, index) => {
    if (name === 'help') {
      lines.push(`${index === names.length - 1 ? '└── ' : '├── '}help [command]`.padEnd(39) + 'show what a command does and the options it takes');
      return;
    }
    const command = program.commands.find((candidate) => candidate.name() === name);
    if (command) add(command, '', index === names.length - 1, [name]);
  });
  return lines.join('\n');
}

const navigation = JSON.parse(readFileSync(path.join(root, 'docs.json'), 'utf8'));
const tab = navigation.navigation.tabs.find((candidate) => candidate.tab === 'CLI');
if (!tab) throw new Error('CLI navigation tab not found');
tab.groups = CLI_GROUPS;
// Preserve incoming links to the removed command-family pages.
const redirects = [
  {
    "source": "/cli/reference/agents",
    "destination": "/cli/reference/agents-create",
    "permanent": true
  },
  {
    "source": "/cli/reference/attachments",
    "destination": "/cli/reference/attachments-allocate",
    "permanent": true
  },
  {
    "source": "/cli/reference/auth",
    "destination": "/cli/reference/auth-login",
    "permanent": true
  },
  {
    "source": "/cli/reference/blocked-handles",
    "destination": "/cli/reference/blocked-handles-list",
    "permanent": true
  },
  {
    "source": "/cli/reference/chats",
    "destination": "/cli/reference/chats-list",
    "permanent": true
  },
  {
    "source": "/cli/reference/chats-messages",
    "destination": "/cli/reference/chats-messages-list",
    "permanent": true
  },
  {
    "source": "/cli/reference/chats-participants",
    "destination": "/cli/reference/chats-participants-add",
    "permanent": true
  },
  {
    "source": "/cli/reference/chats-typing",
    "destination": "/cli/reference/chats-typing-start",
    "permanent": true
  },
  {
    "source": "/cli/reference/connect",
    "destination": "/cli/connect",
    "permanent": true
  },
  {
    "source": "/cli/reference/contact-card",
    "destination": "/cli/reference/contact-card-get",
    "permanent": true
  },
  {
    "source": "/cli/reference/doctor",
    "destination": "/cli/doctor",
    "permanent": true
  },
  {
    "source": "/cli/reference/index",
    "destination": "/cli/index",
    "permanent": true
  },
  {
    "source": "/cli/reference/messages",
    "destination": "/cli/reference/messages-send",
    "permanent": true
  },
  {
    "source": "/cli/reference/profiles",
    "destination": "/cli/reference/profiles-add",
    "permanent": true
  },
  {
    "source": "/cli/reference/watch",
    "destination": "/cli/watch",
    "permanent": true
  },
  {
    "source": "/cli/reference/webhooks",
    "destination": "/cli/reference/webhooks-events",
    "permanent": true
  },
  {
    "source": "/cli/reference/webhooks-subscriptions",
    "destination": "/cli/reference/webhooks-subscriptions-list",
    "permanent": true
  }
];
for (const redirect of redirects) {
  const existing = navigation.redirects.findIndex((entry) => entry.source === redirect.source);
  if (existing === -1) navigation.redirects.push(redirect);
  else navigation.redirects[existing] = redirect;
}

const overview = `---
title: "CLI"
sidebarTitle: "Introduction"
description: "Connect and manage an agent from your terminal."
keywords: ["CLI", "relaymessenger", "command reference"]
---

Connect and manage an agent from your terminal.

Use Node.js 22.22.3 or newer.

## Install

${fence}bash
npm install --global relaymessenger@0.1.6-staging.37
npx relaymessenger@0.1.6-staging.37 --help
${fence}

Run ${tick}npx relaymessenger@0.1.6-staging.37 <command> --help${tick} for one command's options. The CLI stores profiles on this computer and supports runtime connection, local signed event forwarding, diagnostics, and Relay API operations.

Use ${tick}--json${tick} for machine-readable results. [Create an agent](/agents/create-agent), [list agents](/agents/list-agents), or [delete an agent](/agents/delete-agent) from the CLI.

## Command tree

${fence}text command-tree
${commandTree()}
${fence}

[Connect a runtime](/integrations/claude-code) · [Install Relay guidance](/integrations/skills)

Source: [Relay-SDK CLI](https://github.com/RelayMessenger/Relay-SDK/tree/staging/packages/cli).

## When it fails

| Exit | Meaning |
| --- | --- |
| 0 | Command succeeded. |
| 1 | The command failed for a reason outside the classified cases. |
| 2 | The command needs input that was not available, or the options were invalid. |
| 3 | The named Relay resource does not exist. |
| 4 | The Agent Token is missing or was rejected. |

With ${tick}--json${tick}, failures use an object with ${tick}error${tick}, ${tick}code${tick}, and ${tick}next_step${tick}.

## Next steps

- [Connect](/cli/connect)
- [Watch](/cli/watch)
- [Authentication](/cli/auth)
`;

const outputs = new Map([...pages].map(([slug, content]) => [path.join(directory, `${slug}.mdx`), content]));
outputs.set(path.join(root, 'cli/index.mdx'), overview);
outputs.set(path.join(root, 'docs.json'), JSON.stringify(navigation, null, 2) + '\n');
const stale = existsSync(directory) ? readdirSync(directory).filter((name) => name.endsWith('.mdx') && !pages.has(name.slice(0, -4))) : [];
if (stale.length) throw new Error(`Stale generated pages require explicit removal: ${stale.join(', ')}`);
const changed = [...outputs].filter(([file, content]) => !existsSync(file) || readFileSync(file, 'utf8') !== content);
if (check && changed.length) {
  console.error(`CLI reference differs in ${changed.length} files:\n${changed.map(([file]) => path.relative(root, file)).join('\n')}`);
  process.exitCode = 1;
} else if (!check) {
  mkdirSync(directory, { recursive: true });
  for (const [file, content] of changed) writeFileSync(file, content);
}
console.log(`CLI reference: ${pages.size} pages; ${changed.length} ${check ? 'differences' : 'files written'}.`);
